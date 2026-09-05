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
