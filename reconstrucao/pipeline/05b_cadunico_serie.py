import urllib.request, json, ssl, pandas as pd, time
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import RAW, INTERIM_ORIG, PROCESSED_ORIG, OUT
ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
B = "https://aplicacoes.mds.gov.br/sagi/servicos/misocial"
F = ["codigo_ibge","anomes","cadun_qtd_familias_cadastradas_i",
     "cadun_qtd_familias_cadastradas_pobreza_pbf_i","cadun_qtd_familias_cadastradas_baixa_renda_i",
     "cadun_qtd_familias_cadastradas_rfpc_ate_meio_sm_i","cadun_qtd_familias_cadastradas_rfpc_acima_meio_sm_i"]
def puxa(anomes):
    docs, start = [], 0
    while True:
        u = f"{B}?q=anomes:{anomes}&rows=2000&start={start}&wt=json&fl={','.join(F)}"
        req = urllib.request.Request(u, headers={"User-Agent":"Mozilla/5.0"})
        d = json.loads(urllib.request.urlopen(req, timeout=120, context=ctx).read().decode("utf-8"))
        got = d["response"]["docs"]; docs += got
        start += len(got)
        if start >= d["response"]["numFound"] or not got: break
        time.sleep(0.3)
    df = pd.DataFrame(docs)
    df["cod_ibge"] = pd.to_numeric(df.codigo_ibge, errors="coerce")
    for c in F[2:]: df[c] = pd.to_numeric(df.get(c), errors="coerce")
    print(f"  {anomes}: {len(df)} municipios", flush=True)
    return df
todos = []
for am in ("202412","202603","202608"):
    todos.append(puxa(am))
t = pd.concat(todos)
t.to_csv(str(OUT)+"/cadunico_sagi.csv", index=False)
print()
print("=== NACIONAL: familias ate 1/2 SM per capita (criterio TSEE) ===")
for am, g in t.groupby("anomes"):
    print(f"  {am}: ate_meio_sm {g.cadun_qtd_familias_cadastradas_rfpc_ate_meio_sm_i.sum():>12,.0f}"
          f" | pobreza {g.cadun_qtd_familias_cadastradas_pobreza_pbf_i.sum():>12,.0f}"
          f" | baixa_renda {g.cadun_qtd_familias_cadastradas_baixa_renda_i.sum():>11,.0f}"
          f" | total {g.cadun_qtd_familias_cadastradas_i.sum():>12,.0f}")
