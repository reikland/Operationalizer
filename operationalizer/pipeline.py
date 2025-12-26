import asyncio
from typing import Any, Dict, List

import pandas as pd

from operationalizer.cache import ensure_question_examples_file
from operationalizer.utils import clean_indents, to_dict

from forecasting_tools.agents_and_tools.question_generators.question_decomposer import (
    DecompositionResult,
    QuestionDecomposer,
)
from forecasting_tools.agents_and_tools.question_generators.question_operationalizer import (
    QuestionOperationalizer,
)


def build_related_research(decomp: DecompositionResult, q_obj: Any) -> str:
    qd = to_dict(q_obj)
    return clean_indents(
        f"""
        Decomposer general research & approach:
        {decomp.general_research_and_approach}

        Proto-question (from decomposer):
        - Title: {qd.get("question_or_idea_text")}
        - Resolution process: {qd.get("resolution_process")}
        - Expected resolution date: {qd.get("expected_resolution_date")}
        - Background information: {qd.get("background_information")}
        - Past resolution / base rate: {qd.get("past_resolution")}
        - Other information: {qd.get("other_information")}
        """
    ).strip()


async def run_pipeline(
    topics: List[str],
    mode: str,
    total_questions: int,
    additional_context: str,
    decomposer_model: str,
    operationalizer_model: str,
) -> pd.DataFrame:
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

    ensure_question_examples_file()
    operationalizer = QuestionOperationalizer(model=operationalizer_model)

    sem = asyncio.Semaphore(4)

    async def operationalize_one(q_obj):
        async with sem:
            title = q_obj.question_or_idea_text
            related = build_related_research(decomp, q_obj)
            sq = await operationalizer.operationalize_question(
                question_title=title,
                related_research=related,
                additional_context=additional_context,
            )
            return q_obj, sq

    pairs = await asyncio.gather(*[operationalize_one(q) for q in decomp.decomposed_questions])

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
