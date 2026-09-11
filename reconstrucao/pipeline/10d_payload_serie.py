"""Serie mensal do CadUnico no payload do app, codificada em delta.

Duas competencias do SAGI retornam 5.571 documentos com todos os campos ausentes:
abril de 2025 e setembro de 2026. O numFound diz que estao completas; so a leitura
dos valores revela o vazio. Elas sao excluidas e a lacuna fica declarada em `falhas`,
para que o grafico interrompa a linha em vez de desenhar queda a zero.

A codificacao guarda o primeiro valor e depois a diferenca para o mes anterior.
Sobre 31 competencias e 5.570 municipios isso reduz o payload de 2,37 MB para
1,64 MB, e de 0,93 MB para 0,59 MB depois da compressao que o servidor aplica.
"""
import pandas as pd, numpy as np, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import RAW, INTERIM_ORIG, PROCESSED_ORIG, OUT

VAZIAS = {202504, 202609}          # competencias sem nenhum valor no indice misocial

t = pd.read_csv(str(OUT) + "/cadunico_mensal.csv")
D = json.load(open(str(OUT) + "/dados.json", encoding="utf-8"))
malha = [c // 10 for c in D["cod"]]                    # ibge7 do app -> ibge6 do SAGI

comp = sorted(int(c) for c in t.anomes.unique() if int(c) not in VAZIAS)
print(f"competencias no arquivo: {t.anomes.nunique()} | usaveis: {len(comp)} ({comp[0]} a {comp[-1]})")
print(f"excluidas por virem sem valor: {sorted(VAZIAS)}")

fora = sorted(set(t.ibge6.unique()) - set(malha))
if fora:
    g = t[(t.ibge6.isin(fora)) & (t.anomes == comp[-1])]
    print(f"municipios do SAGI fora da malha de 2022: {fora} "
          f"({int(g.eleg.sum())} familias elegiveis em {comp[-1]})")

def serie(campo):
    """Matriz municipio x competencia, na ordem do payload."""
    p = (t[~t.anomes.isin(VAZIAS)]
         .pivot(index="ibge6", columns="anomes", values=campo)
         .reindex(malha)[comp])
    return p.values

def delta(mat):
    """Primeiro valor absoluto, depois a diferenca para o mes anterior.
       None onde o municipio nao tem valor naquela competencia."""
    saida = []
    for linha in mat:
        seq, ant = [], None
        for x in linha:
            if pd.isna(x):
                seq.append(None)
                continue
            x = int(x)
            seq.append(x if ant is None else x - ant)
            ant = x
        saida.append(seq)
    return saida

serie_mensal = {
    "comp": comp,
    "falhas": sorted(VAZIAS),
    "pob": delta(serie("pob")),
    "bxr": delta(serie("bxr")),
    "eleg": delta(serie("eleg")),
}

D["serie"] = serie_mensal
texto = json.dumps(D, separators=(",", ":"), ensure_ascii=False)
open(str(OUT) + "/dados.json", "w", encoding="utf-8").write(texto)
print(f"\ndados.json: {os.path.getsize(str(OUT)+'/dados.json')/1e6:.2f} MB")

# conferencia: reconstruir o delta e comparar com o total conhecido
def reconstroi(seq):
    v, ac = [], None
    for x in seq:
        if x is None: v.append(None); continue
        ac = x if ac is None else ac + x
        v.append(ac)
    return v

k = comp.index(202412)
soma = sum(reconstroi(s)[k] or 0 for s in serie_mensal["pob"])
print(f"pobreza em dez/2024, reconstruida do delta: {soma:,.0f}")
print(f"  referencia de docs/VALIDACAO.md         : 20,298,905")
print(f"  {'confere' if soma == 20298905 else 'DIVERGE'}")
