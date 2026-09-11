import pandas as pd, numpy as np
from collections import Counter
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import RAW, INTERIM_ORIG, PROCESSED_ORIG, OUT
d=pd.read_csv(str(OUT)+"/app_dados.csv")
q=d.cobertura.quantile([.25,.5,.75]).values
print("cobertura quartis:",np.round(q,1))
conc=set()
for uf,g in d.groupby("uf"):
    g=g.sort_values("lacuna_pos",ascending=False); t=g.lacuna_pos.sum(); c=0
    for _,r in g.iterrows():
        c+=r.lacuna_pos; conc.add(int(r.cod_ibge))
        if c>=t/2: break
def b_cob(r): return 0 if r.cobertura<q[0] else 1 if r.cobertura<q[1] else 2 if r.cobertura<q[2] else 3
def b_esc(r):
    if int(r.cod_ibge) in conc: return 0            # peso estadual
    return 1 if r.lacuna_pos>=1000 else 2 if r.lacuna_pos>=100 else 3
def b_qual(r):
    if pd.isna(r.violacao): return 0                 # sem dado
    if r.violacao==1: return 1                       # violacao
    if r.d3_max>=1 and r.n_conj>1: return 2          # desigualdade interna
    return 3                                         # dentro
def b_peso(r):
    if r.peso_pob80_social>0.10: return 0
    if r.peso_pob80_cheia>0.10: return 1
    return 2
def b_tar(r):
    return 0 if r.rank_tarifa<=557 else 1 if r.rank_tarifa<=2785 else 2
def b_flag(r):
    f=0
    if r.sobrecobertura==1: f|=1
    if r.subsidio_indisponivel==1: f|=2
    return f
B=d.apply(lambda r:(b_cob(r),b_esc(r),b_qual(r),b_peso(r),b_tar(r),b_flag(r)),axis=1)
C=Counter(B)
print()
print("combinacoes distintas:",len(C),"de",len(d),"municipios")
top=C.most_common(8)
print("maior grupo:",top[0][1],"municipios (",round(100*top[0][1]/len(d),1),"%)")
print("as 8 mais comuns cobrem",round(100*sum(c for _,c in top)/len(d),1),"%")
print("municipios em combinacao unica (so eles):",sum(1 for v in C.values() if v==1))
print()
for i,nm in enumerate(["cobertura","escala","qualidade","peso","tarifa","flags"]):
    print(f"  {nm:10s}", dict(sorted(Counter(x[i] for x in B).items())))
