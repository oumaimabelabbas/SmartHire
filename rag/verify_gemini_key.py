#!/usr/bin/env python3
"""Verify if the Gemini API key is valid before running the service."""

import sys
import requests
from config import settings

def verify_gemini_key() -> bool:
    """
    Verify that the Gemini API key is valid by making a test call.

    Returns:
        True if the key is valid, False otherwise.
    """
    if not settings.GEMINI_API_KEY:
        print("❌ ERREUR: GEMINI_API_KEY non configurée dans .env")
        print("   Veuillez définir votre clé API Gemini dans le fichier .env")
        print("   Obtenez une clé sur: https://makersuite.google.com/app/apikey")
        return False

    print(f"🔍 Vérification de la clé Gemini API...")
    print(f"   Clé: {settings.GEMINI_API_KEY[:20]}...")
    print(f"   Modèle: {settings.GEMINI_MODEL}")
    print(f"   URL: {settings.GEMINI_BASE_URL}")

    url = f"{settings.GEMINI_BASE_URL.rstrip('/')}/models/{settings.GEMINI_MODEL}:generateContent"

    # Minimal test payload
    payload = {
        "contents": [{"role": "user", "parts": [{"text": "test"}]}],
        "generationConfig": {"temperature": 0.0},
    }

    try:
        response = requests.post(
            url,
            params={"key": settings.GEMINI_API_KEY},
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=10,
        )

        if response.status_code == 404:
            print("❌ ERREUR 404: Votre clé Gemini est invalide ou révoquée")
            print("   Vérifiez votre clé sur: https://makersuite.google.com/app/apikey")
            return False
        elif response.status_code == 401:
            print("❌ ERREUR 401: Authentification échouée")
            print("   Votre clé API n'est pas valide")
            print("   Vérifiez votre clé sur: https://makersuite.google.com/app/apikey")
            return False
        elif response.status_code == 403:
            print("❌ ERREUR 403: Accès refusé")
            print("   Vérifiez que votre compte a accès à l'API Gemini")
            return False
        elif response.status_code >= 400:
            print(f"❌ ERREUR {response.status_code}: {response.text}")
            return False
        else:
            print("✅ La clé Gemini API est valide!")
            return True

    except requests.exceptions.Timeout:
        print("❌ ERREUR: Timeout lors de la vérification")
        print("   Vérifiez votre connexion Internet")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ ERREUR: Impossible de se connecter à l'API Gemini")
        print("   Vérifiez votre connexion Internet")
        return False
    except Exception as e:
        print(f"❌ ERREUR: {str(e)}")
        return False

if __name__ == "__main__":
    if verify_gemini_key():
        print("\n✨ Vous êtes prêt à utiliser Gemini!")
        sys.exit(0)
    else:
        print("\n⚠️  Veuillez configurer votre clé Gemini avant de continuer")
        sys.exit(1)

