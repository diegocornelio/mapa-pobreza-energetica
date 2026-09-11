import geopandas as gpd, pandas as pd, numpy as np, json
from shapely.geometry import MultiPolygon, Polygon
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import RAW, INTERIM_ORIG, PROCESSED_ORIG, OUT
gdf=gpd.read_parquet(str(INTERIM_ORIG)+"/municipios.parquet")[["cod_ibge","uf","geometry"]].to_crs(5880)
d=pd.read_csv(str(OUT)+"/app_dados.csv")
gdf=gdf.merge(d[["cod_ibge"]],on="cod_ibge")
gdf=gdf.set_index("cod_ibge").loc[d.cod_ibge].reset_index()
W=1400.0; xmin,ymin,xmax,ymax=gdf.total_bounds; sc=W/(xmax-xmin); H=(ymax-ymin)*sc
def topath(g,tol):
    g=g.simplify(tol,preserve_topology=True)
    polys=g.geoms if isinstance(g,MultiPolygon) else [g]
    out=[]
    for p in polys:
        if p.is_empty or not isinstance(p,Polygon): continue
        xs,ys=p.exterior.coords.xy
        pts=[(int(round((x-xmin)*sc)),int(round((ymax-y)*sc))) for x,y in zip(xs,ys)]
        ded=[pts[0]]
        for q in pts[1:]:
            if q!=ded[-1]: ded.append(q)
        if len(ded)<3: continue
        out.append("M"+" ".join(f"{a},{b}" for a,b in ded)+"Z")
    return "".join(out)
gdf["p"]=[topath(g,2000) for g in gdf.geometry]
ufg=gdf.dissolve("uf").reset_index()
ufg["p"]=[topath(g,3000) for g in ufg.geometry]
print("municipios sem path:",int((gdf.p.str.len()==0).sum()))
js={"vb":[round(W),round(H)],"codes":d.cod_ibge.tolist(),"paths":gdf.p.tolist(),
    "uf_paths":{r.uf:r.p for r in ufg.itertuples()}}
open(str(OUT)+"/geo.json","w",encoding="utf-8").write(json.dumps(js,separators=(",",":")))
import os; print("geo.json: %.2f MB"%(os.path.getsize(str(OUT)+"/geo.json")/1e6))
