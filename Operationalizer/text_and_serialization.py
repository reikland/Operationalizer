"""
text_and_serialization.py

Responsabilités :
- Nettoyer les indents (pour prompts)
- Convertir objets pydantic / dict / list en dict JSON-friendly
- Construire le bloc "related research" pour l'operationalizer
"""

from __future__ import annotations

import textwrap
from typing import Any


def clean_indents(s: str) -> str:
    return textwrap.dedent(s).strip()


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
