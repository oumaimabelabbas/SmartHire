"""Service pour normaliser et parser l'offre d'emploi"""
import logging
import re
from typing import List
from models.offer_model import OffreDTO, NormalizedOfferDTO

logger = logging.getLogger(__name__)

class OfferParser:
    """Parse et normalise les offres d'emploi"""

    # Listes de technologies et compétences connues
    COMMON_TECHNOLOGIES = [
        "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust",
        "PHP", "Ruby", "Kotlin", "Spring Boot", "Django", "Flask", "FastAPI",
        "React", "Vue.js", "Angular", "Next.js", "PostgreSQL", "MongoDB",
        "Docker", "Kubernetes", "AWS", "Azure", "Git", "CI/CD"
    ]

    COMMON_SKILLS = [
        "Leadership", "Gestion de projet", "Communication", "Travail en équipe",
        "Autonomie", "Rigueur", "Agile", "Scrum", "Problem-solving"
    ]

    @staticmethod
    def normalize_offer(offre: OffreDTO) -> NormalizedOfferDTO:
        """
        Normaliser une offre pour le scoring

        Étapes :
        1. Fusionner tout le texte
        2. Extraire technologies
        3. Extraire compétences
        4. Nettoyer et standardiser
        """
        try:
            logger.info(f"📋 Normalisation offre: {offre.titre}")

            # Étape 1 : Fusionner tout le texte
            all_text = " ".join([
                offre.titre or "",
                offre.description or "",
                offre.a_propos_role or "",
                offre.a_propos_entreprise or "",
                " ".join(offre.responsabilites),
                " ".join(offre.profil_recherche)
            ])

            # Étape 2 : Extraire technologies
            technologies = OfferParser._extract_technologies_from_text(all_text)

            # Étape 3 : Extraire compétences
            skills = OfferParser._extract_skills_from_text(all_text)

            # Étape 4 : Extraire keywords
            keywords = OfferParser._extract_keywords(all_text)

            normalized = NormalizedOfferDTO(
                offre=offre,
                all_text=all_text,
                keywords=keywords,
                required_skills=skills,
                required_technologies=technologies
            )

            logger.info(f"✅ Offre normalisée: {len(technologies)} techs, {len(skills)} skills")
            return normalized

        except Exception as e:
            logger.error(f"❌ Erreur normalisation offre: {str(e)}")
            return NormalizedOfferDTO(
                offre=offre,
                all_text="",
                keywords=[],
                required_skills=[],
                required_technologies=[]
            )

    @staticmethod
    def _extract_technologies_from_text(text: str) -> List[str]:
        """Extraire technologies du texte"""
        found = []
        text_lower = text.lower()

        for tech in OfferParser.COMMON_TECHNOLOGIES:
            if tech.lower() in text_lower and tech not in found:
                found.append(tech)

        return found

    @staticmethod
    def _extract_skills_from_text(text: str) -> List[str]:
        """Extraire compétences du texte"""
        found = []
        text_lower = text.lower()

        for skill in OfferParser.COMMON_SKILLS:
            if skill.lower() in text_lower and skill not in found:
                found.append(skill)

        return found

    @staticmethod
    def _extract_keywords(text: str) -> List[str]:
        """Extraire mots-clés importants"""
        # Enlever les mots vides
        stop_words = {
            "le", "la", "les", "de", "du", "et", "ou", "un", "une",
            "the", "a", "an", "and", "or", "in", "is", "are"
        }

        # Tokenizer simple
        words = re.findall(r'\b\w+\b', text.lower())

        # Filtrer et retourner les mots clés
        keywords = [w for w in set(words) if len(w) > 3 and w not in stop_words]

        return keywords[:20]  # Retourner les top 20

