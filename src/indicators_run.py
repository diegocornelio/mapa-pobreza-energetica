"""IPEM: Índice de Pobreza Energética Municipal.

Reúso de dados abertos (ANEEL, MDS, IBGE) para o 2º Concurso de Reúso de Dados Abertos da CGU.

Autor: Diego H. C. de Rezende, fundador da Struktur Energia.
Engenheiro de Computação e mestre em Engenharia de Software, com experiência em desenvolvimento de software, ciência de dados, gestão de projetos e operação de sistemas em ambientes de alta complexidade e missão crítica. Fundador da Struktur Energia, iniciativa dedicada a inteligência de mercado, eficiência energética e gestão estratégica de energia. Cursa o MBA em Gestão de Riscos na Comercialização de Energia (USP/CCEE) e o MBA em Data Science, Inteligência Artificial e Analytics (USP/ESALQ).

Repositório: https://github.com/diegocornelio/mapa-pobreza-energetica
Licença do código: MIT. Licença dos dados derivados: CC-BY 4.0.
"""
import pandas as pd

from config.settings import BASE_CONSUMPTION_KWH, INTERIM, PROCESSED, RAW
from src.export import export_all
from src.indicators import calculate_indicators, calculate_ipem


def sinais_precariedade_comercial() -> pd.DataFrame:
    """Devolve camada separada de sinais comerciais por distribuidora."""
    path = RAW / "aneel" / "indger" / "2026-09-05" / "indger-dados-comerciais.parquet"
    cols = [
        "SigAgente",
        "DatReferenciaInformada",
        "QtdUCAtiva",
        "QtdInspecVerifProcIrregular",
        "QtdTermosOcorrInspecao",
        "QtdTermosOcorrInspecaoCobr",
    ]
    df = pd.read_parquet(path, columns=cols)
    df["data_referencia"] = pd.to_datetime(df["DatReferenciaInformada"], errors="coerce")
    ano = df[df["data_referencia"].dt.year == 2024].copy()
    for col in cols[2:]:
        ano[col] = pd.to_numeric(ano[col], errors="coerce").fillna(0)
    sinais = (
        ano.groupby("SigAgente", as_index=False)
        .agg(
            unidades_consumidoras=("QtdUCAtiva", "sum"),
            inspecoes_irregularidade=("QtdInspecVerifProcIrregular", "sum"),
            termos_ocorrencia=("QtdTermosOcorrInspecao", "sum"),
            termos_cobrados=("QtdTermosOcorrInspecaoCobr", "sum"),
        )
        .sort_values("SigAgente")
    )
    sinais["taxa_inspecao_por_1000_uc"] = (
        1000 * sinais["inspecoes_irregularidade"] / sinais["unidades_consumidoras"].replace(0, pd.NA)
    )
    sinais["escala_perda"] = "distribuidora"
    sinais["nota_limite"] = (
        "Não medem roubo real; registram sinais comerciais publicados pela ANEEL no INDGER."
    )
    return sinais


def gerar_saidas_processadas() -> pd.DataFrame:
    """Grava CSV, GeoJSON e camada separada de sinais comerciais."""
    base = pd.read_parquet(INTERIM / "base_mestre.parquet")
    out = calculate_ipem(calculate_indicators(base, consumption_kwh=BASE_CONSUMPTION_KWH))
    out["subsidio_tsee_reais"] = out["subsidio_tsee_reais"].clip(lower=0)
    out["subsidio_por_familia"] = out["subsidio_tsee_reais"] / out[
        "beneficiarios_tsee"
    ].replace(0, pd.NA)
    out = out.sort_values(["ranking", "cod_ibge"], na_position="last").reset_index(drop=True)
    export_all(out, sinais_precariedade_comercial())
    PROCESSED.mkdir(parents=True, exist_ok=True)
    return out


if __name__ == "__main__":
    gerar_saidas_processadas()
