#!/usr/bin/env python3
"""Script Windows pour tester la clé Gemini et lancer le service RAG"""

import os
import sys
import subprocess
from pathlib import Path

def print_banner(text):
    """Afficher un bannière"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")

def main():
    # Configuration de base
    script_dir = Path(__file__).parent.absolute()
    print_banner("SmartHire RAG - Vérification Gemini API")

    print(f"📍 Répertoire: {script_dir}")

    # Vérifier le fichier .env
    env_file = script_dir / ".env"
    if not env_file.exists():
        print("❌ Erreur: Le fichier .env n'existe pas!")
        print(f"   Créez le fichier: {env_file}")
        sys.exit(1)

    # Charger la configuration
    print("📋 Configuration chargée depuis .env")

    # Vérifier que verify_gemini_key.py existe
    verify_script = script_dir / "verify_gemini_key.py"
    if not verify_script.exists():
        print("❌ Erreur: Le fichier verify_gemini_key.py n'existe pas!")
        sys.exit(1)

    # Exécuter la vérification
    print("\n🔍 Vérification de la clé Gemini API...")
    print("-" * 60)

    try:
        result = subprocess.run(
            [sys.executable, str(verify_script)],
            cwd=str(script_dir),
            capture_output=False,
            text=True
        )

        if result.returncode != 0:
            print("\n❌ La clé Gemini n'est pas valide!")
            print("💡 Pour corriger:")
            print("   1. Allez sur: https://makersuite.google.com/app/apikey")
            print("   2. Générez une nouvelle clé API")
            print("   3. Mettez à jour GEMINI_API_KEY dans le fichier .env")
            print("   4. Relancez ce script")
            sys.exit(1)

        print("\n✅ La clé Gemini est valide!")
        print("\n💡 Prêt à démarrer le service RAG!")

    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

