import pandas as pd, numpy as np
df=pd.read_csv("ipem_v4.csv")
cde=pd.read_csv("cde_municipal.csv")
df=df.merge(cde,on="cod_ibge",how="left")
df["subsidio_familia_liq"]=df.subs_liquido/df.linhas_tsee.replace(0,np.nan)
df["lacuna_pos"]=df.lacuna_bruta.clip(lower=0)
df["rs_nao_acessado"]=df.lacuna_pos*df.subsidio_familia_liq
df["cobertura"]=100*df.beneficiarios_tsee/df.familias_elegiveis
print("=== R$/familia com CDE LIQUIDA (sem clip) ===")
s=df.subsidio_familia_liq.dropna()
print(f"  min={s.min():.2f} MED={s.median():.2f} max={s.max():.2f} | negativos: {int((s<0).sum())} municipios")
print(f"  R$ nao acessado nacional: R$ {df.rs_nao_acessado.clip(lower=0).sum():,.0f}/mes")
print("\n=== CONCENTRACAO DENTRO DE CADA UF (o que um gestor estadual opera) ===")
out=[]
for uf,g in df.groupby("uf"):
    g=g.sort_values("lacuna_pos",ascending=False); tot=g.lacuna_pos.sum()
    if tot<=0: continue
    c=g.lacuna_pos.cumsum()/tot
    n50=int((c<0.5).sum())+1
    out.append({"uf":uf,"mun":len(g),"lacuna":int(tot),"mun_para_50pct":n50,"pct_dos_mun":round(100*n50/len(g),1)})
o=pd.DataFrame(out).sort_values("mun_para_50pct")
print(o.to_string(index=False))
df.to_csv("ipem_v5.csv",index=False)
