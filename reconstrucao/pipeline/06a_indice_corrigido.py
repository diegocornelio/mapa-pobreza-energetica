import pandas as pd, numpy as np
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import RAW, INTERIM_ORIG, PROCESSED_ORIG, OUT
T=str(OUT)
df=pd.read_csv(str(PROCESSED_ORIG))
tar=pd.read_csv(T+"/tarifa_municipal.csv"); d3=pd.read_csv(T+"/d3_pond.csv").rename(columns={"d3_pond":"d3_corr","dec_h_pond":"dec_h_ano"}); d4=pd.read_csv(T+"/d4_corrigido.csv")
df=df.merge(tar[["cod_ibge","tarifa_municipal"]],on="cod_ibge",how="left")
df=df.merge(d3[["cod_ibge","d3_corr","dec_h_ano","d3_max","n_conj"]],on="cod_ibge",how="left")
df=df.merge(d4[["cod_ibge","dom_total_mun","d4_corr","favela_mapeada"]],on="cod_ibge",how="left")
df["d2_corr"]=(df.tarifa_municipal*100)/df.renda_referencia
def wmm(s,q=0.99):
    s=s.astype(float); s=s.clip(upper=s.quantile(q)); sp=s.max()-s.min()
    return pd.Series(np.nan,index=s.index) if (pd.isna(sp) or sp==0) else (s-s.min())/sp
D=["d1_lacuna_tsee","d2_corr","d3_corr","d4_corr"]
for c in D: df["n_"+c]=100*wmm(df[c])
nc=["n_"+c for c in D]
df["n_dim_validas"]=df[nc].notna().sum(axis=1)
df["ipem_v2"]=np.where(df.n_dim_validas==4, df[nc].mean(axis=1), np.nan)
print("=== IPEM v2 (4 dimensoes corrigidas) ===")
print("municipios com 4 dimensoes:", int((df.n_dim_validas==4).sum()), "de", len(df))
print("faltantes por dimensao:", {c:int(df["n_"+c].isna().sum()) for c in D})
df["rk_old"]=df.ipem.rank(ascending=False,method="min"); df["rk_new"]=df.ipem_v2.rank(ascending=False,method="min")
v=df.dropna(subset=["ipem_v2"])
print("\ndeslocamento mediano:", int((v.rk_old-v.rk_new).abs().median()))
a=set(df.nsmallest(100,"rk_old").cod_ibge); b=set(df.nsmallest(100,"rk_new").cod_ibge)
print("sobreposicao top-100:", len(a&b), "/100")
print("spearman antigo x v2: %.4f" % v.ipem.rank().corr(v.ipem_v2.rank()))
print("\n--- correlacao de cada dimensao com o indice (rank) ---")
for c in D: print("  %-10s %+.4f" % (c, v[c].rank().corr(v.ipem_v2.rank())))
print("\n--- TOP 20 IPEM v2 ---")
cols=["nome_uf","ipem_v2","rk_new","rk_old","d1_lacuna_tsee","tarifa_municipal","d2_corr","dec_h_ano","d3_corr","d4_corr"]
print(df.nsmallest(20,"rk_new")[cols].round(3).to_string(index=False))
df.to_csv(T+"/ipem_v2.csv",index=False)
