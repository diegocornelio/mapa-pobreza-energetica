import pandas as pd, numpy as np
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import RAW, INTERIM_ORIG, PROCESSED_ORIG, OUT, LINHA_POBREZA
d=pd.read_csv(str(OUT)+"/app_dados.csv")
# Regra VIGENTE na data de referencia. REN ANEEL 1.147/2025, art. 2o, que da nova
# redacao ao art. 179, paragrafo 1o da REN 1.000/2021, lido em fonte primaria:
#   I  - para a parcela do consumo menor ou igual a 80 kWh/mes: reducao de 100%
#   II - para a parcela do consumo maior que 80 kWh/mes:        reducao de 0%
# A reducao incide sobre a tarifa B1 subclasse baixa renda. A resolucao produz
# efeitos na data de publicacao, 09/12/2025 (art. 13, IV), e a gratuidade em si
# vigora desde 05/07/2025, pela MP 1.300/2025, convertida na Lei 15.235/2025.
# A palavra "parcela" e o que define a forma: e por faixa de consumo, e nao um
# limiar que cancela o beneficio inteiro de quem ultrapassa os 80 kWh.
def fator(k):
    """Fracao do consumo que o beneficiario paga, na regra vigente."""
    return max(0.0, k-80)/k

# Regra ANTERIOR, escalonada, da Lei 12.212/2010. Vigorou ate 04/07/2025 e e a que
# vale para a leitura de dezembro de 2024. Fica aqui porque os validadores que
# invertem o subsidio daquela data dependem dela, e porque a comparacao entre as
# duas datas so faz sentido com cada uma sob a sua propria regra.
def fator_ate_julho_2025(k):
    f1=min(k,30)*0.35
    f2=max(0,min(k,100)-30)*0.60
    f3=max(0,min(k,220)-100)*0.90
    f4=max(0,k-220)*1.0
    return (f1+f2+f3+f4)/k

print("  regra vigente (REN 1.147/2025):")
for k in [30,80,100,220]: print(f"    {k:3d} kWh -> paga {fator(k):.4f}  (desconto {100*(1-fator(k)):.1f}%)")
print("  regra anterior (Lei 12.212/2010), para a leitura de dez/2024:")
for k in [30,80,100,220]: print(f"    {k:3d} kWh -> paga {fator_ate_julho_2025(k):.4f}  (desconto {100*(1-fator_ate_julho_2025(k)):.1f}%)")
F80=fator(80)
d["conta_cheia80"]=d.tarifa_municipal*80
d["conta_social80"]=d.tarifa_baixa_renda*80*F80
d["econ_mes"]=d.conta_cheia80-d.conta_social80
d["peso_social_ef"]=d.conta_social80/(LINHA_POBREZA*d.moradores_por_domicilio)
# O que as FAMILIAS do municipio deixam de receber por mes. Nao confundir com
# rs_nao_acessado, que e o subsidio que a CDE deixa de desembolsar: aquele mede o
# gasto do fundo, este mede o alivio que nao chega a mesa. Os dois sao verdadeiros
# e diferentes, e o segundo e maior, porque a economia da familia inclui a conta
# inteira ate 80 kWh e o fundo reembolsa pela tarifa da subclasse Baixa Renda.
d["perda_familias_mes"]=d.lacuna_pos*d.econ_mes
print()
print("=== conta de 80 kWh (sem tributos) ===")
print(f"  cheia   : mediana {d.conta_cheia80.median():6.2f}  min {d.conta_cheia80.min():6.2f}  max {d.conta_cheia80.max():6.2f}")
print(f"  social  : mediana {d.conta_social80.median():6.2f}  min {d.conta_social80.min():6.2f}  max {d.conta_social80.max():6.2f}")
print(f"  economia: mediana R$ {d.econ_mes.median():.2f}/mes  ->  R$ {12*d.econ_mes.median():.2f}/ano por familia")
print()
print()
print("=== o consumo implicito da CDE, sob a regra vigente ===")
# Sob a gratuidade, o subsidio por beneficiario e tarifa_baixa_renda x min(consumo, 80).
# Invertendo: consumo = subsidio / tarifa_baixa_renda, enquanto ficar abaixo do teto.
_ki = (d.subsidio_familia_mar26/d.tarifa_baixa_renda).dropna()
_ki = _ki[(_ki>0)&np.isfinite(_ki)]
print(f"  mediana {_ki.median():.1f} kWh  |  p10 {_ki.quantile(.10):.1f}  p90 {_ki.quantile(.90):.1f}")
print(f"  abaixo do teto de 80 kWh: {int((_ki<=80).sum())} de {len(_ki)} ({100*(_ki<=80).mean():.1f}%)")
print("  a regra anterior, aplicada a estes mesmos dados, implicaria consumo")
print("  fisicamente implausivel: e a assinatura de que a regra mudou.")
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
