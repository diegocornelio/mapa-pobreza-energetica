from pathlib import Path

import pandas as pd


def read_csv_flexible(path: str | Path, sep: str | None = None) -> pd.DataFrame:
    """Le CSV tentando separadores e encodings; rejeita leitura de uma coluna."""
    path = Path(path)
    separators = [sep] if sep else [";", ",", "\t"]
    encodings = ["utf-8", "latin-1", "cp1252"]
    errors = []
    for encoding in encodings:
        for separator in separators:
            try:
                df = pd.read_csv(path, sep=separator, encoding=encoding, low_memory=False)
            except Exception as exc:
                errors.append(f"{encoding}/{separator!r}: {exc}")
                continue
            if df.shape[1] > 1:
                return df
            errors.append(f"{encoding}/{separator!r}: 1 coluna (separador errado?)")
    raise ValueError(f"Nao foi possivel ler {path}. Tentativas: {errors[:6]}")


def br_number_to_float(series: pd.Series) -> pd.Series:
    """'1.234,56' -> 1234.56. Strings vazias viram NaN."""
    return pd.to_numeric(
        series.astype(str)
        .str.strip()
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .replace({"": None, "nan": None, "None": None}),
        errors="coerce",
    )


def normalize_cod_ibge(series: pd.Series, malha_7: pd.Series | None = None) -> pd.Series:
    """Converte para Int64 de 7 digitos; resolve codigo de 6 digitos pela malha."""
    cod = pd.to_numeric(series, errors="coerce").astype("Int64")
    if malha_7 is None:
        return cod
    seis_para_sete = {int(c) // 10: int(c) for c in malha_7.dropna()}
    return cod.map(
        lambda c: seis_para_sete.get(int(c), c)
        if pd.notna(c) and c < 1_000_000
        else c
    ).astype("Int64")
