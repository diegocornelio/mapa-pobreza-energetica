import pandas as pd, numpy as np
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import RAW, INTERIM_ORIG, PROCESSED_ORIG, OUT, LINHA_POBREZA
d=pd.read_csv(str(OUT)+"/app_dados.csv")
# desconto escalonado TSEE, Lei 12.212/2010 art.2 + REN ANEEL 1000/2021: cumulativo por faixa
def fator(k):
    f1=min(k,30)*0.35
    f2=max(0,min(k,100)-30)*0.60
    f3=max(0,min(k,220)-100)*0.90
    f4=max(0,k-220)*1.0
    return (f1+f2+f3+f4)/k
for k in [30,80,100,220]: print(f"  {k:3d} kWh -> fator {fator(k):.4f}  (desconto {100*(1-fator(k)):.1f}%)")
F80=fator(80)
d["conta_cheia80"]=d.tarifa_municipal*80
d["conta_social80"]=d.tarifa_baixa_renda*80*F80
d["econ_mes"]=d.conta_cheia80-d.conta_social80
d["peso_social_ef"]=d.conta_social80/(LINHA_POBREZA*d.moradores_por_domicilio)
print()
print("=== conta de 80 kWh (sem tributos) ===")
print(f"  cheia   : mediana {d.conta_cheia80.median():6.2f}  min {d.conta_cheia80.min():6.2f}  max {d.conta_cheia80.max():6.2f}")
print(f"  social  : mediana {d.conta_social80.median():6.2f}  min {d.conta_social80.min():6.2f}  max {d.conta_social80.max():6.2f}")
print(f"  economia: mediana R$ {d.econ_mes.median():.2f}/mes  ->  R$ {12*d.econ_mes.median():.2f}/ano por familia")
print()
print("=== peso na faixa de pobreza, 80 kWh ===")
print(f"  tarifa cheia          : mediana {100*d.peso_pob80_cheia.median():5.2f}%  acima de 10%: {int((d.peso_pob80_cheia>0.10).sum())}")
print(f"  ANTES (base sem desc.): mediana {100*d.peso_pob80_social.median():5.2f}%  acima de 10%: {int((d.peso_pob80_social>0.10).sum())}  <-- ERRADO")
print(f"  CORRETO (com desconto): mediana {100*d.peso_social_ef.median():5.2f}%  acima de 10%: {int((d.peso_social_ef>0.10).sum())}")
print()
print("=== valor mecanico de fechar a lacuna (tarifa publicada, sem CDE) ===")
tot=(d.lacuna_pos*d.econ_mes).sum()
print(f"  alivio mensal as familias se a lacuna fosse fechada: R$ {tot:,.0f}/mes  =  R$ {12*tot:,.0f}/ano")
print(f"  subsidio medio observado na CDE por familia: R$ {d.subsidio_familia_liq.median():.2f}/mes")
d.to_csv(str(OUT)+"/app_dados2.csv",index=False)
