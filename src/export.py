"""IPEM: Índice de Pobreza Energética Municipal.

Reúso de dados abertos (ANEEL, MDS, IBGE) para o 2º Concurso de Reúso de Dados Abertos da CGU.

Autor: Diego H. C. de Rezende, fundador da Struktur Energia.
Engenheiro de Computação e mestre em Engenharia de Software, com experiência em desenvolvimento de software, ciência de dados, gestão de projetos e operação de sistemas em ambientes de alta complexidade e missão crítica. Fundador da Struktur Energia, iniciativa dedicada a inteligência de mercado, eficiência energética e gestão estratégica de energia. Cursa o MBA em Gestão de Riscos na Comercialização de Energia (USP/CCEE) e o MBA em Data Science, Inteligência Artificial e Analytics (USP/ESALQ).

Repositório: https://github.com/diegocornelio/mapa-pobreza-energetica
Licença do código: MIT. Licença dos dados derivados: CC-BY 4.0.
"""
import geopandas as gpd
import pandas as pd

from config.settings import INTERIM, PROCESSED


def export_all(ipem: pd.DataFrame, sinais: pd.DataFrame) -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    ipem.to_csv(PROCESSED / "ipem_municipios.csv", index=False, encoding="utf-8")
    sinais.to_csv(
        PROCESSED / "sinais_precariedade_comercial.csv", index=False, encoding="utf-8"
    )
    geo = gpd.read_parquet(INTERIM / "municipios.parquet")[["cod_ibge", "geometry"]]
    geo["geometry"] = geo.geometry.simplify(0.01, preserve_topology=True)
    cols = ["cod_ibge", "nome_uf", "uf", "ipem", "ranking", "faixa", "dois_piores_indicadores"]
    geo.merge(ipem[cols], on="cod_ibge").to_file(
        PROCESSED / "ipem.geojson", driver="GeoJSON"
    )
