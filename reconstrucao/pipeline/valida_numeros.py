"""Recalcula os numeros centrais por caminho independente e compara com o payload do app."""
import pandas as pd, numpy as np, json
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import RAW, INTERIM_ORIG, PROCESSED_ORIG, OUT
D = json.load(open(str(OUT)+"/dados.json", encoding="utf-8"))
P = pd.read_csv(str(OUT)+"/painel_municipal.csv")
S = pd.read_csv(str(OUT)+"/cadunico_sagi.csv")
A = pd.read_csv(str(OUT)+"/por_agente.csv", index_col=0)
F = pd.read_csv(str(OUT)+"/decfec_2024_2025.csv")

def cmp(rot, calc, app, tol=0.51):
    ok = "ok " if abs(calc-app) <= tol else "DIVERGE"
    print(f"  {ok}  {rot:52s} recalculado {calc:>14,.2f}   app {app:>14,.2f}")

print("=== 1. FAMILIAS NAO ATENDIDAS ===")
ele26 = S[S.anomes==202603].cadun_qtd_familias_cadastradas_rfpc_ate_meio_sm_i.sum()
ele_cecad = P.familias_elegiveis.sum()
b24, b26 = P.beneficiarios_tsee.sum(), P.ben26.sum()
print(f"  elegiveis CECAD ago/2026 : {ele_cecad:>12,.0f}")
print(f"  elegiveis SAGI  mar/2026 : {ele26:>12,.0f}")
cmp("nao atendidas com CDE dez/2024", ele_cecad-b24, sum(D['lac']))
cmp("nao atendidas com CDE mar/2026", ele_cecad-b26, sum(x for x in D['na26'] if x))
cmp("cobertura dez/2024 (%)", 100*b24/ele_cecad, 100*b24/ele_cecad, 0.01)
print(f"  -> o app exibe na home: {sum(D['lac']):,.0f} (base dez/2024)")

print("\n=== 2. CONTINUIDADE ===")
cmp("municipios acima do limite 2024", (F.rel2024>=1).sum(), D['cont']['viol24'])
cmp("municipios acima do limite 2025", (F.rel2025>=1).sum(), D['cont']['viol25'])
cmp("reincidentes", ((F.viol24==1)&(F.viol25==1)).sum(), D['cont']['reinc'])
cmp("deixaram de passar", ((F.viol24==1)&(F.viol25==0)).sum(), D['cont']['saiu'])
cmp("passaram a ficar acima", ((F.viol24==0)&(F.viol25==1)).sum(), D['cont']['entrou'])
soma = D['cont']['reinc']+D['cont']['saiu']+D['cont']['entrou']+D['cont']['limpo']
print(f"  {'ok ' if soma==D['cont']['n'] else 'DIVERGE'}  as quatro categorias somam {soma} e o total com dado e {D['cont']['n']}")

print("\n=== 3. TARIFA ===")
t = [x for x in D['tar'] if x]
cmp("tarifa minima", min(t), min(t), 0.0001)
cmp("tarifa maxima", max(t), max(t), 0.0001)
cmp("amplitude", max(t)/min(t), max(t)/min(t), 0.001)
print(f"  -> {min(t):.4f} a {max(t):.4f} = {max(t)/min(t):.2f}x")

print("\n=== 4. FRACAO DA CONTA COBERTA ===")
f24 = [x for x in D['frac24'] if x is not None]
f26 = [x for x in D['frac26'] if x is not None]
med = lambda a: sorted(a)[len(a)//2]
cmp("mediana 2024 (%)", 100*med(f24), 100*D['nac']['fr24'], 0.06)
cmp("mediana 2026 (%)", 100*med(f26), 100*D['nac']['fr26'], 0.06)
pares = [(a,b) for a,b in zip(D['frac24'],D['frac26']) if a is not None and b is not None]
ganho = sum(1 for a,b in pares if b>a)
cmp("municipios com ganho (%)", 100*ganho/len(pares), D['nac']['ganho_pct'], 0.06)
print(f"  -> {ganho} de {len(pares)} municipios")

print("\n=== 5. DECOMPOSICAO POR DISTRIBUIDORA ===")
A['d'] = A.mar26 - A.dez24
ENEL, EDP = ["ELETROPAULO","ENEL RJ","ENEL CE"], ["EDP ES","EDP SP"]
cmp("Enel", A.loc[A.index.isin(ENEL),'d'].sum(), D['nac']['enel'])
cmp("EDP", A.loc[A.index.isin(EDP),'d'].sum(), D['nac']['edp'])
cmp("demais", A.loc[~A.index.isin(ENEL+EDP),'d'].sum(), D['nac']['resto'])
tot = D['nac']['enel']+D['nac']['edp']+D['nac']['resto']
cmp("soma das tres partes = variacao nacional", tot, D['nac']['b26']-D['nac']['b24'], 200)

print("\n=== 6. CADUNICO ===")
fl = D['fluxo']
for k, col in (("pob","cadun_qtd_familias_cadastradas_pobreza_pbf_i"),
               ("bxr","cadun_qtd_familias_cadastradas_baixa_renda_i"),
               ("ele","cadun_qtd_familias_cadastradas_rfpc_ate_meio_sm_i")):
    for am, suf in ((202412,"24"),(202603,"26")):
        cmp(f"{col.split('_')[-2]} {am}", S[S.anomes==am][col].sum(), fl[k+suf])
print(f"  {'ok ' if abs((fl['pob24']+fl['bxr24'])-fl['ele24'])<2 else 'DIVERGE'}  pobreza+baixa renda = elegiveis em 2024")
print(f"  {'ok ' if abs((fl['pob26']+fl['bxr26'])-fl['ele26'])<2 else 'DIVERGE'}  pobreza+baixa renda = elegiveis em 2026")
print(f"  variacao do universo elegivel: {100*(fl['ele26']/fl['ele24']-1):+.2f}%")
print(f"  sairam da faixa de pobreza: {fl['pob24']-fl['pob26']:,.0f}")

print("\n=== 7. MUNICIPIOS COM DUAS CONCESSIONARIAS ===")
pares2 = D['pares']
opostos = sum(1 for x in pares2 if x['d'][0]['v'] < 0 < x['d'][-1]['v'])
cmp("municipios com 2+", len(pares2), D['nac']['mun2dist'])
cmp("com sinais opostos", opostos, D['nac']['mun2dist_opostos'])
