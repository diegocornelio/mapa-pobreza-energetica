import pandas as pd, numpy as np
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import RAW, INTERIM_ORIG, PROCESSED_ORIG, OUT
B=str(RAW)+"/aneel"
num = lambda s: pd.to_numeric(s.astype(str).str.replace(".","",regex=False).str.replace(",",".",regex=False), errors="coerce")
T = pd.read_csv(B+"/tarifas/2026-09-05/tarifas-homologadas-distribuidoras-energia-eletrica.csv", sep=";", encoding="utf-8", low_memory=False, dtype=str)
st = lambda c: T[c].astype(str).str.strip()
sel = (st("DscSubGrupo")=="B1") & (st("DscModalidadeTarifaria")=="Convencional") & (st("DscClasse")=="Residencial") \
      & (st("DscSubClasse")=="Residencial") & (st("DscBaseTarifaria")=="Tarifa de Aplicação") & (st("DscDetalhe")=="Não se aplica")
b=T[sel].copy(); b["ini"]=pd.to_datetime(b.DatInicioVigencia,errors="coerce"); b["fim"]=pd.to_datetime(b.DatFimVigencia,errors="coerce")
b["tar"]=(num(b.VlrTUSD)+num(b.VlrTE))/1000.0
ref=pd.Timestamp("2024-12-01"); v=b[(b.ini<=ref)&(b.fim>=ref)&(b.tar>0)].copy()
v["cnpj"]=pd.to_numeric(v.NumCNPJDistribuidora, errors="coerce")
tc = v.dropna(subset=["cnpj"]).groupby("cnpj").tar.median().reset_index()
print("distribuidoras (CNPJ) com tarifa 2024-12:", len(tc))
g = pd.read_parquet(B+"/indger/2026-09-05/indger-dados-comerciais.parquet", columns=["NumCNPJ","SigAgente","CodMunicipioIBGE","DatReferenciaInformada","QtdUCAtiva"])
g["dt"]=pd.to_datetime(g.DatReferenciaInformada,errors="coerce"); g=g[g.dt.dt.year==2024]
g["cnpj"]=pd.to_numeric(g.NumCNPJ,errors="coerce"); g["uc"]=pd.to_numeric(g.QtdUCAtiva,errors="coerce").fillna(0)
g["cod_ibge"]=pd.to_numeric(g.CodMunicipioIBGE,errors="coerce")
g=g.dropna(subset=["cod_ibge","cnpj"]); g["cod_ibge"]=g.cod_ibge.astype(int)
par=g.groupby(["cod_ibge","cnpj"],as_index=False).uc.sum()
j=par.merge(tc,on="cnpj",how="left")
cob=j.groupby("cod_ibge").apply(lambda x: x.uc[x.tar.notna()].sum()/max(x.uc.sum(),1), include_groups=False).rename("cob")
print("municipios INDGER:", par.cod_ibge.nunique())
print("com >=90%% das UC casadas a uma tarifa:", (cob>=0.9).sum(), f"({100*(cob>=0.9).mean():.1f}%)")
jj=j.dropna(subset=["tar"])
wm=jj.groupby("cod_ibge").apply(lambda x: np.average(x.tar,weights=x.uc) if x.uc.sum()>0 else x.tar.mean(), include_groups=False).rename("tarifa_municipal").reset_index()
wm=wm.merge(cob.reset_index(),on="cod_ibge")
ok=wm[wm.cob>=0.9]
print("\n=== TARIFA MUNICIPAL (ponderada por UC, cobertura>=90%%) ===")
print("municipios:", len(ok))
print(f"min={ok.tarifa_municipal.min():.4f} p25={ok.tarifa_municipal.quantile(.25):.4f} MED={ok.tarifa_municipal.median():.4f} p75={ok.tarifa_municipal.quantile(.75):.4f} max={ok.tarifa_municipal.max():.4f}")
print(f"amplitude = {ok.tarifa_municipal.max()/ok.tarifa_municipal.min():.2f}x | constante do projeto = 0.695701")
wm.to_csv(str(OUT)+"/tarifa_municipal.csv", index=False)
