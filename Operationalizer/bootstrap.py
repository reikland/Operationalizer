"""
bootstrap.py

Responsabilités :
- Définir un dossier cache (macOS: ~/Library/Caches, sinon ~/.cache)
- Chdir vers ce cache pour éviter les problèmes de chemins relatifs attendus upstream
- S'assurer que le fichier JSON d'exemples attendu par forecasting_tools existe en local
"""

from __future__ import annotations

import json
import os
from pathlib import Path


APP_DIR = Path(__file__).resolve().parent

mac_cache_root = Path.home() / "Library" / "Caches"
cache_root = mac_cache_root if mac_cache_root.exists() else (Path.home() / ".cache")
CACHE_DIR = cache_root / "forecasting-tools-streamlit-app"

EXAMPLES_REL = Path(
    "forecasting_tools/agents_and_tools/question_generators/q3_q4_quarterly_questions.json"
)
EXAMPLES_PATH = CACHE_DIR / EXAMPLES_REL


def bootstrap_runtime(*, do_chdir: bool = True) -> None:
    """
    Prépare le runtime pour éviter les collisions/chemins relatifs.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if do_chdir:
        os.chdir(CACHE_DIR)


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


def bootstrap_all() -> None:
    """
    Appelé tout en haut de app.py, AVANT tout import forecasting_tools.
    """
    bootstrap_runtime(do_chdir=True)
    ensure_question_examples_file()
