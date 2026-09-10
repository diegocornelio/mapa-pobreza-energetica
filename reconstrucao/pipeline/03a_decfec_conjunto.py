import pandas as pd, numpy as np
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import RAW, INTERIM_ORIG, PROCESSED_ORIG, OUT
B=str(RAW)+"/aneel"
# --- DEC/FEC anual 2024 por conjunto = SOMA dos 12 meses ---
d = pd.read_parquet(B+"/decfec/2026-09-05/indicadores-continuidade-coletivos-2020-2029.parquet",
  columns=["IdeConjUndConsumidoras","SigIndicador","AnoIndice","NumPeriodoIndice","VlrIndiceEnviado"])
d = d[(d.AnoIndice==2024) & (d.SigIndicador.isin(["DEC","FEC"]))]
anual = d.groupby(["IdeConjUndConsumidoras","SigIndicador"]).agg(
  soma12=("VlrIndiceEnviado","sum"), media12=("VlrIndiceEnviado","mean"), meses=("VlrIndiceEnviado","size")).reset_index()
print("conjuntos-indicador 2024:", len(anual), "| meses por serie:", anual.meses.value_counts().to_dict())
# --- limites 2024 ---
L = pd.read_csv(B+"/decfec/2026-09-05/indicadores-continuidade-coletivos-limite.csv", sep=";", low_memory=False)
L["VlrLimite"]=L.VlrLimite.astype(str).str.replace(".","",regex=False).str.replace(",",".",regex=False).astype(float)
L = L[(L.AnoLimiteQualidade==2024)&(L.SigIndicador.isin(["DEC","FEC"]))][["IdeConjUndConsumidoras","SigIndicador","VlrLimite"]]
L = L.drop_duplicates(["IdeConjUndConsumidoras","SigIndicador"])
print("limites 2024:", len(L))
m = anual.merge(L, on=["IdeConjUndConsumidoras","SigIndicador"], how="inner")
m["rel_ATUAL_media_sobre_limite"] = m.media12/m.VlrLimite
m["rel_CORRIGIDO_soma_sobre_limite"] = m.soma12/m.VlrLimite
print("\n=== COMPARACAO (conjuntos com limite 2024:", len(m), ") ===")
for ind in ["DEC","FEC"]:
    x=m[m.SigIndicador==ind]
    print(f"  {ind}: apurado anual mediano={x.soma12.median():.2f} | limite mediano={x.VlrLimite.median():.2f}")
    print(f"     razao ATUAL (media/limite)   mediana={x.rel_ATUAL_media_sobre_limite.median():.4f} max={x.rel_ATUAL_media_sobre_limite.max():.3f} | violacoes(>=1): {(x.rel_ATUAL_media_sobre_limite>=1).sum()}")
    print(f"     razao CORRIGIDA (soma/limite) mediana={x.rel_CORRIGIDO_soma_sobre_limite.median():.4f} max={x.rel_CORRIGIDO_soma_sobre_limite.max():.3f} | violacoes(>=1): {(x.rel_CORRIGIDO_soma_sobre_limite>=1).sum()} ({100*(x.rel_CORRIGIDO_soma_sobre_limite>=1).mean():.1f}%)")
m.to_parquet(str(OUT)+"/decfec_conj_2024.parquet")
