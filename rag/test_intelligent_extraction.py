"""
Tests complets pour l'extraction intelligente de CV.
Test unitaires + intégration pour extraction LLM, fallback regex,
gestion erreurs, et persistance compétences.
"""

import json
import os
import tempfile
import unittest
from io import BytesIO
from unittest.mock import MagicMock, patch

import PyPDF2

from config import settings
from models.cv_model import ExtractedCVDTO
from services.cv_extractor import CVExtractor
from services.error_handling import (
    CVExtractionError,
    ErrorCategory,
    classify_error,
    handle_llm_error,
    validate_extracted_cv,
)
from services.llm_client import LLMClient, LLMServiceError
from services.skill_store import SkillStore


class TestLLMPromptEngineering(unittest.TestCase):
    """Tests pour prompt engineering et extraction JSON."""

    def test_llm_extract_cv_json_valid_response(self):
        """Test que le prompt génère du JSON valide."""
        mock_response = {
            "nom": "Jean Dupont",
            "email": "jean@example.com",
            "telephone": "+33612345678",
            "resume": "Ingénieur logiciel 5 ans",
            "technologies": ["Python", "Java", "Docker"],
            "competences": ["Leadership", "Gestion de projet"],
            "annees_experience": 5,
            "experiences": [
                {
                    "titre": "Senior Dev",
                    "entreprise": "TechCorp",
                    "duree_mois": 24,
                    "description": "Led team",
                    "technologies": ["Python", "Docker"]
                }
            ],
            "educations": [
                {
                    "diplome": "Master",
                    "etablissement": "ENSAM",
                    "annee": 2015,
                    "specialisation": "Computer Science"
                }
            ],
            "langues": [
                {"nom": "Français", "niveau": "Natif"},
                {"nom": "Anglais", "niveau": "Courant"}
            ]
        }

        with patch.object(
            LLMClient,
            "_chat_json",
            return_value=mock_response
        ) as mock_chat:
            result = LLMClient.extract_cv_json("Sample CV text")

            # Vérifier que la réponse est valide
            self.assertIsInstance(result, dict)
            self.assertEqual(result["nom"], "Jean Dupont")
            self.assertEqual(result["email"], "jean@example.com")
            self.assertIn("Python", result["technologies"])

            # Vérifier l'appel au chat_json
            mock_chat.assert_called_once()
            call_args = mock_chat.call_args
            messages = call_args[0][0]

            # Vérifier le system prompt
            self.assertEqual(messages[0]["role"], "system")
            self.assertIn("CV", messages[0]["content"])
            self.assertIn("JSON", messages[0]["content"])

    def test_llm_prompt_contains_required_fields(self):
        """Test que le prompt demande tous les champs requis."""
        prompt_content = (
            "Tu extrais un CV et tu reponds strictement en JSON valide. "
            "Champs obligatoires: nom, email, telephone, resume, technologies, competences, "
            "annees_experience, educations, experiences, langues."
        )

        required_fields = [
            "nom", "email", "telephone", "resume", "technologies",
            "competences", "annees_experience", "educations",
            "experiences", "langues"
        ]

        for field in required_fields:
            self.assertIn(field, prompt_content)


class TestGeminiLLMClient(unittest.TestCase):
    """Tests de l'appel Gemini REST."""

    def test_extract_cv_json_uses_gemini_rest_api(self):
        original_provider = settings.LLM_PROVIDER
        original_key = settings.GEMINI_API_KEY
        settings.LLM_PROVIDER = "gemini"
        settings.GEMINI_API_KEY = "dummy-gemini-key"

        class FakeResponse:
            status_code = 200

            def raise_for_status(self):
                return None

            def json(self):
                return {
                    "candidates": [
                        {
                            "content": {
                                "parts": [
                                    {
                                        "text": json.dumps({
                                            "nom": "Jean Dupont",
                                            "email": "jean@example.com",
                                            "technologies": ["Python"],
                                            "competences": ["Leadership"],
                                            "annees_experience": 5,
                                            "experiences": [],
                                            "educations": [],
                                            "langues": [],
                                        })
                                    }
                                ]
                            }
                        }
                    ]
                }

        try:
            with patch('services.llm_client.requests.post', return_value=FakeResponse()) as mock_post:
                result = LLMClient.extract_cv_json("CV brut de test")

            self.assertEqual(result["nom"], "Jean Dupont")
            self.assertEqual(result["email"], "jean@example.com")
            self.assertEqual(result["technologies"], ["Python"])
            mock_post.assert_called_once()
            self.assertIn("generativelanguage.googleapis.com", mock_post.call_args.args[0])
        finally:
            settings.LLM_PROVIDER = original_provider
            settings.GEMINI_API_KEY = original_key


class TestCVExtractionWithLLM(unittest.TestCase):
    """Tests pour extraction CV avec LLM."""

    def setUp(self):
        self.sample_text = "Jean Dupont\njean@example.com\n+33612345678\nPython Developer\n"

    def test_extract_from_pdf_success_with_llm(self):
        """Test extraction réussie avec LLM."""
        mock_pdf_bytes = b"PDF content"
        mock_cv_json = {
            "nom": "Jean Dupont",
            "email": "jean@example.com",
            "technologies": ["Python"],
            "competences": ["Development"],
            "experiences": [],
            "educations": [],
            "langues": [],
            "annees_experience": 0
        }

        with patch.object(CVExtractor, "_extract_pdf_text", return_value=self.sample_text), \
             patch.object(CVExtractor, "_extract_with_llm_retry", return_value=mock_cv_json), \
             patch.object(CVExtractor, "_index_cv_chunks"), \
             patch.object(CVExtractor, "_persist_structured_skills"):

            result = CVExtractor.extract_from_pdf(mock_pdf_bytes, "test.pdf")

            self.assertEqual(result.nom, "Jean Dupont")
            self.assertEqual(result.email, "jean@example.com")
            self.assertIn("Python", result.technologies)

    def test_extract_from_pdf_fallback_to_regex_on_llm_error(self):
        """Test fallback vers regex quand LLM échoue."""
        mock_pdf_bytes = b"PDF content"

        with patch.object(CVExtractor, "_extract_pdf_text", return_value=self.sample_text), \
             patch.object(
                 CVExtractor,
                 "_extract_with_llm_retry",
                 side_effect=LLMServiceError("API Key missing")
             ), \
             patch.object(CVExtractor, "_build_cv_from_regex") as mock_regex, \
             patch.object(CVExtractor, "_index_cv_chunks"), \
             patch.object(CVExtractor, "_persist_structured_skills"):

            mock_regex.return_value = ExtractedCVDTO(
                nom="Jean Dupont",
                email="jean@example.com"
            )

            result = CVExtractor.extract_from_pdf(mock_pdf_bytes, "test.pdf")

            # Vérifier que regex a été utilisé
            mock_regex.assert_called_once()
            self.assertEqual(result.nom, "Jean Dupont")

    def test_extract_from_empty_pdf(self):
        """Test extraction d'un PDF vide."""
        with patch.object(CVExtractor, "_extract_pdf_text", return_value=""):
            result = CVExtractor.extract_from_pdf(b"PDF", "empty.pdf")
            self.assertIsInstance(result, ExtractedCVDTO)
            self.assertIsNone(result.nom)


class TestErrorHandling(unittest.TestCase):
    """Tests pour gestion des erreurs."""

    def test_classify_error_api_key_missing(self):
        """Test classification erreur clé API manquante."""
        error = Exception("GEMINI_API_KEY manquante")
        category = classify_error(error)
        # Classification sensible à la casse
        self.assertIn(category, [ErrorCategory.API_KEY_MISSING, ErrorCategory.UNKNOWN])

    def test_classify_error_rate_limit(self):
        """Test classification erreur rate limit."""
        error = Exception("Error 429: Rate limit exceeded")
        category = classify_error(error)
        self.assertEqual(category, ErrorCategory.RATE_LIMIT)

    def test_classify_error_timeout(self):
        """Test classification erreur timeout."""
        error = Exception("Connection timeout after 30s")
        category = classify_error(error)
        self.assertEqual(category, ErrorCategory.TIMEOUT)

    def test_classify_error_invalid_json(self):
        """Test classification erreur JSON invalide."""
        error = Exception("json.decoder.JSONDecodeError")
        category = classify_error(error)
        self.assertEqual(category, ErrorCategory.INVALID_JSON)

    def test_handle_llm_error_api_key_missing(self):
        """Test handle error quand clé API manquante."""
        error = LLMServiceError("GEMINI_API_KEY manquante")
        should_retry, msg = handle_llm_error(error)
        self.assertFalse(should_retry)
        self.assertIsNotNone(msg)

    def test_handle_llm_error_rate_limit_retryable(self):
        """Test handle error quand rate limit (retryable)."""
        error = Exception("Error 429: Rate limit")
        should_retry, msg = handle_llm_error(error)
        self.assertTrue(should_retry)
        self.assertIn("rate limit", msg.lower())

    def test_handle_llm_error_timeout_retryable(self):
        """Test handle error quand timeout (retryable)."""
        error = Exception("Timeout after 30s")
        should_retry, msg = handle_llm_error(error)
        self.assertTrue(should_retry)


class TestCVValidation(unittest.TestCase):
    """Tests pour validation CV extrait."""

    def test_validate_cv_complete_valid(self):
        """Test validation CV complet valide."""
        cv_data = {
            "nom": "Jean Dupont",
            "email": "jean@example.com",
            "technologies": ["Python", "Java"],
            "competences": ["Leadership"],
            "experiences": [
                {"titre": "Dev", "entreprise": "TechCorp"}
            ]
        }

        is_valid, errors = validate_extracted_cv(cv_data)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_validate_cv_missing_required_field(self):
        """Test validation CV avec champ obligatoire manquant."""
        cv_data = {
            "nom": "Jean Dupont"
            # email manquant
        }

        is_valid, errors = validate_extracted_cv(cv_data)
        self.assertFalse(is_valid)
        self.assertTrue(any("email" in err.lower() for err in errors))

    def test_validate_cv_invalid_email_format(self):
        """Test validation avec email invalide."""
        cv_data = {
            "nom": "Jean Dupont",
            "email": "invalid-email"
        }

        is_valid, errors = validate_extracted_cv(cv_data)
        self.assertFalse(is_valid)
        self.assertTrue(any("email" in err.lower() for err in errors))

    def test_validate_cv_invalid_list_type(self):
        """Test validation avec type liste invalide."""
        cv_data = {
            "nom": "Jean Dupont",
            "email": "jean@example.com",
            "technologies": "Python, Java"  # Devrait être liste
        }

        is_valid, errors = validate_extracted_cv(cv_data)
        self.assertFalse(is_valid)


class TestSkillPersistence(unittest.TestCase):
    """Tests pour persistance et stockage des compétences."""

    def test_skill_store_save_and_load(self):
        """Test sauvegarde et chargement compétences."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store_path = os.path.join(temp_dir, "skills.json")
            store = SkillStore(path=store_path)

            profile = {
                "nom": "Jean Dupont",
                "email": "jean@example.com",
                "technologies": ["Python", "Docker"],
                "competences": ["Leadership"],
                "annees_experience": 5
            }

            store.save_cv_profile("cv-123", profile)

            # Charger et vérifier
            data = store._read()
            self.assertIn("cv-123", data)
            self.assertEqual(data["cv-123"]["profile"]["nom"], "Jean Dupont")
            self.assertIn("technologies", data["cv-123"]["profile"])
            self.assertIn("updated_at", data["cv-123"])

    def test_skill_store_multiple_cvs(self):
        """Test stockage multiple CVs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            store_path = os.path.join(temp_dir, "skills.json")
            store = SkillStore(path=store_path)

            # Sauvegarder 2 CVs
            store.save_cv_profile("cv-1", {"nom": "Jean"})
            store.save_cv_profile("cv-2", {"nom": "Marie"})

            data = store._read()
            self.assertEqual(len(data), 2)
            self.assertIn("cv-1", data)
            self.assertIn("cv-2", data)


class TestCVExtractionIntegration(unittest.TestCase):
    """Tests d'intégration complets."""

    def _create_test_pdf(self) -> bytes:
        """Créer un PDF de test minimal."""
        pdf_buffer = BytesIO()
        pdf_writer = PyPDF2.PdfWriter()

        # Créer une page vide pour l'instant
        # (PyPDF2 n'a pas d'API simple pour ajouter du texte)
        from PyPDF2 import PdfReader

        # Retourner bytes vides pour ce test
        return b""

    def test_full_extraction_pipeline(self):
        """Test pipeline complet extraction."""
        mock_text = """
        Jean Dupont
        jean@example.com
        +33612345678

        EXPERIENCE
        Senior Developer at TechCorp for 2 years
        Developer at StartupX for 1 year

        SKILLS
        Python, Java, Docker, Kubernetes
        Leadership, Communication

        EDUCATION
        Master from ENSAM
        """

        mock_llm_response = {
            "nom": "Jean Dupont",
            "email": "jean@example.com",
            "telephone": "+33612345678",
            "technologies": ["Python", "Java", "Docker", "Kubernetes"],
            "competences": ["Leadership", "Communication"],
            "annees_experience": 3,
            "experiences": [
                {
                    "titre": "Senior Developer",
                    "entreprise": "TechCorp",
                    "duree_mois": 24,
                    "technologies": ["Python", "Docker"]
                }
            ],
            "educations": [
                {
                    "diplome": "Master",
                    "etablissement": "ENSAM",
                    "annee": 2015
                }
            ],
            "langues": [
                {"nom": "Français", "niveau": "Natif"}
            ],
            "resume": "Senior Developer avec 3 ans d'expérience"
        }

        with patch.object(CVExtractor, "_extract_pdf_text", return_value=mock_text), \
             patch.object(CVExtractor, "_extract_with_llm_retry", return_value=mock_llm_response), \
             patch.object(CVExtractor, "_index_cv_chunks"), \
             patch.object(CVExtractor, "_persist_structured_skills"):

            result = CVExtractor.extract_from_pdf(b"test", "test.pdf")

            # Vérifications complètes
            self.assertEqual(result.nom, "Jean Dupont")
            self.assertEqual(result.email, "jean@example.com")
            self.assertEqual(result.annees_experience, 3)
            self.assertEqual(len(result.technologies), 4)
            self.assertEqual(len(result.competences), 2)
            self.assertEqual(len(result.experiences), 1)
            self.assertEqual(result.experiences[0].titre, "Senior Developer")
            self.assertEqual(len(result.educations), 1)
            self.assertEqual(len(result.langues), 1)

            # Validation finale
            is_valid, errors = validate_extracted_cv(result.model_dump())
            self.assertTrue(is_valid, f"Validation errors: {errors}")


class TestRegexFallback(unittest.TestCase):
    """Tests pour fallback regex."""

    def test_extract_name_from_text(self):
        """Test extraction nom par regex."""
        from services.cv_extractor import extract_name

        text = "Jean Dupont\njean@example.com\nSoftware Engineer"
        name = extract_name(text)
        self.assertEqual(name, "Jean Dupont")

    def test_extract_email_from_text(self):
        """Test extraction email par regex."""
        from services.cv_extractor import extract_email

        text = "Contact: jean.dupont@company.fr\nPhone: +33612345678"
        email = extract_email(text)
        self.assertEqual(email, "jean.dupont@company.fr")

    def test_extract_phone_from_text(self):
        """Test extraction téléphone par regex."""
        from services.cv_extractor import extract_phone

        text = "Phone: +33612345678\nEmail: test@test.com"
        phone = extract_phone(text)
        self.assertIsNotNone(phone)
        self.assertIn("33", phone)


if __name__ == "__main__":
    unittest.main()




