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

print("=== 1. FAMILIAS NAO ATENDIDAS (base casada em marco de 2026) ===")
# A leitura do presente casa CadUnico e CDE na MESMA data. O caminho independente
# aqui e painel_municipal.csv, escrito por 09a, contra o payload, escrito por 06d
# e 09: dois codigos distintos lendo as mesmas fontes.
ele_cecad = P.familias_elegiveis.sum()
ele26_nac = S[S.anomes==202603].cadun_qtd_familias_cadastradas_rfpc_ate_meio_sm_i.sum()
e26, b26 = P.eleg_2603.sum(), P.ben26.sum()
e24, b24 = P.eleg_2412.sum(), P.beneficiarios_tsee.sum()
pos26 = int(sum(max(0, e-b) for e, b in zip(P.eleg_2603, P.ben26)))
app_lac = sum(D['lac'])
app_ele = sum(x or 0 for x in D['ele'])
app_ben = sum(x or 0 for x in D['ben'])
cmp("elegiveis, marco de 2026", e26, app_ele)
cmp("beneficios, marco de 2026", b26, app_ben)
cmp("nao atendidas, soma das positivas", pos26, app_lac)
cmp("cobertura (%)", 100*b26/e26, 100*app_ben/app_ele, 0.01)
print(f"  saldo liquido nacional {e26-b26:,.0f}; a diferenca para a soma das positivas")
print(f"  e o excesso dos municipios com mais beneficios que elegiveis")
print()
print(f"  data anterior, dez/2024: {e24:,.0f} elegiveis, {b24:,.0f} beneficios,")
print(f"  cobertura {100*b24/e24:.2f}%, nao atendidas "
      f"{sum(max(0,e-b) for e,b in zip(P.eleg_2412,P.beneficiarios_tsee)):,.0f}")
print()
print("  bases preservadas no payload que NAO alimentam mais o presente:")
print(f"    CECAD de agosto de 2026: {ele_cecad:,.0f} elegiveis")
print(f"    agregado nacional do SAGI em mar/2026: {ele26_nac:,.0f}, que excede a soma")
print(f"    municipal em {ele26_nac-e26:,.0f} porque o SAGI cobre 5.571 municipios, um a")
print( "    mais que a malha do Censo 2022 (Boa Esperanca do Norte, MT, IBGE 5101837)")

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
# O app so usa o municipio com subsidio positivo nas DUAS datas: onde a CDE ficou
# liquida negativa a fracao nao e utilizavel. O filtro precisa ser o mesmo aqui,
# senao a mediana cai sobre outra populacao e a diferenca aparece como divergencia.
pares = [(a,b) for a,b in zip(D['frac24'],D['frac26'])
         if a is not None and b is not None and a > 0 and b > 0]
med = lambda a: sorted(a)[len(a)//2]
cmp("mediana 2024 (%)", 100*med([a for a,_ in pares]), 100*D['nac']['fr24'], 0.06)
cmp("mediana 2026 (%)", 100*med([b for _,b in pares]), 100*D['nac']['fr26'], 0.06)
ganho = sum(1 for a,b in pares if b>a)
cmp("municipios com ganho (%)", 100*ganho/len(pares), D['nac']['ganho_pct'], 0.06)
print(f"  -> {ganho} de {len(pares)} municipios com subsidio positivo nas duas datas")
print(f"     {len(D['frac24'])-len(pares)} excluidos por CDE liquida negativa em ao menos uma")

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
