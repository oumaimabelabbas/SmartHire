from models.cv_model import ExtractedCVDTO
from models.offer_model import OffreDTO, NormalizedOfferDTO
from services.scoring import CVScoringService

cv = ExtractedCVDTO(
    cv_id="cv-live-1",
    nom="Test Candidate",
    email="test@example.com",
    technologies=["Python", "Docker", "SQL", "Airflow"],
    competences=["Communication", "Problem-solving"],
    annees_experience=6,
    resume="Data engineer with ETL pipelines and cloud experience",
)

offre = OffreDTO(
    titre="Data Engineer Python",
    description="Build ETL pipelines and APIs on cloud",
    entreprise="DataBridge",
    localisation="Remote",
    profil_recherche=["Python", "Docker", "SQL", "Airflow", "Communication"],
)

normalized = NormalizedOfferDTO(
    offre=offre,
    all_text="Data engineer python docker sql airflow etl cloud api communication",
    keywords=["python", "docker", "sql", "airflow", "etl", "cloud"],
    required_skills=["Communication"],
    required_technologies=["Python", "Docker", "SQL", "Airflow"],
)

result = CVScoringService.score_cv_vs_offer(cv, normalized)

print("OVERALL", result.get("overall_score"))
print("STATUS", result.get("status"))
print("EXPLANATION", result.get("explanation"))
print("SUB", result.get("sub_scores"))
print("STRENGTHS", result.get("strengths"))
print("GAPS", result.get("gaps"))

