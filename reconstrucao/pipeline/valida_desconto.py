import pandas as pd, numpy as np
d=pd.read_csv("app_dados2.csv")
d=d[d.subsidio_indisponivel==0].copy()
print("municipios com subsidio observado utilizavel:",len(d))
# desconto em R$ por kWh consumido, segundo a regra, para um consumo k
def desconto_rs(tar_br,k):
    d1=min(k,30)*0.65
    d2=max(0,min(k,100)-30)*0.40
    d3=max(0,min(k,220)-100)*0.10
    return tar_br*(d1+d2+d3)
# inverter: qual k reproduz o subsidio observado?
def implied_k(sub,tar_br):
    lo,hi=1.0,400.0
    if desconto_rs(tar_br,hi)<sub: return np.nan
    if desconto_rs(tar_br,lo)>sub: return np.nan
    for _ in range(60):
        mid=(lo+hi)/2
        if desconto_rs(tar_br,mid)<sub: lo=mid
        else: hi=mid
    return (lo+hi)/2
d["k_implicito"]=[implied_k(s,t) for s,t in zip(d.subsidio_familia_liq,d.tarifa_baixa_renda)]
k=d.k_implicito.dropna()
print()
print("=== TESTE 1: consumo implicito pela regra ===")
print(f"  n={len(k)} de {len(d)}  |  fora do intervalo resolvivel: {d.k_implicito.isna().sum()}")
print(f"  p05={k.quantile(.05):6.1f}  p25={k.quantile(.25):6.1f}  MEDIANA={k.median():6.1f}  p75={k.quantile(.75):6.1f}  p95={k.quantile(.95):6.1f} kWh")
print(f"  fracao entre 40 e 150 kWh: {100*((k>=40)&(k<=150)).mean():.1f}%")
print()
print("=== TESTE 2: o subsidio observado escala com a tarifa? ===")
print("   (se a regra estiver certa, subsidio/tarifa deve ser aprox. constante = kWh descontados)")
r=d.subsidio_familia_liq/d.tarifa_baixa_renda
print(f"  razao: p25={r.quantile(.25):.1f}  MEDIANA={r.median():.1f}  p75={r.quantile(.75):.1f}  CV={r.std()/r.mean():.3f}")
r2=d.subsidio_familia_liq
print(f"  para comparar, CV do subsidio bruto: {r2.std()/r2.mean():.3f}")
print(f"  spearman(subsidio_por_familia, tarifa_baixa_renda) = {d.subsidio_familia_liq.rank().corr(d.tarifa_baixa_renda.rank()):+.4f}")
