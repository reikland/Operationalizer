"""
async_utils.py

Responsabilité :
- Exécuter proprement un coroutine async depuis Streamlit, même si un event loop tourne déjà
"""

from __future__ import annotations

import asyncio
from typing import Any


def run_async(coro: Any) -> Any:
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
