"""Gestion centralisée des erreurs LLM et extraction."""

import logging
import time
from typing import Any, Callable, Dict, Optional, TypeVar
from functools import wraps
import requests

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ExtractionError(Exception):
    """Erreur générale d'extraction."""
    pass


class LLMRetryableError(Exception):
    """Erreur qui peut être réessayée."""
    pass


class LLMFatalError(Exception):
    """Erreur fatale qui nécessite un fallback."""
    pass


class CVExtractionError(ExtractionError):
    """Erreur spécifique à l'extraction de CV."""
    pass


class SkillStorageError(ExtractionError):
    """Erreur lors de la sauvegarde des compétences."""
    pass


class ErrorCategory:
    """Catégories d'erreurs pour classification."""
    API_KEY_MISSING = "API_KEY_MISSING"
    RATE_LIMIT = "RATE_LIMIT"
    TIMEOUT = "TIMEOUT"
    INVALID_JSON = "INVALID_JSON"
    PDF_CORRUPT = "PDF_CORRUPT"
    NETWORK_ERROR = "NETWORK_ERROR"
    UNKNOWN = "UNKNOWN"


def classify_error(exception: Exception) -> str:
    """Classer une erreur pour savoir comment la gérer."""
    error_str = str(exception).lower()

    if "api key" in error_str or "authentication" in error_str:
        return ErrorCategory.API_KEY_MISSING
    elif "rate limit" in error_str or "429" in error_str:
        return ErrorCategory.RATE_LIMIT
    elif "timeout" in error_str or "408" in error_str:
        return ErrorCategory.TIMEOUT
    elif "json" in error_str or "json.decoder" in error_str:
        return ErrorCategory.INVALID_JSON
    elif "pdf" in error_str or "corrupt" in error_str:
        return ErrorCategory.PDF_CORRUPT
    elif isinstance(exception, requests.exceptions.ConnectionError):
        return ErrorCategory.NETWORK_ERROR
    else:
        return ErrorCategory.UNKNOWN


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    backoff_factor: float = 2.0,
    retryable_exceptions: tuple = (LLMRetryableError, requests.exceptions.Timeout)
) -> Callable:
    """
    Décorateur pour retry avec backoff exponentiel.

    Args:
        max_retries: Nombre maximum de tentatives
        base_delay: Délai initial en secondes
        max_delay: Délai maximum entre les retries
        backoff_factor: Facteur de multiplication du délai
        retryable_exceptions: Exceptions à retry
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            delay = base_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    logger.debug(f"Tentative {attempt + 1}/{max_retries + 1} pour {func.__name__}")
                    return func(*args, **kwargs)

                except retryable_exceptions as e:
                    last_exception = e

                    if attempt < max_retries:
                        logger.warning(
                            f"Tentative {attempt + 1} échouée pour {func.__name__}: {str(e)}. "
                            f"Retry dans {delay:.1f}s..."
                        )
                        time.sleep(delay)
                        delay = min(delay * backoff_factor, max_delay)
                    else:
                        logger.error(
                            f"Toutes les {max_retries + 1} tentatives ont échoué pour {func.__name__}"
                        )
                        raise

            if last_exception:
                raise last_exception

        return wrapper
    return decorator


def safe_extract_json(
    llm_response: str,
    default_value: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Extraire JSON de manière sécurisée avec gestion d'erreurs.

    Args:
        llm_response: Réponse du LLM
        default_value: Valeur par défaut en cas d'erreur

    Returns:
        Dict parsé ou default_value
    """
    import json

    if not llm_response or not isinstance(llm_response, str):
        logger.error("Réponse LLM invalide: pas de contenu")
        return default_value or {}

    try:
        # Essayer de parser directement
        return json.loads(llm_response)
    except json.JSONDecodeError as e:
        logger.warning(f"Erreur JSON simple: {e}")

        # Essayer de nettoyer et re-parser
        try:
            cleaned = llm_response.strip()
            if cleaned.startswith('```json'):
                cleaned = cleaned[7:]
            if cleaned.startswith('```'):
                cleaned = cleaned[3:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]

            return json.loads(cleaned.strip())
        except json.JSONDecodeError as e2:
            logger.error(f"Erreur JSON après nettoyage: {e2}")
            raise CVExtractionError(f"Impossible de parser JSON: {str(e2)}") from e2


def handle_llm_error(
    error: Exception,
    context: str = ""
) -> tuple[bool, Optional[str]]:
    """
    Déterminer comment gérer une erreur LLM.

    Args:
        error: L'exception
        context: Contexte pour le logging

    Returns:
        (should_retry: bool, error_message: Optional[str])
    """
    category = classify_error(error)

    if category == ErrorCategory.API_KEY_MISSING:
        logger.error(f"❌ Clé API Gemini manquante {context}")
        return False, "Clé API Gemini non configurée"

    elif category == ErrorCategory.RATE_LIMIT:
        logger.warning(f"⏱️  Rate limit Gemini {context} - retry recommandé")
        return True, "Rate limit Gemini - tentative suivante..."

    elif category == ErrorCategory.TIMEOUT:
        logger.warning(f"⏱️  Timeout Gemini {context} - retry recommandé")
        return True, "Timeout - tentative suivante..."

    elif category == ErrorCategory.INVALID_JSON:
        logger.error(f"❌ Réponse JSON invalide {context}")
        return False, "Réponse LLM invalide"

    elif category == ErrorCategory.PDF_CORRUPT:
        logger.error(f"❌ PDF corrompu {context}")
        return False, "Fichier PDF corrompu ou invalide"

    elif category == ErrorCategory.NETWORK_ERROR:
        logger.warning(f"🌐 Erreur réseau {context} - retry recommandé")
        return True, "Erreur réseau - tentative suivante..."

    else:
        logger.error(f"❌ Erreur inconnue {context}: {str(error)}")
        return False, f"Erreur: {str(error)}"


def log_extraction_attempt(
    cv_id: Optional[str],
    filename: str,
    success: bool,
    duration_seconds: float,
    mode: str,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Logger une tentative d'extraction avec métriques.

    Args:
        cv_id: ID du CV extrait
        filename: Nom du fichier
        success: Si extraction réussie
        duration_seconds: Temps d'exécution
        mode: Mode d'extraction (llm_json, regex_fallback, etc.)
        details: Détails supplémentaires
    """
    status = "✅" if success else "❌"
    details_str = ""

    if details:
        if "error" in details:
            details_str = f" - Erreur: {details['error']}"
        if "fallback_reason" in details:
            details_str += f" - Fallback: {details['fallback_reason']}"

    logger.info(
        f"{status} Extraction [{mode}] ({cv_id or 'N/A'}) "
        f"- {filename} - {duration_seconds:.2f}s{details_str}"
    )


def validate_extracted_cv(cv_data: Dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Valider une CV extraite.

    Args:
        cv_data: Données extraites

    Returns:
        (is_valid: bool, errors: list[str])
    """
    errors = []

    # Champs obligatoires
    required_fields = ["nom", "email"]
    for field in required_fields:
        if not cv_data.get(field):
            errors.append(f"Champ obligatoire manquant: {field}")

    # Validations de format
    if cv_data.get("email") and "@" not in str(cv_data.get("email")):
        errors.append("Format email invalide")

    # Validations de liste
    if cv_data.get("technologies") and not isinstance(cv_data.get("technologies"), list):
        errors.append("Technologies doit être une liste")

    if cv_data.get("competences") and not isinstance(cv_data.get("competences"), list):
        errors.append("Compétences doit être une liste")

    # Validations de structure
    if cv_data.get("experiences"):
        if not isinstance(cv_data.get("experiences"), list):
            errors.append("Expériences doit être une liste")
        else:
            for i, exp in enumerate(cv_data.get("experiences", [])):
                if not isinstance(exp, dict):
                    errors.append(f"Expérience {i} invalide")
                elif not exp.get("titre") or not exp.get("entreprise"):
                    errors.append(f"Expérience {i} incomplet")

    return len(errors) == 0, errors



