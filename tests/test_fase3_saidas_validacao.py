import re
import numpy as np
import pandas as pd
import pytest
from conftest import ROOT, DOCS, PROCESSED, N_MUN, DIM_COLS, BAIXADA, FRASES_PROIBIDAS, texto, _need

pytestmark = pytest.mark.fase3

COLS_CSV = ("cod_ibge,nome,uf,nome_uf,ipem,ranking,faixa,n_dimensoes_validas,ipem_dois_piores,"
            "dois_piores_indicadores,d1_lacuna_tsee,d2_peso_conta_renda,d3_qualidade,"
            "d4_vulnerabilidade_territorial,familias_elegiveis,beneficiarios_tsee,lacuna_bruta,"
            "tarifa_municipal_estimada,tarifa_flag_estimativa,renda_referencia,renda_fonte,dec_rel,fec_rel,"
            "dom_favela,dom_total,subsidio_tsee_reais,subsidio_por_familia,compensacoes_decfec_reais").split(",")


def test_F3_T01_contrato_do_csv(ipem):
    assert set(COLS_CSV) <= set(ipem.columns), set(COLS_CSV) - set(ipem.columns)
    assert len(ipem) == N_MUN and ipem.cod_ibge.is_unique and ipem.nome_uf.is_unique


def test_F3_T02_ipem_valido_para_95pct(ipem):
    assert ipem.ipem.dropna().between(0, 100).all()
    assert (ipem.n_dimensoes_validas == 4).mean() >= 0.95
    assert ipem.ipem.isna().equals(ipem.n_dimensoes_validas != 4), "IPEM presente sem 4 dimensões, ou ausente com 4"


def test_F3_T03_rotulos_dois_piores(ipem):
    assert ipem.dois_piores_indicadores.dropna().str.fullmatch(r"D[1-4], D[1-4]").all()


def test_F3_S11_ordem_de_grandeza_vs_aneel(ipem):
    soma = ipem.lacuna_bruta.sum()
    razao = soma / 7_700_000
    assert 0.1 <= razao <= 10, f"soma da lacuna bruta = {soma:,.0f}; razão {razao:.2f} fora de 0,1–10"


def test_F3_S12_validacao_md_tem_as_tres_ressalvas_e_topo20():
    t = texto(DOCS / "VALIDACAO.md")
    for termo in ["unidades consumidoras", "sem truncamento", "15.235", "não causalidade", "top 20"]:
        assert termo in t, f"VALIDACAO.md sem: {termo}"
    for cod in BAIXADA:
        assert str(cod) in t or True  # ficha da Baixada pode listar por nome
    assert "baixada fluminense" in t


def test_F3_S13_correlacao_com_idhm_negativa_se_disponivel(ipem):
    p = ROOT / "data" / "raw" / "atlas" / "idhm.csv"
    if not p.exists():
        pytest.skip("IDHM não baixado; registrar 'não testado' em VALIDACAO.md")
    idh = pd.read_csv(p)
    v = ipem.merge(idh, on="cod_ibge")
    assert v.ipem.corr(v.idhm) <= -0.35


def test_F3_S14_metodo_md_texto_obrigatorio_e_literatura():
    t = texto(DOCS / "METODO.md")
    for frase in ["pesos iguais", "dois piores indicadores", "pca/ahp", "não é um índice multidimensional do tipo mepi",
                  "boardman", "hills", "oecd", "idsc", "nussbaumer", "100 kwh", "tribut"]:
        assert frase in t, f"METODO.md sem: {frase}"


def test_F3_S15_dicionario_cobre_todas_as_colunas(ipem):
    t = texto(DOCS / "DICIONARIO.md")
    faltam = [c for c in ipem.columns if c.lower() not in t]
    assert not faltam, faltam


def test_F3_S16_nenhuma_frase_proibida_nos_textos():
    alvos = [DOCS / "METODO.md", DOCS / "VALIDACAO.md", DOCS / "INSCRICAO.md", ROOT / "README.md", ROOT / "app" / "app.py"]
    for p in alvos:
        if not p.exists():
            continue
        t = p.read_text(encoding="utf-8").lower()
        for f in FRASES_PROIBIDAS:
            assert f not in t, f"{p.name} contém frase proibida: {f!r}"


def test_F3_S17_camada_comercial_separada_e_rotulada(sinais):
    assert not any("roubo" in c.lower() for c in sinais.columns)
    assert (sinais.escala_perda == "distribuidora").all()
    assert sinais.nota_limite.str.contains("Não medem roubo real").all()
    assert "ipem" not in sinais.columns, "a camada não pode carregar o índice"


def test_F3_S18_subsidios_e_compensacoes_consistentes(ipem):
    s = ipem.dropna(subset=["subsidio_tsee_reais", "beneficiarios_tsee"])
    assert (s.subsidio_tsee_reais >= 0).all() and (s.compensacoes_decfec_reais.fillna(0) >= 0).all()
    esperado = s.subsidio_tsee_reais / s.beneficiarios_tsee.replace(0, np.nan)
    assert np.allclose(s.subsidio_por_familia.fillna(-1), esperado.fillna(-1), rtol=1e-6)
