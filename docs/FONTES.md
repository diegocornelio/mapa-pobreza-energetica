# Fontes

Oito conjuntos abertos, de três órgãos federais. O registro completo, com URL, nome de
arquivo preservado, data de download e data de referência, está em
`data/sources/fontes.csv`.

Os dados brutos somam cerca de 3 GB e **não acompanham o repositório**. As URLs abaixo
permitem rebaixá-los.

---

## ANEEL

| conjunto | arquivo | referência | uso |
|---|---|---|---|
| Beneficiários da CDE | `cde-beneficiarios-01dec2024.zip`, 345 MB, com CSV de 2,3 GB | dez/2024 | linhas de benefício da Tarifa Social e valor do subsídio, por `CodIbgeMunicipio` |
| Tarifas homologadas | `tarifas-homologadas-distribuidoras-energia-eletrica.csv`, 85 MB | dez/2024 | tarifa B1 residencial, subclasses Residencial e Baixa Renda, por vigência |
| Continuidade DEC e FEC | `indicadores-continuidade-coletivos-2020-2029.parquet`, 29 MB | 2024 | interrupção apurada por conjunto consumidor, mês a mês |
| Limites de continuidade | `indicadores-continuidade-coletivos-limite.csv`, 25 MB | 2024 | limite anual de DEC e FEC por conjunto |
| IndQual Município | `indqual-municipio.csv`, 2,1 MB | ago/2026 | ponte entre conjunto consumidor e município |
| INDGER | `indger-dados-comerciais.parquet`, 14 MB | 2024 | unidades consumidoras ativas por município e CNPJ de distribuidora |

Portal: `dadosabertos.aneel.gov.br`

## MDS

| conjunto | arquivo | referência | uso |
|---|---|---|---|
| CECAD, painel municipal | 5.598 arquivos HTML, um por código IBGE, 400 MB | ago/2026 | famílias cadastradas e faixas de renda |

Portal: `cecad.cidadania.gov.br/painel01.php`. A coleta exige sessão por UF; não há
variável de município na exportação padrão do TABCAD.

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
| CDE | lida integralmente, 18,3 milhões de linhas em streaming | CPF mascarado na origem impede deduplicação; a contagem usa linhas |
| Tarifas | lida | subclasses Residencial e Baixa Renda; a Baixa Renda é base, não conta final |
| Continuidade | lida | `NumPeriodoIndice` só assume 1 a 12; não há registro anual |
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
