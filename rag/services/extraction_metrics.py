"""
Métriques et monitoring pour extraction intelligente de CV.
Trace les performances, taux de succès, et erreurs.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ExtractionMetrics:
    """Collecte et analyse les métriques d'extraction."""

    def __init__(self, metrics_dir: str = "data"):
        self.metrics_dir = metrics_dir
        self.metrics_file = os.path.join(metrics_dir, "extraction_metrics.jsonl")
        os.makedirs(metrics_dir, exist_ok=True)

    def record_extraction(
        self,
        cv_id: str,
        filename: str,
        mode: str,
        success: bool,
        duration_seconds: float,
        llm_duration: Optional[float] = None,
        error_category: Optional[str] = None,
        technologies_count: int = 0,
        skills_count: int = 0,
        experiences_count: int = 0
    ) -> None:
        """
        Enregistrer une tentative d'extraction.

        Args:
            cv_id: ID du CV
            filename: Nom du fichier
            mode: Mode d'extraction (llm_json, regex_fallback, etc.)
            success: Si extraction réussie
            duration_seconds: Temps total
            llm_duration: Temps LLM si applicable
            error_category: Catégorie d'erreur si échec
            technologies_count: Nombre de technologies extraites
            skills_count: Nombre de compétences extraites
            experiences_count: Nombre d'expériences extraites
        """
        metric = {
            "timestamp": datetime.utcnow().isoformat(),
            "cv_id": cv_id,
            "filename": filename,
            "mode": mode,
            "success": success,
            "duration_seconds": duration_seconds,
            "llm_duration": llm_duration,
            "error_category": error_category,
            "technologies_count": technologies_count,
            "skills_count": skills_count,
            "experiences_count": experiences_count
        }

        # Écrire en JSONL
        try:
            with open(self.metrics_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(metric) + "\n")
        except Exception as e:
            logger.error(f"Erreur écriture métriques: {e}")

    def get_statistics(self, last_hours: int = 24) -> Dict[str, Any]:
        """
        Calculer statistiques des dernières N heures.

        Args:
            last_hours: Nombre d'heures à analyser

        Returns:
            Dict avec statistiques
        """
        if not os.path.exists(self.metrics_file):
            return self._default_stats()

        cutoff_time = datetime.utcnow() - timedelta(hours=last_hours)
        metrics = []

        try:
            with open(self.metrics_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        metric = json.loads(line)
                        metric_time = datetime.fromisoformat(metric["timestamp"])
                        if metric_time >= cutoff_time:
                            metrics.append(metric)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"Erreur lecture métriques: {e}")
            return self._default_stats()

        return self._calculate_stats(metrics)

    def _calculate_stats(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculer statistiques à partir des métriques."""
        if not metrics:
            return self._default_stats()

        total = len(metrics)
        successful = sum(1 for m in metrics if m.get("success"))
        failed = total - successful

        # Taux d'extraction LLM vs regex
        llm_count = sum(1 for m in metrics if m.get("mode") == "llm_json")
        regex_count = sum(1 for m in metrics if "regex" in m.get("mode", ""))

        # Erreurs par catégorie
        error_categories: Dict[str, int] = {}
        for m in metrics:
            if m.get("error_category"):
                cat = m["error_category"]
                error_categories[cat] = error_categories.get(cat, 0) + 1

        # Durées
        durations = [m["duration_seconds"] for m in metrics if m.get("duration_seconds")]
        avg_duration = sum(durations) / len(durations) if durations else 0
        max_duration = max(durations) if durations else 0

        # Données extraites
        techs = [m["technologies_count"] for m in metrics if successful]
        skills = [m["skills_count"] for m in metrics if successful]
        exps = [m["experiences_count"] for m in metrics if successful]

        return {
            "period_hours": 24,
            "total_extractions": total,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total * 100) if total > 0 else 0,

            "extraction_modes": {
                "llm_json": llm_count,
                "regex_fallback": regex_count,
                "other": total - llm_count - regex_count
            },

            "error_categories": error_categories,

            "duration": {
                "average_seconds": avg_duration,
                "max_seconds": max_duration,
                "min_seconds": min(durations) if durations else 0
            },

            "extraction_quality": {
                "avg_technologies": sum(techs) / len(techs) if techs else 0,
                "avg_skills": sum(skills) / len(skills) if skills else 0,
                "avg_experiences": sum(exps) / len(exps) if exps else 0
            }
        }

    def _default_stats(self) -> Dict[str, Any]:
        """Retourner stats vides."""
        return {
            "period_hours": 24,
            "total_extractions": 0,
            "successful": 0,
            "failed": 0,
            "success_rate": 0,
            "extraction_modes": {"llm_json": 0, "regex_fallback": 0, "other": 0},
            "error_categories": {},
            "duration": {"average_seconds": 0, "max_seconds": 0, "min_seconds": 0},
            "extraction_quality": {"avg_technologies": 0, "avg_skills": 0, "avg_experiences": 0}
        }

    def print_statistics(self, last_hours: int = 24) -> None:
        """Afficher statistiques en format lisible."""
        stats = self.get_statistics(last_hours)

        print("\n" + "=" * 60)
        print("📊 STATISTIQUES EXTRACTION CV")
        print("=" * 60)
        print(f"Période: Dernières {stats['period_hours']}h")
        print(f"Total: {stats['total_extractions']} extractions")
        print(f"✅ Succès: {stats['successful']} ({stats['success_rate']:.1f}%)")
        print(f"❌ Échecs: {stats['failed']}")

        print(f"\n📈 Modes d'extraction:")
        modes = stats['extraction_modes']
        print(f"  LLM JSON: {modes['llm_json']} ({modes['llm_json']/max(stats['total_extractions'],1)*100:.1f}%)")
        print(f"  Regex Fallback: {modes['regex_fallback']} ({modes['regex_fallback']/max(stats['total_extractions'],1)*100:.1f}%)")

        if stats['error_categories']:
            print(f"\n❌ Erreurs par catégorie:")
            for cat, count in stats['error_categories'].items():
                print(f"  {cat}: {count}")

        print(f"\n⏱️  Durées:")
        print(f"  Moyenne: {stats['duration']['average_seconds']:.2f}s")
        print(f"  Min: {stats['duration']['min_seconds']:.2f}s")
        print(f"  Max: {stats['duration']['max_seconds']:.2f}s")

        print(f"\n📋 Qualité extraction:")
        quality = stats['extraction_quality']
        print(f"  Technologies/CV: {quality['avg_technologies']:.1f}")
        print(f"  Compétences/CV: {quality['avg_skills']:.1f}")
        print(f"  Expériences/CV: {quality['avg_experiences']:.1f}")
        print("=" * 60 + "\n")


class ExtractionHealthCheck:
    """Health check pour l'extraction."""

    def __init__(self, metrics: ExtractionMetrics):
        self.metrics = metrics

    def is_healthy(self) -> bool:
        """Vérifier si le service d'extraction fonctionne correctement."""
        stats = self.metrics.get_statistics(last_hours=1)

        # Critères de santé
        if stats['total_extractions'] == 0:
            # Pas de données, c'est ok
            return True

        success_rate = stats['success_rate']
        if success_rate < 80:
            logger.warning(f"⚠️  Taux de succès bas: {success_rate:.1f}%")
            return False

        avg_duration = stats['duration']['average_seconds']
        if avg_duration > 30:
            logger.warning(f"⚠️  Durée extraction élevée: {avg_duration:.1f}s")
            return False

        return True

    def get_health_report(self) -> Dict[str, Any]:
        """Rapport de santé détaillé."""
        stats = self.metrics.get_statistics(last_hours=1)

        return {
            "status": "healthy" if self.is_healthy() else "unhealthy",
            "statistics": stats,
            "checks": {
                "success_rate": {
                    "value": stats['success_rate'],
                    "threshold": 80,
                    "passed": stats['success_rate'] >= 80
                },
                "average_duration": {
                    "value": stats['duration']['average_seconds'],
                    "threshold": 30,
                    "passed": stats['duration']['average_seconds'] <= 30
                },
                "llm_availability": {
                    "llm_extractions": stats['extraction_modes']['llm_json'],
                    "regex_fallbacks": stats['extraction_modes']['regex_fallback'],
                    "passed": stats['extraction_modes']['llm_json'] > 0
                }
            }
        }


# Instance globale
extraction_metrics = ExtractionMetrics()
health_check = ExtractionHealthCheck(extraction_metrics)


