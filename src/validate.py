"""IPEM: Índice de Pobreza Energética Municipal.

Reúso de dados abertos (ANEEL, MDS, IBGE) para o 2º Concurso de Reúso de Dados Abertos da CGU.

Autor: Diego H. C. de Rezende, fundador da Struktur Energia.
Engenheiro de Computação e mestre em Engenharia de Software, com experiência em desenvolvimento de software, ciência de dados, gestão de projetos e operação de sistemas em ambientes de alta complexidade e missão crítica. Fundador da Struktur Energia, iniciativa dedicada a inteligência de mercado, eficiência energética e gestão estratégica de energia. Cursa o MBA em Gestão de Riscos na Comercialização de Energia (USP/CCEE) e o MBA em Data Science, Inteligência Artificial e Analytics (USP/ESALQ).

Repositório: https://github.com/diegocornelio/mapa-pobreza-energetica
Licença do código: MIT. Licença dos dados derivados: CC-BY 4.0.
"""
import pandas as pd

from config.settings import DIM_COLS, MIN_MAIN_COVERAGE, N_MUNICIPIOS_ESPERADO


def validate_outputs(df: pd.DataFrame) -> list[str]:
    errors = []
    if len(df) != N_MUNICIPIOS_ESPERADO:
        errors.append(f"Esperados {N_MUNICIPIOS_ESPERADO} municipios, obtidos {len(df)}")
    if df["cod_ibge"].duplicated().any():
        errors.append("cod_ibge duplicado")
    if not df["ipem"].dropna().between(0, 100).all():
        errors.append("IPEM fora de 0-100")
    if (df["n_dimensoes_validas"] == 4).mean() < MIN_MAIN_COVERAGE:
        errors.append("Menos de 95% dos municipios com 4 dimensoes validas")
    for col in DIM_COLS:
        if df[col].notna().mean() < MIN_MAIN_COVERAGE:
            errors.append(f"Cobertura baixa: {col}")
    return errors


def ordem_de_grandeza_aneel(df: pd.DataFrame, referencia_aneel: float = 7_700_000) -> dict:
    soma = df["lacuna_bruta"].sum()
    return {
        "soma_lacuna_bruta": soma,
        "referencia_aneel": referencia_aneel,
        "razao": soma / referencia_aneel,
        "aprovado_ordem_grandeza": 0.1 <= soma / referencia_aneel <= 10,
    }
