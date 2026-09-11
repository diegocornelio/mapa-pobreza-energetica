"""Cobertura, familias nao atendidas e concentracao, na BASE CASADA POR DATA.

Ate aqui a leitura "atual" do aplicativo cruzava CadUnico de agosto de 2026 com
CDE de dezembro de 2024, vinte meses de defasagem. A cobertura de um municipio
saia de um numerador e um denominador medidos em datas diferentes, e a propria
pagina de comparacao afirmava o contrario, que cada data usa o CadUnico do seu
proprio mes. Este passo passa a casar as duas pontas em marco de 2026:

  elegiveis   SAGI, competencia 202603
  beneficios  CDE, arquivo de 01mar2026, o unico mes de 2026 com as 103 distribuidoras
  subsidio    CDE do mesmo arquivo

O efeito medido da troca, no agregado nacional:
  nao atendidas     9.968.144  ->  10.440.849
  cobertura            64,28%  ->      62,53%
  sobrecobertura   80 municipios -> 35, porque mais da metade daquela anomalia era
                   artefato da defasagem, e nao unidade consumidora contra familia

As colunas de dezembro de 2024 continuam existindo (familias_elegiveis do CECAD e
beneficiarios_tsee da CDE de dez/2024), porque a pagina de comparacao entre as duas
datas depende delas. O que muda e qual par alimenta a leitura do presente.

O codigo do SAGI tem seis digitos, sem digito verificador; o da CDE tem sete.
"""
import pandas as pd, numpy as np
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import RAW, INTERIM_ORIG, PROCESSED_ORIG, OUT

df = pd.read_csv(str(OUT) + "/ipem_v4.csv")

# --- CDE de dezembro de 2024: fica, porque a comparacao temporal usa ---
cde = pd.read_csv(str(OUT) + "/cde_municipal.csv")
df = df.merge(cde, on="cod_ibge", how="left")

# --- o par casado de marco de 2026 -------------------------------------------
c26 = pd.read_csv(str(OUT) + "/cde_municipal_2026_03.csv").rename(
    columns={"ben_2026_03": "ben_mar26", "subs_2026_03": "subs_mar26"})
df = df.merge(c26, on="cod_ibge", how="left")

CAMPO_ELEG = "cadun_qtd_familias_cadastradas_rfpc_ate_meio_sm_i"
sg = pd.read_csv(str(OUT) + "/cadunico_sagi.csv")
sg = sg[sg.anomes == 202603][["codigo_ibge", CAMPO_ELEG]].rename(
    columns={"codigo_ibge": "ibge6", CAMPO_ELEG: "eleg_mar26"})
df["ibge6"] = df.cod_ibge // 10
df = df.merge(sg, on="ibge6", how="left")
falta = int(df.eleg_mar26.isna().sum()) + int(df.ben_mar26.isna().sum())
if falta:
    print(f"  ATENCAO: {falta} municipios sem o par casado; ficam como nulo, nao como zero")
df["ben_mar26"] = df.ben_mar26.fillna(0)

# --- a leitura do presente, casada em marco de 2026 --------------------------
df["familias_elegiveis_mar26"] = df.eleg_mar26
df["beneficiarios_mar26"] = df.ben_mar26
df["lacuna_bruta_casada"] = df.familias_elegiveis_mar26 - df.beneficiarios_mar26
df["lacuna_pos"] = df.lacuna_bruta_casada.clip(lower=0)
df["cobertura"] = 100 * df.beneficiarios_mar26 / df.familias_elegiveis_mar26.replace(0, np.nan)

# subsidio por familia na MESMA data do contingente, para que o valor em reais
# nao volte a cruzar a quantidade de uma data com o preco de outra
df["subsidio_familia_mar26"] = df.subs_mar26 / df.beneficiarios_mar26.replace(0, np.nan)
df["subsidio_familia_liq"] = df.subs_liquido / df.linhas_tsee.replace(0, np.nan)   # dez/2024, preservado
df["rs_nao_acessado"] = df.lacuna_pos * df.subsidio_familia_mar26

print("=== BASE CASADA: marco de 2026 nas duas pontas ===")
e, b = df.familias_elegiveis_mar26.sum(), df.beneficiarios_mar26.sum()
print(f"  elegiveis   {e:>12,.0f}")
print(f"  beneficios  {b:>12,.0f}")
print(f"  cobertura   {100*b/e:>11.2f}%")
print(f"  nao atendidas (soma das positivas) {df.lacuna_pos.sum():>12,.0f}")
print(f"  sobrecobertura (mais beneficios que elegiveis): {int((df.lacuna_bruta_casada<0).sum())} municipios")
print()
print("=== para conferencia, a base cruzada que saiu de uso ===")
ev, bv = df.familias_elegiveis.sum(), df.beneficiarios_tsee.sum()
print(f"  CECAD ago/2026 x CDE dez/2024: cobertura {100*bv/ev:.2f}% | nao atendidas "
      f"{(df.familias_elegiveis-df.beneficiarios_tsee).clip(lower=0).sum():,.0f}")

s = df.subsidio_familia_mar26.dropna()
print()
print("=== R$ por familia, CDE de marco de 2026 ===")
print(f"  min {s.min():.2f} | MED {s.median():.2f} | max {s.max():.2f} | negativos: {int((s<0).sum())} municipios")
print(f"  R$ nao acessado nacional: R$ {df.rs_nao_acessado.clip(lower=0).sum():,.0f}/mes")

print("\n=== CONCENTRACAO DENTRO DE CADA UF (o que um gestor estadual opera) ===")
out = []
for uf, g in df.groupby("uf"):
    g = g.sort_values("lacuna_pos", ascending=False); tot = g.lacuna_pos.sum()
    if tot <= 0: continue
    c = g.lacuna_pos.cumsum() / tot
    n50 = int((c < 0.5).sum()) + 1
    out.append({"uf": uf, "mun": len(g), "lacuna": int(tot),
                "mun_para_50pct": n50, "pct_dos_mun": round(100 * n50 / len(g), 1)})
o = pd.DataFrame(out).sort_values("mun_para_50pct")
print(o.to_string(index=False))

df.drop(columns=["ibge6"]).to_csv(str(OUT) + "/ipem_v5.csv", index=False)
