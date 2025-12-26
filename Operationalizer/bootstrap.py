# bootstrap.py
from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path
import os
import threading

APP_DIR = Path(__file__).resolve().parent

mac_cache_root = Path.home() / "Library" / "Caches"
cache_root = mac_cache_root if mac_cache_root.exists() else (Path.home() / ".cache")
CACHE_DIR = cache_root / "forecasting-tools-streamlit-app"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

EXAMPLES_REL = Path(
    "forecasting_tools/agents_and_tools/question_generators/q3_q4_quarterly_questions.json"
)
EXAMPLES_PATH = CACHE_DIR / EXAMPLES_REL

_CWD_LOCK = threading.Lock()


def ensure_question_examples_file() -> Path:
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


@contextmanager
def forecasting_tools_cwd():
    """
    Contexte sécurisé: on se place dans CACHE_DIR uniquement pendant l'usage
    de forecasting_tools (qui attend un chemin relatif), puis on revient.
    """
    ensure_question_examples_file()
    with _CWD_LOCK:
        prev = Path.cwd()
        os.chdir(CACHE_DIR)
        try:
            yield
        finally:
            os.chdir(prev)


def bootstrap_all() -> None:
    """
    Important: NE PAS chdir ici.
    On s'assure seulement que le fichier attendu existe dans le cache.
    """
    ensure_question_examples_file()
