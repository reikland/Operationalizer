import json
import os
from pathlib import Path
from typing import Any

mac_cache_root = Path.home() / "Library" / "Caches"
cache_root = mac_cache_root if mac_cache_root.exists() else (Path.home() / ".cache")
CACHE_DIR = cache_root / "forecasting-tools-streamlit-app"

EXAMPLES_REL = Path(
    "forecasting_tools/agents_and_tools/question_generators/q3_q4_quarterly_questions.json"
)
EXAMPLES_PATH = CACHE_DIR / EXAMPLES_REL


def initialize_cache() -> None:
    """Prepare the cache directory and ensure the examples JSON exists."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    os.chdir(CACHE_DIR)
    ensure_question_examples_file()


def ensure_question_examples_file() -> Path:
    """Guarantee the question examples JSON is present in the cache."""
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
    except Exception:
        fallback_examples: list[dict[str, Any]] = [
            {
                "question_text": "Will the fallback example file load correctly?",
                "resolution_criteria": "The app reads the local JSON without errors.",
                "resolution_date": "2026-12-31",
                "extra_context": "Local stub provided when upstream data is unavailable.",
            }
        ]
        EXAMPLES_PATH.write_text(
            json.dumps(fallback_examples, indent=2), encoding="utf-8"
        )

    return EXAMPLES_PATH
