# Reprodução

## Antes de começar

**Os dados brutos não acompanham o repositório.** São cerca de 3 GB, com um CSV de 2,3 GB
dentro do zip da CDE. As URLs de origem estão em `data/sources/fontes.csv` e resumidas em
`docs/FONTES.md`.

Dependências: `pandas`, `pyarrow`, `geopandas`. A tabela SIDRA 4712 é buscada por API
durante a execução, então é preciso rede.

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

python 01_cde.py                  # ~8 min, streaming de 2,3 GB
python 02_tarifa.py               # tarifa municipal, ponte por CNPJ
python 03a_decfec_conjunto.py     # DEC/FEC anual por conjunto
python 03b_decfec_municipio.py    # agregação ponderada por consumidores
python 04_territorio.py           # requisição à API do SIDRA 4712
python 05_domicilio.py            # moradores por domicílio
python 06a_indice_corrigido.py
python 06b_renda_domiciliar.py
python 06c_faixas_cadunico.py
python 06d_concentracao.py
python 06e_distribuidora.py
python 07_tarifa_social.py        # desconto escalonado
python 08_geometria.py            # projeção SIRGAS 2000 e paths SVG
python 09_payload.py              # dados.json

python build_app.py               # gera app/mapa.html
```

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

Confira também o tamanho de `reconstrucao/app/mapa.html`: cerca de 1,94 MB.

## Registro de reprodução

Quem reproduzir deve registrar aqui: nome, data, sistema, e quais dos 13 valores
divergiram.

| nome | data | sistema | resultado |
|---|---|---|---|
| Diego H. C. de Rezende | 2026-09-10 | Windows 11, Python 3.11 | execução original, ad hoc, fora desta pasta |

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
sem ter validado nada. O conserto está previsto em `refatoracao.md`.

## Fontes sujeitas a retificação

ANEEL, MDS e IBGE publicam retificações. Uma reexecução em data posterior pode divergir
legitimamente dos números de referência se a fonte tiver sido republicada. O campo
`metadata_modified` em `data/sources/fontes.csv` registra a versão usada.
