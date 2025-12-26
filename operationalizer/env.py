import os


def configure_env(provider: str, api_key: str, asknews_key: str, perplexity_key: str) -> None:
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
