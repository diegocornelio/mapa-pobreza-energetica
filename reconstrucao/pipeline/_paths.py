"""Caminhos do pipeline de reconstrução do Mapa da Pobreza Energética.

RAW aponta para o diretório de dados brutos baixados em 2026-09-05.
Ele NÃO acompanha o repositório: são cerca de 3 GB, com um CSV de 2,3 GB
dentro do zip da CDE. As URLs de origem estão em data/sources/fontes.csv.

Ajuste RAW e PROCESSED_ORIG para a sua máquina antes de rodar.
"""
from pathlib import Path

RAW = Path(r"C:/Users/diego/Desktop/IndiceMunicipalPobrezaEnergetica - IMPE/data/raw")
INTERIM_ORIG = Path(r"C:/Users/diego/Desktop/IndiceMunicipalPobrezaEnergetica - IMPE/data/interim")
PROCESSED_ORIG = Path(__file__).resolve().parents[2] / "data" / "processed" / "ipem_municipios.csv"
OUT = Path(__file__).resolve().parents[1] / "dados"
OUT.mkdir(parents=True, exist_ok=True)
