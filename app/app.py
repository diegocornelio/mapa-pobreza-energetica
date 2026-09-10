"""IPEM: Índice de Pobreza Energética Municipal.

Reúso de dados abertos (ANEEL, MDS, IBGE) para o 2º Concurso de Reúso de Dados Abertos da CGU.

Autor: Diego H. C. de Rezende, fundador da Struktur Energia.
Engenheiro de Computação e mestre em Engenharia de Software, com experiência em desenvolvimento de software, ciência de dados, gestão de projetos e operação de sistemas em ambientes de alta complexidade e missão crítica. Fundador da Struktur Energia, iniciativa dedicada a inteligência de mercado, eficiência energética e gestão estratégica de energia. Cursa o MBA em Gestão de Riscos na Comercialização de Energia (USP/CCEE) e o MBA em Data Science, Inteligência Artificial e Analytics (USP/ESALQ).

Repositório: https://github.com/diegocornelio/mapa-pobreza-energetica
Licença do código: MIT. Licença dos dados derivados: CC-BY 4.0.
"""
from pathlib import Path

import pandas as pd
import streamlit as st

BASE = Path(__file__).resolve().parents[1]
DADOS = BASE / "data" / "processed"

st.set_page_config(page_title="IPEM: Índice de Pobreza Energética Municipal", layout="wide")


@st.cache_data
def carregar_ipem() -> pd.DataFrame:
    """Devolve o CSV processado usado pelo app."""
    return pd.read_csv(DADOS / "ipem_municipios.csv")


@st.cache_data
def carregar_sinais() -> pd.DataFrame:
    """Devolve a camada separada de sinais comerciais."""
    return pd.read_csv(DADOS / "sinais_precariedade_comercial.csv")


def botao_download(df: pd.DataFrame, chave: str) -> None:
    """Renderiza download do CSV principal."""
    st.download_button(
        "Baixar CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="ipem_municipios.csv",
        mime="text/csv",
        key=chave,
    )


def ficha_municipal(df: pd.DataFrame) -> None:
    """Renderiza ficha do município selecionado."""
    opcoes = sorted(df["nome_uf"].dropna().unique())
    escolhido = st.selectbox("Município", opcoes, key="mun")
    linha = df.loc[df["nome_uf"] == escolhido].iloc[0]
    c1, c2, c3 = st.columns(3)
    c1.metric("IPEM (0 a 100)", f"{linha.ipem:.2f}")
    c2.metric("Posição no ranking", int(linha.ranking))
    c3.metric("Lacuna TSEE", f"{linha.lacuna_bruta:,.0f}".replace(",", "."))
    st.markdown(f"Faixa: {linha.faixa}")
    st.markdown(f"Dois piores: {linha.dois_piores_indicadores}")


ipem = carregar_ipem()
sinais = carregar_sinais()

st.title("IPEM: Índice de Pobreza Energética Municipal")
botao_download(ipem, "download_topo")
st.caption("Não identifica famílias; os resultados municipais estão sujeitos a retificação das fontes.")
st.info("Não medem roubo real; os sinais comerciais ficam em camada separada e em escala de distribuidora.")

abas = st.tabs(["Mapa", "Prioridade", "Município", "Tarifa Social", "Subsídios", "Sinais", "Método"])

with abas[0]:
    ufs = ["Brasil"] + sorted(ipem["uf"].dropna().unique())
    uf = st.selectbox("UF", ufs, key="uf_mapa")
    mapa = ipem if uf == "Brasil" else ipem[ipem["uf"] == uf]
    st.dataframe(mapa[["ranking", "nome_uf", "ipem", "faixa"]], hide_index=True)

with abas[1]:
    st.dataframe(
        ipem.sort_values("ranking").head(100)[
            ["ranking", "nome_uf", "ipem", "dois_piores_indicadores"]
        ],
        hide_index=True,
    )

with abas[2]:
    ficha_municipal(ipem)

with abas[3]:
    st.dataframe(
        ipem[["nome_uf", "familias_elegiveis", "beneficiarios_tsee", "lacuna_bruta"]]
        .sort_values("lacuna_bruta", ascending=False)
        .head(100),
        hide_index=True,
    )

with abas[4]:
    st.dataframe(
        ipem[["nome_uf", "subsidio_tsee_reais", "subsidio_por_familia"]]
        .sort_values("subsidio_tsee_reais", ascending=False)
        .head(100),
        hide_index=True,
    )

with abas[5]:
    st.dataframe(sinais, hide_index=True)

with abas[6]:
    st.markdown((BASE / "docs" / "METODO.md").read_text(encoding="utf-8"))

botao_download(ipem, "download_rodape")
st.caption("Autor: Diego H. C. de Rezende (Struktur Energia)")
st.markdown("Repositório: https://github.com/diegocornelio/mapa-pobreza-energetica")
