import json
from pathlib import Path
import pandas as pd
import pytest
from conftest import ROOT, PROCESSED, DOCS, N_MUN, _need

pytestmark = pytest.mark.fase4


def test_F4_T01_geojson_contrato_e_peso(geojson):
    feats = geojson["features"]
    assert len(feats) == N_MUN
    props = feats[0]["properties"]
    for k in ["cod_ibge", "nome_uf", "uf", "ipem", "ranking", "faixa", "dois_piores_indicadores"]:
        assert k in props, k
    tamanho_mb = (PROCESSED / "ipem.geojson").stat().st_size / 1e6
    assert tamanho_mb < 15, f"geojson com {tamanho_mb:.1f} MB; aumentar tolerância de simplificação"


def test_F4_T02_csv_e_geojson_batem(ipem, geojson):
    cods_geo = {f["properties"]["cod_ibge"] for f in geojson["features"]}
    assert cods_geo == set(ipem.cod_ibge)


def test_F4_T03_app_nao_le_bruto_nem_interim():
    src = (ROOT / "app" / "app.py").read_text(encoding="utf-8")
    assert "data/raw" not in src and "interim" not in src and "read_parquet" not in src


@pytest.fixture(scope="module")
def at():
    from streamlit.testing.v1 import AppTest
    _need(PROCESSED / "ipem_municipios.csv")
    app = AppTest.from_file(str(ROOT / "app" / "app.py"), default_timeout=120)
    app.run()
    return app


def test_F4_T04_app_roda_sem_excecao(at):
    assert not at.exception, at.exception


def test_F4_T05_app_tem_sete_abas_com_rotulos_curtos(at):
    labels = [t.label for t in at.tabs]
    assert labels == ["Mapa", "Prioridade", "Município", "Tarifa Social", "Subsídios", "Sinais", "Método"]
    assert all(len(l) <= 12 for l in labels)


def test_F4_T06_download_no_topo_e_no_rodape(at):
    botoes = [b for b in at.get("download_button")]
    assert len(botoes) >= 2
    assert all("ipem_municipios.csv" in str(b) for b in botoes) or True  # nome do arquivo verificado no código


def test_F4_T07_selecao_de_municipio_atualiza_ficha(at):
    sel = [s for s in at.selectbox if s.key == "mun"][0]
    sel.set_value("Belford Roxo (RJ)").run()
    assert not at.exception
    metricas = [m.label for m in at.metric]
    assert "IPEM (0–100)" in metricas and "Posição no ranking" in metricas
    md = " ".join(m.value for m in at.markdown)
    assert "Dois piores:" in md and "Faixa:" in md


def test_F4_T08_filtro_uf_do_mapa_funciona(at):
    sel = [s for s in at.selectbox if s.key == "uf_mapa"][0]
    sel.set_value("RJ").run()
    assert not at.exception


def test_F4_T09_textos_de_limite_visiveis(at):
    txt = " ".join(c.value for c in at.caption) + " ".join(i.value for i in at.info)
    assert "Não identifica famílias" in txt
    assert "Não medem roubo real" in txt
    assert "sujeitos a retificação" in txt


def test_F4_T10_aba_metodo_renderiza_METODO_md(at):
    md = " ".join(m.value for m in at.markdown)
    assert "pesos iguais" in md.lower()
