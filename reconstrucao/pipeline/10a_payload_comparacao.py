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

novo = {
  "cob24": col(p.cob_2412,1), "cob26": col(p.cob_2603,1), "dcob": col(p.d_cob,1),
  "ben24": col(p.beneficiarios_tsee), "ben26": col(p.ben26),
  "pob24": col(p.pob_2412), "pob26": col(p.pob_2603),
  "bxr24": col(p.bxr_2412), "bxr26": col(p.bxr_2603),
  "ele24": col(p.eleg_2412), "ele26": col(p.eleg_2603),
  "frac24": col(p.frac24,3), "frac26": col(p.frac26,3),
  "na26": col(p.nao_atend_2603),
  "agvar": AG, "pares": PARES,
  "fluxo": {"pob24": 20298905, "pob26": 19358045, "bxr24": 7584379, "bxr26": 8471663,
            "ele24": 27883284, "ele26": 27829708, "cad24": 41539082, "cad26": 42242445},
  "nac": {"b24": 17882926, "b26": 17403015,
          "enel": -736756, "edp": -68029, "resto": 325021,
          "fr24": 0.582, "fr26": 0.881, "ganho_pct": 99.7,
          "mun2dist": len(PARES), "mun2dist_opostos": int(sum(1 for x in PARES if x["d"][0]["v"] < 0 < x["d"][-1]["v"]))}
}
base.update(novo)
open(str(OUT)+"/dados.json","w",encoding="utf-8").write(json.dumps(base, separators=(",",":"), ensure_ascii=False))
print("dados.json: %.2f MB" % (os.path.getsize(str(OUT)+"/dados.json")/1e6))
print("distribuidoras no payload:", len(AG), "| municipios com 2+ concessionarias:", len(PARES),
      "| com sinais opostos:", novo["nac"]["mun2dist_opostos"])
