import pandas as pd, numpy as np
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import RAW, INTERIM_ORIG, PROCESSED_ORIG, OUT
B=str(RAW)+"/aneel"
d=pd.read_parquet(B+"/decfec/2026-09-05/indicadores-continuidade-coletivos-2020-2029.parquet",
  columns=["IdeConjUndConsumidoras","SigIndicador","AnoIndice","NumPeriodoIndice","VlrIndiceEnviado"])
d=d[d.AnoIndice==2024]
con=d[d.SigIndicador=="NumCon"].groupby("IdeConjUndConsumidoras").VlrIndiceEnviado.mean().rename("consumidores")
print("conjuntos com NumCon:",len(con),"| total consumidores:", f"{con.sum():,.0f}")
m=pd.read_parquet("decfec_conj_2024.parquet")
q=pd.read_csv(B+"/indqual/2026-09-05/indqual-municipio.csv",sep=";",encoding="latin-1",low_memory=False)
q=q.rename(columns={"IdeConjUnidConsumidoras":"IdeConjUndConsumidoras","CodMunicipio":"cod_ibge"})[["IdeConjUndConsumidoras","cod_ibge"]].drop_duplicates()
p=m.pivot_table(index="IdeConjUndConsumidoras",columns="SigIndicador",values=["soma12","VlrLimite"],aggfunc="first")
p.columns=[f"{a}_{b}" for a,b in p.columns]; p=p.reset_index().join(con,on="IdeConjUndConsumidoras")
p["rel_dec"]=p.soma12_DEC/p.VlrLimite_DEC; p["rel_fec"]=p.soma12_FEC/p.VlrLimite_FEC
p["rel"]=p[["rel_dec","rel_fec"]].max(axis=1)
j=q.merge(p,on="IdeConjUndConsumidoras",how="inner").dropna(subset=["rel"])
j["w"]=j.consumidores.fillna(0)
def agg(x):
    w=x.w.sum()
    return pd.Series({"d3_max":x.rel.max(),
      "d3_pond":(np.average(x.rel,weights=x.w) if w>0 else x.rel.mean()),
      "dec_h_pond":(np.average(x.soma12_DEC,weights=x.w) if w>0 else x.soma12_DEC.mean()),
      "n_conj":x.IdeConjUndConsumidoras.nunique(),"consumidores":w})
mun=j.groupby("cod_ibge").apply(agg,include_groups=False).reset_index()
print("\n=== max x ponderado por consumidores ===")
print("municipios:",len(mun))
print("d3_max  mediana %.3f  | violacoes(>=1): %d (%.1f%%)"%(mun.d3_max.median(),(mun.d3_max>=1).sum(),100*(mun.d3_max>=1).mean()))
print("d3_pond mediana %.3f  | violacoes(>=1): %d (%.1f%%)"%(mun.d3_pond.median(),(mun.d3_pond>=1).sum(),100*(mun.d3_pond>=1).mean()))
print("DEC anual ponderado: mediana %.2f h | p95 %.2f h | max %.2f h"%(mun.dec_h_pond.median(),mun.dec_h_pond.quantile(.95),mun.dec_h_pond.max()))
for c,nm in [(3304557,"Rio de Janeiro"),(3550308,"Sao Paulo"),(1302603,"Manaus"),(1501402,"Belem")]:
    r=mun[mun.cod_ibge==c]
    if len(r): r=r.iloc[0]; print(f"  {nm:16s} conj={int(r.n_conj):3d} d3_max={r.d3_max:.2f} d3_pond={r.d3_pond:.2f} DEC_pond={r.dec_h_pond:.1f}h")
mun.to_csv("d3_pond.csv",index=False)
