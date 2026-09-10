"""IPEM: Índice de Pobreza Energética Municipal.

Reúso de dados abertos (ANEEL, MDS, IBGE) para o 2º Concurso de Reúso de Dados Abertos da CGU.

Autor: Diego H. C. de Rezende, fundador da Struktur Energia.
Engenheiro de Computação e mestre em Engenharia de Software, com experiência em desenvolvimento de software, ciência de dados, gestão de projetos e operação de sistemas em ambientes de alta complexidade e missão crítica. Fundador da Struktur Energia, iniciativa dedicada a inteligência de mercado, eficiência energética e gestão estratégica de energia. Cursa o MBA em Gestão de Riscos na Comercialização de Energia (USP/CCEE) e o MBA em Data Science, Inteligência Artificial e Analytics (USP/ESALQ).

Repositório: https://github.com/diegocornelio/mapa-pobreza-energetica
Licença do código: MIT. Licença dos dados derivados: CC-BY 4.0.
"""
import numpy as np
import pandas as pd

from config.settings import DIM_COLS, DIM_LABELS


def safe_divide(num: pd.Series, den: pd.Series) -> pd.Series:
    den = den.replace({0: np.nan})
    return num / den


def winsorized_minmax(series: pd.Series, upper_q: float = 0.99) -> pd.Series:
    """Min-max apos corte no percentil upper_q. NaN permanece NaN."""
    s = series.astype(float).copy()
    upper = s.quantile(upper_q)
    s = s.clip(upper=upper)
    span = s.max() - s.min()
    if pd.isna(span) or span == 0:
        return pd.Series(np.where(s.isna(), np.nan, 0.0), index=s.index)
    return (s - s.min()) / span


def calculate_indicators(df: pd.DataFrame, consumption_kwh: int) -> pd.DataFrame:
    out = df.copy()
    gap_num = out["familias_elegiveis"] - out["beneficiarios_tsee"]
    out["lacuna_bruta"] = gap_num
    out["d1_lacuna_tsee"] = safe_divide(
        gap_num.clip(lower=0), out["familias_elegiveis"]
    ).clip(0, 1)
    out["conta_estimada"] = out["tarifa_municipal_estimada"] * consumption_kwh
    out["d2_peso_conta_renda"] = safe_divide(
        out["conta_estimada"], out["renda_referencia"]
    )
    out["d3_qualidade"] = out[["dec_rel", "fec_rel"]].max(axis=1, skipna=False)
    out["d4_vulnerabilidade_territorial"] = safe_divide(
        out["dom_favela"], out["dom_total"]
    ).fillna(0)
    return out


def calculate_ipem(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in DIM_COLS:
        out[f"n_{col}"] = 100 * winsorized_minmax(out[col])
    norm_cols = [f"n_{col}" for col in DIM_COLS]

    out["n_dimensoes_validas"] = out[norm_cols].notna().sum(axis=1)
    completo = out["n_dimensoes_validas"] == len(DIM_COLS)
    out["ipem"] = np.where(completo, out[norm_cols].mean(axis=1), np.nan)

    def dois_piores(row: pd.Series) -> pd.Series:
        if row.isna().any():
            return pd.Series(
                {"ipem_dois_piores": np.nan, "dois_piores_indicadores": None}
            )
        top = row.nlargest(2)
        labels = [DIM_LABELS[c.removeprefix("n_")] for c in top.index]
        return pd.Series(
            {"ipem_dois_piores": top.mean(), "dois_piores_indicadores": ", ".join(labels)}
        )

    out[["ipem_dois_piores", "dois_piores_indicadores"]] = out[norm_cols].apply(
        dois_piores, axis=1
    )
    out["ranking"] = out["ipem"].rank(ascending=False, method="min").astype("Int64")
    pct = out["ipem"].rank(pct=True, method="average")
    bins = [0, 0.25, 0.5, 0.75, 1.0000001]
    labels = ["Baixa", "Media", "Alta", "Muito alta"]
    out["faixa"] = pd.cut(pct, bins=bins, labels=labels, include_lowest=True, right=True)
    out["faixa"] = out["faixa"].astype("object").replace({"Media": "Média"})
    return out
