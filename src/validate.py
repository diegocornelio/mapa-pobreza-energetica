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
