"""
csv_io.py

Responsabilité :
- Lire un CSV uploadé (comma ou semicolon) de manière tolérante
"""

from __future__ import annotations

import pandas as pd


def read_csv_flexible(uploaded_file) -> pd.DataFrame:
    try:
        return pd.read_csv(uploaded_file)
    except Exception:
        try:
            uploaded_file.seek(0)
        except Exception:
            pass
        return pd.read_csv(uploaded_file, sep=";")
