from __future__ import annotations

import asyncio
import json
import os
import re
import textwrap
import urllib.request
from pathlib import Path
from typing import Any, List, Optional

# Path relatif attendu upstream par forecasting_tools (open() relatif au CWD)
EXAMPLES_REL = Path(
    "forecasting_tools/agents_and_tools/question_generators/q3_q4_quarterly_questions.json"
)

# URL raw GitHub (optionnelle) pour récupérer le fichier réel sans importer forecasting_tools
EXAMPLES_RAW_URL = (
    "https://raw.githubusercontent.com/Metaculus/forecasting-tools/main/"
    "forecasting_tools/agents_and_tools/question_generators/q3_q4_quarterly_questions.json"
)

_SPLIT_RE = re.compile(r"[;\n,\|]+")


def clean_indents(s: str) -> str:
    return textwrap.dedent(s).strip()


def run_async(coro):
    """Run an async coroutine from Streamlit safely."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            new_loop = asyncio.new_event_loop()
            try:
                return new_loop.run_until_complete(coro)
            finally:
                new_loop.close()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def get_app_dir(app_file: str) -> Path:
    return Path(app_file).resolve().parent


def examples_runtime_path() -> Path:
    """
    Chemin ABSOLU du fichier examples, mais placé à un emplacement RELATIF
    au CWD (Path.cwd()) pour satisfaire le open(relpath) upstream.
    """
    return Path.cwd() / EXAMPLES_REL


def _download_text(url: str, timeout_sec: int = 10) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
        data = resp.read()
    # Le fichier upstream est du JSON UTF-8
    return data.decode("utf-8")


def ensure_question_examples_file() -> Path:
    """
    Assure l'existence du fichier JSON AU CHEMIN RELATIF attendu par forecasting_tools,
    sans jamais toucher au CWD.

    Stratégie:
    1) Si déjà présent: ok.
    2) Sinon, essaie de télécharger le JSON upstream (raw GitHub).
    3) Sinon, fallback minimal.
    """
    p = examples_runtime_path()
    if p.exists():
        return p

    p.parent.mkdir(parents=True, exist_ok=True)

    # Try remote download first (no forecasting_tools import needed)
    try:
        txt = _download_text(EXAMPLES_RAW_URL, timeout_sec=10)
        # Valide JSON (évite d'écrire du HTML d'erreur)
        json.loads(txt)
        p.write_text(txt, encoding="utf-8")
        return p
    except Exception:
        fallback_examples = [
            {
                "question_text": "Will the fallback example file load correctly?",
                "resolution_criteria": "The app reads the local JSON without errors.",
                "resolution_date": "2026-12-31",
                "extra_context": "Local stub provided when upstream data is unavailable.",
            }
        ]
        p.write_text(json.dumps(fallback_examples, indent=2), encoding="utf-8")
        return p


def parse_topics_cell(x: Any) -> List[str]:
    if x is None:
        return []
    if isinstance(x, float) and (x != x):  # NaN
        return []

    if isinstance(x, list):
        raw = x
    else:
        s = str(x).strip()
        if not s:
            return []
        if s.startswith("[") and s.endswith("]"):
            try:
                j = json.loads(s)
                raw = j if isinstance(j, list) else _SPLIT_RE.split(s)
            except Exception:
                raw = _SPLIT_RE.split(s)
        else:
            raw = _SPLIT_RE.split(s)

    out: List[str] = []
    for t in raw:
        tt = str(t).strip()
        if tt:
            out.append(tt)
    return out


def unique_preserve_order(items: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for it in items:
        if it not in seen:
            seen.add(it)
            out.append(it)
    return out


def to_dict(obj: Any) -> Any:
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, list):
        return [to_dict(x) for x in obj]
    if isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    if hasattr(obj, "model_dump") and callable(getattr(obj, "model_dump")):
        return to_dict(obj.model_dump())
    if hasattr(obj, "dict") and callable(getattr(obj, "dict")):
        return to_dict(obj.dict())
    return str(obj)


def build_related_research(decomp: Any, q_obj: Any) -> str:
    qd = to_dict(q_obj)
    return clean_indents(
        f"""
        Decomposer general research & approach:
        {getattr(decomp, "general_research_and_approach", "")}

        Proto-question (from decomposer):
        - Title: {qd.get("question_or_idea_text")}
        - Resolution process: {qd.get("resolution_process")}
        - Expected resolution date: {qd.get("expected_resolution_date")}
        - Background information: {qd.get("background_information")}
        - Past resolution / base rate: {qd.get("past_resolution")}
        - Other information: {qd.get("other_information")}
        """
    ).strip()


def configure_env(provider: str, api_key: str, asknews_key: str = "", perplexity_key: str = "") -> None:
    # Clean any prior config
    for k in [
        "OPENAI_API_KEY",
        "OPENAI_BASE_URL",
        "OPENAI_API_BASE",
        "OPENROUTER_API_KEY",
        "OPENROUTER_BASE_URL",
    ]:
        os.environ.pop(k, None)

    if api_key:
        if provider == "OpenRouter":
            base = "https://openrouter.ai/api/v1"
            os.environ["OPENAI_API_KEY"] = api_key
            os.environ["OPENROUTER_API_KEY"] = api_key
            os.environ["OPENAI_BASE_URL"] = base
            os.environ["OPENAI_API_BASE"] = base
            os.environ["OPENROUTER_BASE_URL"] = base
        else:
            os.environ["OPENAI_API_KEY"] = api_key

    if asknews_key:
        os.environ["ASKNEWS_API_KEY"] = asknews_key
    if perplexity_key:
        os.environ["PERPLEXITY_API_KEY"] = perplexity_key
        os.environ["PPLX_API_KEY"] = perplexity_key
