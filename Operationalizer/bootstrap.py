"""
bootstrap.py

Responsabilités :
- Définir un dossier cache (macOS: ~/Library/Caches, sinon ~/.cache)
- S'assurer que le fichier JSON d'exemples attendu par forecasting_tools existe
- IMPORTANT : ne jamais faire de chdir global (sinon Streamlit casse au rerun)
- Fournir un context manager pour exécuter forecasting_tools avec le bon cwd
"""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from pathlib import Path

# Répertoire du code (utile pour debug / affichage dans l'UI)
APP_DIR = Path(__file__).resolve().parent

# Cache cross-platform (Streamlit Cloud: /home/appuser/.cache/...)
mac_cache_root = Path.home() / "Library" / "Caches"
cache_root = mac_cache_root if mac_cache_root.exists() else (Path.home() / ".cache")
CACHE_DIR = cache_root / "forecasting-tools-streamlit-app"

# Chemin relatif attendu upstream
EXAMPLES_REL = Path(
    "forecasting_tools/agents_and_tools/question_generators/q3_q4_quarterly_questions.json"
)
EXAMPLES_PATH = CACHE_DIR / EXAMPLES_REL


def ensure_question_examples_file() -> Path:
    """
    Crée (si absent) le JSON d'exemples attendu par forecasting_tools
    à un chemin relatif particulier.
    """
    if EXAMPLES_PATH.exists():
        return EXAMPLES_PATH

    EXAMPLES_PATH.parent.mkdir(parents=True, exist_ok=True)

    try:
        import importlib.resources as resources

        pkg_file = (
            resources.files("forecasting_tools.agents_and_tools.question_generators")
            .joinpath(EXAMPLES_REL.name)
        )
        EXAMPLES_PATH.write_text(pkg_file.read_text(encoding="utf-8"), encoding="utf-8")
        return EXAMPLES_PATH

    except Exception:
        # Fallback minimal, conforme à ton ancien schéma ("question_text", etc.)
        fallback_examples = [
            {
                "question_text": "Will the fallback example file load correctly?",
                "resolution_criteria": "The app reads the local JSON without errors.",
                "resolution_date": "2026-12-31",
                "extra_context": "Local stub provided when upstream data is unavailable.",
            }
        ]
        EXAMPLES_PATH.write_text(json.dumps(fallback_examples, indent=2), encoding="utf-8")
        return EXAMPLES_PATH


@contextmanager
def in_forecasting_tools_cwd():
    """
    À utiliser autour de TOUT import + usage de forecasting_tools.
    forecasting_tools ouvre parfois des fichiers via des chemins relatifs, donc on
    met temporairement le cwd sur CACHE_DIR (puis on le restaure).
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    prev = os.getcwd()
    os.chdir(CACHE_DIR)
    try:
        yield CACHE_DIR
    finally:
        os.chdir(prev)


def bootstrap_all() -> None:
    """
    Appelé tout en haut de app.py, AVANT tout import forecasting_tools.
    Ne change PAS le cwd globalement.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    ensure_question_examples_file()

