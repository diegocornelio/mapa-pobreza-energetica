"""Comparacao nacional dez/2024 x mar/2026, base completa de 103 distribuidoras."""
import pandas as pd, numpy as np, sys
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import RAW, INTERIM_ORIG, PROCESSED_ORIG, OUT
TAG = sys.argv[1] if len(sys.argv) > 1 else "2026_03"
ROT = {"2026_03": "mar/2026", "2026_04": "abr/2026"}[TAG]
REF = {"2026_03": pd.Timestamp("2026-03-01"), "2026_04": pd.Timestamp("2026-04-01")}[TAG]
RAW = str(RAW)+"/aneel"
num = lambda s: pd.to_numeric(s.astype(str).str.replace(".","",regex=False).str.replace(",",".",regex=False), errors="coerce")

d = pd.read_csv(str(OUT)+"/app_dados2.csv")
n = pd.read_csv(str(OUT)+f"/cde_municipal_{TAG}.csv").rename(columns={f"ben_{TAG}":"ben26", f"subs_{TAG}":"subs26"})
m = d.merge(n, on="cod_ibge", how="left")
print(f"=== cobertura do arquivo {ROT} ===")
print(f"  municipios presentes: {int(m.ben26.notna().sum())} de {len(m)}")
m["ben26"] = m.ben26.fillna(0); m["subs26"] = m.subs26.fillna(0)

# --- 1. familias nao atendidas ---
ele = m.familias_elegiveis.sum(); b24 = m.beneficiarios_tsee.sum(); b26 = m.ben26.sum()
print()
print("=== 1. FAMILIAS NAO ATENDIDAS (denominador: CECAD ago/2026) ===")
print(f"  familias elegiveis:                {ele:>12,.0f}")
print(f"  beneficios dez/2024 (defasagem 20m): {b24:>12,.0f}  cobertura {100*b24/ele:.1f}%  nao atendidas {ele-b24:>12,.0f}")
print(f"  beneficios {ROT} (defasagem 5m):   {b26:>12,.0f}  cobertura {100*b26/ele:.1f}%  nao atendidas {ele-b26:>12,.0f}")

# --- 2. tarifa municipal em cada data ---
T = pd.read_csv(RAW+"/tarifas/2026-09-05/tarifas-homologadas-distribuidoras-energia-eletrica.csv",
                sep=";", encoding="utf-8", low_memory=False, dtype=str)
st = lambda c: T[c].astype(str).str.strip()
sel = ((st("DscSubGrupo")=="B1")&(st("DscBaseTarifaria")=="Tarifa de Aplicação")
       &(st("DscModalidadeTarifaria")=="Convencional")&(st("DscDetalhe")=="Não se aplica")
       &(st("DscSubClasse")=="Baixa Renda"))
b = T[sel].copy()
b["ini"]=pd.to_datetime(b.DatInicioVigencia,errors="coerce"); b["fim"]=pd.to_datetime(b.DatFimVigencia,errors="coerce")
b["tar"]=(num(b.VlrTUSD)+num(b.VlrTE))/1000.0; b["cnpj"]=pd.to_numeric(b.NumCNPJDistribuidora,errors="coerce")
G = pd.read_parquet(RAW+"/indger/2026-09-05/indger-dados-comerciais.parquet",
                    columns=["NumCNPJ","CodMunicipioIBGE","DatReferenciaInformada","QtdUCAtiva"])
G["dt"]=pd.to_datetime(G.DatReferenciaInformada,errors="coerce")
G["cnpj"]=pd.to_numeric(G.NumCNPJ,errors="coerce"); G["uc"]=pd.to_numeric(G.QtdUCAtiva,errors="coerce").fillna(0)
G["cod_ibge"]=pd.to_numeric(G.CodMunicipioIBGE,errors="coerce"); G=G.dropna(subset=["cod_ibge","cnpj"]); G["cod_ibge"]=G.cod_ibge.astype(int)
def tmun(ref, ano):
    v = b[(b.ini<=ref)&(b.fim>=ref)&(b.tar>0)].groupby("cnpj").tar.median().rename("t").reset_index()
    p = G[G.dt.dt.year==ano].groupby(["cod_ibge","cnpj"],as_index=False).uc.sum().merge(v,on="cnpj",how="left").dropna(subset=["t"])
    return p.groupby("cod_ibge").apply(lambda x: np.average(x.t,weights=x.uc) if x.uc.sum()>0 else x.t.mean(), include_groups=False).rename("tar").reset_index()
m = m.merge(tmun(pd.Timestamp("2024-12-01"),2024).rename(columns={"tar":"tar24"}), on="cod_ibge", how="left")
m = m.merge(tmun(REF,2026).rename(columns={"tar":"tar26"}), on="cod_ibge", how="left")

m["spb24"] = m.subs_liquido/m.beneficiarios_tsee.replace(0,np.nan)
m["spb26"] = m.subs26/m.ben26.replace(0,np.nan)
m["frac24"] = m.spb24/(m.tar24*80)
m["frac26"] = m.spb26/(m.tar26*80)
k = (m.frac24>0)&(m.frac26>0)&np.isfinite(m.frac24)&np.isfinite(m.frac26)
v = m[k]
print()
print(f"=== 2. FRACAO DA CONTA DE 80 kWh COBERTA ({len(v)} municipios) ===")
for c,rot in (("frac24","dez/2024"),("frac26",ROT)):
    s=v[c]; print(f"  {rot}: p25 {100*s.quantile(.25):5.1f}% | MED {100*s.median():5.1f}% | p75 {100*s.quantile(.75):5.1f}%")
g = v.frac26-v.frac24
print(f"  ganho: MED {100*g.median():+.1f} pp | municipios com ganho: {int((g>0).sum())} ({100*(g>0).mean():.1f}%)")
print(f"  reajuste tarifario por municipio: MED {(v.tar26/v.tar24).median():.3f}x | com queda: {int(((v.tar26/v.tar24)<1).sum())}")

# --- 3. delta por UF ---
print()
print("=== 3. POR UF ===")
u = m.groupby("uf").agg(ele=("familias_elegiveis","sum"), b24=("beneficiarios_tsee","sum"), b26=("ben26","sum")).reset_index()
u["cob24"]=100*u.b24/u.ele; u["cob26"]=100*u.b26/u.ele; u["dpp"]=u.cob26-u.cob24
u = u.sort_values("dpp", ascending=False)
print(u.assign(cob24=u.cob24.round(1), cob26=u.cob26.round(1), dpp=u.dpp.round(1))[["uf","cob24","cob26","dpp"]].to_string(index=False))
m.to_csv(str(OUT)+f"/nacional_{TAG}.csv", index=False)
