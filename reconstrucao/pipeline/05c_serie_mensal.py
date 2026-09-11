"""Serie mensal do CadUnico por municipio, via API do SAGI.

O 05b busca tres competencias para a comparacao entre duas datas. Este script
busca a serie inteira, mes a mes, que e o que sustenta o grafico temporal do
painel municipal.

A cobertura foi conferida antes de escrever o script: toda competencia de
jan/2024 a set/2026 retorna 5.571 municipios. O codigo do SAGI tem seis digitos,
sem digito verificador, e a juncao com a malha do IBGE exige esse ajuste.
"""
import urllib.request, json, ssl, pandas as pd, time, sys
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import RAW, INTERIM_ORIG, PROCESSED_ORIG, OUT

ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
B = "https://aplicacoes.mds.gov.br/sagi/servicos/misocial"
F = ["codigo_ibge", "anomes",
     "cadun_qtd_familias_cadastradas_i",
     "cadun_qtd_familias_cadastradas_pobreza_pbf_i",
     "cadun_qtd_familias_cadastradas_baixa_renda_i",
     "cadun_qtd_familias_cadastradas_rfpc_ate_meio_sm_i"]

def competencias(ini=(2024, 1), fim=(2026, 9)):
    a, m = ini
    while (a, m) <= fim:
        yield f"{a}{m:02d}"
        m += 1
        if m == 13: a, m = a + 1, 1

def puxa(anomes):
    docs, start = [], 0
    while True:
        u = f"{B}?q=anomes:{anomes}&rows=2000&start={start}&wt=json&fl={','.join(F)}"
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
        d = json.loads(urllib.request.urlopen(req, timeout=120, context=ctx).read().decode("utf-8"))
        got = d["response"]["docs"]; docs += got
        start += len(got)
        if start >= d["response"]["numFound"] or not got: break
        time.sleep(0.2)
    df = pd.DataFrame(docs)
    df["ibge6"] = pd.to_numeric(df.codigo_ibge, errors="coerce")
    for c in F[2:]: df[c] = pd.to_numeric(df.get(c), errors="coerce")
    return df

todos = []
for am in competencias():
    for tentativa in range(3):
        try:
            df = puxa(am); break
        except Exception as e:
            if tentativa == 2:
                print(f"  {am}: FALHOU apos 3 tentativas ({type(e).__name__})", flush=True)
                df = None
            else:
                time.sleep(3)
    if df is None: continue
    todos.append(df)
    print(f"  {am}: {len(df)} municipios", flush=True)

t = pd.concat(todos, ignore_index=True)
t = t.rename(columns={
    "cadun_qtd_familias_cadastradas_i": "cad",
    "cadun_qtd_familias_cadastradas_pobreza_pbf_i": "pob",
    "cadun_qtd_familias_cadastradas_baixa_renda_i": "bxr",
    "cadun_qtd_familias_cadastradas_rfpc_ate_meio_sm_i": "eleg"})
t = t[["ibge6", "anomes", "cad", "pob", "bxr", "eleg"]].dropna(subset=["ibge6"])
t["ibge6"] = t.ibge6.astype(int)
t.to_csv(str(OUT) + "/cadunico_mensal.csv", index=False)

print()
print(f"=== SERIE MENSAL: {t.anomes.nunique()} competencias, {t.ibge6.nunique()} municipios ===")
n = t.groupby("anomes")[["pob", "bxr", "eleg"]].sum()
print(n.assign(pob=lambda x: (x.pob / 1e6).round(2), bxr=lambda x: (x.bxr / 1e6).round(2),
               eleg=lambda x: (x.eleg / 1e6).round(2)).to_string())
print()
print("valores em milhoes de familias. eleg = renda familiar per capita ate meio salario minimo.")
