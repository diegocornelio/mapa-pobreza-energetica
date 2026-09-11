import pandas as pd, numpy as np
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import RAW, INTERIM_ORIG, PROCESSED_ORIG, OUT
B=str(RAW)+"/aneel"
df=pd.read_csv(str(OUT)+"/ipem_v5.csv")
g=pd.read_parquet(B+"/indger/2026-09-05/indger-dados-comerciais.parquet",columns=["SigAgente","NomAgente","CodMunicipioIBGE","DatReferenciaInformada","QtdUCAtiva"])
g["dt"]=pd.to_datetime(g.DatReferenciaInformada,errors="coerce"); g=g[g.dt.dt.year==2024]
g["uc"]=pd.to_numeric(g.QtdUCAtiva,errors="coerce").fillna(0)
g["cod_ibge"]=pd.to_numeric(g.CodMunicipioIBGE,errors="coerce"); g=g.dropna(subset=["cod_ibge"]); g["cod_ibge"]=g.cod_ibge.astype(int)
dom=g.groupby(["cod_ibge","NomAgente"],as_index=False).uc.sum().sort_values("uc",ascending=False).drop_duplicates("cod_ibge")
dom=dom.rename(columns={"NomAgente":"distribuidora"})[["cod_ibge","distribuidora"]]
dom["distribuidora"]=dom.distribuidora.astype(str).str.strip()
df=df.merge(dom,on="cod_ibge",how="left")
print("distribuidoras distintas:",df.distribuidora.nunique(),"| sem nome:",df.distribuidora.isna().sum())
df["peso_pob80_cheia"]=(df.tarifa_municipal*80)/df.renda_dom_teto_pob
df["peso_pob80_social"]=(df.tarifa_baixa_renda*80)/df.renda_dom_teto_pob
df["rank_tarifa"]=df.tarifa_municipal.rank(ascending=False,method="min").astype(int)
df["violacao"]=np.where(df.d3_corr.isna(),np.nan,(df.d3_corr>=1).astype(float))
# Sobrecobertura na MESMA base que produz a lacuna. Usar lacuna_bruta (dez/2024)
# aqui e lacuna_pos (mar/2026) ali faria a bandeira contradizer o contingente no
# mesmo municipio, sem erro nenhum na execucao.
df["sobrecobertura"]=(df.lacuna_bruta_casada<0).astype(int)
df["subsidio_indisponivel"]=(df.subs_mar26<=0).astype(int)
cols=["cod_ibge","nome","uf","distribuidora","familias_cadastradas","familias_pobreza","familias_baixa_renda",
  "familias_elegiveis","beneficiarios_tsee",
  "familias_elegiveis_mar26","beneficiarios_mar26","subsidio_familia_mar26","lacuna_bruta_casada",
  "cobertura","lacuna_pos","sobrecobertura","subs_liquido",
  "subsidio_familia_liq","rs_nao_acessado","subsidio_indisponivel","tarifa_municipal","tarifa_baixa_renda",
  "rank_tarifa","moradores_por_domicilio","peso_pob80_cheia","peso_pob80_social","dec_h_ano","d3_corr","d3_max",
  "n_conj","violacao","dom_favela","dom_total_mun","d4_corr","favela_mapeada","renda_referencia"]
out=df[cols].copy()
print("linhas:",len(out))
print(out.isna().sum()[out.isna().sum()>0].to_string())
out.to_csv(str(OUT)+"/app_dados.csv",index=False)
print("\nOK app_dados.csv")
