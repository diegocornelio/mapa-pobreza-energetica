from pathlib import Path

import pandas as pd

from src.io_utils import read_csv_flexible


def inspect_file(path: str | Path, n: int = 3) -> dict:
    df = read_csv_flexible(path)
    return {
        "path": str(path),
        "shape": df.shape,
        "columns": list(df.columns),
        "sample": df.head(n).to_dict(orient="records"),
    }


def require_columns(df: pd.DataFrame, columns: list[str], source: str) -> None:
    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise ValueError(f"{source}: colunas obrigatorias ausentes: {missing}")


def left_join_all(base: pd.DataFrame, tables: list[pd.DataFrame]) -> pd.DataFrame:
    out = base.copy()
    for table in tables:
        out = out.merge(table, on="cod_ibge", how="left")
    return out


def coverage_report(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame(
        {"column": columns, "coverage": [df[col].notna().mean() for col in columns]}
    )
