"""Modèles de données pour le CV"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ExperienceDTO(BaseModel):
    """Expérience professionnelle"""
    titre: str
    entreprise: str
    duree_mois: Optional[int] = None
    description: Optional[str] = None
    technologies: List[str] = []

class EducationDTO(BaseModel):
    """Formation/Éducation"""
    diplome: str
    etablissement: str
    annee: Optional[int] = None
    specialisation: Optional[str] = None

class LanguageDTO(BaseModel):
    """Langue maîtrisée"""
    nom: str
    niveau: str  # A1, A2, B1, B2, C1, C2

class ExtractedCVDTO(BaseModel):
    """Données extraites d'un CV"""
    cv_id: Optional[str] = None
    nom: Optional[str] = None
    email: Optional[str] = None
    telephone: Optional[str] = None
    resume: Optional[str] = None

    # Listes structurées
    experiences: List[ExperienceDTO] = []
    educations: List[EducationDTO] = []
    competences: List[str] = []
    technologies: List[str] = []
    langues: List[LanguageDTO] = []

    # Méta-données
    annees_experience: int = 0
    derniere_experience: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "nom": "Jean Dupont",
                "email": "jean@example.com",
                "annees_experience": 5,
                "competences": ["Leadership", "Gestion de projet"],
                "technologies": ["Python", "Java", "Spring Boot"]
            }
        }

