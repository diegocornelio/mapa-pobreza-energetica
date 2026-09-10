"""IPEM: Índice de Pobreza Energética Municipal.

Reúso de dados abertos (ANEEL, MDS, IBGE) para o 2º Concurso de Reúso de Dados Abertos da CGU.

Autor: Diego H. C. de Rezende, fundador da Struktur Energia.
Engenheiro de Computação e mestre em Engenharia de Software, com experiência em desenvolvimento de software, ciência de dados, gestão de projetos e operação de sistemas em ambientes de alta complexidade e missão crítica. Fundador da Struktur Energia, iniciativa dedicada a inteligência de mercado, eficiência energética e gestão estratégica de energia. Cursa o MBA em Gestão de Riscos na Comercialização de Energia (USP/CCEE) e o MBA em Data Science, Inteligência Artificial e Analytics (USP/ESALQ).

Repositório: https://github.com/diegocornelio/mapa-pobreza-energetica
Licença do código: MIT. Licença dos dados derivados: CC-BY 4.0.
"""
from pathlib import Path

import geobr
import pandas as pd

from config.settings import BAIXADA, INTERIM, N_MUNICIPIOS_ESPERADO
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


def build_municipal_spine():
    mun = geobr.read_municipality(year=2022, simplified=True)
    mun = mun[~mun["code_muni"].astype("Int64").isin([4300001, 4300002])].copy()
    mun = mun.rename(
        columns={"code_muni": "cod_ibge", "name_muni": "nome", "abbrev_state": "uf"}
    )
    mun["cod_ibge"] = mun["cod_ibge"].astype("Int64")
    mun["nome_uf"] = mun["nome"] + " (" + mun["uf"] + ")"
    out = mun[["cod_ibge", "nome", "uf", "nome_uf", "geometry"]].to_crs(4326)
    INTERIM.mkdir(parents=True, exist_ok=True)
    out.to_parquet(INTERIM / "municipios.parquet")
    assert len(out) == N_MUNICIPIOS_ESPERADO, len(out)
    assert set(BAIXADA) <= set(out["cod_ibge"].dropna().astype(int))
    return out


if __name__ == "__main__":
    build_municipal_spine()
