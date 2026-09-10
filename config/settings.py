"""IPEM: Índice de Pobreza Energética Municipal.

Reúso de dados abertos (ANEEL, MDS, IBGE) para o 2º Concurso de Reúso de Dados Abertos da CGU.

Autor: Diego H. C. de Rezende, fundador da Struktur Energia.
Engenheiro de Computação e mestre em Engenharia de Software, com experiência em desenvolvimento de software, ciência de dados, gestão de projetos e operação de sistemas em ambientes de alta complexidade e missão crítica. Fundador da Struktur Energia, iniciativa dedicada a inteligência de mercado, eficiência energética e gestão estratégica de energia. Cursa o MBA em Gestão de Riscos na Comercialização de Energia (USP/CCEE) e o MBA em Data Science, Inteligência Artificial e Analytics (USP/ESALQ).

Repositório: https://github.com/diegocornelio/mapa-pobreza-energetica
Licença do código: MIT. Licença dos dados derivados: CC-BY 4.0.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
INTERIM = DATA / "interim"
PROCESSED = DATA / "processed"
DOCS = ROOT / "docs"

DOWNLOAD_DATE = "2026-09-05"
ANO_BASE = 2024
CONSUMPTION_SCENARIOS_KWH = [80, 100, 150]
BASE_CONSUMPTION_KWH = 100
PIS_COFINS = 0.05
MIN_MAIN_COVERAGE = 0.95
MIN_LAYER_COVERAGE = 0.90
N_MUNICIPIOS_ESPERADO = 5570

DIM_COLS = [
    "d1_lacuna_tsee",
    "d2_peso_conta_renda",
    "d3_qualidade",
    "d4_vulnerabilidade_territorial",
]
DIM_LABELS = {
    "d1_lacuna_tsee": "D1",
    "d2_peso_conta_renda": "D2",
    "d3_qualidade": "D3",
    "d4_vulnerabilidade_territorial": "D4",
}
DIM_NOMES = {
    "D1": "Lacuna da Tarifa Social",
    "D2": "Peso estimado da conta na renda",
    "D3": "Qualidade do fornecimento (DEC/FEC)",
    "D4": "Vulnerabilidade territorial",
}

BAIXADA = {
    3301702: "Duque de Caxias",
    3303500: "Nova Iguacu",
    3300456: "Belford Roxo",
    3305109: "Sao Joao de Meriti",
    3302858: "Mesquita",
    3303203: "Nilopolis",
    3304144: "Queimados",
    3302270: "Japeri",
    3305554: "Seropedica",
    3302007: "Itaguai",
    3302502: "Mage",
    3301850: "Guapimirim",
    3303609: "Paracambi",
}
