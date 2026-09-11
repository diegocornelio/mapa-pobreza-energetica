import pandas as pd, numpy as np, json, os
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import RAW, INTERIM_ORIG, PROCESSED_ORIG, OUT
geo = json.load(open(str(OUT)+"/geo.json", encoding="utf-8"))
ordem = geo["codes"]                          # ordem que os paths SVG esperam
p = pd.read_csv(str(OUT)+"/painel_municipal.csv").set_index("cod_ibge").reindex(ordem).reset_index()
print("municipios alinhados:", len(p), "| faltando:", int(p.nome.isna().sum()))

base = json.load(open(str(OUT)+"/dados.json", encoding="utf-8"))
assert base["codes" if "codes" in base else "cod"] == ordem or base["cod"] == ordem

def col(s, dec=None):
    if dec is None: return [None if pd.isna(x) else int(x) for x in s]
    return [None if pd.isna(x) else round(float(x), dec) for x in s]

# --- distribuidora: variacao nacional de cada agente ---
ag = pd.read_csv(str(OUT)+"/por_agente.csv", index_col=0)
ag["var"] = 100*(ag.mar26/ag.dez24.replace(0, np.nan) - 1)
ag = ag[ag.dez24 >= 1000].sort_values("dez24", ascending=False)
AG = [{"n": i, "b24": int(r.dez24), "b26": int(r.mar26), "v": round(float(r["var"]), 1)}
      for i, r in ag.iterrows() if np.isfinite(r["var"])]

# --- os municipios com 2+ distribuidoras ---
j = pd.read_csv(str(OUT)+"/mun_agente.csv")
j["var"] = 100*(j.b26/j.b24.replace(0, np.nan) - 1)
v = j[(j.b24 >= 100) & np.isfinite(j["var"])]
cnt = v.groupby("cod_ibge").agente.nunique()
multi = cnt[cnt >= 2].index
w = v[v.cod_ibge.isin(multi)].merge(p[["cod_ibge","nome","uf"]], on="cod_ibge", how="left")
PARES = []
for c, g in w.groupby("cod_ibge"):
    g = g.sort_values("var")
    PARES.append({"nome": g.nome.iloc[0], "uf": g.uf.iloc[0],
                  "d": [{"a": r.agente, "v": round(float(r["var"]),1), "n": int(r.b24)} for _, r in g.iterrows()]})
PARES.sort(key=lambda x: x["d"][-1]["v"] - x["d"][0]["v"], reverse=True)


# --- agregados nacionais: derivados, nunca escritos a mao ---------------------
# Estes numeros eram literais no codigo. Uma reexecucao que produzisse valores
# diferentes continuaria publicando os antigos, e a pagina exibiria cifra velha
# afirmando ser calculada. docs/VALIDACAO.md promete o contrario, entao a
# promessa passou a valer aqui.

# O fluxo do CadUnico vem do agregado nacional do SAGI, e nao da soma municipal:
# docs/VALIDACAO.md secao 5 registra a escolha (940.860 pelo agregado direto,
# contra 940.966 pela soma por municipio). O SAGI cobre 5.571 municipios, um a
# mais que a malha do Censo 2022: Boa Esperanca do Norte (MT, IBGE 5101837),
# instalado depois do Censo. A diferenca esta declarada em docs/LIMITES.md.
sg = pd.read_csv(str(OUT)+"/cadunico_mensal.csv")
def nac_sagi(anomes):
    g = sg[sg.anomes == anomes]
    assert len(g) and g.eleg.notna().any(), f"competencia {anomes} sem valor no SAGI"
    return {c: int(g[c].sum()) for c in ("cad", "pob", "bxr", "eleg")}
s24, s26 = nac_sagi(202412), nac_sagi(202603)
FLUXO = {"pob24": s24["pob"], "pob26": s26["pob"],
         "bxr24": s24["bxr"], "bxr26": s26["bxr"],
         "ele24": s24["eleg"], "ele26": s26["eleg"],
         "cad24": s24["cad"], "cad26": s26["cad"],
         "saiu_pob": s24["pob"] - s26["pob"]}

# Beneficios: soma municipal sobre a malha publicada.
B24, B26 = int(p.beneficiarios_tsee.sum()), int(p.ben26.sum())

# Decomposicao por grupo economico. Os dois grupos sao os que concentram a queda;
# o terceiro termo e o complemento, de modo que a soma das tres partes fecha com
# a variacao por agente. O residuo contra a soma municipal vem de codigos da CDE
# fora da malha do IBGE de 2022, e esta declarado em docs/LIMITES.md.
ENEL = ["ELETROPAULO", "ENEL RJ", "ENEL CE"]
EDP  = ["EDP ES", "EDP SP"]
agf = pd.read_csv(str(OUT)+"/por_agente.csv", index_col=0)
agf["d"] = agf.mar26 - agf.dez24
V_ENEL = int(agf.loc[agf.index.isin(ENEL), "d"].sum())
V_EDP  = int(agf.loc[agf.index.isin(EDP),  "d"].sum())
V_RESTO = int(agf.loc[~agf.index.isin(ENEL + EDP), "d"].sum())

# Fracao da conta coberta: so entram os municipios com subsidio positivo nas DUAS
# datas. Onde a CDE ficou liquida negativa o valor nao e utilizavel, e misturar as
# duas populacoes moveria a mediana. O mesmo filtro esta no agregado COB do app.
k = p.frac24.notna() & p.frac26.notna() & (p.frac24 > 0) & (p.frac26 > 0)
f24, f26 = p.loc[k, "frac24"], p.loc[k, "frac26"]
GANHO = int((f26 > f24).sum())
NAC = {"b24": B24, "b26": B26,
       "enel": V_ENEL, "edp": V_EDP, "resto": V_RESTO,
       "fr24": round(float(f24.median()), 5), "fr26": round(float(f26.median()), 5),
       "ganho": GANHO, "ganho_n": int(k.sum()),
       "ganho_pct": round(100 * GANHO / int(k.sum()), 2),
       "mun2dist": len(PARES),
       "mun2dist_opostos": int(sum(1 for x in PARES if x["d"][0]["v"] < 0 < x["d"][-1]["v"]))}

print("=== agregados nacionais derivados ===")
print(f"  beneficios      {B24:>12,} -> {B26:>12,}   ({B26-B24:+,})")
print(f"  Enel/EDP/demais {V_ENEL:+,} / {V_EDP:+,} / {V_RESTO:+,}  soma {V_ENEL+V_EDP+V_RESTO:+,}")
print(f"  CadUnico pobreza{s24['pob']:>12,} -> {s26['pob']:>12,}   sairam {FLUXO['saiu_pob']:+,}")
print(f"  elegiveis       {s24['eleg']:>12,} -> {s26['eleg']:>12,}   ({100*(s26['eleg']/s24['eleg']-1):+.2f}%)")
print(f"  fracao coberta  {100*NAC['fr24']:.2f}% -> {100*NAC['fr26']:.2f}%  ganho em {GANHO} de {int(k.sum())} ({NAC['ganho_pct']}%)")

novo = {
  "cob24": col(p.cob_2412,1), "cob26": col(p.cob_2603,1), "dcob": col(p.d_cob,1),
  "ben24": col(p.beneficiarios_tsee), "ben26": col(p.ben26),
  "pob24": col(p.pob_2412), "pob26": col(p.pob_2603),
  "bxr24": col(p.bxr_2412), "bxr26": col(p.bxr_2603),
  "ele24": col(p.eleg_2412), "ele26": col(p.eleg_2603),
  "frac24": col(p.frac24,5), "frac26": col(p.frac26,5),
  "na26": col(p.nao_atend_2603),
  "agvar": AG, "pares": PARES,
  "fluxo": FLUXO,
  "nac": NAC
}
base.update(novo)
open(str(OUT)+"/dados.json","w",encoding="utf-8").write(json.dumps(base, separators=(",",":"), ensure_ascii=False))
print("dados.json: %.2f MB" % (os.path.getsize(str(OUT)+"/dados.json")/1e6))
print("distribuidoras no payload:", len(AG), "| municipios com 2+ concessionarias:", len(PARES),
      "| com sinais opostos:", novo["nac"]["mun2dist_opostos"])
