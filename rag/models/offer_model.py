"""Modèles de données pour l'offre d'emploi"""
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class ModeTravail(str, Enum):
    """Mode de travail"""
    ON_SITE = "ON_SITE"
    REMOTE = "REMOTE"
    HYBRID = "HYBRID"

class TypeContrat(str, Enum):
    """Type de contrat"""
    CDI = "CDI"
    CDD = "CDD"
    STAGE = "STAGE"
    FREELANCE = "FREELANCE"

class OffreDTO(BaseModel):
    """Structure de l'offre d'emploi"""
    id: Optional[int] = None
    titre: str
    description: str
    entreprise: str
    localisation: str

    # Métier
    mode_travail: ModeTravail = ModeTravail.ON_SITE
    type_contrat: TypeContrat = TypeContrat.CDI

    # Listes structurées
    responsabilites: List[str] = []
    profil_recherche: List[str] = []
    technologies_requises: List[str] = []
    competences_requises: List[str] = []

    # Contexte
    a_propos_role: Optional[str] = None
    a_propos_entreprise: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "titre": "Développeur Backend",
                "entreprise": "TechCorp",
                "technologies_requises": ["Python", "Django", "PostgreSQL"],
                "competences_requises": ["Travail en équipe", "Problem-solving"]
            }
        }

class NormalizedOfferDTO(BaseModel):
    """Offre normalisée pour le scoring"""
    offre: OffreDTO
    all_text: str  # Texte complet fusionné
    keywords: List[str]  # Mots-clés extraits
    required_skills: List[str]  # Compétences requises
    required_technologies: List[str]  # Technologies requises

