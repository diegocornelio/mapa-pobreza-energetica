import pandas as pd, numpy as np
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import RAW, INTERIM_ORIG, PROCESSED_ORIG, OUT
B = str(RAW)+"/aneel"
d = pd.read_parquet(B+"/decfec/2026-09-05/indicadores-continuidade-coletivos-2020-2029.parquet",
                    columns=["IdeConjUndConsumidoras","SigIndicador","AnoIndice","NumPeriodoIndice","VlrIndiceEnviado"])
L = pd.read_csv(B+"/decfec/2026-09-05/indicadores-continuidade-coletivos-limite.csv", sep=";", low_memory=False)
L["VlrLimite"] = L.VlrLimite.astype(str).str.replace(".","",regex=False).str.replace(",",".",regex=False).astype(float)
q = pd.read_csv(B+"/indqual/2026-09-05/indqual-municipio.csv", sep=";", encoding="latin-1", low_memory=False)
q = q.rename(columns={"IdeConjUnidConsumidoras":"IdeConjUndConsumidoras","CodMunicipio":"cod_ibge"})[["IdeConjUndConsumidoras","cod_ibge"]].drop_duplicates()

def ano(a):
    x = d[(d.AnoIndice==a) & d.SigIndicador.isin(["DEC","FEC"])]
    ser = x.groupby(["IdeConjUndConsumidoras","SigIndicador"]).agg(soma=("VlrIndiceEnviado","sum"), n=("VlrIndiceEnviado","size")).reset_index()
    ser = ser[ser.n==12]
    lim = L[(L.AnoLimiteQualidade==a)&(L.SigIndicador.isin(["DEC","FEC"]))][["IdeConjUndConsumidoras","SigIndicador","VlrLimite"]].drop_duplicates(["IdeConjUndConsumidoras","SigIndicador"])
    m = ser.merge(lim, on=["IdeConjUndConsumidoras","SigIndicador"])
    m["rel"] = m.soma/m.VlrLimite
    con = d[(d.AnoIndice==a)&(d.SigIndicador=="NumCon")].groupby("IdeConjUndConsumidoras").VlrIndiceEnviado.mean().rename("cons")
    p = m.pivot_table(index="IdeConjUndConsumidoras", columns="SigIndicador", values=["rel","soma"])
    p.columns=[f"{x}_{y}" for x,y in p.columns]; p=p.join(con).reset_index()
    p["pior"] = p[["rel_DEC","rel_FEC"]].max(axis=1)
    j = q.merge(p, on="IdeConjUndConsumidoras", how="inner").dropna(subset=["pior"])
    j["w"] = j.cons.fillna(0)
    g = j.groupby("cod_ibge").apply(lambda x: pd.Series({
        "rel": np.average(x.pior, weights=x.w) if x.w.sum()>0 else x.pior.mean(),
        "dec_h": np.average(x.soma_DEC, weights=x.w) if x.w.sum()>0 else x.soma_DEC.mean(),
        "nconj": x.IdeConjUndConsumidoras.nunique()}), include_groups=False).reset_index()
    print(f"  {a}: {len(g)} municipios | conjuntos violando DEC: {int((m[(m.SigIndicador=='DEC')].rel>=1).sum())} de {m[m.SigIndicador=='DEC'].shape[0]}")
    return g.rename(columns={"rel":f"rel{a}","dec_h":f"dec{a}","nconj":f"nc{a}"})

print("=== apuracao ===")
a24, a25 = ano(2024), ano(2025)
m = a24.merge(a25, on="cod_ibge", how="inner")
m["viol24"]=(m.rel2024>=1).astype(int); m["viol25"]=(m.rel2025>=1).astype(int)
print()
print("=== MUNICIPIOS ACIMA DO LIMITE ===")
print(f"  2024: {int(m.viol24.sum()):5d} de {len(m)} ({100*m.viol24.mean():.1f}%)")
print(f"  2025: {int(m.viol25.sum()):5d} de {len(m)} ({100*m.viol25.mean():.1f}%)")
print()
print("=== TRANSICAO ===")
print(f"  violava e deixou de violar : {int(((m.viol24==1)&(m.viol25==0)).sum()):5d}")
print(f"  nao violava e passou a violar: {int(((m.viol24==0)&(m.viol25==1)).sum()):5d}")
print(f"  violava nos dois anos       : {int(((m.viol24==1)&(m.viol25==1)).sum()):5d}")
print(f"  dentro do limite nos dois   : {int(((m.viol24==0)&(m.viol25==0)).sum()):5d}")
print()
print("=== DEC ANUAL PONDERADO ===")
print(f"  2024: mediana {m.dec2024.median():.2f} h | 2025: mediana {m.dec2025.median():.2f} h ({100*(m.dec2025.median()/m.dec2024.median()-1):+.1f}%)")
print(f"  razao sobre o limite: 2024 med {m.rel2024.median():.3f} | 2025 med {m.rel2025.median():.3f}")
print(f"  municipios que pioraram: {int((m.rel2025>m.rel2024).sum())} ({100*(m.rel2025>m.rel2024).mean():.1f}%)")
m.to_csv(str(OUT)+"/decfec_2024_2025.csv", index=False)
