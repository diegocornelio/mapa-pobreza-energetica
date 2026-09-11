import pandas as pd, numpy as np, json, os
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import RAW, INTERIM_ORIG, PROCESSED_ORIG, OUT
geo = json.load(open(str(OUT)+"/geo.json", encoding="utf-8")); ordem = geo["codes"]
base = json.load(open(str(OUT)+"/dados.json", encoding="utf-8"))

a = pd.read_csv(str(OUT)+"/decfec_2024_2025.csv").set_index("cod_ibge").reindex(ordem).reset_index()
s = pd.read_csv(str(OUT)+"/dec_semestre.csv").set_index("cod_ibge").reindex(ordem).reset_index()

def col(x, dec=None):
    if dec is None: return [None if pd.isna(v) else int(v) for v in x]
    return [None if pd.isna(v) else round(float(v), dec) for v in x]

# situacao 2024/2025: 0 sempre dentro, 1 deixou de passar, 2 passou a ficar acima, 3 reincidente
sit = np.select(
    [a.viol24.eq(1) & a.viol25.eq(1), a.viol24.eq(1) & a.viol25.eq(0),
     a.viol24.eq(0) & a.viol25.eq(1), a.viol24.eq(0) & a.viol25.eq(0)],
    [3, 1, 2, 0], default=np.nan)

base.update({
  "rel24": col(a.rel2024,3), "rel25": col(a.rel2025,3),
  "h24": col(a.dec2024,1), "h25": col(a.dec2025,1),
  "sit": [None if pd.isna(v) else int(v) for v in sit],
  "s24": col(s.s2024,2), "s25": col(s.s2025,2), "s26": col(s.s2026,2),
  "cont": {
    "viol24": int(a.viol24.sum()), "viol25": int(a.viol25.sum()), "n": int(a.viol24.notna().sum()),
    "reinc": int(((a.viol24==1)&(a.viol25==1)).sum()),
    "saiu":  int(((a.viol24==1)&(a.viol25==0)).sum()),
    "entrou":int(((a.viol24==0)&(a.viol25==1)).sum()),
    "limpo": int(((a.viol24==0)&(a.viol25==0)).sum()),
    "h24": round(float(a.dec2024.median()),2), "h25": round(float(a.dec2025.median()),2)},
  "tend": {
    "conj": 2995, "n": int(s.s2024.notna().sum()),
    "p24": 5.16, "p25": 4.63, "p26": 4.36,
    "m24": round(float(s.s2024.median()),2), "m25": round(float(s.s2025.median()),2), "m26": round(float(s.s2026.median()),2),
    "melhorou": int((s.s2026 < s.s2024*0.95).sum()),
    "piorou":   int((s.s2026 > s.s2024*1.05).sum()),
    "estavel":  int(((s.s2026 >= s.s2024*0.95) & (s.s2026 <= s.s2024*1.05)).sum())}
})
open(str(OUT)+"/dados.json","w",encoding="utf-8").write(json.dumps(base, separators=(",",":"), ensure_ascii=False))
print("dados.json: %.2f MB" % (os.path.getsize(str(OUT)+"/dados.json")/1e6))
print("situacao 2024/2025:", {k:int(v) for k,v in pd.Series(sit).value_counts().sort_index().items()},
      " (0=sempre dentro, 1=deixou de passar, 2=passou a ficar acima, 3=reincidente)")
print("tendencia:", base["tend"]["melhorou"], "melhorou |", base["tend"]["estavel"], "estavel |", base["tend"]["piorou"], "piorou")
