# Fontes

As fontes brutas usadas na Fase 2 estão registradas em `data/sources/fontes.csv`. O arquivo informa órgão, conjunto, recurso, nome original preservado, caminho local, data de referência, escala, licença, uso no projeto e observação metodológica.

## Estado de Leitura

| source_id | estado | uso |
|---|---|---|
| `aneel_cde` | arquivo bruto lido | Beneficiários e subsídios TSEE por `CodIbgeMunicipio`. |
| `mds_cecad` | HTML municipal lido | Famílias cadastradas e faixas de renda CECAD por município. |
| `aneel_tarifas` | arquivo bruto lido | Tarifa B1 residencial convencional por distribuidora, convertida para estimativa municipal. |
| `aneel_indger` | parquet lido | Coluna municipal `CodMunicipioIBGE` e distribuidora dominante por unidades consumidoras. |
| `aneel_decfec` | parquets e CSV lidos | DEC, FEC, limites e compensações por conjunto consumidor. |
| `aneel_indqual` | CSV lido | Ponte municipal entre conjuntos consumidores e municípios. |
| `ibge_favelas` | export SIDRA lido | Domicílios em favelas e comunidades urbanas por município. |
| `ibge_renda` | exports SIDRA por UF lidos | Renda de referência aproximada por faixas do Censo 2022. |

## Limites

A CDE possui coluna municipal real, mas o CPF/CNPJ do beneficiário vem mascarado na base aberta; por isso a contagem de `beneficiarios_tsee` usa linhas de benefício TSEE no mês de referência. A tarifa homologada é observada por distribuidora, não por município; a versão municipal é uma estimativa conservadora, marcada em `tarifa_flag_estimativa`. A renda do IBGE foi obtida por classes de rendimento nominal mensal domiciliar per capita; a média municipal é aproximação por pontos médios das faixas, e essa hipótese cairia se uma tabela municipal de renda média per capita diretamente observada fosse incorporada em etapa posterior.
