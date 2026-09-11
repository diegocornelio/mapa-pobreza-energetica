"""Procedencia do indicador de continuidade: o numero e do municipio ou do conjunto?

A ANEEL apura DEC e FEC por CONJUNTO CONSUMIDOR, e um conjunto atravessa varios
municipios. Onde um municipio e servido por um unico conjunto compartilhado, o
indicador municipal e o valor daquele conjunto replicado, sem nada de proprio do
municipio. A ficha municipal precisa dizer isso, em vez de exibir o numero como se
fosse medicao daquele lugar.

Este passo grava, por municipio:
  ncj   quantos conjuntos o atendem (com DEC apurado em 2024)
  nviz  quantos OUTROS municipios dividem ao menos um desses conjuntos
  excl  1 se todos os seus conjuntos sao exclusivos dele

A contagem usa a mesma juncao que produz d3 em 03b/03c: IndQual restrito aos
conjuntos que tem apuracao completa de doze meses em 2024.
"""
import pandas as pd, numpy as np, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import RAW, INTERIM_ORIG, PROCESSED_ORIG, OUT

B = str(RAW) + "/aneel"
m = pd.read_parquet(str(OUT) + "/decfec_conj_2024.parquet")
conj_ok = set(m.IdeConjUndConsumidoras.unique())
print(f"conjuntos com apuracao completa em 2024: {len(conj_ok)}")

q = pd.read_csv(B + "/indqual/2026-09-05/indqual-municipio.csv",
                sep=";", encoding="latin-1", low_memory=False)
q = q.rename(columns={"IdeConjUnidConsumidoras": "IdeConjUndConsumidoras",
                      "CodMunicipio": "cod_ibge"})[["IdeConjUndConsumidoras", "cod_ibge"]].drop_duplicates()
q = q[q.IdeConjUndConsumidoras.isin(conj_ok)]
q = q.dropna(subset=["cod_ibge"])
q["cod_ibge"] = pd.to_numeric(q.cod_ibge, errors="coerce")
q = q.dropna(subset=["cod_ibge"]); q["cod_ibge"] = q.cod_ibge.astype(int)
print(f"pares conjunto-municipio: {len(q)} | municipios: {q.cod_ibge.nunique()}")

por_mun = q.groupby("cod_ibge").IdeConjUndConsumidoras.apply(set).to_dict()
por_conj = q.groupby("IdeConjUndConsumidoras").cod_ibge.apply(set).to_dict()

D = json.load(open(str(OUT) + "/dados.json", encoding="utf-8"))
ncj, nviz, excl = [], [], []
for cod in D["cod"]:
    cs = por_mun.get(cod)
    if not cs:
        ncj.append(None); nviz.append(None); excl.append(None); continue
    vizinhos = set()
    for c in cs:
        vizinhos |= por_conj.get(c, set())
    vizinhos.discard(cod)
    ncj.append(len(cs))
    nviz.append(len(vizinhos))
    excl.append(1 if len(vizinhos) == 0 else 0)

D["ncj"], D["nviz"], D["excl"] = ncj, nviz, excl
open(str(OUT) + "/dados.json", "w", encoding="utf-8").write(
    json.dumps(D, separators=(",", ":"), ensure_ascii=False))

tem = [k for k, v in enumerate(ncj) if v is not None]
um = [k for k in tem if ncj[k] == 1]
exclusivos = [k for k in tem if excl[k] == 1]
print()
print("=== PROCEDENCIA DO INDICADOR DE CONTINUIDADE ===")
print(f"  municipios com apuracao            : {len(tem)}")
print(f"  atendidos por um unico conjunto    : {len(um)} ({100*len(um)/len(tem):.1f}%)")
print(f"  cujos conjuntos sao so deles       : {len(exclusivos)} ({100*len(exclusivos)/len(tem):.1f}%)")
print(f"  que dividem conjunto com outro     : {len(tem)-len(exclusivos)} ({100*(len(tem)-len(exclusivos))/len(tem):.1f}%)")
v = [nviz[k] for k in tem if nviz[k]]
if v:
    v.sort()
    print(f"  municipios coirmaos, mediana {v[len(v)//2]} | maximo {v[-1]}")
i = D["cod"].index(1300300) if 1300300 in D["cod"] else None
if i is not None:
    print(f"\n  Autazes: {ncj[i]} conjunto, dividido com {nviz[i]} outros municipios")
print(f"\ndados.json: {os.path.getsize(str(OUT)+'/dados.json')/1e6:.2f} MB")
