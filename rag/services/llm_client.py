"""LLM client and prompt engineering for Gemini-first RAG."""

import json
import logging
import re
from typing import Any, Dict, List

import requests

from config import settings

logger = logging.getLogger(__name__)


class LLMServiceError(Exception):
    """Raised when the LLM API call fails."""


class LLMClient:
    """Gemini-first helper for structured extraction, scoring and chatbot."""

    _FRENCH_OUTPUT_RULE = (
        "Langue de sortie obligatoire: francais uniquement. "
        "N'utilise jamais l'anglais pour les phrases generees (sauf noms propres, acronymes techniques ou technologies)."
    )
    _SENSITIVE_ERROR_PATTERNS = [
        re.compile(r"([?&]key=)[^&\s]+", re.IGNORECASE),
        re.compile(r"(gemini[_-]?api[_-]?key\s*[=:]\s*)[^\s,;]+", re.IGNORECASE),
        re.compile(r"AIza[0-9A-Za-z_\-]{20,}"),
        re.compile(r"AQ\.[0-9A-Za-z_\-\.]{10,}"),
    ]

    @staticmethod
    def _require_gemini_key() -> None:
        if not settings.GEMINI_API_KEY:
            raise LLMServiceError("Probleme de cle Gemini: GEMINI_API_KEY manquante")

    @staticmethod
    def _chat_json(messages: List[Dict[str, str]], temperature: float = 0.0) -> Dict[str, Any]:
        return LLMClient._chat_json_gemini(messages, temperature=temperature)


    @staticmethod
    def _chat_json_gemini(messages: List[Dict[str, str]], temperature: float = 0.0) -> Dict[str, Any]:
        LLMClient._require_gemini_key()
        payload = LLMClient._build_gemini_payload(messages, temperature)
        url = f"{settings.GEMINI_BASE_URL.rstrip('/')}/models/{settings.GEMINI_MODEL}:generateContent"

        try:
            response = requests.post(
                url,
                params={"key": settings.GEMINI_API_KEY},
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=settings.GEMINI_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            body = response.json()
            content = LLMClient._extract_gemini_text(body)
            return LLMClient._parse_json_text(content)
        except requests.exceptions.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            if status_code in {401, 403, 404}:
                error_msg = (
                    f"Probleme de cle Gemini ({status_code}): authentification invalide ou acces refuse. "
                    "Verifie GEMINI_API_KEY dans .env."
                )
                logger.error(error_msg)
                raise LLMServiceError(error_msg) from exc
            raise LLMServiceError(LLMClient._sanitize_error_message(str(exc))) from exc
        except Exception as exc:
            raise LLMServiceError(LLMClient._sanitize_error_message(str(exc))) from exc

    @staticmethod
    def _build_gemini_payload(messages: List[Dict[str, str]], temperature: float) -> Dict[str, Any]:
        system_parts = [LLMClient._FRENCH_OUTPUT_RULE]
        contents = []

        for message in messages:
            role = str(message.get("role", "user")).lower()
            text = str(message.get("content", ""))
            if not text:
                continue
            if role == "system":
                system_parts.append(text)
            else:
                contents.append(
                    {
                        "role": "user" if role not in {"user", "model"} else role,
                        "parts": [{"text": text}],
                    }
                )

        payload: Dict[str, Any] = {
            "contents": contents or [{"role": "user", "parts": [{"text": ""}]}],
            "generationConfig": {
                "temperature": temperature,
                "responseMimeType": "application/json",
            },
        }

        if system_parts:
            payload["systemInstruction"] = {"parts": [{"text": "\n\n".join(system_parts)}]}

        return payload

    @staticmethod
    def _extract_gemini_text(body: Dict[str, Any]) -> str:
        candidates = body.get("candidates") or []
        if not candidates:
            raise LLMServiceError("Réponse Gemini vide")

        first_candidate = candidates[0] or {}
        content = first_candidate.get("content") or {}
        parts = content.get("parts") or []
        texts = []
        for part in parts:
            if isinstance(part, dict) and part.get("text"):
                texts.append(str(part["text"]))

        text = "".join(texts).strip()
        if not text:
            raise LLMServiceError("Réponse Gemini sans texte exploitable")
        return text

    @staticmethod
    def _parse_json_text(content: str) -> Dict[str, Any]:
        cleaned = content.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise LLMServiceError(f"JSON Gemini invalide: {exc}") from exc

    @staticmethod
    def extract_cv_json(cv_text: str) -> Dict[str, Any]:
        """
        Extraire un CV en JSON structuré.

        Args:
            cv_text: Texte brut du CV (max 12000 caractères)

        Returns:
            Dict avec structure définie

        Raises:
            LLMServiceError: Si extraction échoue
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "Tu es un expert en extraction de données de CV. "
                    "Tu extrais les informations d'un CV brut et tu reponds STRICTEMENT en JSON valide. "
                    "Toutes les valeurs textuelles que tu generes doivent etre en francais. "
                    "\n"
                    "Structure JSON requise:\n"
                    "{\n"
                    '  "nom": "string (nom complet du candidat)",\n'
                    '  "email": "string (adresse email)",\n'
                    '  "telephone": "string (numero de telephone, optionnel)",\n'
                    '  "resume": "string (resume professionnel, max 500 chars)",\n'
                    '  "technologies": ["list of tech/programming languages"],\n'
                    '  "competences": ["list of soft skills"],\n'
                    '  "annees_experience": "int (years of experience)",\n'
                    '  "experiences": [\n'
                    "    {\n"
                    '      "titre": "job title",\n'
                    '      "entreprise": "company name",\n'
                    '      "duree_mois": "int or null",\n'
                    '      "description": "string or null",\n'
                    '      "technologies": ["list of techs used"]\n'
                    "    }\n"
                    "  ],\n"
                    '  "educations": [\n'
                    "    {\n"
                    '      "diplome": "degree name",\n'
                    '      "etablissement": "school/university",\n'
                    '      "annee": "int or null",\n'
                    '      "specialisation": "string or null"\n'
                    "    }\n"
                    "  ],\n"
                    '  "langues": [\n'
                    "    {\n"
                    '      "nom": "language name",\n'
                    '      "niveau": "proficiency level (Native, Fluent, Intermediate, Beginner)"\n'
                    "    }\n"
                    "  ]\n"
                    "}\n"
                    "\n"
                    "REGLES IMPORTANTES:\n"
                    "1. Reponds UNIQUEMENT avec du JSON valide\n"
                    "2. Ne pas inclure de texte avant ou apres le JSON\n"
                    "3. Normalise les technologies (ex: 'python' -> 'Python', 'js' -> 'JavaScript')\n"
                    "4. Normalise les competences (ex: 'teamwork' -> 'Travail en equipe')\n"
                    "5. Si un champ est manquant, utilise une valeur par defaut (liste vide, null, ou string vide)\n"
                    "6. Les annees_experience doivent etre un entier\n"
                    "7. Valide que le JSON est bien forme"
                ),
            },
            {
                "role": "user",
                "content": f"Extrait les donnees de ce CV brut et reponds en JSON valide UNIQUEMENT:\n\n{cv_text[:12000]}"
            },
        ]

        result = LLMClient._chat_json(messages, temperature=0.0)

        # Validation rapide
        if not result.get("nom"):
            raise LLMServiceError("Extraction LLM: 'nom' champ manquant")

        return result

    @staticmethod
    def evaluate_cv_offer_match(
        cv_payload: Dict[str, Any],
        offer_payload: Dict[str, Any],
        evidence_chunks: List[str],
    ) -> Dict[str, Any]:
        messages = [
            {
                "role": "system",
                "content": (
                    "Tu es un expert RH technique. Tu évalues le matching CV/offre uniquement à partir des evidences fournies. "
                    "Réponds en francais STRICTEMENT en JSON valide avec les cles: "
                    "overall_score (0-100), sub_scores (technologies, skills, experience, semantic), "
                    "strengths (liste), gaps (liste), improvements (liste max 5), explanation (diagnostic court). "
                    "Regles: "
                    "1) overall_score cohérent avec les sub_scores. "
                    "2) strengths/gaps doivent citer des points précis, pas génériques, max 3 items chacun, pas de doublons. "
                    "3) improvements = actions concrètes mesurables, 3 a 5 items, 1 phrase chacun. "
                    "4) explanation = francais uniquement, format strict 'Score global X. Points forts: ...', 1 phrase, max 200 caracteres. "
                    "5) Style phrases courtes, sans guillemets ni jargon. "
                    "6) N'invente pas d'informations absentes des evidences."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"CV structure:\n{json.dumps(cv_payload, ensure_ascii=True)}\n\n"
                    f"Offre structuree:\n{json.dumps(offer_payload, ensure_ascii=True)}\n\n"
                    f"Evidences retrieval (chunks):\n{json.dumps(evidence_chunks[:6], ensure_ascii=True)}"
                ),
            },
        ]
        result = LLMClient._chat_json(messages, temperature=0.1)
        result.setdefault("overall_score", 0)
        result.setdefault("sub_scores", {})
        result.setdefault("strengths", [])
        result.setdefault("gaps", [])
        result.setdefault("improvements", [])
        result.setdefault("explanation", "Evaluation generee par LLM")
        return result

    @staticmethod
    def chatbot_cv_improvement(
        question: str,
        cv_payload: Dict[str, Any],
        offer_payload: Dict[str, Any],
        evidence_chunks: List[str],
        history: List[Dict[str, str]] | None = None,
    ) -> Dict[str, Any]:
        history = history or []
        messages = [
            {
                "role": "system",
                "content": (
                    "Tu es un coach CV concis. Tu aides le candidat a ameliorer son CV pour une offre precise. "
                    "Utilise uniquement les evidences retrieval. Reponds en francais STRICTEMENT en JSON valide avec les cles: "
                    "answer (resume court en 1 a 2 phrases), "
                    "strengths (liste vide), improvement_areas (liste vide), "
                    "action_items (liste de 1 a 3 actions), rewritten_bullets (liste vide). "
                    "Regles: "
                    "1) Reponds STRICTEMENT a la question. "
                    "2) Si la question demande un nombre (ex: 2 ou 3), respecte ce nombre. "
                    "3) Chaque action doit etre specifique, mesurable, et liee a l'offre. "
                    "4) Phrases completes et comprehensibles, pas de texte coupe. "
                    "5) Pas de repetition entre answer et action_items. "
                    "6) Style phrases courtes, sans guillemets ni jargon. "
                    "7) N'invente pas d'informations absentes des evidences. "
                    "8) Si la question est hors sujet, reponds une phrase courte demandant une question CV/offre."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Question candidat: {question}\n"
                    f"CV structure: {json.dumps(cv_payload, ensure_ascii=True)}\n"
                    f"Offre structuree: {json.dumps(offer_payload, ensure_ascii=True)}\n"
                    f"Evidences retrieval: {json.dumps(evidence_chunks[:8], ensure_ascii=True)}\n"
                    f"Historique: {json.dumps(history[-6:], ensure_ascii=True)}"
                ),
            },
        ]
        result = LLMClient._chat_json(messages, temperature=0.2)
        result.setdefault("answer", "")
        result.setdefault("strengths", [])
        result.setdefault("improvement_areas", [])
        result.setdefault("action_items", [])
        result.setdefault("rewritten_bullets", [])
        return result

    @staticmethod
    def _sanitize_error_message(message: str) -> str:
        text = " ".join(str(message or "").split())
        if not text:
            return "Erreur Gemini indisponible"

        sanitized = text
        for pattern in LLMClient._SENSITIVE_ERROR_PATTERNS:
            sanitized = pattern.sub(r"\1[REDACTED]" if pattern.groups else "[REDACTED]", sanitized)

        sanitized = re.sub(
            r"https?://[^\s]*generativelanguage\.googleapis\.com[^\s]*",
            "https://generativelanguage.googleapis.com/[REDACTED]",
            sanitized,
            flags=re.IGNORECASE,
        )
        return sanitized

