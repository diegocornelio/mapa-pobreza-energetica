import pandas as pd, numpy as np
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import RAW, INTERIM_ORIG, PROCESSED_ORIG, OUT
B=str(RAW)+"/aneel"
num=lambda s: pd.to_numeric(s.astype(str).str.replace(".","",regex=False).str.replace(",",".",regex=False),errors="coerce")
T=pd.read_csv(B+"/tarifas/2026-09-05/tarifas-homologadas-distribuidoras-energia-eletrica.csv",sep=";",encoding="utf-8",low_memory=False,dtype=str)
st=lambda c: T[c].astype(str).str.strip()
base=(st("DscSubGrupo")=="B1")&(st("DscBaseTarifaria")=="Tarifa de Aplicação")&(st("DscModalidadeTarifaria")=="Convencional")&(st("DscDetalhe")=="Não se aplica")&(st("DscSubClasse")=="Baixa Renda")
b=T[base].copy(); b["ini"]=pd.to_datetime(b.DatInicioVigencia,errors="coerce"); b["fim"]=pd.to_datetime(b.DatFimVigencia,errors="coerce")
b["tar"]=(num(b.VlrTUSD)+num(b.VlrTE))/1000.0; b["cnpj"]=pd.to_numeric(b.NumCNPJDistribuidora,errors="coerce")
ref=pd.Timestamp("2024-12-01"); v=b[(b.ini<=ref)&(b.fim>=ref)&(b.tar>0)]
tb=v.groupby("cnpj").tar.median().rename("tarifa_br").reset_index()
g=pd.read_parquet(B+"/indger/2026-09-05/indger-dados-comerciais.parquet",columns=["NumCNPJ","CodMunicipioIBGE","DatReferenciaInformada","QtdUCAtiva"])
g["dt"]=pd.to_datetime(g.DatReferenciaInformada,errors="coerce"); g=g[g.dt.dt.year==2024]
g["cnpj"]=pd.to_numeric(g.NumCNPJ,errors="coerce"); g["uc"]=pd.to_numeric(g.QtdUCAtiva,errors="coerce").fillna(0)
g["cod_ibge"]=pd.to_numeric(g.CodMunicipioIBGE,errors="coerce"); g=g.dropna(subset=["cod_ibge","cnpj"]); g["cod_ibge"]=g.cod_ibge.astype(int)
par=g.groupby(["cod_ibge","cnpj"],as_index=False).uc.sum().merge(tb,on="cnpj",how="left").dropna(subset=["tarifa_br"])
mb=par.groupby("cod_ibge").apply(lambda x: np.average(x.tarifa_br,weights=x.uc) if x.uc.sum()>0 else x.tarifa_br.mean(),include_groups=False).rename("tarifa_baixa_renda").reset_index()
df=pd.read_csv("ipem_v3.csv").merge(mb,on="cod_ibge",how="left")
print("municipios com tarifa Baixa Renda:",df.tarifa_baixa_renda.notna().sum())
SM=1412.0; TETO_BR=SM/2; TETO_POB=218.0
df["renda_dom_teto_br"]=TETO_BR*df.moradores_por_domicilio
df["renda_dom_teto_pob"]=TETO_POB*df.moradores_por_domicilio
df["peso_br_cheia"]=(df.tarifa_municipal*100)/df.renda_dom_teto_br
df["peso_br_social"]=(df.tarifa_baixa_renda*100)/df.renda_dom_teto_br
df["peso_pob_cheia"]=(df.tarifa_municipal*100)/df.renda_dom_teto_pob
df["peso_pob_social"]=(df.tarifa_baixa_renda*100)/df.renda_dom_teto_pob
print("\n=== PESO DA CONTA DE 100 kWh SOBRE A RENDA DO DOMICILIO ===")
print("(teto da faixa CadUnico x tamanho medio do domicilio do municipio; tarifa sem tributos)")
for c,nm in [("peso_br_cheia","faixa BAIXA RENDA, tarifa cheia"),("peso_br_social","faixa BAIXA RENDA, tarifa social"),
             ("peso_pob_cheia","faixa POBREZA, tarifa cheia"),("peso_pob_social","faixa POBREZA, tarifa social")]:
    s=df[c].dropna(); print(f"  {nm:36s} MED={s.median()*100:6.2f}%  p90={s.quantile(.9)*100:6.2f}%  max={s.max()*100:6.2f}%  >10%%: {int((s>0.10).sum())}")
df.to_csv("ipem_v4.csv",index=False)
print("\n=== D1 x D3 CORRIGIDO: sao as mesmas cidades? ===")
w=df.dropna(subset=["d3_corr"])
q1=w.d1_lacuna_tsee.quantile(.75); q3=w.d3_corr.quantile(.75)
dup=w[(w.d1_lacuna_tsee>=q1)&(w.d3_corr>=q3)]
print(f"  no pior quartil de D1 E de D3: {len(dup)} | esperado se independentes: {0.0625*len(w):.0f} | razao {len(dup)/(0.0625*len(w)):.2f}x")
print("  spearman(D1, D3 corrigido) = %.4f" % w.d1_lacuna_tsee.rank().corr(w.d3_corr.rank()))
viol=w.d3_corr>=1
print(f"  municipios em VIOLACAO do limite: {int(viol.sum())} | destes, no pior quartil de lacuna TSEE: {int((viol&(w.d1_lacuna_tsee>=q1)).sum())}")
