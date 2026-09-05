"""IPEM: Índice de Pobreza Energética Municipal.

Reúso de dados abertos (ANEEL, MDS, IBGE) para o 2º Concurso de Reúso de Dados Abertos da CGU.

Autor: Diego H. C. de Rezende, fundador da Struktur Energia.
Engenheiro de Computação e mestre em Engenharia de Software, com experiência em desenvolvimento de software, ciência de dados, gestão de projetos e operação de sistemas em ambientes de alta complexidade e missão crítica. Fundador da Struktur Energia, iniciativa dedicada a inteligência de mercado, eficiência energética e gestão estratégica de energia. Cursa o MBA em Gestão de Riscos na Comercialização de Energia (USP/CCEE) e o MBA em Data Science, Inteligência Artificial e Analytics (USP/ESALQ).

Repositório: https://github.com/diegocornelio/ipem-pobreza-energetica-municipal
Licença do código: MIT. Licença dos dados derivados: CC-BY 4.0.
"""
from pathlib import Path
import re
import time
import unicodedata

import pandas as pd
import requests

from config.settings import DOWNLOAD_DATE, INTERIM, RAW

DATASETS = {
    "aneel_cde": {
        "org": "aneel",
        "slug": "beneficiarios-cde",
        "url": "https://dadosabertos.aneel.gov.br/dataset/beneficiarios-da-cde",
        "manual": True,
    },
    "aneel_decfec": {
        "org": "aneel",
        "slug": "dec-fec",
        "url": "https://dadosabertos.aneel.gov.br/dataset/indicadores-coletivos-de-continuidade-dec-e-fec",
        "manual": True,
    },
    "aneel_indqual": {
        "org": "aneel",
        "slug": "indqual-municipio",
        "url": "https://dadosabertos.aneel.gov.br/dataset/indqual-municipio",
        "manual": True,
    },
    "aneel_indger": {
        "org": "aneel",
        "slug": "indger",
        "url": "https://dadosabertos.aneel.gov.br/dataset/indger-indicadores-gerenciais-da-distribuicao",
        "manual": True,
    },
    "mds_cecad": {
        "org": "mds",
        "slug": "cecad-painel",
        "url": "https://cecad.cidadania.gov.br/",
        "manual": True,
    },
}

CECAD_BASE_URL = "https://cecad.cidadania.gov.br"
CECAD_REFERENCIA = "2026-08"
USER_AGENT = "IPEM-pobreza-energetica (reuso dados abertos CGU; contato no README)"


def raw_dir(org: str, slug: str) -> Path:
    path = RAW / org / slug / DOWNLOAD_DATE
    path.mkdir(parents=True, exist_ok=True)
    return path


def download_file(url: str, target: Path) -> Path:
    with requests.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()
        with target.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
    return target


def sessao_cecad() -> requests.Session:
    """Devolve sessão HTTP identificada para acessar o painel CECAD."""
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def get_com_tentativas(session: requests.Session, url: str, timeout: int = 30) -> str:
    """Devolve HTML; falha após três tentativas sem resposta válida."""
    ultimo_erro = None
    for tentativa in range(3):
        try:
            response = session.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as exc:
            ultimo_erro = exc
            time.sleep(2**tentativa)
    raise RuntimeError(f"Falha ao acessar {url}: {ultimo_erro}")


def numero_br(texto: str) -> int:
    """Converte número brasileiro inteiro para `int`; falha se não houver dígitos."""
    digitos = re.sub(r"\D", "", texto)
    if not digitos:
        raise ValueError(f"Número ausente em {texto!r}")
    return int(digitos)


def sem_acentos(texto: str) -> str:
    """Devolve texto em maiúsculas sem acentos para comparação de títulos."""
    normalizado = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in normalizado if not unicodedata.combining(c)).upper()


def ufs_do_painel(html: str) -> list[tuple[str, str]]:
    """Extrai pares `codigo_uf, sigla` do seletor principal do painel."""
    pares = re.findall(r"<option\s+value='(\d{2})'>([A-Z]{2})-", html)
    if len(pares) != 27:
        raise ValueError(f"Esperadas 27 UFs no painel CECAD, obtidas {len(pares)}")
    return pares


def municipios_do_select(html: str) -> list[dict[str, str]]:
    """Extrai código e nome municipal do HTML do seletor CECAD."""
    opcoes = re.findall(r"<option\s+value='([0-9]{7})'>(.*?)</option>", html, re.S)
    return [{"cod_ibge": codigo, "nome": re.sub(r"\s+", " ", nome).strip()} for codigo, nome in opcoes]


def valor_apos_rotulo(html: str, rotulo: str) -> int:
    """Extrai o primeiro valor numérico informado após um rótulo do painel."""
    padrao = re.compile(
        re.escape(rotulo) + r".{0,500}?<div class=\"dado_textoc\">([0-9.]+)</div>",
        re.S | re.I,
    )
    encontrado = padrao.search(html)
    if not encontrado:
        raise ValueError(f"Rótulo não encontrado no painel CECAD: {rotulo}")
    return numero_br(encontrado.group(1))


def titulo_municipal(html: str) -> str:
    """Extrai o título territorial do painel municipal."""
    encontrado = re.search(r"<h4>\s*Cadastro Único\s*([^<]+)</h4>", html, re.I)
    if not encontrado:
        raise ValueError("Título municipal ausente no painel CECAD")
    return re.sub(r"\s+", " ", encontrado.group(1)).strip()


def linha_cecad(cod_ibge: str, nome: str, uf: str, html: str) -> dict[str, object]:
    """Converte HTML municipal do CECAD em uma linha tabular."""
    titulo = titulo_municipal(html)
    titulo_normalizado = sem_acentos(titulo)
    nome_normalizado = sem_acentos(nome)
    if titulo_normalizado == "BRASIL" or nome_normalizado not in titulo_normalizado:
        raise ValueError(f"Sessão CECAD não posicionada em {nome}-{uf}: {titulo}")
    familias_cadastradas = valor_apos_rotulo(html, "Famílias Cadastradas")
    familias_pobreza = valor_apos_rotulo(html, "em situação de Pobreza")
    familias_baixa_renda = valor_apos_rotulo(html, "em situação de Baixa Renda")
    familias_acima_meio_sm = valor_apos_rotulo(
        html, "com renda per capita mensal Acima de ½ Sal. min."
    )
    return {
        "cod_ibge": int(cod_ibge),
        "familias_cadastradas": familias_cadastradas,
        "familias_pobreza": familias_pobreza,
        "familias_baixa_renda": familias_baixa_renda,
        "familias_acima_meio_sm": familias_acima_meio_sm,
        "familias_elegiveis": familias_pobreza + familias_baixa_renda,
        "renda_referencia": pd.NA,
        "renda_fonte": "IBGE Censo 2022 (Plano B)",
        "source_id": "mds_cecad",
        "data_referencia": CECAD_REFERENCIA,
    }


def coletar_cecad_painel(intervalo_segundos: float = 1.0) -> pd.DataFrame:
    """Coleta o painel municipal CECAD e grava parquet intermediário."""
    destino = raw_dir("mds", "cecad-painel")
    session = sessao_cecad()
    inicial = get_com_tentativas(session, f"{CECAD_BASE_URL}/painel01.php")
    linhas = []
    for codigo_uf, sigla in ufs_do_painel(inicial):
        select_path = destino / f"select_{codigo_uf}.html"
        if select_path.exists():
            select_html = select_path.read_text(encoding="utf-8")
        else:
            select_url = (
                f"{CECAD_BASE_URL}/layout/system_config/classes/seleciona_local_class.php"
                f"?p_chama=ax&uf_ibge={codigo_uf}&p_digito=7"
            )
            select_html = get_com_tentativas(session, select_url)
            select_path.write_text(select_html, encoding="utf-8")
            time.sleep(intervalo_segundos)
        for municipio in municipios_do_select(select_html):
            html_path = destino / f"{municipio['cod_ibge']}.html"
            if html_path.exists():
                html = html_path.read_text(encoding="utf-8")
            else:
                url = (
                    f"{CECAD_BASE_URL}/painel01.php"
                    f"?p_ibge={codigo_uf}&mu_ibge={municipio['cod_ibge']}"
                )
                html = get_com_tentativas(session, url)
                html_path.write_text(html, encoding="utf-8")
                time.sleep(intervalo_segundos)
            try:
                linhas.append(linha_cecad(municipio["cod_ibge"], municipio["nome"], sigla, html))
            except ValueError:
                select_html = get_com_tentativas(
                    session,
                    f"{CECAD_BASE_URL}/layout/system_config/classes/seleciona_local_class.php"
                    f"?p_chama=ax&uf_ibge={codigo_uf}&p_digito=7",
                )
                select_path.write_text(select_html, encoding="utf-8")
                url = (
                    f"{CECAD_BASE_URL}/painel01.php"
                    f"?p_ibge={codigo_uf}&mu_ibge={municipio['cod_ibge']}"
                )
                html = get_com_tentativas(session, url)
                html_path.write_text(html, encoding="utf-8")
                linhas.append(linha_cecad(municipio["cod_ibge"], municipio["nome"], sigla, html))
                time.sleep(intervalo_segundos)
    df = pd.DataFrame(linhas).sort_values("cod_ibge").reset_index(drop=True)
    spine_path = INTERIM / "municipios.parquet"
    if spine_path.exists():
        codigos_malha = set(pd.read_parquet(spine_path, columns=["cod_ibge"]).cod_ibge.astype(int))
        df = df[df["cod_ibge"].isin(codigos_malha)].reset_index(drop=True)
    INTERIM.mkdir(parents=True, exist_ok=True)
    df.to_parquet(INTERIM / "cadunico_municipio.parquet", index=False)
    return df


if __name__ == "__main__":
    coletar_cecad_painel()
