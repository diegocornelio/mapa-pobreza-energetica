"""Geometria municipal em WGS84, para uma biblioteca de mapa de verdade.

Ate aqui este passo projetava a malha em SIRGAS 2000 / Policonica (EPSG:5880) e
gravava caminho SVG com coordenada inteira, ja escalado para uma viewBox de 1400
unidades. Aquilo servia a um coropleto desenhado a mao e tinha tres limitacoes:

  1. o enquadramento era sequestrado pelo extremo leste da malha, que e o
     arquipelago de Trindade e Martim Vaz, dentro do poligono de Vitoria/ES, a
     cerca de 1.100 km da costa. O envelope ficava 4.819 km de largura contra os
     4.326 km do continente, entao 11% da tela era Atlantico vazio;
  2. o arredondamento para inteiro dava 3,44 km por unidade, o que e grosseiro
     para qualquer aproximacao;
  3. nao havia zoom, deslocamento nem toque de verdade, porque nao havia mapa,
     havia um desenho.

Agora grava GeoJSON em coordenada geografica, que a biblioteca reprojeta sozinha
conforme o nivel de zoom. A simplificacao continua sendo de 2 km, feita no plano
projetado, que e onde tolerancia em metros faz sentido; o arredondamento para
tres casas decimais vale cerca de 111 m, bem abaixo do vertice mais proximo que
a simplificacao deixa, de modo que nao se perde nada visivel.

Custo medido: 2,30 MB crus, 0,51 MB depois da compressao que o servidor aplica,
contra 866 KB do formato anterior.
"""
import geopandas as gpd, pandas as pd, json, os, sys
from shapely.geometry import MultiPolygon
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import RAW, INTERIM_ORIG, PROCESSED_ORIG, OUT

CASAS = 3          # ~111 m
TOL_MUN = 2000     # metros, no plano projetado
TOL_UF = 3000
MIN_PARTE_KM2 = 20 # descarta lasca de dissolve na camada estadual

gdf = gpd.read_parquet(str(INTERIM_ORIG) + "/municipios.parquet")[["cod_ibge", "uf", "geometry"]]
d = pd.read_csv(str(OUT) + "/app_dados.csv")
gdf = gdf.merge(d[["cod_ibge"]], on="cod_ibge")
gdf = gdf.set_index("cod_ibge").loc[d.cod_ibge].reset_index()   # ordem do payload

proj = gdf.to_crs(5880)

def arred(c):
    if isinstance(c[0], (int, float)):
        return [round(c[0], CASAS), round(c[1], CASAS)]
    return [arred(x) for x in c]

def colecao(geoms, ids, tol, topologia=True):
    g = gpd.GeoSeries(geoms, crs=5880).simplify(tol, preserve_topology=topologia).to_crs(4326)
    feats = []
    for i, geom in zip(ids, g):
        if geom is None or geom.is_empty:
            feats.append({"type": "Feature", "id": i, "properties": {}, "geometry": None})
            continue
        gj = geom.__geo_interface__
        feats.append({"type": "Feature", "id": i, "properties": {},
                      "geometry": {"type": gj["type"], "coordinates": arred(gj["coordinates"])}})
    return {"type": "FeatureCollection", "features": feats}

mun = colecao(proj.geometry.tolist(), [int(x) for x in gdf.cod_ibge], TOL_MUN)
# A camada estadual sai de um dissolve, que produz milhares de lascas nas frestas
# de ponto flutuante entre municipios vizinhos: 898 partes, mediana de 0,014 km2.
# Pior, com preserve_topology a simplificacao se recusa a agir sobre essa geometria
# e o resultado fica em 163 mil vertices e 3,3 MB, mais que a malha municipal
# inteira. Descartadas as lascas e liberada a simplificacao, sao 4.949 vertices e
# 0,09 MB, sem diferenca visivel num contorno de separacao.
def sem_lascas(x):
    partes = list(x.geoms) if x.geom_type == "MultiPolygon" else [x]
    grandes = [p for p in partes if p.area >= MIN_PARTE_KM2 * 1e6] or [max(partes, key=lambda p: p.area)]
    return (MultiPolygon(grandes) if len(grandes) > 1 else grandes[0]).buffer(0)

ufp = proj.assign(uf=gdf.uf.values).dissolve("uf").reset_index()
uf = colecao([sem_lascas(x) for x in ufp.geometry], ufp.uf.tolist(), TOL_UF, topologia=False)

vazios = sum(1 for f in mun["features"] if f["geometry"] is None)
print(f"municipios: {len(mun['features'])} | sem geometria: {vazios}")
print(f"unidades da federacao: {len(uf['features'])}")

# Enquadramento inicial: o continente, sem as ilhas oceanicas. Trindade e Martim
# Vaz continuam no mapa, alcancaveis por deslocamento; elas so deixam de mandar
# no zoom de abertura.
ILHAS_OCEANICAS = {3205309, 2605459, 2611606}     # Vitoria/ES, Fernando de Noronha e afins
cont = gdf[~gdf.cod_ibge.isin(ILHAS_OCEANICAS)].to_crs(4326)
x0, y0, x1, y1 = cont.total_bounds
foco = [[round(y0, CASAS), round(x0, CASAS)], [round(y1, CASAS), round(x1, CASAS)]]
todo = gdf.to_crs(4326).total_bounds
print(f"enquadramento do continente: {x1-x0:.2f} graus de longitude")
print(f"envelope com as ilhas      : {todo[2]-todo[0]:.2f} graus")

js = {"codes": [int(x) for x in gdf.cod_ibge], "foco": foco, "mun": mun, "uf": uf}
p = str(OUT) + "/geo.json"
open(p, "w", encoding="utf-8").write(json.dumps(js, separators=(",", ":")))
print(f"geo.json: {os.path.getsize(p)/1e6:.2f} MB")
