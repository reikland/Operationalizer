"""
topics_parsing.py

Responsabilités :
- Parser une cellule (str/list/NaN) en liste de topics
- Conserver l'ordre tout en dédoublonnant
"""

from __future__ import annotations

import json
import re
from typing import Any, List

import pandas as pd


_SPLIT_RE = re.compile(r"[;\n,\|]+")


def parse_topics_cell(x: Any) -> List[str]:
    if x is None:
        return []
    if isinstance(x, float) and pd.isna(x):
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
