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
from conftest import DIM_COLS
from src.indicators import calculate_indicators, calculate_ipem, winsorized_minmax

pytestmark = pytest.mark.fase3


def _df(n=500, seed=1):
    rng = np.random.default_rng(seed)
    return pd.DataFrame({
        "cod_ibge": range(n),
        "familias_elegiveis": rng.integers(100, 50000, n).astype(float),
        "beneficiarios_tsee": rng.integers(0, 50000, n).astype(float),
        "tarifa_municipal_estimada": rng.uniform(0.6, 1.2, n),
        "renda_referencia": rng.uniform(300, 1500, n),
        "dec_rel": rng.uniform(0.3, 3, n), "fec_rel": rng.uniform(0.3, 3, n),
        "dom_favela": np.where(rng.random(n) < 0.12, rng.integers(10, 5000, n), 0).astype(float),
        "dom_total": rng.integers(500, 300000, n).astype(float),
    })


def test_F3_S01_ipem_e_media_simples_das_quatro_dimensoes_normalizadas():
    out = calculate_ipem(calculate_indicators(_df(), 100))
    esperado = out[[f"n_{c}" for c in DIM_COLS]].mean(axis=1)
    assert np.allclose(out.ipem, esperado, equal_nan=True), "pesos não são iguais"


def test_F3_S02_normalizacao_min_max_0_100_com_winsorizacao():
    out = calculate_ipem(calculate_indicators(_df(), 100))
    for c in DIM_COLS:
        n = out[f"n_{c}"]
        assert n.min() == 0 and abs(n.max() - 100) < 1e-9, c
        # valores acima do p99 colapsam no teto
        p99 = out[c].quantile(0.99)
        assert (n[out[c] >= p99] == 100).all(), f"{c}: winsorização no p99 não aplicada"


def test_F3_S03_monotonicidade_pior_insumo_pior_indice():
    """Semântico: piorar qualquer dimensão de um município nunca reduz seu IPEM."""
    base = _df()
    ref = calculate_ipem(calculate_indicators(base, 100)).ipem
    piores = {
        "beneficiarios_tsee": lambda s: s * 0.5,        # menos beneficiários -> mais lacuna
        "tarifa_municipal_estimada": lambda s: s * 1.2,  # conta mais cara
        "renda_referencia": lambda s: s * 0.8,           # menos renda
        "dec_rel": lambda s: s * 1.5,                    # pior qualidade
        "dom_favela": lambda s: (s + 100).clip(upper=base.dom_total),
    }
    for col, f in piores.items():
        alt = base.copy(); alt.loc[7, col] = f(alt.loc[[7], col]).iloc[0]
        novo = calculate_ipem(calculate_indicators(alt, 100)).ipem
        assert novo[7] >= ref[7] - 1e-9, f"piorar {col} reduziu o IPEM"


def test_F3_S04_consumo_de_referencia_nao_altera_ranking_relativo():
    """D2 é razão; mudar 100 para 150 kWh escala D2 e não muda a ordem de D2."""
    base = _df()
    a = calculate_indicators(base, 100).d2_peso_conta_renda.rank()
    b = calculate_indicators(base, 150).d2_peso_conta_renda.rank()
    assert (a == b).all()


def test_F3_S05_dois_piores_e_media_das_duas_maiores_dimensoes():
    out = calculate_ipem(calculate_indicators(_df(), 100))
    n = out[[f"n_{c}" for c in DIM_COLS]]
    esperado = n.apply(lambda r: r.nlargest(2).mean(), axis=1)
    assert np.allclose(out.ipem_dois_piores, esperado, equal_nan=True)
    assert (out.ipem_dois_piores >= out.ipem - 1e-9).all(), "dois piores nunca é menor que a média"


def test_F3_S06_faixas_sao_quartis_equilibrados():
    out = calculate_ipem(calculate_indicators(_df(2000), 100))
    prop = out.faixa.value_counts(normalize=True)
    assert prop.between(0.20, 0.30).all(), prop.to_dict()
    assert list(prop.index) and set(prop.index) == {"Baixa", "Média", "Alta", "Muito alta"}


def test_F3_S07_ranking_coerente_com_ipem():
    out = calculate_ipem(calculate_indicators(_df(), 100))
    o = out.dropna(subset=["ipem"]).sort_values("ranking")
    assert (o.ipem.diff().dropna() <= 1e-9).all()
    assert o.ranking.min() == 1


def test_F3_S08_lacuna_bruta_preserva_negativos_para_validacao():
    df = _df(); df.loc[3, "beneficiarios_tsee"] = df.loc[3, "familias_elegiveis"] * 2
    out = calculate_indicators(df, 100)
    assert out.loc[3, "lacuna_bruta"] < 0 and out.loc[3, "d1_lacuna_tsee"] == 0


def test_F3_S09_d4_ausente_vira_zero_mas_d1_a_d3_ausentes_nao():
    df = _df()
    df.loc[1, "dom_favela"] = np.nan
    df.loc[2, "dec_rel"] = np.nan; df.loc[2, "fec_rel"] = np.nan
    out = calculate_ipem(calculate_indicators(df, 100))
    assert out.loc[1, "d4_vulnerabilidade_territorial"] == 0 and pd.notna(out.loc[1, "ipem"])
    assert pd.isna(out.loc[2, "d3_qualidade"]) and pd.isna(out.loc[2, "ipem"])


def test_F3_S10_invariancia_por_permutacao_de_linhas():
    df = _df(); out1 = calculate_ipem(calculate_indicators(df, 100)).set_index("cod_ibge")
    out2 = calculate_ipem(calculate_indicators(df.sample(frac=1, random_state=9), 100)).set_index("cod_ibge")
    assert np.allclose(out1.ipem.sort_index(), out2.ipem.sort_index(), equal_nan=True)
    assert (out1.ranking.sort_index() == out2.ranking.sort_index()).all()
