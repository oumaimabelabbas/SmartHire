import os
import tempfile
import unittest
from unittest.mock import patch

from config import settings
from models.cv_model import ExtractedCVDTO
from models.offer_model import NormalizedOfferDTO, OffreDTO
from services.embedding_service import EmbeddingService
from services.llm_client import LLMClient, LLMServiceError
from services.scoring import CVScoringService
from services.text_chunker import TextChunker
from services.vector_store import LocalVectorStore


class TestRagPipeline(unittest.TestCase):
    def test_chunking_produces_overlapping_chunks(self):
        text = " ".join([f"token{i}" for i in range(320)])
        chunks = TextChunker.chunk_text(text, chunk_size_words=100, overlap_words=20)

        self.assertGreaterEqual(len(chunks), 3)
        self.assertIn("token99", chunks[0])
        self.assertIn("token80", chunks[1])

    def test_vector_store_search(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store_path = os.path.join(temp_dir, "vectors_chroma")
            store = LocalVectorStore(path=store_path)
            chunks = [
                "python docker airflow pipeline",
                "frontend react typescript ui",
                "spring boot java api",
            ]
            vectors = [
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0],
            ]
            store.upsert_chunks("cv-1", chunks, vectors, metadata={"source": "test"})

            query_vector = [0.9, 0.05, 0.05]
            matches = store.search(query_vector, top_k=2, doc_id="cv-1")

            self.assertEqual(len(matches), 2)
            self.assertTrue(any("python" in item.text for item in matches))

    def test_scoring_with_vector_retrieval(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store_path = os.path.join(temp_dir, "vectors_chroma")
            store = LocalVectorStore(path=store_path)

            CVScoringService._vector_store = store

            cv = ExtractedCVDTO(
                cv_id="cv-rag-1",
                nom="Test User",
                technologies=["Python", "Docker"],
                competences=["Communication"],
                annees_experience=4,
                resume="Data engineer with Python and Docker experience",
            )
            chunks = [
                "Built python airflow pipelines and docker deployment",
                "Maintained ETL monitoring and data quality checks",
            ]
            vectors = [
                [1.0, 0.0, 0.0],
                [0.7, 0.2, 0.1],
            ]
            store.upsert_chunks(cv.cv_id, chunks, vectors, metadata={"source": "cv"})

            offre = OffreDTO(
                titre="Data Engineer Python",
                description="Build ETL pipelines on cloud",
                entreprise="TechAtlas",
                localisation="Casablanca",
                profil_recherche=["Python", "Docker", "Communication"],
            )
            normalized = NormalizedOfferDTO(
                offre=offre,
                all_text="Data engineer python docker airflow ETL cloud",
                keywords=["python", "docker", "etl"],
                required_skills=["Communication"],
                required_technologies=["Python", "Docker"],
            )

            mock_llm_result = {
                "overall_score": 84,
                "sub_scores": {"technologies": 90, "skills": 80, "experience": 85, "semantic": 82},
                "strengths": ["Python", "Docker"],
                "gaps": ["AWS"],
                "improvements": ["Ajouter un projet AWS"],
                "explanation": "Bon match global avec axe cloud.",
            }

            with patch.object(EmbeddingService, "embed_texts", return_value=[[1.0, 0.0, 0.0]]), patch.object(
                LLMClient,
                "evaluate_cv_offer_match",
                return_value=mock_llm_result,
            ):
                result = CVScoringService.score_cv_vs_offer(cv, normalized)

            self.assertEqual(result["status"], "SUCCESS")
            self.assertIn("retrieved_evidence", result)
            self.assertEqual(result["overall_score"], 84)
            self.assertTrue(result["improvements"])

    def test_scoring_falls_back_locally_when_llm_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store_path = os.path.join(temp_dir, "vectors_chroma")
            store = LocalVectorStore(path=store_path)

            CVScoringService._vector_store = store

            cv = ExtractedCVDTO(
                cv_id="cv-rag-2",
                nom="Test User",
                technologies=["Python", "Docker", "SQL"],
                competences=["Communication", "Problem-solving"],
                annees_experience=3,
                resume="Data engineer with Python and SQL experience",
            )
            store.upsert_chunks(
                cv.cv_id,
                ["Built Python ETL pipelines with Docker and SQL"],
                [[1.0, 0.0, 0.0]],
                metadata={"source": "cv"},
            )

            offre = OffreDTO(
                titre="Data Engineer Python",
                description="Build ETL pipelines on cloud",
                entreprise="TechAtlas",
                localisation="Casablanca",
                profil_recherche=["Python", "Docker", "Communication"],
                technologies_requises=["Python", "Docker"],
                competences_requises=["Communication"],
            )
            normalized = NormalizedOfferDTO(
                offre=offre,
                all_text="Data engineer python docker airflow ETL cloud",
                keywords=["python", "docker", "etl"],
                required_skills=["Communication"],
                required_technologies=["Python", "Docker"],
            )

            with patch.object(EmbeddingService, "embed_texts", return_value=[[1.0, 0.0, 0.0]]), patch.object(
                LLMClient,
                "evaluate_cv_offer_match",
                side_effect=LLMServiceError("429 Too Many Requests"),
            ):
                result = CVScoringService.score_cv_vs_offer(cv, normalized)

            self.assertEqual(result["status"], "SUCCESS")
            self.assertGreater(result["overall_score"], 0)
            self.assertIn("fallback", result["explanation"].lower())
            self.assertTrue(result["strengths"])
            self.assertTrue(result["retrieved_evidence"])

    def test_local_scoring_separates_technologies_and_skills(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = LocalVectorStore(path=os.path.join(temp_dir, "vectors_chroma"))
            CVScoringService._vector_store = store

            cv = ExtractedCVDTO(
                cv_id="cv-rag-3",
                nom="Test User",
                technologies=["Java", "Spring Boot", "Docker", "PostgreSQL"],
                competences=["Communication"],
                annees_experience=6,
                resume="Backend engineer with Java Spring Boot and PostgreSQL",
            )

            offre = OffreDTO(
                titre="Backend Java",
                description="Build APIs with Java and Spring Boot",
                entreprise="TechAtlas",
                localisation="Casablanca",
                profil_recherche=["Java", "Spring Boot", "PostgreSQL", "Leadership"],
            )
            normalized = NormalizedOfferDTO(
                offre=offre,
                all_text="Java Spring Boot PostgreSQL Leadership",
                keywords=["java", "spring boot", "postgresql", "leadership"],
                required_skills=[],
                required_technologies=[],
            )

            with patch.object(EmbeddingService, "embed_texts", return_value=[[1.0, 0.0, 0.0]]), patch.object(
                LLMClient,
                "evaluate_cv_offer_match",
                side_effect=LLMServiceError("429 Too Many Requests"),
            ):
                result = CVScoringService.score_cv_vs_offer(cv, normalized)

            gap_requirements = [gap["requirement"] for gap in result["gaps"]]
            gap_categories = {gap["requirement"]: gap.get("category") for gap in result["gaps"]}

            self.assertEqual(result["status"], "SUCCESS")
            self.assertIn("Java", result["strengths"])
            self.assertIn("Spring Boot", result["strengths"])
            self.assertIn("PostgreSQL", result["strengths"])
            self.assertNotIn("Java", gap_requirements)
            self.assertEqual(gap_categories.get("Leadership"), "skill")
            self.assertTrue(any(item in ["Java", "Spring Boot", "PostgreSQL"] for item in result["strengths"]))

    def test_chatbot_answer_uses_retrieval_context(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = LocalVectorStore(path=os.path.join(temp_dir, "vectors_chroma"))
            CVScoringService._vector_store = store

            cv = ExtractedCVDTO(
                cv_id="cv-chat-1",
                nom="Candidate",
                technologies=["Python"],
                competences=["Communication"],
                resume="Built ETL pipelines and data quality checks",
            )
            store.upsert_chunks(
                cv.cv_id,
                ["Implemented ETL with Python and Airflow"],
                [[1.0, 0.0, 0.0]],
            )

            offre = OffreDTO(
                titre="Data Engineer",
                description="Need ETL and cloud experience",
                entreprise="TechAtlas",
                localisation="Casablanca",
            )
            normalized = NormalizedOfferDTO(
                offre=offre,
                all_text="ETL cloud Python",
                keywords=["etl", "python", "cloud"],
                required_skills=["Communication"],
                required_technologies=["Python", "AWS"],
            )

            with patch.object(EmbeddingService, "embed_texts", return_value=[[1.0, 0.0, 0.0]]), patch.object(
                LLMClient,
                "chatbot_cv_improvement",
                return_value={"answer": "Ajoute un projet AWS", "action_items": ["Ajouter AWS"], "rewritten_bullets": []},
            ):
                answer = CVScoringService.answer_chatbot_question(
                    cv=cv,
                    offer=normalized,
                    question="Comment ameliorer mon CV pour cette offre?",
                )

            self.assertIn("answer", answer)
            self.assertTrue(answer["action_items"])

    def test_chatbot_actions_format_is_compact_and_fixed(self):
        payload = {
            "answer": "",
            "strengths": ["Python", "Docker"],
            "improvement_areas": ["AWS", "Airflow"],
            "action_items": [
                "Reecris le resume en ciblant Java Spring Boot API REST microservices",
                "Ajoute 2 projets backend avec stack, role et resultats mesurables",
                "Element supplementaire a ignorer",
            ],
            "rewritten_bullets": ["irrelevant"],
        }

        result = CVScoringService._compact_chatbot_response(
            payload,
            question="Propose 2 actions concretes pour ameliorer mon CV",
        )

        self.assertTrue(result["answer"].startswith("2 actions concretes :"))
        self.assertIn("1)", result["answer"])
        self.assertIn("2)", result["answer"])
        self.assertEqual(len(result["action_items"]), 2)
        self.assertEqual(result["strengths"], [])
        self.assertEqual(result["improvement_areas"], [])

    def test_chatbot_actions_format_falls_back_when_missing_actions(self):
        payload = {
            "answer": "",
            "strengths": ["Python"],
            "improvement_areas": ["Docker", "AWS"],
            "action_items": [],
            "rewritten_bullets": [],
        }

        result = CVScoringService._compact_chatbot_response(
            payload,
            question="Donne moi 2 actions concretes",
        )

        self.assertEqual(len(result["action_items"]), 2)
        self.assertTrue(result["answer"].startswith("2 actions concretes :"))
        self.assertIn("1)", result["answer"])
        self.assertIn("2)", result["answer"])

    def test_diagnostic_summary_replaces_advisory_explanation(self):
        result = CVScoringService._build_diagnostic_summary(
            overall_score=51,
            sub_scores={"technologies": 40, "skills": 60, "experience": 50, "semantic": 55},
            llm_explanation="Ajoute Docker et renforce AWS pour mieux correspondre.",
        )

        self.assertIn("Diagnostic matching", result)
        self.assertNotIn("Ajoute", result)
        self.assertNotIn("renforce", result.lower())

    def test_llm_extraction_without_key_raises(self):
        original_key = settings.GEMINI_API_KEY
        settings.GEMINI_API_KEY = ""
        try:
            with self.assertRaises(LLMServiceError):
                LLMClient.extract_cv_json("Sample CV")
        finally:
            settings.GEMINI_API_KEY = original_key


if __name__ == "__main__":
    unittest.main()




