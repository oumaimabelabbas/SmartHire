"""Service d'extraction de CV depuis PDF."""

import hashlib
import logging
import re
import time
from typing import Any, Dict, Optional

import PyPDF2

from config import settings
from models.cv_model import EducationDTO, ExperienceDTO, ExtractedCVDTO, LanguageDTO
from services.embedding_service import EmbeddingService
from services.error_handling import (
    CVExtractionError,
    handle_llm_error,
    log_extraction_attempt,
    retry_with_backoff,
    validate_extracted_cv,
)
from services.llm_client import LLMClient, LLMServiceError
from services.skill_store import SkillStore
from services.text_chunker import TextChunker
from services.vector_store import LocalVectorStore
from services.extraction_metrics import extraction_metrics

logger = logging.getLogger(__name__)


class CVExtractor:
    """Extrait les donnees structurees d un CV PDF avec pipeline LLM + fallback regex."""

    _vector_store = LocalVectorStore()
    _skill_store = SkillStore()

    @staticmethod
    def extract_from_pdf(pdf_bytes: bytes, filename: str = "CV.pdf") -> ExtractedCVDTO:
        """
        Extraire un CV depuis un fichier PDF.

        Args:
            pdf_bytes: Contenu du fichier PDF
            filename: Nom du fichier (pour logging)

        Returns:
            ExtractedCVDTO avec données structurées

        Raises:
            CVExtractionError: Si extraction échoue complètement
        """
        start_time = time.time()
        extraction_mode = "unknown"
        cv = ExtractedCVDTO()

        try:
            logger.info(f"🔍 Début extraction CV: {filename}")

            # Étape 1 : Extraire texte du PDF
            text = CVExtractor._extract_pdf_text(pdf_bytes)
            if not text.strip():
                logger.warning(f"⚠️  PDF vide ou sans texte: {filename}")
                log_extraction_attempt(
                    cv_id=None,
                    filename=filename,
                    success=False,
                    duration_seconds=time.time() - start_time,
                    mode="pdf_empty"
                )
                return ExtractedCVDTO()

            # Étape 2 : Essayer extraction LLM
            llm_payload: Optional[Dict[str, Any]] = None
            llm_error: Optional[str] = None

            try:
                logger.debug("📡 Appel API LLM pour extraction JSON...")
                llm_payload = CVExtractor._extract_with_llm_retry(text)
                extraction_mode = "llm_json"
                logger.debug("✅ Extraction LLM réussie")

            except LLMServiceError as exc:
                should_retry, error_msg = handle_llm_error(exc, "extraction CV")
                llm_error = error_msg

                if should_retry:
                    logger.info("⚠️  LLM extraction a échoué, passage au fallback regex")
                else:
                    logger.error(f"❌ LLM extraction fatale: {error_msg}")

            # Étape 3 : Construire CV
            if llm_payload:
                try:
                    cv = CVExtractor._build_cv_from_llm(llm_payload, text)
                    logger.debug(f"✅ CV construit à partir LLM: {cv.nom}")
                except Exception as e:
                    logger.warning(f"⚠️  Erreur parsing réponse LLM: {e}, fallback regex")
                    cv = CVExtractor._build_cv_from_regex(text)
                    extraction_mode = "regex_after_llm_error"
            else:
                logger.info("📋 Utilisation extraction regex")
                cv = CVExtractor._build_cv_from_regex(text)
                extraction_mode = "regex_fallback"

            # Étape 4 : Générer ID et indexer
            cv.cv_id = CVExtractor._generate_cv_id(text, cv.email, cv.nom)
            CVExtractor._index_cv_chunks(cv.cv_id, text, cv.nom)
            CVExtractor._persist_structured_skills(cv)

            # Validation
            is_valid, validation_errors = validate_extracted_cv(cv.model_dump())
            if not is_valid:
                logger.warning(f"⚠️  CV extraction avec warnings: {', '.join(validation_errors)}")

            duration = time.time() - start_time
            log_extraction_attempt(
                cv_id=cv.cv_id,
                filename=filename,
                success=True,
                duration_seconds=duration,
                mode=extraction_mode,
                details={"technologies_count": len(cv.technologies), "skills_count": len(cv.competences)}
            )

            # Enregistrer les métriques
            extraction_metrics.record_extraction(
                cv_id=cv.cv_id or "unknown",
                filename=filename,
                mode=extraction_mode,
                success=True,
                duration_seconds=duration,
                technologies_count=len(cv.technologies),
                skills_count=len(cv.competences),
                experiences_count=len(cv.experiences)
            )

            logger.info(
                f"✅ CV extrait: {cv.nom} [{extraction_mode}] "
                f"({len(cv.technologies)} techs, {len(cv.competences)} skills) - {duration:.2f}s"
            )
            return cv

        except Exception as exc:
            duration = time.time() - start_time
            logger.error(f"❌ Extraction échouée: {str(exc)}", exc_info=True)

            log_extraction_attempt(
                cv_id=None,
                filename=filename,
                success=False,
                duration_seconds=duration,
                mode="extraction_failed",
                details={"error": str(exc), "fallback_reason": llm_error}
            )

            # Enregistrer échec des métriques
            from services.error_handling import classify_error
            error_category = classify_error(exc)
            extraction_metrics.record_extraction(
                cv_id="unknown",
                filename=filename,
                mode="extraction_failed",
                success=False,
                duration_seconds=duration,
                error_category=error_category
            )

            # Retourner quand même un CV vide plutôt que de lever
            return ExtractedCVDTO()

    @staticmethod
    @retry_with_backoff(max_retries=2, base_delay=1.0, max_delay=10.0)
    def _extract_with_llm_retry(text: str) -> Dict[str, Any]:
        """
        Extraire JSON LLM avec retry et gestion d'erreurs.

        Args:
            text: Texte brut du CV

        Returns:
            Dict JSON structuré

        Raises:
            LLMServiceError: Si extraction échoue
        """
        try:
            return LLMClient.extract_cv_json(text)
        except Exception as e:
            category = handle_llm_error(e, "extraction JSON")[0]
            if category:  # should_retry
                raise LLMServiceError(f"Retryable LLM error: {str(e)}") from e
            raise

    @staticmethod
    def _extract_pdf_text(pdf_bytes: bytes) -> str:
        pdf_reader = PyPDF2.PdfReader(open_pdf_from_bytes(pdf_bytes))
        pages = []
        for page in pdf_reader.pages:
            pages.append(page.extract_text() or "")
        return "\n".join(pages)

    @staticmethod
    def _build_cv_from_regex(text: str) -> ExtractedCVDTO:
        cv = ExtractedCVDTO()
        cv.nom = extract_name(text)
        cv.email = extract_email(text)
        cv.telephone = extract_phone(text)
        cv.competences = extract_skills(text)
        cv.technologies = extract_technologies(text)
        cv.experiences = extract_experiences(text)
        cv.educations = extract_educations(text)
        cv.langues = extract_languages(text)
        cv.annees_experience = calculate_experience_years(cv.experiences)
        cv.resume = text[:1000]
        return cv

    @staticmethod
    def _build_cv_from_llm(payload: Dict[str, Any], text: str) -> ExtractedCVDTO:
        experiences = []
        for item in payload.get("experiences", []) or []:
            if isinstance(item, dict):
                experiences.append(
                    ExperienceDTO(
                        titre=str(item.get("titre") or ""),
                        entreprise=str(item.get("entreprise") or ""),
                        duree_mois=to_int(item.get("duree_mois")),
                        description=item.get("description"),
                        technologies=to_str_list(item.get("technologies")),
                    )
                )

        educations = []
        for item in payload.get("educations", []) or []:
            if isinstance(item, dict):
                educations.append(
                    EducationDTO(
                        diplome=str(item.get("diplome") or ""),
                        etablissement=str(item.get("etablissement") or ""),
                        annee=to_int(item.get("annee")),
                        specialisation=item.get("specialisation"),
                    )
                )

        langues = []
        for item in payload.get("langues", []) or []:
            if isinstance(item, dict):
                langues.append(
                    LanguageDTO(
                        nom=str(item.get("nom") or ""),
                        niveau=str(item.get("niveau") or "Intermediaire"),
                    )
                )

        return ExtractedCVDTO(
            nom=payload.get("nom") or extract_name(text),
            email=payload.get("email") or extract_email(text),
            telephone=payload.get("telephone") or extract_phone(text),
            resume=(payload.get("resume") or text[:1000]),
            experiences=experiences,
            educations=educations,
            competences=to_str_list(payload.get("competences")),
            technologies=to_str_list(payload.get("technologies")),
            langues=langues,
            annees_experience=to_int(payload.get("annees_experience"))
            or calculate_experience_years(experiences),
        )

    @staticmethod
    def _generate_cv_id(text: str, email: Optional[str], name: Optional[str]) -> str:
        raw = f"{email or ''}|{name or ''}|{len(text)}|{text[:200]}"
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def _index_cv_chunks(cv_id: str, text: str, name: Optional[str]) -> None:
        chunks = TextChunker.chunk_text(
            text,
            chunk_size_words=settings.CHUNK_SIZE_WORDS,
            overlap_words=settings.CHUNK_OVERLAP_WORDS,
        )
        if not chunks:
            return

        vectors = EmbeddingService.embed_texts(chunks)
        CVExtractor._vector_store.upsert_chunks(
            doc_id=cv_id,
            chunks=chunks,
            vectors=vectors,
            metadata={"source": "cv", "candidate_name": name or "Unknown"},
        )

    @staticmethod
    def _persist_structured_skills(cv: ExtractedCVDTO) -> None:
        if not cv.cv_id:
            return
        CVExtractor._skill_store.save_cv_profile(
            cv.cv_id,
            {
                "nom": cv.nom,
                "email": cv.email,
                "technologies": cv.technologies,
                "competences": cv.competences,
                "annees_experience": cv.annees_experience,
            },
        )

def open_pdf_from_bytes(pdf_bytes: bytes):
    """Convertir bytes en fichier PDF"""
    from io import BytesIO
    return BytesIO(pdf_bytes)

def extract_name(text: str) -> Optional[str]:
    """Extraire le nom (généralement en haut du CV)"""
    lines = text.split('\n')
    # Prendre les premières lignes non vides
    for line in lines[:5]:
        line = line.strip()
        if line and len(line) > 2:
            return line
    return None

def extract_email(text: str) -> Optional[str]:
    """Extraire email avec regex"""
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(pattern, text)
    return match.group(0) if match else None

def extract_phone(text: str) -> Optional[str]:
    """Extraire numéro téléphone"""
    pattern = r'(\+?\d{1,3}[-.\s]?)?\d{9,15}'
    match = re.search(pattern, text)
    return match.group(0) if match else None

def extract_skills(text: str) -> list[str]:
    """Extraire compétences transversales"""
    skills_keywords = [
        "Leadership", "Gestion de projet", "Communication", "Travail en équipe",
        "Autonomie", "Rigueur", "Organisation", "Créativité", "Analyse",
        "Problem-solving", "Mentoring", "Résolution de conflits", "Scalabilité",
        "Agile", "Scrum", "Kanban"
    ]

    found_skills = []
    text_lower = text.lower()

    for skill in skills_keywords:
        if skill.lower() in text_lower:
            found_skills.append(skill)

    return found_skills

def extract_technologies(text: str) -> list[str]:
    """Extraire technologies/langages de programmation"""
    techs = [
        "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust",
        "PHP", "Ruby", "Kotlin", "Swift", "Objective-C",
        "Spring Boot", "Django", "Flask", "FastAPI", "Express.js", "React",
        "Vue.js", "Angular", "Next.js", "Svelte",
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "Cassandra", "ElasticSearch",
        "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Terraform",
        "Git", "CI/CD", "Jenkins", "GitLab CI", "GitHub Actions",
        "Microservices", "REST API", "GraphQL", "gRPC"
    ]

    found_techs = []
    for tech in techs:
        if tech in text:
            found_techs.append(tech)

    return found_techs

def extract_experiences(text: str) -> list[ExperienceDTO]:
    """Extraire expériences professionnelles"""
    experiences = []

    # Regex pour chercher sections "Expérience" ou "Professionnel"
    exp_section = re.search(r'(?:expérience|professionnel|career)(.*?)(?:éducation|formation|education|skills|competences)',
                            text, re.IGNORECASE | re.DOTALL)

    if exp_section:
        exp_text = exp_section.group(1)
        # Chercher patterns comme "Titre at Entreprise"
        pattern = r'([^•\n]+)\s+(?:at|@|chez|à)\s+([^•\n]+)'
        matches = re.finditer(pattern, exp_text, re.IGNORECASE)

        for match in matches:
            exp = ExperienceDTO(
                titre=match.group(1).strip(),
                entreprise=match.group(2).strip()
            )
            experiences.append(exp)

    return experiences

def extract_educations(text: str) -> list[EducationDTO]:
    """Extraire formations/diplômes"""
    educations = []

    edu_section = re.search(r'(?:éducation|formation|education)(.*?)(?:skills|competences|experience)',
                           text, re.IGNORECASE | re.DOTALL)

    if edu_section:
        edu_text = edu_section.group(1)
        # Chercher diplômes
        degrees = ["Master", "Bachelor", "Licence", "Diplôme", "Certificat", "BTS"]
        for degree in degrees:
            if degree in edu_text:
                edu = EducationDTO(
                    diplome=degree,
                    etablissement="Université/École"
                )
                educations.append(edu)

    return educations

def extract_languages(text: str) -> list[LanguageDTO]:
    """Extraire langues maîtrisées"""
    languages = []

    lang_keywords = ["Français", "Anglais", "Espagnol", "Allemand", "Chinois", "Japonais"]
    levels = ["Natif", "Courant", "Intermédiaire", "Débutant", "Fluent", "Native"]

    for lang in lang_keywords:
        if lang in text:
            # Chercher le niveau
            level = "Intermédiaire"
            for lv in levels:
                if lv in text:
                    level = lv
                    break

            languages.append(LanguageDTO(nom=lang, niveau=level))

    return languages

def calculate_experience_years(experiences: list[ExperienceDTO]) -> int:
    """Calculer années d'expérience totales"""
    if not experiences:
        return 0
    return len(experiences)  # Approximation simple


def to_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def to_int(value: Any) -> Optional[int]:
    try:
        if value is None or value == "":
            return None
        return int(value)
    except Exception:
        return None


