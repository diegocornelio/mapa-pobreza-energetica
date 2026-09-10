import pandas as pd, zipfile, numpy as np
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import RAW, INTERIM_ORIG, PROCESSED_ORIG, OUT
z=zipfile.ZipFile(str(RAW)+"/aneel/cde/2026-09-05/cde-beneficiarios-01dec2024.zip")
n=z.infolist()[0].filename
acc={}; ntot=0; tipos={}
with z.open(n) as fh:
    for ch in pd.read_csv(fh, chunksize=2_000_000, encoding="latin-1",
        usecols=["SigAgente","CodIbgeMunicipio","DscTipoSubsidio","VlrSubsidio"], dtype=str, low_memory=False):
        ntot+=len(ch)
        for k,v in ch.DscTipoSubsidio.value_counts().items(): tipos[k]=tipos.get(k,0)+v
        c=ch[ch.DscTipoSubsidio.astype(str).str.strip()=="SubsBaixaRenda"].copy()
        if not len(c): continue
        c["v"]=pd.to_numeric(c.VlrSubsidio.astype(str).str.replace(".","",regex=False).str.replace(",",".",regex=False),errors="coerce")
        c["m"]=pd.to_numeric(c.CodIbgeMunicipio,errors="coerce")
        c=c.dropna(subset=["m"]); c["m"]=c.m.astype(int)
        g=c.groupby("m").agg(linhas=("v","size"), pos=("v",lambda s:s[s>0].sum()), neg=("v",lambda s:s[s<0].sum()),
                             n_neg=("v",lambda s:(s<0).sum()), liq=("v","sum"))
        for m,r in g.iterrows():
            a=acc.setdefault(m,[0,0.0,0.0,0,0.0])
            a[0]+=r.linhas; a[1]+=r.pos; a[2]+=r.neg; a[3]+=r.n_neg; a[4]+=r.liq
        print("processadas", ntot, "linhas", flush=True)
df=pd.DataFrame([{"cod_ibge":k,"linhas_tsee":v[0],"subs_pos":v[1],"subs_neg":v[2],"n_negativos":v[3],"subs_liquido":v[4]} for k,v in acc.items()])
df.to_csv(str(OUT)+"/cde_municipal.csv",index=False)
print("\nTIPOS DE SUBSIDIO:", tipos)
print("municipios:",len(df),"| linhas TSEE:",int(df.linhas_tsee.sum()))
print("soma positiva: R$ %.2f" % df.subs_pos.sum())
print("soma negativa: R$ %.2f" % df.subs_neg.sum())
print("liquido      : R$ %.2f" % df.subs_liquido.sum())
print("municipios com algum negativo:", int((df.n_negativos>0).sum()))
print("municipios com liquido < 0:", int((df.subs_liquido<0).sum()))
