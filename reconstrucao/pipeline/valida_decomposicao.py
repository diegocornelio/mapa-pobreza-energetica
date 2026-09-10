import pandas as pd, numpy as np
d=pd.read_csv("app_dados2.csv"); u=d[d.subsidio_indisponivel==0]
F80=(30*0.35+50*0.60)/80
tar=u.tarifa_municipal.median(); tas=u.tarifa_baixa_renda.median()
print(f"tarifa residencial mediana R$ {tar:.4f} | subclasse Baixa Renda R$ {tas:.4f} (dif {100*(1-tas/tar):.1f}%)")
print()
print("=== decomposicao da economia da familia a 80 kWh ===")
a=(tar-tas)*80; b=tas*80*(1-F80)
print(f"  (1) troca de subclasse Residencial -> Baixa Renda : R$ {a:6.2f}")
print(f"  (2) desconto escalonado sobre a Baixa Renda       : R$ {b:6.2f}")
print(f"  economia total da familia                         : R$ {a+b:6.2f}   <- e o que o app chama de economia")
print()
print("=== o que a CDE observa ===")
print(f"  subsidio observado por familia (mediana)          : R$ {u.subsidio_familia_liq.median():6.2f}")
print(f"  so o desconto escalonado a 80 kWh                 : R$ {b:6.2f}")
print(f"  so o desconto escalonado a 97,7 kWh               : R$ {tas*(0.65*30+0.40*67.7):6.2f}")
print()
print("  -> a CDE bate com o DESCONTO a ~98 kWh, nao com a economia total a 80 kWh.")
print("  -> minha frase anterior comparava grandezas diferentes que por acaso ficaram proximas.")
