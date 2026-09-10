import urllib.request, json, pandas as pd, numpy as np
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import RAW, INTERIM_ORIG, PROCESSED_ORIG, OUT
d=json.loads(urllib.request.urlopen("https://apisidra.ibge.gov.br/values/t/4712/n6/all/v/allxp/p/2022",timeout=60).read().decode("utf-8"))[1:]
tot=pd.DataFrame([{"cod_ibge":int(r["D1C"]),"dom_total_mun":pd.to_numeric(r["V"],errors="coerce")} for r in d if r["D2C"]=="381"])
tot=tot.dropna().drop_duplicates("cod_ibge")
print("municipios com total de domicilios:",len(tot))
p=str(RAW)+"/ibge/favelas/2026-09-05/sidra_9887_favelas_municipios_2022.json"
j=json.load(open(p,encoding="utf-8"))
fav=pd.DataFrame([{"cod_ibge":int(s["localidade"]["id"]),"dom_favela":pd.to_numeric(s["serie"]["2022"],errors="coerce")}
  for b in j if str(b["id"])=="9909" for s in b["resultados"][0]["series"]]).dropna()
print("municipios com favela mapeada:",len(fav))
m=tot.merge(fav,on="cod_ibge",how="left")
m["dom_favela"]=m.dom_favela.fillna(0)
m["d4_corr"]=m.dom_favela/m.dom_total_mun
m["favela_mapeada"]=m.cod_ibge.isin(fav.cod_ibge)
print("\n=== D4 CORRIGIDO = domicilios em favela / domicilios do municipio ===")
x=m[m.favela_mapeada]
print(f"nos 656 com favela: min={x.d4_corr.min():.4f} MED={x.d4_corr.median():.4f} p75={x.d4_corr.quantile(.75):.4f} p95={x.d4_corr.quantile(.95):.4f} max={x.d4_corr.max():.4f}")
print("\n-- capitais, ANTES (composicao de especie) x DEPOIS (participacao real) --")
ipm=pd.read_csv(str(PROCESSED_ORIG),usecols=["cod_ibge","nome_uf","d4_vulnerabilidade_territorial"])
cmp=m.merge(ipm,on="cod_ibge")
for c in [3304557,3550308,2304400,2611606,2927408,1302603,1501402,3106200,5300108]:
    r=cmp[cmp.cod_ibge==c].iloc[0]
    print(f"  {r.nome_uf:22s} antes={r.d4_vulnerabilidade_territorial:.3f}  depois={r.d4_corr:.3f}  ({r.dom_favela:,.0f} de {r.dom_total_mun:,.0f} domicilios)")
print("\n-- 8 maiores participacoes reais --")
print(cmp.nlargest(8,"d4_corr")[["nome_uf","dom_favela","dom_total_mun","d4_corr","d4_vulnerabilidade_territorial"]].round(3).to_string(index=False))
m.to_csv(str(OUT)+"/d4_corrigido.csv",index=False)
