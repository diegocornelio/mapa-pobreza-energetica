"""IPEM: Índice de Pobreza Energética Municipal.

Reúso de dados abertos (ANEEL, MDS, IBGE) para o 2º Concurso de Reúso de Dados Abertos da CGU.

Autor: Diego H. C. de Rezende, fundador da Struktur Energia.
Engenheiro de Computação e mestre em Engenharia de Software, com experiência em desenvolvimento de software, ciência de dados, gestão de projetos e operação de sistemas em ambientes de alta complexidade e missão crítica. Fundador da Struktur Energia, iniciativa dedicada a inteligência de mercado, eficiência energética e gestão estratégica de energia. Cursa o MBA em Gestão de Riscos na Comercialização de Energia (USP/CCEE) e o MBA em Data Science, Inteligência Artificial e Analytics (USP/ESALQ).

Repositório: https://github.com/diegocornelio/mapa-pobreza-energetica
Licença do código: MIT. Licença dos dados derivados: CC-BY 4.0.
"""
import numpy as np
import pandas as pd
import pytest

pytestmark = pytest.mark.fase3

from src.indicators import calculate_indicators, calculate_ipem


def _base(n: int = 4) -> pd.DataFrame:
    return pd.DataFrame({
        "cod_ibge": range(1, n + 1),
        "familias_elegiveis": [100.0] * n,
        "beneficiarios_tsee": [90.0, 50.0, 20.0, 100.0][:n],
        "tarifa_municipal_estimada": [0.8, 1.0, 1.2, 0.7][:n],
        "renda_referencia": [800.0, 600.0, 400.0, 1000.0][:n],
        "dec_rel": [0.8, 1.2, 2.0, 0.5][:n],
        "fec_rel": [0.7, 1.5, 1.0, 0.4][:n],
        "dom_favela": [10.0, 20.0, 30.0, 0.0][:n],
        "dom_total": [100.0] * n,
    })


def test_ipem_limitado_e_rotulos_curtos():
    out = calculate_ipem(calculate_indicators(_base(), consumption_kwh=100))
    assert out["ipem"].between(0, 100).all()
    assert out["ipem_dois_piores"].between(0, 100).all()
    assert set(out["faixa"].astype(str)) <= {"Baixa", "Média", "Alta", "Muito alta"}
    # T1: rótulos curtos
    assert out["dois_piores_indicadores"].str.fullmatch(r"D[1-4], D[1-4]").all()


def test_sem_uma_dimensao_nao_ha_ipem():
    # T2: renda ausente -> IPEM NaN, não média de 3 dimensões
    df = _base()
    df.loc[1, "renda_referencia"] = np.nan
    out = calculate_ipem(calculate_indicators(df, consumption_kwh=100))
    assert pd.isna(out.loc[1, "ipem"])
    assert out.loc[1, "n_dimensoes_validas"] == 3
    assert pd.isna(out.loc[1, "ranking"])
    assert out.drop(index=1)["ipem"].notna().all()


def test_faixa_nao_quebra_com_empates():
    # T3: metade dos municípios com todos os indicadores iguais
    rng = np.random.default_rng(0)
    n = 2000
    df = pd.DataFrame({
        "cod_ibge": range(n),
        "familias_elegiveis": rng.integers(50, 50000, n).astype(float),
        "beneficiarios_tsee": rng.integers(0, 50000, n).astype(float),
        "tarifa_municipal_estimada": rng.uniform(0.6, 1.2, n),
        "renda_referencia": rng.uniform(300, 1500, n),
        "dec_rel": rng.uniform(0.3, 3, n),
        "fec_rel": rng.uniform(0.3, 3, n),
        "dom_favela": 0.0,
        "dom_total": rng.integers(500, 300000, n).astype(float),
    })
    df.loc[:1000, ["dec_rel", "fec_rel"]] = 1.0
    df.loc[:1000, "beneficiarios_tsee"] = df.loc[:1000, "familias_elegiveis"]
    df.loc[:1000, "tarifa_municipal_estimada"] = 0.8
    df.loc[:1000, "renda_referencia"] = 1000.0
    out = calculate_ipem(calculate_indicators(df, consumption_kwh=100))
    assert out["faixa"].notna().all()
    assert out["ipem"].notna().all()
