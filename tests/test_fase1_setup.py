"""IPEM: Índice de Pobreza Energética Municipal.

Reúso de dados abertos (ANEEL, MDS, IBGE) para o 2º Concurso de Reúso de Dados Abertos da CGU.

Autor: Diego H. C. de Rezende, fundador da Struktur Energia.
Engenheiro de Computação e mestre em Engenharia de Software, com experiência em desenvolvimento de software, ciência de dados, gestão de projetos e operação de sistemas em ambientes de alta complexidade e missão crítica. Fundador da Struktur Energia, iniciativa dedicada a inteligência de mercado, eficiência energética e gestão estratégica de energia. Cursa o MBA em Gestão de Riscos na Comercialização de Energia (USP/CCEE) e o MBA em Data Science, Inteligência Artificial e Analytics (USP/ESALQ).

Repositório: https://github.com/diegocornelio/ipem-pobreza-energetica-municipal
Licença do código: MIT. Licença dos dados derivados: CC-BY 4.0.
"""
import importlib
import re
import subprocess
import sys
from conftest import ROOT, DATA, DOCS
import pytest

pytestmark = pytest.mark.fase1

PASTAS = ["app", "app/assets", "config", "data/raw", "data/interim", "data/processed",
          "data/sources", "docs", "docs/comprovantes", "notebooks", "src", "tests"]
ARQUIVOS = [".gitignore", "requirements.txt", "Makefile", "run_all.py", "LICENSE", "LICENSE-DATA",
            "README.md", "config/settings.py", "src/__init__.py", "src/io_utils.py",
            "src/indicators.py", "src/prepare.py", "src/validate.py", "src/export.py",
            "data/sources/fontes.csv", "docs/FONTES.md", "docs/COLUNAS.md"]
NOTEBOOKS = ["00_inventario", "01_inspecao_colunas", "02_base_mestre", "03_indice_validacao", "04_storytelling"]
PINS = {"pandas": "2.2.2", "duckdb": "1.0.0", "pyarrow": "17.0.0", "geopandas": "1.0.1",
        "geobr": "0.2.2", "streamlit": "1.37.1", "plotly": "5.23.0", "requests": "2.32.3",
        "openpyxl": "3.1.5", "pytest": "8.3.2"}


def test_F1_T01_estrutura_de_pastas():
    faltam = [p for p in PASTAS if not (ROOT / p).is_dir()]
    assert not faltam, f"pastas ausentes: {faltam}"


def test_F1_T02_arquivos_obrigatorios():
    faltam = [a for a in ARQUIVOS if not (ROOT / a).is_file()]
    assert not faltam, f"arquivos ausentes: {faltam}"
    for path in ROOT.rglob("*.py"):
        if ".venv" in path.parts:
            continue
        assert "Autor: Diego H. C. de Rezende" in path.read_text(encoding="utf-8").split('"""', 2)[1], path


def test_F1_T03_notebooks_existem_e_sao_json_validos():
    import json
    for nb in NOTEBOOKS:
        p = ROOT / "notebooks" / f"{nb}.ipynb"
        assert p.is_file(), nb
        json.loads(p.read_text(encoding="utf-8"))


def test_F1_T04_gitignore_exclui_dados_brutos():
    gi = (ROOT / ".gitignore").read_text()
    for regra in ["data/raw/", "data/interim/", "*.zip", ".venv/"]:
        assert regra in gi, regra


def test_F1_T05_requirements_com_versoes_fixadas():
    linhas = [l.strip() for l in (ROOT / "requirements.txt").read_text().splitlines() if l.strip()]
    pinned = dict(l.split("==") for l in linhas)
    assert pinned == PINS, f"pins divergentes: {set(pinned.items()) ^ set(PINS.items())}"


def test_F1_T06_ambiente_importa_tudo():
    for mod in ["pandas", "duckdb", "pyarrow", "geopandas", "geobr", "plotly", "streamlit", "requests", "openpyxl"]:
        importlib.import_module(mod)


def test_F1_T07_licencas_corretas():
    lic = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "MIT License" in lic and "Permission is hereby granted" in lic
    ld = (ROOT / "LICENSE-DATA").read_text(encoding="utf-8")
    assert "CC BY 4.0" in ld or "Creative Commons Attribution 4.0" in ld


def test_F1_T08_readme_declara_licencas_e_reproducao():
    rd = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "MIT" in rd and "CC-BY 4.0" in rd
    assert "run_all.py" in rd
    assert "Sobre o autor" in rd and "Diego H. C. de Rezende" in rd


def test_F1_T09_fontes_csv_tem_cabecalho_da_v7():
    cab = (DATA / "sources" / "fontes.csv").read_text(encoding="utf-8").splitlines()[0]
    esperado = ("source_id,orgao,dataset,resource_name,original_filename,local_path,url,download_date,"
                "data_reference_date,metadata_modified,geographic_scale,temporal_scale,license,used_in,notes")
    assert cab.strip() == esperado


def test_F1_T10_settings_consistente():
    sys.path.insert(0, str(ROOT))
    from config import settings as s
    assert s.N_MUNICIPIOS_ESPERADO == 5570
    assert s.BASE_CONSUMPTION_KWH in s.CONSUMPTION_SCENARIOS_KWH
    assert set(s.DIM_LABELS.values()) == {"D1", "D2", "D3", "D4"}
    assert set(s.DIM_LABELS) == set(s.DIM_COLS)
    assert len(s.BAIXADA) == 13


def test_F1_T11_run_all_e_executavel_sintaticamente():
    subprocess.run([sys.executable, "-m", "py_compile", str(ROOT / "run_all.py")], check=True)


def test_F1_T12_repositorio_git_com_commit_e_remote_publico():
    log = subprocess.run(["git", "log", "--oneline"], cwd=ROOT, capture_output=True, text=True)
    assert log.returncode == 0 and log.stdout.strip(), "sem commit"
    remote = subprocess.run(["git", "remote", "get-url", "origin"], cwd=ROOT, capture_output=True, text=True)
    assert remote.returncode == 0 and "github.com" in remote.stdout, "origin não aponta para o GitHub"
    url = remote.stdout.strip().replace("git@github.com:", "https://github.com/").removesuffix(".git")
    try:
        import requests
        r = requests.get(url, timeout=20)
        assert r.status_code == 200, f"repositório não é público ou não existe: {url} -> {r.status_code}"
    except ImportError:
        pytest.skip("requests indisponível; verificar manualmente que a URL abre sem login")
