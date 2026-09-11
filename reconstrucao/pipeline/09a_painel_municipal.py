import pandas as pd, numpy as np
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import RAW, INTERIM_ORIG, PROCESSED_ORIG, OUT
t = pd.read_csv(str(OUT)+"/cadunico_sagi.csv"); t["ibge6"]=pd.to_numeric(t.codigo_ibge,errors="coerce")
R = {"cadun_qtd_familias_cadastradas_i":"cad","cadun_qtd_familias_cadastradas_pobreza_pbf_i":"pob",
     "cadun_qtd_familias_cadastradas_baixa_renda_i":"bxr","cadun_qtd_familias_cadastradas_rfpc_ate_meio_sm_i":"eleg"}
w = {}
for am in (202412, 202603):
    x = t[t.anomes==am].rename(columns=R).set_index("ibge6")[list(R.values())]
    w[am] = x.add_suffix(f"_{str(am)[2:]}")
c = w[202412].join(w[202603], how="inner").reset_index()

d = pd.read_csv(str(OUT)+"/nacional_2026_03.csv")
d["ibge6"] = d.cod_ibge // 10
m = d.merge(c, on="ibge6", how="left")

# cobertura com denominador de cada data
m["cob_2412"] = 100*m.beneficiarios_tsee/m.eleg_2412.replace(0,np.nan)
m["cob_2603"] = 100*m.ben26/m.eleg_2603.replace(0,np.nan)
m["d_cob"] = m.cob_2603 - m.cob_2412
m["d_ben"] = m.ben26 - m.beneficiarios_tsee
m["saiu_pobreza"] = m.pob_2412 - m.pob_2603         # >0 = familias sairam da faixa de pobreza
m["d_eleg"] = m.eleg_2603 - m.eleg_2412
m["nao_atend_2603"] = (m.eleg_2603 - m.ben26).clip(lower=0)

def rot(r):
    if pd.isna(r.d_cob): return "sem dado"
    if r.d_cob <= -5: return "caiu muito"
    if r.d_cob < -1:  return "caiu"
    if r.d_cob <= 1:  return "estavel"
    if r.d_cob < 5:   return "subiu"
    return "subiu muito"
m["status_cob"] = m.apply(rot, axis=1)

print("=== COBERTURA: o que aconteceu em cada municipio ===")
print(m.status_cob.value_counts().reindex(["caiu muito","caiu","estavel","subiu","subiu muito","sem dado"]).to_string())
print(f"\n  delta de cobertura: p10 {m.d_cob.quantile(.10):+.1f} | MED {m.d_cob.median():+.1f} | p90 {m.d_cob.quantile(.90):+.1f} pp")
print(f"  municipios com queda: {int((m.d_cob<0).sum())} ({100*(m.d_cob<0).mean():.1f}%)")
print()
print("=== FAMILIAS QUE SAIRAM DA FAIXA DE POBREZA (dez/2024 -> mar/2026) ===")
print(f"  nacional: {m.saiu_pobreza.sum():,.0f}")
print(f"  municipios com saida liquida: {int((m.saiu_pobreza>0).sum())} ({100*(m.saiu_pobreza>0).mean():.1f}%)")
print(f"  por municipio: p10 {m.saiu_pobreza.quantile(.10):+,.0f} | MED {m.saiu_pobreza.median():+,.0f} | p90 {m.saiu_pobreza.quantile(.90):+,.0f}")
print(f"  variacao do universo ELEGIVEL: nacional {m.d_eleg.sum():+,.0f} | municipios com queda {int((m.d_eleg<0).sum())}")
print()
print("=== a saida da pobreza explica a queda de cobertura? ===")
k = m.d_cob.notna() & m.saiu_pobreza.notna() & (m.eleg_2412>500)
print(f"  spearman(saiu_pobreza_relativo, d_cob) = {(m.loc[k,'saiu_pobreza']/m.loc[k,'eleg_2412']).rank().corr(m.loc[k,'d_cob'].rank()):+.4f}  n={int(k.sum())}")
print(f"  spearman(d_eleg_relativo,       d_cob) = {(m.loc[k,'d_eleg']/m.loc[k,'eleg_2412']).rank().corr(m.loc[k,'d_cob'].rank()):+.4f}")
m.to_csv(str(OUT)+"/painel_municipal.csv", index=False)
print("\n  -> painel_municipal.csv gravado com", len(m), "municipios")
