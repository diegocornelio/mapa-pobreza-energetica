"""Recalcula os numeros centrais por caminho independente e compara com o payload do app."""
import pandas as pd, numpy as np, json, sys
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import RAW, INTERIM_ORIG, PROCESSED_ORIG, OUT, REF_TARIFA, ANO_UC
D = json.load(open(str(OUT)+"/dados.json", encoding="utf-8"))
P = pd.read_csv(str(OUT)+"/painel_municipal.csv")
S = pd.read_csv(str(OUT)+"/cadunico_sagi.csv")
A = pd.read_csv(str(OUT)+"/por_agente.csv", index_col=0)
F = pd.read_csv(str(OUT)+"/decfec_2024_2025.csv")

# Uma validacao so tem poder se os dois lados chegarem ao mesmo numero por caminhos
# INDEPENDENTES. Se ambos descendem do mesmo artefato, a comparacao nao pode falhar:
# nao e um teste, e uma tautologia. Este arquivo ja teve cinco delas, comparando
# min(t) com min(t) sobre o proprio payload.
#
# Por isso ha duas funcoes, e nao uma. `cmp` exige declarar de qual fonte ANTERIOR ao
# payload veio o lado recalculado, e recusa a declaracao vazia. `coer` e para conferir
# coerencia entre dois campos do payload, o que e util e nao e a mesma coisa: nao
# detecta erro de calculo, so incoerencia interna. O resumo final separa as duas.
CONTA = {"independente": 0, "coerencia": 0, "falhas": 0}

def cmp_f(rot, fonte, calc, app, tol=0.51):
    return cmp(rot, calc, app, tol, fonte)

def cmp(rot, calc, app, tol=0.51, fonte=None):
    """Fonte independente contra payload. `fonte` diz de onde veio o lado esquerdo."""
    if not fonte:
        raise ValueError(f"cmp('{rot}') sem fonte declarada: uma comparacao cujo lado "
                         "recalculado sai do payload nao pode falhar e nao valida nada")
    ok = abs(calc - app) <= tol
    CONTA["independente"] += 1
    CONTA["falhas"] += 0 if ok else 1
    print(f"  {'ok ' if ok else 'DIVERGE'}  {rot:48s} {fonte:22s} {calc:>14,.2f}   app {app:>14,.2f}")

def coer(rot, a, b, tol=0.51):
    """Coerencia entre dois campos do proprio payload."""
    ok = abs(a - b) <= tol
    CONTA["coerencia"] += 1
    CONTA["falhas"] += 0 if ok else 1
    print(f"  {'ok ' if ok else 'DIVERGE'}  {rot:48s} {'(coerencia interna)':22s} {a:>14,.2f}   vs  {b:>14,.2f}")

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
cmp_f("elegiveis, marco de 2026", "painel_municipal (09a)", e26, app_ele)
cmp_f("beneficios, marco de 2026", "painel_municipal (09a)", b26, app_ben)
cmp_f("nao atendidas, soma das positivas", "painel_municipal (09a)", pos26, app_lac)
cmp_f("cobertura (%)", "painel_municipal (09a)", 100*b26/e26, 100*app_ben/app_ele, 0.01)
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
cmp_f("municipios acima do limite 2024", "decfec_2024_2025 (03c)", (F.rel2024>=1).sum(), D['cont']['viol24'])
cmp_f("municipios acima do limite 2025", "decfec_2024_2025 (03c)", (F.rel2025>=1).sum(), D['cont']['viol25'])
cmp_f("reincidentes", "decfec_2024_2025 (03c)", ((F.viol24==1)&(F.viol25==1)).sum(), D['cont']['reinc'])
cmp_f("deixaram de passar", "decfec_2024_2025 (03c)", ((F.viol24==1)&(F.viol25==0)).sum(), D['cont']['saiu'])
cmp_f("passaram a ficar acima", "decfec_2024_2025 (03c)", ((F.viol24==0)&(F.viol25==1)).sum(), D['cont']['entrou'])
soma = D['cont']['reinc']+D['cont']['saiu']+D['cont']['entrou']+D['cont']['limpo']
print(f"  {'ok ' if soma==D['cont']['n'] else 'DIVERGE'}  as quatro categorias somam {soma} e o total com dado e {D['cont']['n']}")

print("\n=== 3. TARIFA ===")
# Esta secao comparava min(t) com min(t) sobre o proprio payload: nao podia falhar.
# Agora a tarifa municipal e reconstruida do arquivo bruto da ANEEL, refazendo a soma
# TUSD+TE, a mediana por CNPJ e a media ponderada por unidades consumidoras, e so
# entao comparada com o que o payload publica. Isso testa 02_tarifa.py de verdade.
B = str(RAW) + "/aneel"
_num = lambda x: pd.to_numeric(x.astype(str).str.replace(".", "", regex=False)
                                .str.replace(",", ".", regex=False), errors="coerce")
Tb = pd.read_csv(B + "/tarifas/2026-09-05/tarifas-homologadas-distribuidoras-energia-eletrica.csv",
                 sep=";", encoding="utf-8", low_memory=False, dtype=str)
_st = lambda c: Tb[c].astype(str).str.strip()
_sel = ((_st("DscSubGrupo") == "B1") & (_st("DscModalidadeTarifaria") == "Convencional")
        & (_st("DscClasse") == "Residencial") & (_st("DscSubClasse") == "Residencial")
        & (_st("DscBaseTarifaria") == "Tarifa de Aplicação") & (_st("DscDetalhe") == "Não se aplica"))
_bb = Tb[_sel].copy()
_bb["ini"] = pd.to_datetime(_bb.DatInicioVigencia, errors="coerce")
_bb["fim"] = pd.to_datetime(_bb.DatFimVigencia, errors="coerce")
_bb["tar"] = (_num(_bb.VlrTUSD) + _num(_bb.VlrTE)) / 1000.0
_bb["cnpj"] = pd.to_numeric(_bb.NumCNPJDistribuidora, errors="coerce")
_ref = pd.Timestamp(REF_TARIFA)
_vv = _bb[(_bb.ini <= _ref) & (_bb.fim >= _ref) & (_bb.tar > 0)]
_tc = _vv.dropna(subset=["cnpj"]).groupby("cnpj").tar.median().reset_index()
_Gg = pd.read_parquet(B + "/indger/2026-09-05/indger-dados-comerciais.parquet",
                      columns=["NumCNPJ", "CodMunicipioIBGE", "DatReferenciaInformada", "QtdUCAtiva"])
_Gg["dt"] = pd.to_datetime(_Gg.DatReferenciaInformada, errors="coerce")
_Gg = _Gg[_Gg.dt.dt.year == ANO_UC]
_Gg["cnpj"] = pd.to_numeric(_Gg.NumCNPJ, errors="coerce")
_Gg["uc"] = pd.to_numeric(_Gg.QtdUCAtiva, errors="coerce").fillna(0)
_Gg["cod_ibge"] = pd.to_numeric(_Gg.CodMunicipioIBGE, errors="coerce")
_Gg = _Gg.dropna(subset=["cod_ibge", "cnpj"]); _Gg["cod_ibge"] = _Gg.cod_ibge.astype(int)
_par = (_Gg.groupby(["cod_ibge", "cnpj"], as_index=False).uc.sum()
            .merge(_tc, on="cnpj", how="left").dropna(subset=["tar"]))
_re = _par.groupby("cod_ibge").apply(
    lambda x: np.average(x.tar, weights=x.uc) if x.uc.sum() > 0 else x.tar.mean(),
    include_groups=False)
_pay = pd.Series({c: v for c, v in zip(D["cod"], D["tar"]) if v is not None})
_j = pd.DataFrame({"re": _re, "pay": _pay}).dropna()
cmp("tarifa minima", _j.re.min(), _j.pay.min(), 0.0001, fonte="ANEEL, arquivo bruto")
cmp("tarifa maxima", _j.re.max(), _j.pay.max(), 0.0001, fonte="ANEEL, arquivo bruto")
cmp("amplitude", _j.re.max() / _j.re.min(), _j.pay.max() / _j.pay.min(), 0.001,
    fonte="ANEEL, arquivo bruto")
# O payload grava a tarifa com quatro casas (09_payload.py, col(...,4)). Recalculando
# do arquivo bruto, 5.431 dos 5.570 municipios batem digito a digito; os outros 139
# diferem por exatamente UMA unidade na ultima casa, porque o recalculo cai do outro
# lado do meio-passo do arredondamento. E artefato de ponto flutuante, nao de calculo.
# Por isso a afirmacao verificada e a honesta: reproduz dentro de uma unidade da
# ultima casa publicada, em todos. O numero de coincidencias exatas fica ao lado.
_dif = (_j.re.round(4) - _j.pay).abs()
_exatos = int((_dif < 1e-9).sum())
cmp("tarifa reproduzida ate a ultima casa publicada", float((_dif <= 1.0001e-4).sum()),
    float(len(_j)), 0.5, fonte="ANEEL, arquivo bruto")
print(f"  -> {_j.pay.min():.4f} a {_j.pay.max():.4f} = {_j.pay.max()/_j.pay.min():.2f}x")
print(f"     coincidencia digito a digito em {_exatos:,} de {len(_j):,}; maior diferenca {_dif.max():.6f}")
print(f"     referencia: {REF_TARIFA}, a mesma do CadUnico e da CDE, com pesos de UC de {ANO_UC}")

print("\n=== 4. FRACAO DA CONTA COBERTA ===")
# O app so usa o municipio com subsidio positivo nas DUAS datas: onde a CDE ficou
# liquida negativa a fracao nao e utilizavel. O filtro precisa ser o mesmo aqui,
# senao a mediana cai sobre outra populacao e a diferenca aparece como divergencia.
pares = [(a,b) for a,b in zip(D['frac24'],D['frac26'])
         if a is not None and b is not None and a > 0 and b > 0]
med = lambda a: sorted(a)[len(a)//2]
coer("mediana da fracao coberta 2024 (%)", 100*med([a for a,_ in pares]), 100*D['nac']['fr24'], 0.06)
coer("mediana da fracao coberta 2026 (%)", 100*med([b for _,b in pares]), 100*D['nac']['fr26'], 0.06)
ganho = sum(1 for a,b in pares if b>a)
coer("municipios com ganho (%)", 100*ganho/len(pares), D['nac']['ganho_pct'], 0.06)
print(f"  -> {ganho} de {len(pares)} municipios com subsidio positivo nas duas datas")
print(f"     {len(D['frac24'])-len(pares)} excluidos por CDE liquida negativa em ao menos uma")

print("\n=== 5. DECOMPOSICAO POR DISTRIBUIDORA ===")
A['d'] = A.mar26 - A.dez24
ENEL, EDP = ["ELETROPAULO","ENEL RJ","ENEL CE"], ["EDP ES","EDP SP"]
cmp_f("Enel", "por_agente.csv (10c)", A.loc[A.index.isin(ENEL),'d'].sum(), D['nac']['enel'])
cmp_f("EDP", "por_agente.csv (10c)", A.loc[A.index.isin(EDP),'d'].sum(), D['nac']['edp'])
cmp_f("demais", "por_agente.csv (10c)", A.loc[~A.index.isin(ENEL+EDP),'d'].sum(), D['nac']['resto'])
tot = D['nac']['enel']+D['nac']['edp']+D['nac']['resto']
coer("soma das tres partes = variacao nacional", tot, D['nac']['b26']-D['nac']['b24'], 200)

print("\n=== 6. CADUNICO ===")
fl = D['fluxo']
for k, col in (("pob","cadun_qtd_familias_cadastradas_pobreza_pbf_i"),
               ("bxr","cadun_qtd_familias_cadastradas_baixa_renda_i"),
               ("ele","cadun_qtd_familias_cadastradas_rfpc_ate_meio_sm_i")):
    for am, suf in ((202412,"24"),(202603,"26")):
        cmp(f"{col.split('_')[-2]} {am}", S[S.anomes==am][col].sum(), fl[k+suf], fonte="SAGI (05b)")
print(f"  {'ok ' if abs((fl['pob24']+fl['bxr24'])-fl['ele24'])<2 else 'DIVERGE'}  pobreza+baixa renda = elegiveis em 2024")
print(f"  {'ok ' if abs((fl['pob26']+fl['bxr26'])-fl['ele26'])<2 else 'DIVERGE'}  pobreza+baixa renda = elegiveis em 2026")
print(f"  variacao do universo elegivel: {100*(fl['ele26']/fl['ele24']-1):+.2f}%")
print(f"  sairam da faixa de pobreza: {fl['pob24']-fl['pob26']:,.0f}")

print("\n=== 7. MUNICIPIOS COM DUAS CONCESSIONARIAS ===")
# Esta secao lia D['pares'] e comparava com D['nac']['mun2dist'], que 10a escreveu
# como len(PARES) a partir do mesmo PARES: os dois lados saiam da mesma linha do
# mesmo script, e a comparacao nao podia falhar. Agora o recalculo parte de
# mun_agente.csv, escrito por 07b, que e um caminho anterior e distinto.
MA = pd.read_csv(str(OUT) + "/mun_agente.csv")
MA["var"] = 100 * (MA.b26 / MA.b24.replace(0, np.nan) - 1)
_v = MA[(MA.b24 >= 100) & np.isfinite(MA["var"])]
_cnt = _v.groupby("cod_ibge").agente.nunique()
_multi = _cnt[_cnt >= 2].index
_w = _v[_v.cod_ibge.isin(_multi)]
_op = 0
for _c, _g in _w.groupby("cod_ibge"):
    _o = _g.sort_values("var")["var"]
    if _o.iloc[0] < 0 < _o.iloc[-1]:
        _op += 1
cmp("municipios com 2+", float(len(_multi)), float(D["nac"]["mun2dist"]), 0.5,
    fonte="mun_agente.csv (07b)")
cmp("com sinais opostos", float(_op), float(D["nac"]["mun2dist_opostos"]), 0.5,
    fonte="mun_agente.csv (07b)")

print("\n=== RESUMO: que especie de conferencia foi feita ===")
print(f"  contra fonte anterior ao payload : {CONTA['independente']}")
print(f"  coerencia entre campos do payload: {CONTA['coerencia']}")
print(f"  divergencias                     : {CONTA['falhas']}")
print()
print("  Uma comparacao so detecta erro de calculo se os dois lados vierem por")
print("  caminhos independentes. As de coerencia interna conferem que o agregado")
print("  publicado bate com os campos que o compoem, o que e util e nao e a mesma")
print("  coisa. A funcao cmp recusa chamada sem fonte declarada, para que nenhuma")
print("  tautologia volte a se disfarcar de validacao.")
sys.exit(1 if CONTA["falhas"] else 0)
