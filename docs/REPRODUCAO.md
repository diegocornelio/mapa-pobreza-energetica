# Reprodução

## Antes de começar

**Os dados brutos não acompanham o repositório.** São cerca de 3 GB, com um CSV de 2,3 GB
dentro do zip da CDE. As URLs de origem estão em `data/sources/fontes.csv` e resumidas em
`docs/FONTES.md`.

Dependências em `reconstrucao/pipeline/requirements.txt`, com as versões da execução de
referência: `pandas`, `numpy`, `pyarrow` e `geopandas`, em Python 3.11. A tabela SIDRA 4712
é buscada por API durante a execução, então é preciso rede.

O `requirements.txt` da raiz é outro arquivo: pertence à versão anterior do trabalho,
preservada em `src/` e `tests/`, e lista pacotes que este pipeline não usa.

Ajuste `reconstrucao/pipeline/_paths.py`. É o **único arquivo com caminho absoluto**;
todo o resto deriva dele.

```python
RAW = Path(r".../data/raw")            # onde estão os brutos
INTERIM_ORIG = Path(r".../data/interim")  # malha municipal (municipios.parquet)
```

## Execução

Na ordem. Cada script grava seus intermediários em `reconstrucao/dados/`.

```
cd reconstrucao/pipeline
python roda_tudo.py
```

O script usa o interpretador que o invocou, ou o apontado por `PIPELINE_PYTHON`. Antes de
começar ele confere as dependências e diz qual falta, porque o erro mais provável de quem
reproduz é chamar o Python do sistema em vez do ambiente virtual:

```
PIPELINE_PYTHON=/caminho/para/.venv/bin/python python roda_tudo.py
```

As vinte e cinco etapas são executadas na ordem, com o tempo de cada uma. A primeira falha
interrompe a execução e devolve código diferente de zero: as etapas são estritamente
sequenciais, e seguir adiante montaria a página sobre arquivos de uma execução anterior,
com aparência de sucesso. A execução completa leva cerca de seis minutos, dos quais dois e
meio são as duas leituras da CDE, que somam 4,5 GB de CSV em streaming.

Para executar etapa a etapa, a ordem é a numérica dos arquivos: `01` e `01b` leem a CDE nas
duas datas; `02` monta a tarifa municipal; `03a` a `03d` tratam a continuidade, em anos
fechados e no primeiro semestre; `04` e `05` vêm do IBGE; `05b` busca a série do CadÚnico no
SAGI; `06` consolida; `07` aplica o desconto e abre a CDE por distribuidora; `08` projeta a
geometria; `09` e `10` montam os payloads; `build_app.py` gera a página.

Validações avulsas, fora do encadeamento:

```
python valida_desconto.py         # teste por inversão do desconto
python valida_decomposicao.py     # economia da família x subsídio da CDE
python valida_territorio.py       # correlações da participação de favela
python valida_granularidade.py    # distribuição dos encaminhamentos
```

## Conferência obrigatória

**Toda reexecução deve ser conferida contra a seção 1 de `docs/VALIDACAO.md`.** São 13
valores. Qualquer divergência é bug de porte ou mudança de fonte, não variação aceitável.

Confira também o tamanho de `site/index.html`: cerca de 1,94 MB.

## Registro de reprodução

Quem reproduzir deve registrar aqui: nome, data, sistema, e quais dos 13 valores
divergiram.

| nome | data | sistema | resultado |
|---|---|---|---|
| Diego H. C. de Rezende | 2026-09-10 | Windows 11, Python 3.11 | execução original, ad hoc, fora desta pasta |
| Diego H. C. de Rezende | 2026-09-10 | Windows 11, Python 3.11 | primeira execução de ponta a ponta por `roda_tudo.py` |

**Nenhuma reexecução a partir de `reconstrucao/pipeline/` foi feita ainda.** Os scripts
são o código que efetivamente produziu o resultado, preservado como estava e
parametrizado por `_paths.py`. Compilam, mas não foram executados de ponta a ponta a
partir deste diretório. A primeira execução é também o primeiro teste do porte.

## Sobre a versão anterior

`run_all.py`, `src/` e `tests/` reproduzem a **versão anterior** deste trabalho, que
continha os seis defeitos de `docs/CORRECOES.md`. Estão preservados para tornar a
comparação auditável.

Note que `run_all.py` chama `python -m src.validate` e `python -m src.export`, e nenhum
dos dois tem bloco `__main__`: rodam como no-op, retornam zero, e o pipeline imprime "OK"
sem ter validado nada.

## Fontes sujeitas a retificação

ANEEL, MDS e IBGE publicam retificações. Uma reexecução em data posterior pode divergir
legitimamente dos números de referência se a fonte tiver sido republicada. O campo
`metadata_modified` em `data/sources/fontes.csv` registra a versão usada.
