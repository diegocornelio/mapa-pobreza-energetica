import pandas as pd, zipfile, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import RAW, INTERIM_ORIG, PROCESSED_ORIG, OUT
Z   = sys.argv[1] if len(sys.argv) > 1 else str(RAW)+"/aneel/cde/2026-09-05/cde-beneficiarios-01mar2026.zip"
TAG = sys.argv[2] if len(sys.argv) > 2 else "2026_03"
if not os.path.exists(Z):
    # o arquivo e publico; busca no portal da ANEEL quando ausente
    import urllib.request, json, re
    print("baixando a CDE de 03/2026 do portal da ANEEL...", flush=True)
    cat = json.loads(urllib.request.urlopen(
        "https://dadosabertos.aneel.gov.br/api/3/action/package_show?id=beneficiarios-da-cde",
        timeout=90).read().decode("utf-8"))
    alvo = os.path.basename(Z)
    url = next(x["url"] for x in cat["result"]["resources"] if x.get("name") == alvo)
    os.makedirs(os.path.dirname(Z), exist_ok=True)
    urllib.request.urlretrieve(url, Z)
    print("  %.0f MB" % (os.path.getsize(Z)/1e6), flush=True)

z = zipfile.ZipFile(Z); nome = z.infolist()[0].filename
print(f"{TAG}: {nome} ({z.infolist()[0].file_size/1e9:.2f} GB)", flush=True)
acc, ntot, ref = {}, 0, set()
with z.open(nome) as fh:
    for ch in pd.read_csv(fh, chunksize=2_000_000, encoding="latin-1",
            usecols=["CodIbgeMunicipio","AnmReferencia","DscTipoSubsidio","VlrSubsidio"],
            dtype=str, low_memory=False):
        ntot += len(ch); ref |= set(ch.AnmReferencia.dropna().unique())
        c = ch[ch.DscTipoSubsidio.astype(str).str.strip()=="SubsBaixaRenda"].copy()
        if not len(c): continue
        c["v"]=pd.to_numeric(c.VlrSubsidio.astype(str).str.replace(".","",regex=False).str.replace(",",".",regex=False),errors="coerce")
        c["m"]=pd.to_numeric(c.CodIbgeMunicipio,errors="coerce")
        c=c.dropna(subset=["m"]); c["m"]=c.m.astype(int)
        g=c.groupby("m").agg(linhas=("v","size"), liq=("v","sum"))
        for mm,r in g.iterrows():
            a=acc.setdefault(mm,[0,0.0]); a[0]+=r.linhas; a[1]+=r.liq
        print(f"  {ntot:,}", flush=True)
df = pd.DataFrame([{"cod_ibge":k, f"ben_{TAG}":v[0], f"subs_{TAG}":v[1]} for k,v in acc.items()])
df.to_csv(str(OUT)+f"/cde_municipal_{TAG}.csv", index=False)
print(f"\nAnmReferencia: {sorted(ref)}")
print(f"municipios: {len(df)} | linhas: {int(df[f'ben_{TAG}'].sum()):,} | subsidio: R$ {df[f'subs_{TAG}'].sum():,.2f}")
