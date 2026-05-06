"""True LLM-RAG scoring service (retrieval + generation)."""

import logging
import re
from typing import Any, Dict, List

from config import settings
from models.cv_model import ExtractedCVDTO
from models.offer_model import NormalizedOfferDTO
from services.embedding_service import EmbeddingService
from services.llm_client import LLMClient, LLMServiceError
from services.text_chunker import TextChunker
from services.vector_store import LocalVectorStore

logger = logging.getLogger(__name__)


class CVScoringService:
    """Score CV/offre using vector retrieval + Gemini LLM judgment."""

    _vector_store = LocalVectorStore()
    _CHATBOT_MAX_ANSWER_CHARS = 160
    _CHATBOT_MAX_ITEMS = 3
    _CHATBOT_ACTION_ITEMS = 2
    _DIAGNOSTIC_MAX_CHARS = 190
    _SENSITIVE_ERROR_PATTERNS = [
        re.compile(r"([?&]key=)[^&\s]+", re.IGNORECASE),
        re.compile(r"(gemini[_-]?api[_-]?key\s*[=:]\s*)[^\s,;]+", re.IGNORECASE),
        re.compile(r"AIza[0-9A-Za-z_\-]{20,}"),
        re.compile(r"AQ\.[0-9A-Za-z_\-\.]{10,}"),
    ]

    @staticmethod
    def score_cv_vs_offer(cv: ExtractedCVDTO, offer: NormalizedOfferDTO) -> Dict[str, Any]:
        try:
            evidence_chunks = CVScoringService._safe_retrieve_evidence_chunks(cv, offer)

            try:
                llm_result = LLMClient.evaluate_cv_offer_match(
                    cv_payload=CVScoringService._cv_payload(cv),
                    offer_payload=CVScoringService._offer_payload(offer),
                    evidence_chunks=evidence_chunks,
                )

                result = {
                    "overall_score": CVScoringService._as_score(llm_result.get("overall_score", 0)),
                    "sub_scores": CVScoringService._to_sub_scores(llm_result.get("sub_scores", {})),
                    "strengths": CVScoringService._to_string_list(llm_result.get("strengths", []), 8),
                    "gaps": CVScoringService._to_string_list(llm_result.get("gaps", []), 8),
                    "improvements": CVScoringService._to_string_list(llm_result.get("improvements", []), 8),
                    "retrieved_evidence": evidence_chunks,
                    "explanation": CVScoringService._build_diagnostic_summary(
                        overall_score=CVScoringService._as_score(llm_result.get("overall_score", 0)),
                        sub_scores=CVScoringService._to_sub_scores(llm_result.get("sub_scores", {})),
                        llm_explanation=str(llm_result.get("explanation", "")),
                    ),
                    "status": "SUCCESS",
                }
                return result
            except Exception as exc:
                reason = CVScoringService._sanitize_error_reason(str(exc))
                logger.error("Scoring Gemini indisponible: %s", reason)
                raise LLMServiceError(reason or "Scoring Gemini indisponible") from exc

        except Exception as exc:
            if isinstance(exc, LLMServiceError):
                raise
            reason = CVScoringService._sanitize_error_reason(f"Erreur lors du calcul du score: {exc}")
            logger.error("Scoring LLM-RAG failed: %s", reason)
            raise LLMServiceError(reason or "Erreur lors du calcul du score") from exc

    @staticmethod
    def answer_chatbot_question(
        cv: ExtractedCVDTO,
        offer: NormalizedOfferDTO,
        question: str,
        history: List[Dict[str, str]] | None = None,
    ) -> Dict[str, Any]:
        evidence_chunks = CVScoringService.retrieve_evidence_chunks(cv, offer)
        try:
            raw = LLMClient.chatbot_cv_improvement(
                question=question,
                cv_payload=CVScoringService._cv_payload(cv),
                offer_payload=CVScoringService._offer_payload(offer),
                evidence_chunks=evidence_chunks,
                history=history,
            )
            return CVScoringService._compact_chatbot_response(raw, question=question)
        except Exception as exc:
            reason = CVScoringService._sanitize_error_reason(str(exc))
            logger.error("Chatbot Gemini indisponible: %s", reason)
            raise LLMServiceError(reason or "Chatbot Gemini indisponible") from exc

    @staticmethod
    def retrieve_evidence_chunks(cv: ExtractedCVDTO, offer: NormalizedOfferDTO) -> List[str]:
        offer_query = " ".join(
            [
                offer.offre.titre or "",
                offer.offre.description or "",
                offer.all_text or "",
                " ".join(offer.required_technologies or []),
                " ".join(offer.required_skills or []),
            ]
        ).strip()

        if not offer_query:
            return []

        query_vector = EmbeddingService.embed_texts([offer_query])[0]
        matches = []
        if cv.cv_id:
            matches = CVScoringService._vector_store.search(
                query_vector=query_vector,
                top_k=settings.RETRIEVAL_TOP_K,
                doc_id=cv.cv_id,
            )

        if matches:
            return [match.text for match in matches]

        # If cv_id is missing, build temporary chunks from summary fields.
        fallback_text = " ".join(
            [
                cv.resume or "",
                " ".join(cv.technologies or []),
                " ".join(cv.competences or []),
            ]
        ).strip()
        chunks = TextChunker.chunk_text(
            fallback_text,
            chunk_size_words=settings.CHUNK_SIZE_WORDS,
            overlap_words=settings.CHUNK_OVERLAP_WORDS,
        )
        return chunks[: settings.RETRIEVAL_TOP_K]

    @staticmethod
    def _safe_retrieve_evidence_chunks(cv: ExtractedCVDTO, offer: NormalizedOfferDTO) -> List[str]:
        try:
            return CVScoringService.retrieve_evidence_chunks(cv, offer)
        except Exception as exc:
            logger.warning("Evidence retrieval failed, using fallback chunks: %s", exc)
            return CVScoringService._fallback_evidence_chunks(cv, offer)

    @staticmethod
    def _cv_payload(cv: ExtractedCVDTO) -> Dict[str, Any]:
        return {
            "cv_id": cv.cv_id,
            "nom": cv.nom,
            "email": cv.email,
            "technologies": cv.technologies,
            "competences": cv.competences,
            "annees_experience": cv.annees_experience,
            "resume": cv.resume,
        }

    @staticmethod
    def _offer_payload(offer: NormalizedOfferDTO) -> Dict[str, Any]:
        return {
            "titre": offer.offre.titre,
            "description": offer.offre.description,
            "entreprise": offer.offre.entreprise,
            "required_technologies": offer.required_technologies,
            "required_skills": offer.required_skills,
            "all_text": offer.all_text,
        }

    @staticmethod
    def _fallback_evidence_chunks(cv: ExtractedCVDTO, offer: NormalizedOfferDTO) -> List[str]:
        fallback_text = " ".join(
            [
                cv.resume or "",
                " ".join(cv.technologies or []),
                " ".join(cv.competences or []),
                offer.offre.titre or "",
                offer.offre.description or "",
                offer.all_text or "",
                " ".join(offer.required_technologies or []),
                " ".join(offer.required_skills or []),
                " ".join(offer.offre.profil_recherche or []),
                " ".join(offer.offre.technologies_requises or []),
                " ".join(offer.offre.competences_requises or []),
            ]
        ).strip()

        if not fallback_text:
            return []

        chunks = TextChunker.chunk_text(
            fallback_text,
            chunk_size_words=settings.CHUNK_SIZE_WORDS,
            overlap_words=settings.CHUNK_OVERLAP_WORDS,
        )
        return chunks[: settings.RETRIEVAL_TOP_K]

    @staticmethod
    def _local_score_cv_vs_offer(
        cv: ExtractedCVDTO,
        offer: NormalizedOfferDTO,
        evidence_chunks: List[str],
        reason: str,
    ) -> Dict[str, Any]:
        required_technologies, required_skills = CVScoringService._split_offer_requirements(offer)
        cv_technologies = CVScoringService._unique_strings(list(cv.technologies or []))
        cv_skills = CVScoringService._unique_strings(list(cv.competences or []))
        evidence_text = " ".join(evidence_chunks).lower()

        cv_tech_norm = {CVScoringService._normalize(value) for value in cv_technologies}
        cv_skill_norm = {CVScoringService._normalize(value) for value in cv_skills}

        tech_matches = [item for item in required_technologies if CVScoringService._normalize(item) in cv_tech_norm]
        skill_matches = [item for item in required_skills if CVScoringService._normalize(item) in cv_skill_norm]

        tech_gaps = [item for item in required_technologies if CVScoringService._normalize(item) not in cv_tech_norm]
        skill_gaps = [item for item in required_skills if CVScoringService._normalize(item) not in cv_skill_norm]

        tech_score = CVScoringService._ratio_score(len(tech_matches), len(required_technologies))
        skill_score = CVScoringService._ratio_score(len(skill_matches), len(required_skills))

        experience_years = max(0, int(cv.annees_experience or 0))
        experience_score = min(100, experience_years * 20)

        semantic_hits = 0
        for term in required_technologies + required_skills:
            normalized = CVScoringService._normalize(term)
            if normalized and normalized in evidence_text:
                semantic_hits += 1
        semantic_score = min(100, 35 + semantic_hits * 10 + (15 if evidence_chunks else 0))

        overall_score = round(
            tech_score * 0.35
            + skill_score * 0.30
            + experience_score * 0.20
            + semantic_score * 0.15
        )

        strengths = CVScoringService._unique_strings(tech_matches + skill_matches)
        if experience_years > 0:
            strengths.append(f"{experience_years} ans d'experience")
        strengths = strengths[:8]

        gaps = []
        for gap in tech_gaps[:4]:
            gaps.append({"requirement": gap, "category": "technology", "reason": "Technologie requise non detectee dans le CV", "impact": 15})
        for gap in skill_gaps[:4]:
            gaps.append({"requirement": gap, "category": "skill", "reason": "Competence requise non detectee dans le CV", "impact": 10})

        improvements = []
        if tech_gaps:
            improvements.append(f"Renforcer: {', '.join(tech_gaps[:3])}")
        if skill_gaps:
            improvements.append(f"Mettre en avant: {', '.join(skill_gaps[:3])}")
        if experience_years < 3 and required_technologies:
            improvements.append("Ajouter des projets concrets pour illustrer l'experience")
        if not improvements:
            improvements.append("Ajouter des realisations mesurables pour renforcer la candidature")

        explanation = (
            "Score calcule localement sans Gemini (fallback automatique). "
            f"Technologies: {len(tech_matches)}/{len(required_technologies) or 1}, "
            f"Competences: {len(skill_matches)}/{len(required_skills) or 1}, "
            f"Experience: {experience_years} ans."
        )
        if reason:
            explanation += f" Motif du fallback: {reason}."

        return {
            "overall_score": max(0, min(100, overall_score)),
            "sub_scores": {
                "technologies": tech_score,
                "skills": skill_score,
                "experience": experience_score,
                "semantic": semantic_score,
            },
            "strengths": strengths,
            "gaps": gaps,
            "improvements": improvements[:5],
            "retrieved_evidence": evidence_chunks,
            "explanation": explanation,
            "status": "SUCCESS",
        }


    @staticmethod
    def _compact_chatbot_response(payload: Dict[str, Any], question: str = "") -> Dict[str, Any]:
        strengths = CVScoringService._to_string_list(payload.get("strengths", []), CVScoringService._CHATBOT_MAX_ITEMS)
        improvement_areas = CVScoringService._to_string_list(payload.get("improvement_areas", []), CVScoringService._CHATBOT_MAX_ITEMS)
        action_items = CVScoringService._to_string_list(payload.get("action_items", []), CVScoringService._CHATBOT_MAX_ITEMS)
        # Mode pro: chatbot = coaching actionnable uniquement (2 actions courtes).
        action_items = CVScoringService._prepare_action_items(action_items, improvement_areas)
        answer = CVScoringService._format_two_actions_answer(action_items)
        if len(answer) > (CVScoringService._CHATBOT_MAX_ANSWER_CHARS * 2):
            answer = answer[: (CVScoringService._CHATBOT_MAX_ANSWER_CHARS * 2)].rstrip() + "..."

        return {
            "answer": answer,
            "strengths": [],
            "improvement_areas": [],
            "action_items": action_items,
            "rewritten_bullets": [],
            "retrieved_evidence": payload.get("retrieved_evidence", []),
            "history": payload.get("history", []),
        }

    @staticmethod
    def _detect_chatbot_focus(question: str) -> str:
        text = CVScoringService._normalize(question)
        if not text:
            return "general"

        rewrite_markers = {
            "reecris", "reformule", "rewrite", "bullet", "phrase", "resume", "résumé",
        }
        strengths_markers = {
            "point fort", "points forts", "forces", "strength", "strengths", "atout", "atouts",
        }
        actions_markers = {
            "action", "actions", "action concrete", "actions concretes", "plan d action", "plan d'action", "propose 2",
        }
        improvements_markers = {
            "ameliorer", "améliorer", "a renforcer", "a améliorer", "faiblesse", "faiblesses", "improvement", "gap", "gaps",
        }

        if any(marker in text for marker in rewrite_markers):
            return "rewrite"
        if any(marker in text for marker in strengths_markers):
            return "strengths"
        if any(marker in text for marker in actions_markers):
            return "actions"
        if any(marker in text for marker in improvements_markers):
            return "improvements"
        return "general"

    @staticmethod
    def _prepare_action_items(action_items: List[str], improvement_areas: List[str]) -> List[str]:
        cleaned_actions = CVScoringService._to_string_list(action_items, CVScoringService._CHATBOT_MAX_ITEMS)
        cleaned_improvements = CVScoringService._to_string_list(improvement_areas, CVScoringService._CHATBOT_MAX_ITEMS)

        picked = cleaned_actions[: CVScoringService._CHATBOT_ACTION_ITEMS]
        if len(picked) < CVScoringService._CHATBOT_ACTION_ITEMS:
            for item in cleaned_improvements:
                candidate = item
                lower_item = CVScoringService._normalize(candidate)
                if not lower_item.startswith("renforcer "):
                    candidate = f"Renforcer {candidate}"
                picked.append(candidate)
                if len(picked) >= CVScoringService._CHATBOT_ACTION_ITEMS:
                    break

        if len(picked) < CVScoringService._CHATBOT_ACTION_ITEMS:
            defaults = [
                "Reecris le resume en ciblant les competences de l'offre",
                "Ajoute un projet recent avec stack, role et resultat mesurable",
            ]
            for item in defaults:
                picked.append(item)
                if len(picked) >= CVScoringService._CHATBOT_ACTION_ITEMS:
                    break

        return [CVScoringService._compact_action_text(item) for item in picked[: CVScoringService._CHATBOT_ACTION_ITEMS]]

    @staticmethod
    def _compact_action_text(value: str) -> str:
        text = " ".join(str(value or "").strip().split())
        if not text:
            return "Ajouter une experience pertinente et mesurable"
        if len(text) > 95:
            text = text[:95].rstrip() + "..."
        return text.rstrip(". ")

    @staticmethod
    def _format_two_actions_answer(action_items: List[str]) -> str:
        actions = CVScoringService._prepare_action_items(action_items, [])
        return f"2 actions concretes :\n1) {actions[0]}.\n2) {actions[1]}."

    @staticmethod
    def _build_diagnostic_summary(overall_score: int, sub_scores: Dict[str, int], llm_explanation: str) -> str:
        llm_text = " ".join(str(llm_explanation or "").split())
        advisory_markers = (
            "ajoute", "ajouter", "renforce", "renforcer", "ameliore", "améliore", "doit", "devrait", "conseille", "priorise",
        )
        if llm_text and not any(marker in llm_text.lower() for marker in advisory_markers):
            return CVScoringService._compact_diagnostic_text(llm_text)

        tech = sub_scores.get("technologies", 0)
        skills = sub_scores.get("skills", 0)
        experience = sub_scores.get("experience", 0)
        semantic = sub_scores.get("semantic", 0)
        generated = (
            f"Diagnostic matching: score global {overall_score}%. "
            f"Technologies {tech}%, competences {skills}%, experience {experience}%, alignement semantique {semantic}%."
        )
        return CVScoringService._compact_diagnostic_text(generated)

    @staticmethod
    def _compact_diagnostic_text(value: str) -> str:
        text = " ".join(str(value or "").strip().split())
        if not text:
            return "Diagnostic matching indisponible."
        if len(text) > CVScoringService._DIAGNOSTIC_MAX_CHARS:
            text = text[: CVScoringService._DIAGNOSTIC_MAX_CHARS].rstrip() + "..."
        return text

    @staticmethod
    def _split_offer_requirements(offer: NormalizedOfferDTO) -> tuple[List[str], List[str]]:
        technology_seed = CVScoringService._unique_strings(
            list(offer.required_technologies or [])
            + list(offer.offre.technologies_requises or [])
        )
        skill_seed = CVScoringService._unique_strings(
            list(offer.required_skills or [])
            + list(offer.offre.competences_requises or [])
        )

        tech_norm = {CVScoringService._normalize(item) for item in technology_seed}
        skill_norm = {CVScoringService._normalize(item) for item in skill_seed}

        for item in offer.offre.profil_recherche or []:
            normalized = CVScoringService._normalize(item)
            if not normalized:
                continue
            if normalized in tech_norm or normalized in skill_norm:
                continue
            if CVScoringService._looks_like_technology(item):
                technology_seed.append(str(item).strip())
                tech_norm.add(normalized)
            else:
                skill_seed.append(str(item).strip())
                skill_norm.add(normalized)

        return (
            CVScoringService._unique_strings(technology_seed),
            CVScoringService._unique_strings(skill_seed),
        )

    @staticmethod
    def _as_score(value: Any) -> int:
        try:
            score = float(value)
            return max(0, min(100, int(round(score))))
        except Exception:
            return 0

    @staticmethod
    def _to_sub_scores(value: Any) -> Dict[str, int]:
        if not isinstance(value, dict):
            return {}
        mapped: Dict[str, int] = {}
        for key, val in value.items():
            mapped[str(key)] = CVScoringService._as_score(val)
        return mapped

    @staticmethod
    def _to_string_list(value: Any, limit: int) -> List[str]:
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value if str(item).strip()][:limit]

    @staticmethod
    def _normalize(value: Any) -> str:
        return " ".join(str(value or "").strip().lower().split())

    @staticmethod
    def _unique_strings(values: List[str]) -> List[str]:
        seen = set()
        unique = []
        for value in values:
            item = str(value).strip()
            if not item:
                continue
            normalized = CVScoringService._normalize(item)
            if normalized in seen:
                continue
            seen.add(normalized)
            unique.append(item)
        return unique

    @staticmethod
    def _looks_like_technology(value: Any) -> bool:
        text = CVScoringService._normalize(value)
        if not text:
            return False

        tech_markers = {
            "python", "java", "javascript", "typescript", "c#", "c++", "go", "golang", "rust", "php",
            "ruby", "kotlin", "swift", "scala", "sql", "postgres", "postgresql", "mysql", "mongodb",
            "redis", "docker", "kubernetes", "spring", "spring boot", "react", "angular", "vue", "node",
            "nodejs", "fastapi", "flask", "django", "aws", "azure", "gcp", "terraform", "git", "api",
            "rest", "graphql", "ci/cd", "etl", "spark", "hadoop", "linux", "unix", "airflow", "kafka",
        }
        if text in tech_markers:
            return True
        return any(marker in text for marker in tech_markers)

    @staticmethod
    def _ratio_score(matches: int, total: int) -> int:
        if total <= 0:
            return 60
        return max(0, min(100, round((matches / total) * 100)))

    @staticmethod
    def _sanitize_error_reason(value: str) -> str:
        text = " ".join(str(value or "").split())
        if not text:
            return ""

        sanitized = text
        for pattern in CVScoringService._SENSITIVE_ERROR_PATTERNS:
            sanitized = pattern.sub(r"\1[REDACTED]" if pattern.groups else "[REDACTED]", sanitized)

        # Hide full Gemini endpoint if still present after redaction.
        sanitized = re.sub(
            r"https?://[^\s]*generativelanguage\.googleapis\.com[^\s]*",
            "https://generativelanguage.googleapis.com/[REDACTED]",
            sanitized,
            flags=re.IGNORECASE,
        )
        return sanitized

