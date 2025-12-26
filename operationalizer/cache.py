import json
from pathlib import Path
from typing import Any

mac_cache_root = Path.home() / "Library" / "Caches"
cache_root = mac_cache_root if mac_cache_root.exists() else (Path.home() / ".cache")
CACHE_DIR = cache_root / "forecasting-tools-streamlit-app"

EXAMPLES_REL = Path(
    "forecasting_tools/agents_and_tools/question_generators/q3_q4_quarterly_questions.json"
)
EXAMPLES_PATH = CACHE_DIR / EXAMPLES_REL


def initialize_cache(script_dir: Path | None = None) -> None:
    """Prepare cache artifacts without moving the working directory.

    Optionally mirror the main script into the cache directory so
    deployments that still run from the cache path can locate ``app.py``.
    """

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    ensure_question_examples_file()
    mirror_examples_into_cwd()

    if script_dir:
        mirror_script_into_cache(script_dir)


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


def mirror_examples_into_cwd() -> None:
    """Copy examples into the current working directory for relative opens."""

    try:
        cwd_target = Path.cwd() / EXAMPLES_REL
        if cwd_target.exists():
            return

        cwd_target.parent.mkdir(parents=True, exist_ok=True)
        cwd_target.write_text(EXAMPLES_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    except Exception:
        # Best-effort mirror; downstream code still has the cache copy.
        pass


def mirror_script_into_cache(script_dir: Path) -> None:
    """Ensure the primary script is reachable inside the cache directory."""

    try:
        source = script_dir / "app.py"
        if not source.exists():
            return

        target = CACHE_DIR / source.name
        if target.exists():
            return

        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    except Exception:
        # If mirroring fails, the app can still run from its original location.
        pass
