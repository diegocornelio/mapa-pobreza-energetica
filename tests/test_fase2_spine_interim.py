import geopandas as gpd
import pandas as pd
import pytest
from conftest import INTERIM, N_MUN, BAIXADA, _need

pytestmark = pytest.mark.fase2

SCHEMAS = {
    "tsee_municipio": {"cod_ibge", "beneficiarios_tsee", "subsidio_tsee_reais", "source_id", "data_referencia"},
    "cadunico_municipio": {"cod_ibge", "familias_elegiveis", "familias_cadastradas", "renda_referencia", "renda_fonte", "source_id"},
    "tarifa_municipio": {"cod_ibge", "tarifa_municipal_estimada", "tarifa_flag_estimativa", "distribuidoras_usadas"},
    "qualidade_municipio": {"cod_ibge", "dec_apurado", "fec_apurado", "dec_limite", "fec_limite", "dec_rel", "fec_rel", "compensacoes_decfec_reais"},
    "territorio_municipio": {"cod_ibge", "dom_favela", "dom_total"},
}


def test_F2_T06_espinha_5570_baixada_nome_uf_unico():
    mun = gpd.read_parquet(_need(INTERIM / "municipios.parquet"))
    assert len(mun) == N_MUN
    assert set(mun.cod_ibge.dropna().astype(int)) >= BAIXADA
    assert mun.nome_uf.is_unique
    assert mun.crs is not None and mun.crs.to_epsg() == 4326
    assert mun.cod_ibge.astype(int).between(1_100_000, 5_399_999).all()


@pytest.mark.parametrize("nome,cols", SCHEMAS.items())
def test_F2_T07_schema_tabelas_interim(nome, cols):
    df = pd.read_parquet(_need(INTERIM / f"{nome}.parquet"))
    assert cols <= set(df.columns), cols - set(df.columns)
    assert df.cod_ibge.is_unique, f"{nome}: cod_ibge duplicado"


def test_F2_S04_tarifa_com_tributos_em_faixa_plausivel():
    t = pd.read_parquet(_need(INTERIM / "tarifa_municipio.parquet"))
    assert t.tarifa_municipal_estimada.dropna().between(0.60, 1.20).all(), \
        "tarifa fora de 0,60–1,20 R$/kWh: erro de unidade ou tributo duplicado"
    assert t.tarifa_flag_estimativa.all(), "toda tarifa municipal é estimativa e deve ter flag True"


def test_F2_S05_dec_anual_plausivel():
    q = pd.read_parquet(_need(INTERIM / "qualidade_municipio.parquet"))
    assert q.dec_apurado.dropna().median() < 40, "DEC mediano > 40 h: confusão mês/ano?"
    assert (q.dec_apurado.dropna() > 0).mean() > 0.95
    assert (q.dec_rel.dropna() > 0).all() and (q.fec_rel.dropna() > 0).all()
    assert (q.compensacoes_decfec_reais.fillna(0) >= 0).all()


def test_F2_S06_tsee_nacional_na_ordem_de_grandeza_da_aneel():
    t = pd.read_parquet(_need(INTERIM / "tsee_municipio.parquet"))
    total = t.beneficiarios_tsee.sum()
    assert 17_000_000 <= total <= 21_000_000, \
        f"total TSEE = {total:,.0f}; ANEEL informou 17 mi de famílias (10/2024) e a Lei 15.235/2025 ampliou"


def test_F2_S07_cadunico_plausivel_e_renda_rotulada():
    c = pd.read_parquet(_need(INTERIM / "cadunico_municipio.parquet"))
    assert (c.familias_elegiveis <= c.familias_cadastradas).all()
    assert c.renda_fonte.notna().all() and c.renda_fonte.str.len().gt(0).all()
    assert c.renda_referencia.dropna().between(100, 5000).all(), "renda mensal fora de 100–5000: unidade errada?"
    assert 25_000_000 <= c.familias_cadastradas.sum() <= 55_000_000, "CECAD 06/2026: 42,9 mi famílias cadastradas"


def test_F2_S08_favela_zero_significa_ausencia_documentada():
    ter = pd.read_parquet(_need(INTERIM / "territorio_municipio.parquet"))
    assert ter.dom_favela.notna().all(), "dom_favela deve ser 0 (não NaN) onde o IBGE não mapeou favela"
    assert (ter.dom_favela <= ter.dom_total).all()
    assert 600 <= (ter.dom_favela > 0).sum() <= 720, "IBGE 2022: favelas em 656 municípios"


def test_F2_T08_base_mestre_5570_e_cobertura(base_mestre):
    assert len(base_mestre) == N_MUN and base_mestre.cod_ibge.is_unique
    for col in ["familias_elegiveis", "beneficiarios_tsee", "dec_rel", "tarifa_municipal_estimada", "renda_referencia"]:
        assert base_mestre[col].notna().mean() >= 0.95, f"cobertura < 95%: {col}"


def test_F2_S09_sem_preenchimento_silencioso(base_mestre):
    """Se uma fonte falhou para um município, o valor deve estar ausente, não zerado."""
    for col in ["familias_elegiveis", "renda_referencia", "tarifa_municipal_estimada", "dec_rel"]:
        assert (base_mestre[col].dropna() > 0).all(), f"{col} com zero: preenchimento silencioso?"
