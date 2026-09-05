"""IPEM: Índice de Pobreza Energética Municipal.

Reúso de dados abertos (ANEEL, MDS, IBGE) para o 2º Concurso de Reúso de Dados Abertos da CGU.

Autor: Diego H. C. de Rezende, fundador da Struktur Energia.
Engenheiro de Computação e mestre em Engenharia de Software, com experiência em desenvolvimento de software, ciência de dados, gestão de projetos e operação de sistemas em ambientes de alta complexidade e missão crítica. Fundador da Struktur Energia, iniciativa dedicada a inteligência de mercado, eficiência energética e gestão estratégica de energia. Cursa o MBA em Gestão de Riscos na Comercialização de Energia (USP/CCEE) e o MBA em Data Science, Inteligência Artificial e Analytics (USP/ESALQ).

Repositório: https://github.com/diegocornelio/ipem-pobreza-energetica-municipal
Licença do código: MIT. Licença dos dados derivados: CC-BY 4.0.
"""
from pathlib import Path

import requests

from config.settings import DOWNLOAD_DATE, RAW

DATASETS = {
    "aneel_cde": {
        "org": "aneel",
        "slug": "beneficiarios-cde",
        "url": "https://dadosabertos.aneel.gov.br/dataset/beneficiarios-da-cde",
        "manual": True,
    },
    "aneel_decfec": {
        "org": "aneel",
        "slug": "dec-fec",
        "url": "https://dadosabertos.aneel.gov.br/dataset/indicadores-coletivos-de-continuidade-dec-e-fec",
        "manual": True,
    },
    "aneel_indqual": {
        "org": "aneel",
        "slug": "indqual-municipio",
        "url": "https://dadosabertos.aneel.gov.br/dataset/indqual-municipio",
        "manual": True,
    },
    "aneel_indger": {
        "org": "aneel",
        "slug": "indger",
        "url": "https://dadosabertos.aneel.gov.br/dataset/indger-indicadores-gerenciais-da-distribuicao",
        "manual": True,
    },
    "mds_cecad": {
        "org": "mds",
        "slug": "cecad-tabcad",
        "url": "https://cecad.cidadania.gov.br/",
        "manual": True,
    },
}


def raw_dir(org: str, slug: str) -> Path:
    path = RAW / org / slug / DOWNLOAD_DATE
    path.mkdir(parents=True, exist_ok=True)
    return path


def download_file(url: str, target: Path) -> Path:
    with requests.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()
        with target.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
    return target
