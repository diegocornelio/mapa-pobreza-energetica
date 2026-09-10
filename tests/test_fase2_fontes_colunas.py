"""IPEM: Índice de Pobreza Energética Municipal.

Reúso de dados abertos (ANEEL, MDS, IBGE) para o 2º Concurso de Reúso de Dados Abertos da CGU.

Autor: Diego H. C. de Rezende, fundador da Struktur Energia.
Engenheiro de Computação e mestre em Engenharia de Software, com experiência em desenvolvimento de software, ciência de dados, gestão de projetos e operação de sistemas em ambientes de alta complexidade e missão crítica. Fundador da Struktur Energia, iniciativa dedicada a inteligência de mercado, eficiência energética e gestão estratégica de energia. Cursa o MBA em Gestão de Riscos na Comercialização de Energia (USP/CCEE) e o MBA em Data Science, Inteligência Artificial e Analytics (USP/ESALQ).

Repositório: https://github.com/diegocornelio/mapa-pobreza-energetica
Licença do código: MIT. Licença dos dados derivados: CC-BY 4.0.
"""
import re
from conftest import ROOT, RAW, DOCS, texto
import pandas as pd
import pytest

pytestmark = pytest.mark.fase2

OBRIGATORIAS = {"aneel_cde", "mds_cecad", "aneel_tarifas", "aneel_decfec", "aneel_indqual", "ibge_favelas"}
TESTE_OBRIGATORIO = {"aneel_indger"}


def test_F2_T01_toda_fonte_obrigatoria_registrada(fontes):
    assert OBRIGATORIAS <= set(fontes.source_id), OBRIGATORIAS - set(fontes.source_id)


def test_F2_T02_arquivo_bruto_existe_no_caminho_declarado(fontes):
    for _, r in fontes.iterrows():
        p = ROOT / r.local_path
        assert p.is_file() and p.stat().st_size > 0, r.source_id


def test_F2_T03_nomenclatura_de_proveniencia(fontes):
    padrao = re.compile(r"^data/raw/[a-z]+/[a-z0-9\-]+/\d{4}-\d{2}-\d{2}/.+")
    for lp in fontes.local_path:
        assert padrao.match(lp.replace("\\", "/")), lp


def test_F2_T04_nome_original_preservado(fontes):
    for _, r in fontes.iterrows():
        assert isinstance(r.original_filename, str) and r.original_filename.strip(), r.source_id
        # o arquivo local é o original ou um export documentado
        assert (ROOT / r.local_path).name == r.original_filename or "export" in str(r.notes).lower(), r.source_id


def test_F2_T05_datas_e_escala_preenchidas(fontes):
    for col in ["download_date", "data_reference_date", "geographic_scale", "license", "used_in"]:
        assert fontes[col].notna().all(), col


def test_F2_S01_hipoteses_resolvidas_em_COLUNAS():
    """Semântico: as três hipóteses abertas da v7 têm resposta registrada."""
    t = texto(DOCS / "COLUNAS.md")
    for chave in ["tsee_municipal", "indger_municipal", "renda_formato"]:
        assert re.search(chave + r"\s*[:=]\s*\S+", t), f"{chave} não anotado em COLUNAS.md"


def test_F2_S02_colunas_chave_com_nome_real():
    t = texto(DOCS / "COLUNAS.md")
    for fonte in ["cde", "cecad", "tarifa", "dec", "indqual", "favela"]:
        assert fonte in t, f"fonte {fonte} sem linha em COLUNAS.md"
    assert "<coluna" not in t and "esperado" not in t, "ainda há placeholders em COLUNAS.md"


def test_F2_S03_cde_tem_coluna_municipal_ou_plano_b_acionado():
    t = texto(DOCS / "COLUNAS.md")
    assert ("tsee_municipal: true" in t) or ("rateio" in t and "flag" in t), \
        "CDE sem município e sem Plano B documentado"
