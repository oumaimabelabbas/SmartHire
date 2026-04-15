"""
Démonstration pratique de l'extraction intelligente de CV.
Ce script montre comment utiliser le système d'extraction.
"""

import json
from io import BytesIO
from unittest.mock import patch

from models.cv_model import ExtractedCVDTO
from services.cv_extractor import CVExtractor
from services.error_handling import validate_extracted_cv
from services.extraction_metrics import extraction_metrics, health_check
from services.skill_store import SkillStore


def demo_llm_extraction():
    """Démonstration: extraction avec LLM."""
    print("\n" + "=" * 70)
    print("📋 DÉMO 1: Extraction CV avec LLM")
    print("=" * 70)

    # Simuler un PDF
    mock_cv_text = """
    Jean Dupont
    jean.dupont@techmail.com
    +33 6 12 34 56 78

    Senior Software Engineer with 5 years of experience

    EXPERIENCE
    Senior Developer at TechCorp (2022-2024)
    - Led team of 5 developers
    - Built Python/Docker microservices
    - 24 months duration

    Developer at StartupX (2020-2022)
    - Full-stack development
    - React and Node.js
    - 24 months duration

    SKILLS
    Leadership, Agile, Problem-solving, Communication

    TECHNOLOGIES
    Python, Java, JavaScript, Docker, Kubernetes
    PostgreSQL, React, Node.js, AWS, Git

    EDUCATION
    Master in Computer Science from ENSAM (2018)
    Bachelor in Engineering from INSA (2015)

    LANGUAGES
    French (Native), English (Fluent), Spanish (Intermediate)
    """

    # Mock LLM response
    mock_llm_response = {
        "nom": "Jean Dupont",
        "email": "jean.dupont@techmail.com",
        "telephone": "+33612345678",
        "resume": "Senior Software Engineer with 5 years of experience",
        "technologies": ["Python", "Java", "JavaScript", "Docker", "Kubernetes", "PostgreSQL", "React", "Node.js", "AWS"],
        "competences": ["Leadership", "Agile", "Problem-solving", "Communication"],
        "annees_experience": 5,
        "experiences": [
            {
                "titre": "Senior Developer",
                "entreprise": "TechCorp",
                "duree_mois": 24,
                "description": "Led team of 5 developers, built Python/Docker microservices",
                "technologies": ["Python", "Docker"]
            },
            {
                "titre": "Developer",
                "entreprise": "StartupX",
                "duree_mois": 24,
                "description": "Full-stack development with React and Node.js",
                "technologies": ["React", "Node.js"]
            }
        ],
        "educations": [
            {
                "diplome": "Master",
                "etablissement": "ENSAM",
                "annee": 2018,
                "specialisation": "Computer Science"
            },
            {
                "diplome": "Bachelor",
                "etablissement": "INSA",
                "annee": 2015,
                "specialisation": "Engineering"
            }
        ],
        "langues": [
            {"nom": "Français", "niveau": "Natif"},
            {"nom": "Anglais", "niveau": "Courant"},
            {"nom": "Espagnol", "niveau": "Intermédiaire"}
        ]
    }

    with patch.object(CVExtractor, "_extract_pdf_text", return_value=mock_cv_text), \
         patch.object(CVExtractor, "_extract_with_llm_retry", return_value=mock_llm_response), \
         patch.object(CVExtractor, "_index_cv_chunks"), \
         patch.object(CVExtractor, "_persist_structured_skills"):

        result = CVExtractor.extract_from_pdf(b"PDF content", "cv_demo.pdf")

        print(f"\n✅ CV extrait avec succès!")
        print(f"\nDonnées extraites:")
        print(f"  Nom: {result.nom}")
        print(f"  Email: {result.email}")
        print(f"  Téléphone: {result.telephone}")
        print(f"  Années d'expérience: {result.annees_experience}")
        print(f"\n  Technologies ({len(result.technologies)}):")
        for tech in result.technologies[:5]:
            print(f"    - {tech}")
        if len(result.technologies) > 5:
            print(f"    ... et {len(result.technologies) - 5} autres")

        print(f"\n  Compétences ({len(result.competences)}):")
        for skill in result.competences:
            print(f"    - {skill}")

        print(f"\n  Expériences ({len(result.experiences)}):")
        for exp in result.experiences:
            print(f"    - {exp.titre} at {exp.entreprise} ({exp.duree_mois} mois)")

        print(f"\n  Formations ({len(result.educations)}):")
        for edu in result.educations:
            print(f"    - {edu.diplome} from {edu.etablissement} ({edu.annee})")

        print(f"\n  Langues ({len(result.langues)}):")
        for lang in result.langues:
            print(f"    - {lang.nom}: {lang.niveau}")

        # Validation
        is_valid, errors = validate_extracted_cv(result.model_dump())
        print(f"\n✅ Validation: {'OK' if is_valid else 'ERREURS'}")
        if not is_valid:
            for error in errors:
                print(f"  ⚠️  {error}")

        return result


def demo_regex_fallback():
    """Démonstration: fallback vers regex."""
    print("\n" + "=" * 70)
    print("📋 DÉMO 2: Fallback Regex quand LLM échoue")
    print("=" * 70)

    mock_cv_text = """
    JEAN MARTIN
    martin.jean@mail.com
    +33723456789

    10 ans d'expérience en développement

    Compétences: Python, Java, Docker
    """

    from services.llm_client import LLMServiceError

    with patch.object(CVExtractor, "_extract_pdf_text", return_value=mock_cv_text), \
         patch.object(
             CVExtractor,
             "_extract_with_llm_retry",
             side_effect=LLMServiceError("API Key missing")
         ), \
         patch.object(CVExtractor, "_index_cv_chunks"), \
         patch.object(CVExtractor, "_persist_structured_skills"):

        result = CVExtractor.extract_from_pdf(b"PDF", "cv_fallback.pdf")

        print(f"\n⚠️  LLM échoué -> Fallback Regex")
        print(f"\n✅ CV extrait avec regex:")
        print(f"  Nom: {result.nom}")
        print(f"  Email: {result.email}")
        print(f"  Téléphone: {result.telephone}")
        if result.technologies:
            print(f"  Technologies: {', '.join(result.technologies)}")


def demo_validation():
    """Démonstration: validation de CV."""
    print("\n" + "=" * 70)
    print("✅ DÉMO 3: Validation de CV extrait")
    print("=" * 70)

    # CV valide
    print("\nTest 1: CV Valide")
    valid_cv = {
        "nom": "Alice Durand",
        "email": "alice@example.com",
        "technologies": ["Python", "Docker"],
        "competences": ["Leadership"],
        "experiences": [{"titre": "Dev", "entreprise": "TechCorp"}]
    }
    is_valid, errors = validate_extracted_cv(valid_cv)
    print(f"  Résultat: {'✅ VALIDE' if is_valid else '❌ INVALIDE'}")
    if errors:
        for error in errors:
            print(f"    - {error}")

    # CV avec email invalide
    print("\nTest 2: Email Invalide")
    invalid_cv = {
        "nom": "Bob Smith",
        "email": "not-an-email"
    }
    is_valid, errors = validate_extracted_cv(invalid_cv)
    print(f"  Résultat: {'✅ VALIDE' if is_valid else '❌ INVALIDE'}")
    if errors:
        for error in errors:
            print(f"    - {error}")

    # CV avec champs manquants
    print("\nTest 3: Champs Obligatoires Manquants")
    incomplete_cv = {
        "nom": "Charlie Brown"
        # email manquant
    }
    is_valid, errors = validate_extracted_cv(incomplete_cv)
    print(f"  Résultat: {'✅ VALIDE' if is_valid else '❌ INVALIDE'}")
    if errors:
        for error in errors:
            print(f"    - {error}")


def demo_skill_storage():
    """Démonstration: stockage compétences."""
    print("\n" + "=" * 70)
    print("💾 DÉMO 4: Stockage Compétences Structurées")
    print("=" * 70)

    store = SkillStore()

    # Profils de test
    profiles = [
        {
            "nom": "Alice Durand",
            "email": "alice@example.com",
            "technologies": ["Python", "Docker", "Kubernetes"],
            "competences": ["Leadership", "Agile"],
            "annees_experience": 5
        },
        {
            "nom": "Bob Smith",
            "email": "bob@example.com",
            "technologies": ["JavaScript", "React", "Node.js"],
            "competences": ["Communication", "Problem-solving"],
            "annees_experience": 3
        }
    ]

    print(f"\nSauvegarde {len(profiles)} profils...")
    for i, profile in enumerate(profiles, 1):
        store.save_cv_profile(f"cv-{i}", profile)
        print(f"  ✅ {profile['nom']} sauvegardé")

    # Charger et afficher
    print(f"\nChargement des profils...")
    data = store._read()
    for cv_id, entry in data.items():
        profile = entry.get("profile", {})
        print(f"\n  {profile.get('nom')}")
        print(f"    Email: {profile.get('email')}")
        print(f"    Technologies: {', '.join(profile.get('technologies', []))}")
        print(f"    Compétences: {', '.join(profile.get('competences', []))}")
        print(f"    Expérience: {profile.get('annees_experience')} ans")


def demo_metrics():
    """Démonstration: métriques et monitoring."""
    print("\n" + "=" * 70)
    print("📊 DÉMO 5: Métriques et Health Check")
    print("=" * 70)

    # Simuler quelques extractions
    print("\nSimulation d'extractions...")

    for i in range(5):
        extraction_metrics.record_extraction(
            cv_id=f"cv-demo-{i}",
            filename=f"cv_{i}.pdf",
            mode="llm_json" if i % 2 == 0 else "regex_fallback",
            success=i < 4,  # 1 échec
            duration_seconds=2.0 + i * 0.5,
            technologies_count=8 + i,
            skills_count=4,
            experiences_count=3
        )

    # Afficher statistiques
    extraction_metrics.print_statistics(last_hours=24)

    # Health check
    print("\n🏥 Health Check:")
    report = health_check.get_health_report()
    print(f"  Status: {report['status'].upper()}")
    print(f"  Success Rate: {report['checks']['success_rate']['value']:.1f}%")
    print(f"  Avg Duration: {report['checks']['average_duration']['value']:.2f}s")
    print(f"  LLM Extractions: {report['checks']['llm_availability']['llm_extractions']}")


def main():
    """Exécuter toutes les démos."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + " DÉMO: Extraction Intelligente de CV ".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")

    try:
        # Démo 1
        result = demo_llm_extraction()

        # Démo 2
        demo_regex_fallback()

        # Démo 3
        demo_validation()

        # Démo 4
        demo_skill_storage()

        # Démo 5
        demo_metrics()

        print("\n" + "=" * 70)
        print("✅ TOUTES LES DÉMOS COMPLÉTÉES")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\n❌ Erreur during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


