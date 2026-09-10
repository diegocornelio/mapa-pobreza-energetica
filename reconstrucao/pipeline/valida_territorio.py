import pandas as pd, numpy as np
d=pd.read_csv("app_dados.csv")
def sp(a,b,m=None):
    x=d[a]; y=d[b]
    k=x.notna()&y.notna()
    if m is not None: k=k&m
    return x[k].rank().corr(y[k].rank()), int(k.sum())
d["taxa_lacuna"]=d.lacuna_pos/d.familias_elegiveis
d["desc"]=100-d.cobertura
print("=== A participacao de favela prediz alguma medida energetica? ===")
print("   (spearman; TODOS os 5.570 municipios)")
for b,nm in [("taxa_lacuna","taxa de lacuna TSEE"),("desc","% sem Tarifa Social"),("peso_pob80_cheia","peso da conta na faixa de pobreza"),
             ("d3_corr","DEC/FEC sobre o limite"),("tarifa_municipal","tarifa"),("dec_h_ano","DEC anual (h)")]:
    r,n=sp("d4_corr",b); print(f"   favela x {nm:38s} rho={r:+.4f}  n={n}")
print()
print("   (SO os 655 municipios com favela mapeada)")
m=d.favela_mapeada==True
for b,nm in [("taxa_lacuna","taxa de lacuna TSEE"),("desc","% sem Tarifa Social"),("peso_pob80_cheia","peso da conta na faixa de pobreza"),
             ("d3_corr","DEC/FEC sobre o limite"),("dec_h_ano","DEC anual (h)")]:
    r,n=sp("d4_corr",b,m); print(f"   favela x {nm:38s} rho={r:+.4f}  n={n}")
print()
print("=== municipios com favela mapeada vs sem: as medidas energeticas diferem? ===")
for c,nm in [("desc","% sem Tarifa Social"),("peso_pob80_cheia","peso da conta"),("d3_corr","DEC/FEC sobre limite"),("dec_h_ano","DEC h/ano")]:
    a=d.loc[m,c].median(); b=d.loc[~m,c].median()
    print(f"   {nm:26s} COM favela: {a:8.3f}   SEM favela: {b:8.3f}")
