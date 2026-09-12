# -*- coding: utf-8 -*-
"""Regera o dataset municipal que acompanha o repositorio e vai ao portal.

Este arquivo existia sem etapa que o produzisse. Era um instantaneo congelado: o
pipeline inteiro podia ser reexecutado, o aplicativo podia ser reconstruido, e ele
continuava com os valores do dia em que alguem o gravou a mao. Ficou assim por
tempo suficiente para guardar a tarifa de dezembro de 2024 e a regra de desconto
revogada em julho de 2025, enquanto a pagina publicada ja mostrava outra coisa.

Dataset que contradiz o produto e pior do que dataset ausente, porque quem baixa
nao tem como saber qual dos dois esta certo. A etapa existe para que a unica forma
de ele mudar seja o pipeline rodar.

As colunas sao as 35 documentadas em docs/DICIONARIO.md, nessa ordem.
"""
import sys, os, pathlib
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import OUT

DESTINO = pathlib.Path(OUT) / "municipios_corrigido.csv"

COLUNAS = [
    "cod_ibge", "nome", "uf", "distribuidora",
    "familias_cadastradas", "familias_pobreza", "familias_baixa_renda", "familias_elegiveis",
    "beneficiarios_tsee", "cobertura", "lacuna_pos", "sobrecobertura",
    "subs_liquido", "subsidio_familia_liq", "rs_nao_acessado", "subsidio_indisponivel",
    "tarifa_municipal", "tarifa_baixa_renda", "rank_tarifa", "moradores_por_domicilio",
    "peso_pob80_cheia", "dec_h_ano", "d3_corr", "d3_max",
    "n_conj", "violacao", "dom_favela", "dom_total_mun",
    "d4_corr", "favela_mapeada", "renda_referencia", "conta_cheia80",
    "conta_social80", "econ_mes", "peso_social_ef", "perda_familias_mes",
]


def main():
    d = pd.read_csv(str(OUT) + "/app_dados2.csv")
    falta = [c for c in COLUNAS if c not in d.columns]
    if falta:
        raise SystemExit("11_dataset_publicado: colunas ausentes em app_dados2.csv: "
                         + ", ".join(falta))

    antes = None
    if DESTINO.exists():
        antes = pd.read_csv(DESTINO)

    novo = d[COLUNAS].copy()
    novo.to_csv(DESTINO, index=False)
    print(f"dataset publicado: {len(novo)} linhas, {len(novo.columns)} colunas")

    if antes is not None:
        mudou = []
        for c in COLUNAS:
            if c not in antes.columns:
                mudou.append((c, "coluna nova", "")); continue
            a, b = antes[c], novo[c]
            if pd.api.types.is_numeric_dtype(b) and pd.api.types.is_numeric_dtype(a):
                ma, mb = a.median(), b.median()
                if pd.notna(ma) and pd.notna(mb) and abs(ma - mb) > 1e-9:
                    mudou.append((c, f"{ma:,.4f}", f"{mb:,.4f}"))
        if mudou:
            print(f"  {len(mudou)} coluna(s) com mediana diferente da versao anterior:")
            for c, a, b in mudou:
                print(f"    {c:26s} {a:>14s} -> {b:>14s}")
        else:
            print("  nenhuma mediana mudou em relacao a versao anterior")
    return 0


if __name__ == "__main__":
    sys.exit(main())
