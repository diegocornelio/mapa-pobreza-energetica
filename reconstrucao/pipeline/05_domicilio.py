import json, glob, urllib.request, pandas as pd, numpy as np
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import RAW, INTERIM_ORIG, PROCESSED_ORIG, OUT
# moradores por municipio (SIDRA 10296, classe Total)
rows=[]
for p in glob.glob(str(RAW)+"/ibge/censo2022-renda/2026-09-05/*.json"):
    j=json.load(open(p,encoding="utf-8"))
    for b in j:
        for res in b["resultados"]:
            cats=[list(c["categoria"].values())[0] for c in res["classificacoes"]]
            if cats[-1]!="Total": continue
            for s in res["series"]:
                rows.append({"cod_ibge":int(s["localidade"]["id"]),"moradores":pd.to_numeric(s["serie"]["2022"],errors="coerce")})
mor=pd.DataFrame(rows).dropna().drop_duplicates("cod_ibge")
print("municipios com moradores:",len(mor),"| total pais:", f"{mor.moradores.sum():,.0f}")
d4=pd.read_csv(str(OUT)+"/d4_corrigido.csv")
m=mor.merge(d4[["cod_ibge","dom_total_mun"]],on="cod_ibge")
m["moradores_por_domicilio"]=m.moradores/m.dom_total_mun
print("\n=== TAMANHO MEDIO DO DOMICILIO ===")
print(f"min={m.moradores_por_domicilio.min():.2f} p25={m.moradores_por_domicilio.quantile(.25):.2f} MED={m.moradores_por_domicilio.median():.2f} p75={m.moradores_por_domicilio.quantile(.75):.2f} max={m.moradores_por_domicilio.max():.2f}")
print("amplitude: %.2fx" % (m.moradores_por_domicilio.max()/m.moradores_por_domicilio.min()))
m.to_csv(str(OUT)+"/domicilio_tamanho.csv",index=False)
