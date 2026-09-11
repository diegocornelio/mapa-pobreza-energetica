import pandas as pd, numpy as np
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import RAW, INTERIM_ORIG, PROCESSED_ORIG, OUT
B = str(RAW)+"/aneel"
d = pd.read_parquet(B+"/decfec/2026-09-05/indicadores-continuidade-coletivos-2020-2029.parquet",
                    columns=["IdeConjUndConsumidoras","SigIndicador","AnoIndice","NumPeriodoIndice","VlrIndiceEnviado"])
q = pd.read_csv(B+"/indqual/2026-09-05/indqual-municipio.csv", sep=";", encoding="latin-1", low_memory=False)
q = q.rename(columns={"IdeConjUnidConsumidoras":"IdeConjUndConsumidoras","CodMunicipio":"cod_ibge"})[["IdeConjUndConsumidoras","cod_ibge"]].drop_duplicates()
K = 6
base = None
for a in (2024,2025,2026):
    x = d[(d.SigIndicador=="DEC")&(d.AnoIndice==a)&(d.NumPeriodoIndice<=K)]
    c = x.groupby("IdeConjUndConsumidoras").NumPeriodoIndice.nunique()
    ok = set(c[c==K].index); base = ok if base is None else (base & ok)
print(f"base comum jan-jun nos tres anos: {len(base)} conjuntos")
con = d[(d.SigIndicador=="NumCon")&(d.AnoIndice==2025)].groupby("IdeConjUndConsumidoras").VlrIndiceEnviado.mean()
out = {}
for a in (2024,2025,2026):
    x = d[(d.SigIndicador=="DEC")&(d.AnoIndice==a)&(d.NumPeriodoIndice<=K)&(d.IdeConjUndConsumidoras.isin(base))]
    s = x.groupby("IdeConjUndConsumidoras").VlrIndiceEnviado.sum().rename(f"dec{a}")
    out[a] = s
p = pd.concat(out.values(), axis=1).join(con.rename("cons")).reset_index()
w = p.cons.fillna(0)
print()
print("=== DEC acumulado jan-jun, ponderado por consumidores ===")
for a in (2024,2025,2026):
    print(f"  {a}: {np.average(p[f'dec{a}'], weights=w):6.2f} h   | mediana por conjunto {p[f'dec{a}'].median():5.2f} h")
print()
v25 = 100*(np.average(p.dec2025,weights=w)/np.average(p.dec2024,weights=w)-1)
v26 = 100*(np.average(p.dec2026,weights=w)/np.average(p.dec2025,weights=w)-1)
vt  = 100*(np.average(p.dec2026,weights=w)/np.average(p.dec2024,weights=w)-1)
print(f"  2024 -> 2025: {v25:+.1f}%")
print(f"  2025 -> 2026: {v26:+.1f}%")
print(f"  2024 -> 2026: {vt:+.1f}%")
print()
j = q.merge(p, on="IdeConjUndConsumidoras", how="inner")
j["w"] = j.cons.fillna(0)
g = j.groupby("cod_ibge").apply(lambda x: pd.Series({
    f"s{a}": (np.average(x[f"dec{a}"], weights=x.w) if x.w.sum()>0 else x[f"dec{a}"].mean()) for a in (2024,2025,2026)
}), include_groups=False).reset_index()
print(f"=== municipal: {len(g)} municipios ===")
for a in (2024,2025,2026):
    print(f"  {a}: mediana municipal {g[f's{a}'].median():5.2f} h")
g["tend"] = np.where(g.s2026 > g.s2024*1.05, "piorou", np.where(g.s2026 < g.s2024*0.95, "melhorou", "estavel"))
print()
print("=== tendencia municipal jan-jun 2024 -> 2026 ===")
print(g.tend.value_counts().to_string())
g.to_csv(str(OUT)+"/dec_semestre.csv", index=False)
