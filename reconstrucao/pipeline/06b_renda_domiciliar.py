import pandas as pd, numpy as np
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import RAW, INTERIM_ORIG, PROCESSED_ORIG, OUT
df=pd.read_csv(str(OUT)+"/ipem_v2.csv")
hh=pd.read_csv(str(OUT)+"/domicilio_tamanho.csv")
df=df.merge(hh[["cod_ibge","moradores_por_domicilio"]],on="cod_ibge",how="left")
df["renda_domiciliar"]=df.renda_referencia*df.moradores_por_domicilio
df["conta"]=df.tarifa_municipal*100
df["d2_percap"]=df.conta/df.renda_referencia          # o que o projeto faz (denominador per capita)
df["d2_domiciliar"]=df.conta/df.renda_domiciliar      # peso real da conta no orcamento do domicilio
print("=== PESO DA CONTA (100 kWh, tarifa sem tributos) ===")
for c,nm in [("d2_percap","denominador PER CAPITA (atual)"),("d2_domiciliar","denominador DOMICILIAR (correto)")]:
    s=df[c]; print(f"  {nm:34s} MED={s.median()*100:5.2f}%  p90={s.quantile(.9)*100:5.2f}%  max={s.max()*100:5.2f}%")
print("\n  municipios acima de 10%% da renda DOMICILIAR (limiar de Boardman):", int((df.d2_domiciliar>0.10).sum()))
print("  acima de 5%%:", int((df.d2_domiciliar>0.05).sum()), f"({100*(df.d2_domiciliar>0.05).mean():.1f}%)")
print("  referencia POF 2017-18: familias ate R$1.908 gastam 4,4%% da renda com energia")
print("\n=== quanto o denominador muda o ranking ===")
df["rk_pc"]=df.d2_percap.rank(ascending=False); df["rk_dom"]=df.d2_domiciliar.rank(ascending=False)
print("  deslocamento mediano em D2: %d posicoes" % (df.rk_pc-df.rk_dom).abs().median())
a=set(df.nsmallest(100,"rk_pc").cod_ibge); b=set(df.nsmallest(100,"rk_dom").cod_ibge)
print("  sobreposicao dos 100 piores em D2: %d/100" % len(a&b))
print("\n  UFs mais penalizadas pelo denominador per capita (domicilio grande):")
g=df.groupby("uf").moradores_por_domicilio.mean().sort_values(ascending=False)
print("   maiores:", ", ".join(f"{k} {v:.2f}" for k,v in g.head(5).items()))
print("   menores:", ", ".join(f"{k} {v:.2f}" for k,v in g.tail(5).items()))
df.to_csv(str(OUT)+"/ipem_v3.csv",index=False)
