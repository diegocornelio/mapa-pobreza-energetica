# Fontes

Nove conjuntos abertos, de três órgãos federais, em duas datas de referência. O registro completo, com URL, nome de
arquivo preservado, data de download e data de referência, está em
`data/sources/fontes.csv`.

Os dados brutos somam cerca de 3,4 GB e **não acompanham o repositório**. As URLs abaixo
permitem rebaixá-los.

---

## ANEEL

| conjunto | arquivo | referência | uso |
|---|---|---|---|
| Beneficiários da CDE | `cde-beneficiarios-01dec2024.zip`, 345 MB, com CSV de 2,3 GB | dez/2024 | linhas de benefício da Tarifa Social e valor do subsídio, por `CodIbgeMunicipio` |
| Beneficiários da CDE | `cde-beneficiarios-01mar2026.zip`, 326 MB, com CSV de 2,26 GB | mar/2026 | a mesma leitura na data recente, para comparação temporal |
| Tarifas homologadas | `tarifas-homologadas-distribuidoras-energia-eletrica.csv`, 85 MB | dez/2024 | tarifa B1 residencial, subclasses Residencial e Baixa Renda, por vigência |
| Continuidade DEC e FEC | `indicadores-continuidade-coletivos-2020-2029.parquet`, 29 MB | 2020 a 2026 | interrupção apurada por conjunto consumidor, mês a mês; usados 2024 e 2025 fechados e o primeiro semestre de 2026 |
| Limites de continuidade | `indicadores-continuidade-coletivos-limite.csv`, 25 MB | 2024 e 2025 | limite anual de DEC e FEC por conjunto |
| IndQual Município | `indqual-municipio.csv`, 2,1 MB | ago/2026 | ponte entre conjunto consumidor e município |
| INDGER | `indger-dados-comerciais.parquet`, 14 MB | 2024 e 2026 | unidades consumidoras ativas por município e CNPJ de distribuidora; traz ainda 60 colunas comerciais municipais não utilizadas |

Portal: `dadosabertos.aneel.gov.br`

## MDS

| conjunto | acesso | referência | uso |
|---|---|---|---|
| CECAD, painel municipal | 5.598 arquivos HTML, um por código IBGE, 400 MB | ago/2026 | famílias cadastradas e faixas de renda |
| **VIS DATA / SAGI**, índice `misocial` | API, uma requisição por competência | dez/2024, mar/2026, ago/2026 | as mesmas famílias por faixa, com **série mensal histórica** |

Portal do painel: `cecad.cidadania.gov.br/painel01.php`. A coleta exige sessão por UF, e não
há variável de município na exportação padrão do TABCAD. O painel mostra apenas a competência
corrente, o que impede comparação entre datas.

A API do SAGI resolve essa limitação. Em `aplicacoes.mds.gov.br/sagi/servicos/misocial`, o
índice traz `codigo_ibge`, `anomes` e as contagens por faixa de renda, com competências desde
2020. Os campos usados são `cadun_qtd_familias_cadastradas_i`,
`cadun_qtd_familias_cadastradas_pobreza_pbf_i`, `cadun_qtd_familias_cadastradas_baixa_renda_i`
e `cadun_qtd_familias_cadastradas_rfpc_ate_meio_sm_i`, este último correspondendo ao critério
de elegibilidade da Tarifa Social.

Convém registrar a verificação: para agosto de 2026, as quatro variáveis do SAGI são
**idênticas às do painel CECAD nos 5.570 municípios**. A coincidência valida a substituição da
raspagem pela API, e é o que habilita a série histórica. O código do SAGI tem seis dígitos,
sem dígito verificador, e a junção com a malha do IBGE exige esse ajuste.

## IBGE

| tabela SIDRA | variável | referência | uso |
|---|---|---|---|
| **10296** | classes de rendimento nominal mensal domiciliar por pessoa | 2022 | renda de referência e total de moradores; 27 arquivos, um por UF |
| **9887** | 9909, domicílios em favelas e comunidades urbanas | 2022 | numerador da participação territorial |
| **4712** | 381, domicílios particulares permanentes ocupados | 2022 | denominador da participação territorial e do tamanho do domicílio |

API: `apisidra.ibge.gov.br` e `servicodados.ibge.gov.br/api/v3/agregados`.

A tabela 4712 é obtida por requisição direta à API no momento da execução, e cacheada
localmente. As demais foram baixadas em 2026-09-05.

---

## Pontes entre bases

Três junções não triviais sustentam o resultado. Cada uma foi verificada.

**Distribuidora → município.** Feita pelo **`NumCNPJ`**, não pelo `SigAgente`. Pelo nome
do agente casam 560 municípios; pelo CNPJ, os 5.570. A escolha da chave é a diferença
entre uma tarifa municipal completa e uma cobertura de 10%.

**Conjunto consumidor → município.** Feita pelo IndQual, que relaciona
`IdeConjUnidConsumidoras` a `CodMunicipio`. São 42.699 pares, cobrindo 5.557 municípios
com apuração de continuidade em 2024.

**Favela → município.** As tabelas 9887 e 4712 usam o mesmo código municipal e a mesma
espécie de domicílio, o que torna a divisão direta.

---

## Estado de leitura

| fonte | estado | observação |
|---|---|---|
| CDE dez/2024 | lida integralmente, 18,3 milhões de linhas em streaming | CPF mascarado na origem impede deduplicação; a contagem usa linhas |
| CDE mar/2026 | lida integralmente, 17,7 milhões de linhas | **único mês de 2026 com as 103 distribuidoras**; ver `docs/LIMITES.md` |
| SAGI | lida por API, três competências | idêntica ao CECAD em ago/2026, nos 5.570 municípios |
| Tarifas | lida | subclasses Residencial e Baixa Renda, vigências de dez/2024 e mar/2026; a Baixa Renda é base, e não conta final |
| Continuidade | lida | `NumPeriodoIndice` só assume 1 a 12, e não há registro anual; 2026 tem no máximo 7 meses reportados |
| Limites | lida | indexado por `AnoLimiteQualidade`; é anual |
| IndQual | lida | ponte municipal completa |
| INDGER | lida | `NumCNPJ`, `CodMunicipioIBGE` e `QtdUCAtiva` |
| CECAD | 5.598 HTMLs lidos | a soma das três faixas confere com o total de cadastradas |
| SIDRA 10296 | 27 arquivos lidos | unidade é **pessoas**, não domicílios |
| SIDRA 9887 | lida | a variável 1009909 é percentual **dentro** das favelas, e não foi usada |
| SIDRA 4712 | lida por API | variável 381 |

## Licenças

ANEEL: Licença Aberta ANEEL. MDS: dados públicos federais. IBGE: licença IBGE.
Dados derivados deste trabalho: CC-BY 4.0.
