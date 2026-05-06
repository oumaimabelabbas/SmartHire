"""
Serveur FastAPI pour le service RAG SmartHire
Endpoints pour extraction CV et scoring matching
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

# Ajouter le chemin des imports
sys.path.insert(0, '/Rag')

from config import settings
from models.cv_model import ExtractedCVDTO
from models.offer_model import OffreDTO, NormalizedOfferDTO
from services.cv_extractor import CVExtractor
from services.offer_parser import OfferParser
from services.llm_client import LLMServiceError
from services.scoring import CVScoringService

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialiser FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Service RAG pour SmartHire - Extraction CV et Matching Scores"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatbotRAGRequest(BaseModel):
    """Request payload for CV improvement chatbot."""

    question: str = Field(..., min_length=2)
    cv: ExtractedCVDTO
    offre: OffreDTO
    history: Optional[List[Dict[str, str]]] = None

# ==================== HEALTH CHECK ====================

@app.get("/health")
async def health_check():
    """Vérifier que le service est actif"""
    return {
        "status": "✅ Service RAG actif",
        "version": settings.APP_VERSION,
        "port": settings.RAG_SERVICE_PORT
    }

@app.get("/health/extraction")
async def extraction_health_check():
    """Vérifier la santé du service d'extraction"""
    from services.extraction_metrics import health_check
    report = health_check.get_health_report()
    return report

# ==================== EXTRACTION CV ====================

@app.post("/api/extract-cv")
async def extract_cv(file: UploadFile = File(...)):
    """
    Endpoint d'extraction de CV

    📥 Input : Fichier PDF du CV
    📤 Output : ExtractedCVDTO avec données structurées

    Étapes:
    1. Recevoir le fichier PDF
    2. Extraire le texte
    3. Structurer les données (expériences, compétences, etc.)
    4. Retourner DTO structuré
    """
    try:
        logger.info(f"📥 Réception CV: {file.filename}")

        # Vérifier type de fichier
        if file.content_type not in ["application/pdf", "application/octet-stream"]:
            raise HTTPException(status_code=400, detail="Seuls les fichiers PDF sont acceptés")

        # Lire le fichier
        pdf_bytes = await file.read()

        if not pdf_bytes:
            raise HTTPException(status_code=400, detail="Fichier vide")

        # Étape 1 : Extraire du PDF
        extracted_cv = CVExtractor.extract_from_pdf(pdf_bytes)

        logger.info(f"✅ CV extrait: {extracted_cv.nom}")

        return {
            "status": "SUCCESS",
            "data": extracted_cv.model_dump(),
            "message": f"CV de {extracted_cv.nom} extrait avec succès"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur extraction: {str(e)}")
        return {
            "status": "ERROR",
            "data": None,
            "message": f"Erreur lors de l'extraction: {str(e)}"
        }

# ==================== NORMALISATION OFFRE ====================

@app.post("/api/normalize-offer")
async def normalize_offer(offre: OffreDTO):
    """
    Normaliser une offre d'emploi

    📥 Input : OffreDTO (data de l'offre)
    📤 Output : NormalizedOfferDTO avec technos et skills extraites
    """
    try:
        logger.info(f"📋 Normalisation offre: {offre.titre}")

        normalized = OfferParser.normalize_offer(offre)

        return {
            "status": "SUCCESS",
            "data": {
                "titre": normalized.offre.titre,
                "required_technologies": normalized.required_technologies,
                "required_skills": normalized.required_skills,
                "keywords": normalized.keywords[:10]
            }
        }

    except Exception as e:
        logger.error(f"❌ Erreur normalisation: {str(e)}")
        return {
            "status": "ERROR",
            "message": str(e)
        }

# ==================== SCORING / MATCHING ====================

@app.post("/api/score-cv-vs-offer")
async def score_cv_vs_offer(
    cv: ExtractedCVDTO,
    offre: OffreDTO
):
    """
    ⭐ ENDPOINT PRINCIPAL - Calculer score de matching

    📥 Input :
        - cv : ExtractedCVDTO (données du CV)
        - offre : OffreDTO (offre d'emploi)

    📤 Output :
        - overall_score : 0-100
        - sub_scores : détail des scores
        - strengths : forces du candidat
        - gaps : lacunes à combler
        - explanation : texte explicatif

    Algorithme :
    1. Normaliser l'offre
    2. Comparer technologies (35%)
    3. Comparer compétences (30%)
    4. Évaluer expérience (20%)
    5. Analyse sémantique (15%)
    6. Retourner score pondéré
    """
    try:
        logger.info(f"🎯 Scoring: {cv.nom} vs {offre.titre}")

        # Étape 1 : Normaliser offre
        normalized_offer = OfferParser.normalize_offer(offre)

        # Étape 2 : Scorer
        result = CVScoringService.score_cv_vs_offer(cv, normalized_offer)

        if result.get("status") == "ERROR":
            raise HTTPException(
                status_code=503,
                detail=result.get("explanation", "Service de scoring indisponible"),
            )

        logger.info(f"✅ Score calculé: {result['overall_score']:.1f}/100")

        return {
            "status": "SUCCESS",
            "data": result
        }

    except LLMServiceError as e:
        logger.error(f"❌ Erreur scoring Gemini: {str(e)}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Erreur scoring: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chatbot/cv-improvement")
async def chatbot_cv_improvement(request: ChatbotRAGRequest):
    """
    Chatbot RAG cible offre:
    - utilise retrieval sur chunks du CV
    - genere reponse d amelioration via Gemini
    """
    try:
        normalized_offer = OfferParser.normalize_offer(request.offre)
        answer = CVScoringService.answer_chatbot_question(
            cv=request.cv,
            offer=normalized_offer,
            question=request.question,
            history=request.history,
        )
        return {
            "status": "SUCCESS",
            "data": answer,
        }
    except LLMServiceError as e:
        logger.error(f"❌ Erreur chatbot Gemini: {str(e)}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Erreur chatbot: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ENDPOINT COMPLET ====================

@app.post("/api/full-analysis")
async def full_analysis(
    cv_file: UploadFile = File(...),
    offre: OffreDTO = None
):
    """
    Analyse complète en une seule requête:
    1. Extraction CV
    2. Normalisation offre
    3. Scoring matching
    """
    try:
        logger.info("🚀 Analyse complète démarrée")

        # Extraction CV
        pdf_bytes = await cv_file.read()
        extracted_cv = CVExtractor.extract_from_pdf(pdf_bytes)

        if offre is None:
            return {
                "status": "ERROR",
                "message": "Offre d'emploi requise"
            }

        # Scoring
        normalized_offer = OfferParser.normalize_offer(offre)
        scoring_result = CVScoringService.score_cv_vs_offer(extracted_cv, normalized_offer)

        return {
            "status": "SUCCESS",
            "cv_data": extracted_cv.model_dump(),
            "scoring": scoring_result
        }

    except Exception as e:
        logger.error(f"❌ Erreur analyse complète: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== DÉMARRAGE ====================

def startup_checks():
    """Effectuer les vérifications au démarrage"""
    logger.info("🔍 Vérifications au démarrage...")

    # Vérifier la clé Gemini API
    if not settings.GEMINI_API_KEY:
        logger.warning(
            "⚠️  AVERTISSEMENT: GEMINI_API_KEY non configurée.\n"
            "   Le scoring/chatbot RAG sera indisponible tant que Gemini n'est pas configuré.\n"
            "   Pour activer Gemini, definissez GEMINI_API_KEY dans .env"
        )
    else:
        logger.info("✅ GEMINI_API_KEY configuree")

    logger.info(f"📦 Configuration:")
    logger.info(f"   - LLM Provider: {settings.LLM_PROVIDER}")
    logger.info(f"   - Modèle Gemini: {settings.GEMINI_MODEL}")
    logger.info(f"   - URL Gemini: {settings.GEMINI_BASE_URL}")
    logger.info(f"   - Embedding Provider: {settings.EMBEDDING_PROVIDER}")

@app.on_event("startup")
async def startup_event():
    """Event déclenché au démarrage de l'application"""
    startup_checks()

if __name__ == "__main__":
    import uvicorn

    startup_checks()
    logger.info(f"🚀 Démarrage service RAG sur port {settings.RAG_SERVICE_PORT}")
    logger.info(f"📚 Documentation: http://localhost:{settings.RAG_SERVICE_PORT}/docs")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.RAG_SERVICE_PORT,
        log_level="info"
    )

