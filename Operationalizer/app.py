from __future__ import annotations

import os
from pathlib import Path
from typing import List

import pandas as pd
import streamlit as st

from pipeline import run_pipeline
from utils import (
    configure_env,
    examples_abs_path_in_cache,
    get_app_dir,
    parse_topics_cell,
    run_async,
    unique_preserve_order,
)

APP_DIR = get_app_dir(__file__)

st.set_page_config(page_title="Topics CSV → proto-questions → operationalize", layout="wide")
st.title("Topics CSV → proto-questions → operationalized questions (forecasting-tools)")

with st.sidebar:
    st.header("LLM provider")

    provider = st.selectbox("Provider (OpenAI-compatible)", ["OpenRouter", "OpenAI"], index=0)
    llm_api_key = st.text_input("API key", type="password")

    st.divider()
    st.caption("Optional keys for deep-mode tools:")
    asknews_key = st.text_input("ASKNEWS_API_KEY (optional)", type="password")
    perplexity_key = st.text_input("PERPLEXITY_API_KEY (optional)", type="password")

    st.divider()
    mode = st.selectbox("Decomposer mode", ["fast", "deep"], index=0)
    total_questions = st.number_input("Total proto-questions", min_value=1, max_value=100, value=20, step=1)

    st.divider()
    decomposer_model = st.text_input(
        "Decomposer model",
        value="openrouter/perplexity/sonar" if mode == "fast" else "openrouter/google/gemini-2.5-pro-preview",
    )
    operationalizer_model = st.text_input(
        "Operationalizer model",
        value="openrouter/perplexity/sonar-reasoning-pro",
    )

    additional_context = st.text_area(
        "Additional context (optional)",
        value="Generate high-VOI, resolvable forecasting questions aligned with the provided topics.",
        height=120,
    )

if provider == "OpenAI" and (llm_api_key or "").startswith("sk-or-"):
    st.sidebar.error("Provider=OpenAI mais la clé ressemble à une clé OpenRouter (sk-or-v1...).")
    st.stop()

configure_env(provider, llm_api_key, asknews_key, perplexity_key)

with st.sidebar:
    st.divider()
    st.caption(f"Script dir: {APP_DIR}")
    st.caption(f"CWD (repo/runtime): {Path.cwd()}")
    st.caption(f"Examples JSON (cache): {examples_abs_path_in_cache()}")
    st.caption(f"Examples JSON exists: {examples_abs_path_in_cache().exists()}")
    st.caption(f"OPENROUTER_API_KEY set: {bool(os.environ.get('OPENROUTER_API_KEY'))}")
    st.caption(f"OPENAI_API_KEY set: {bool(os.environ.get('OPENAI_API_KEY'))}")
    st.caption(f"OPENAI_API_BASE: {os.environ.get('OPENAI_API_BASE')}")
    st.caption(f"OPENAI_BASE_URL: {os.environ.get('OPENAI_BASE_URL')}")

uploaded = st.file_uploader("Upload CSV", type=["csv"])
if not uploaded:
    st.info("Charge un CSV avec une colonne contenant des topics (ex: 'topics').")
    st.stop()

try:
    df = pd.read_csv(uploaded)
except Exception:
    uploaded.seek(0)
    df = pd.read_csv(uploaded, sep=";")

st.subheader("CSV preview")
st.dataframe(df.head(30), use_container_width=True)

topic_col = st.selectbox(
    "Topic column",
    options=list(df.columns),
    index=(list(df.columns).index("topics") if "topics" in df.columns else 0),
)

all_topics: List[str] = []
for cell in df[topic_col].tolist():
    all_topics.extend(parse_topics_cell(cell))
topics = unique_preserve_order(all_topics)

st.write(f"Topics uniques détectés: **{len(topics)}**")
with st.expander("Voir les topics"):
    st.write(topics)

if not llm_api_key:
    st.warning("Renseigne une API key dans la sidebar pour exécuter la génération.")
    st.stop()

run_btn = st.button("Generate proto-questions and operationalize", type="primary")

if run_btn:
    if not topics:
        st.error("Aucun topic détecté.")
        st.stop()

    with st.spinner("Running decomposer + operationalizer..."):
        out_df = run_async(
            run_pipeline(
                topics=topics,
                mode=mode,
                total_questions=int(total_questions),
                decomposer_model=decomposer_model,
                operationalizer_model=operationalizer_model,
                additional_context=additional_context,
                concurrency=4,
            )
        )

    st.subheader("Results")
    st.dataframe(out_df, use_container_width=True)

    st.download_button(
        "Download results as CSV",
        data=out_df.to_csv(index=False).encode("utf-8"),
        file_name="operationalized_questions.csv",
        mime="text/csv",
    )

