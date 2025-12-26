from __future__ import annotations

import asyncio
from typing import Any, Dict, List

import pandas as pd

from utils import (
    bootstrap_forecasting_tools_runtime,
    build_related_research,
    clean_indents,
    to_dict,
)


async def run_pipeline(
    *,
    topics: List[str],
    mode: str,
    total_questions: int,
    decomposer_model: str,
    operationalizer_model: str,
    additional_context: str,
    concurrency: int = 4,
) -> pd.DataFrame:
    """
    Responsibilities:
    - Bootstrap upstream JSON file expected by forecasting_tools (relative open)
    - Run decomposer (fast/deep)
    - Run operationalizer concurrently
    - Return a DataFrame of results

    Important: forecasting_tools imports are inside the function, AFTER bootstrap.
    """
    # Ensure CWD and examples JSON are correct before importing forecasting_tools
    bootstrap_forecasting_tools_runtime()

    # Delayed imports (critical)
    from forecasting_tools.agents_and_tools.question_generators.question_decomposer import (  # noqa: E402
        QuestionDecomposer,
    )
    from forecasting_tools.agents_and_tools.question_generators.question_operationalizer import (  # noqa: E402
        QuestionOperationalizer,
    )

    topics_block = "\n".join([f"- {t}" for t in topics[:300]])
    fuzzy = clean_indents(
        f"""
        Please generate forecasting proto-questions grounded in the following topics (from a CSV).

        Topics:
        {topics_block}
        """
    ).strip()

    decomposer = QuestionDecomposer()

    if mode == "deep":
        decomp = await decomposer.decompose_into_questions_deep(
            fuzzy_topic_or_question=fuzzy,
            related_research=None,
            additional_context=additional_context,
            number_of_questions=int(total_questions),
            model=decomposer_model,
        )
    else:
        decomp = await decomposer.decompose_into_questions_fast(
            fuzzy_topic_or_question=fuzzy,
            related_research=None,
            additional_context=additional_context,
            number_of_questions=int(total_questions),
            model=decomposer_model,
        )

    # Ensure again (cheap + safe)
    bootstrap_forecasting_tools_runtime()

    operationalizer = QuestionOperationalizer(model=operationalizer_model)

    sem = asyncio.Semaphore(int(concurrency))

    async def operationalize_one(q_obj: Any):
        async with sem:
            title = getattr(q_obj, "question_or_idea_text", None) or str(q_obj)
            related = build_related_research(decomp, q_obj)
            sq = await operationalizer.operationalize_question(
                question_title=title,
                related_research=related,
                additional_context=additional_context,
            )
            return q_obj, sq

    questions = list(getattr(decomp, "decomposed_questions", []) or [])
    pairs = await asyncio.gather(*[operationalize_one(q) for q in questions])

    rows: List[Dict[str, Any]] = []
    for q_obj, sq in pairs:
        qd = to_dict(q_obj)
        sd = to_dict(sq)

        row: Dict[str, Any] = {
            "proto_question_title": qd.get("question_or_idea_text"),
            "decomp_resolution_process": qd.get("resolution_process"),
            "decomp_expected_resolution_date": qd.get("expected_resolution_date"),
            "decomp_background_information": qd.get("background_information"),
            "decomp_past_resolution": qd.get("past_resolution"),
            "decomp_other_information": qd.get("other_information"),
        }

        if isinstance(sd, dict):
            for k, v in sd.items():
                row[f"op_{k}"] = v
        else:
            row["op_question"] = sd

        rows.append(row)

    return pd.DataFrame(rows)
