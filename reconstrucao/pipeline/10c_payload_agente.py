import pandas as pd, numpy as np, json, os
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import RAW, INTERIM_ORIG, PROCESSED_ORIG, OUT
geo = json.load(open(str(OUT)+"/geo.json", encoding="utf-8")); ordem = geo["codes"]
base = json.load(open(str(OUT)+"/dados.json", encoding="utf-8"))

j = pd.read_csv(str(OUT)+"/mun_agente.csv")
dom = j.sort_values("b24", ascending=False).drop_duplicates("cod_ibge")[["cod_ibge","agente","b24","b26"]]
dom = dom.set_index("cod_ibge").reindex(ordem).reset_index()
dom["v"] = 100*(dom.b26/dom.b24.replace(0,np.nan) - 1)

nomes = sorted(dom.agente.dropna().unique().tolist())
idx = {n:i for i,n in enumerate(nomes)}
base["cdeag"] = nomes
base["cdei"] = [None if pd.isna(a) else idx[a] for a in dom.agente]
base["cdev"] = [None if pd.isna(v) or not np.isfinite(v) else round(float(v),1) for v in dom.v]

open(str(OUT)+"/dados.json","w",encoding="utf-8").write(json.dumps(base, separators=(",",":"), ensure_ascii=False))
print("agentes da CDE:", len(nomes), "| municipios com agente:", int(dom.agente.notna().sum()))
print("dados.json: %.2f MB" % (os.path.getsize(str(OUT)+"/dados.json")/1e6))
