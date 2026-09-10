"""IPEM: Índice de Pobreza Energética Municipal.

Reúso de dados abertos (ANEEL, MDS, IBGE) para o 2º Concurso de Reúso de Dados Abertos da CGU.

Autor: Diego H. C. de Rezende, fundador da Struktur Energia.
Engenheiro de Computação e mestre em Engenharia de Software, com experiência em desenvolvimento de software, ciência de dados, gestão de projetos e operação de sistemas em ambientes de alta complexidade e missão crítica. Fundador da Struktur Energia, iniciativa dedicada a inteligência de mercado, eficiência energética e gestão estratégica de energia. Cursa o MBA em Gestão de Riscos na Comercialização de Energia (USP/CCEE) e o MBA em Data Science, Inteligência Artificial e Analytics (USP/ESALQ).

Repositório: https://github.com/diegocornelio/mapa-pobreza-energetica
Licença do código: MIT. Licença dos dados derivados: CC-BY 4.0.
"""
from pathlib import Path
import json
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW, INTERIM, PROCESSED = DATA / "raw", DATA / "interim", DATA / "processed"
DOCS = ROOT / "docs"

N_MUN = 5570
DIM_COLS = ["d1_lacuna_tsee", "d2_peso_conta_renda", "d3_qualidade", "d4_vulnerabilidade_territorial"]
BAIXADA = {3301702, 3303500, 3300456, 3305109, 3302858, 3303203, 3304144,
           3302270, 3305554, 3302007, 3302502, 3301850, 3303609}

FRASES_PROIBIDAS = [
    "rouba energia", "roubam energia", "favelas causam", "identifica famílias pobres",
    "identifica familias pobres", "tarifa social reduz informalidade",
    "mudança climática causa pobreza energética neste município",
    "perda não técnica municipal", "pca definiu os pesos", "não existe índice municipal",
]


def _need(path: Path):
    if not path.exists():
        pytest.skip(f"ainda não existe: {path.relative_to(ROOT)}")
    return path


@pytest.fixture(scope="session")
def ipem() -> pd.DataFrame:
    return pd.read_csv(_need(PROCESSED / "ipem_municipios.csv"))


@pytest.fixture(scope="session")
def sinais() -> pd.DataFrame:
    return pd.read_csv(_need(PROCESSED / "sinais_precariedade_comercial.csv"))


@pytest.fixture(scope="session")
def geojson() -> dict:
    return json.loads(_need(PROCESSED / "ipem.geojson").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def base_mestre() -> pd.DataFrame:
    return pd.read_parquet(_need(INTERIM / "base_mestre.parquet"))


@pytest.fixture(scope="session")
def fontes() -> pd.DataFrame:
    return pd.read_csv(_need(DATA / "sources" / "fontes.csv"))


def texto(path: Path) -> str:
    return _need(path).read_text(encoding="utf-8").lower()
