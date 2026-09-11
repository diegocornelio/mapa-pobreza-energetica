import pandas as pd, zipfile, sys
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import RAW, INTERIM_ORIG, PROCESSED_ORIG, OUT
def agg(Z, tag):
    z=zipfile.ZipFile(Z); n=z.infolist()[0].filename; acc={}
    with z.open(n) as fh:
        for ch in pd.read_csv(fh, chunksize=2_500_000, encoding="latin-1",
                usecols=["SigAgente","CodIbgeMunicipio","DscTipoSubsidio"], dtype=str, low_memory=False):
            c=ch[ch.DscTipoSubsidio.astype(str).str.strip()=="SubsBaixaRenda"]
            if not len(c): continue
            c=c.assign(ag=c.SigAgente.astype(str).str.strip(),
                       m=pd.to_numeric(c.CodIbgeMunicipio,errors="coerce")).dropna(subset=["m"])
            for (mm,a),v in c.groupby(["m","ag"]).size().items():
                acc[(int(mm),a)]=acc.get((int(mm),a),0)+v
    df=pd.DataFrame([{"cod_ibge":k[0],"agente":k[1],tag:v} for k,v in acc.items()])
    print(f"{tag}: {len(df):,} pares municipio-agente", flush=True)
    return df
a=agg(str(RAW)+"/aneel/cde/2026-09-05/cde-beneficiarios-01dec2024.zip","b24")
b=agg(str(RAW)+"/aneel/cde/2026-09-05/cde-beneficiarios-01mar2026.zip","b26")
j=a.merge(b,on=["cod_ibge","agente"],how="outer").fillna(0)
j.to_csv(str(OUT)+"/mun_agente.csv",index=False)
print("pares totais:",len(j))
