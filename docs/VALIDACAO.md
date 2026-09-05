# Validação

A validação da Fase 3 verifica contrato de saída, cobertura municipal, coerência dos rótulos, ordem de grandeza da lacuna TSEE, consistência de subsídios e compensações, e presença das ressalvas metodológicas. O CSV processado tem 5.570 municípios, e a cobertura das quatro dimensões é completa nesta execução porque cada base recebeu tratamento documentado na Fase 2.

O teste de ordem de grandeza compara a soma da lacuna bruta com a referência pública de 7,7 milhões de unidades consumidoras indicada pela ANEEL em contexto de Tarifa Social. O objetivo é detectar erro de unidade, duplicidade ou subcontagem extrema. A Lei 15.235/2025 é mencionada porque altera o contexto de elegibilidade posterior ao ano-base de parte das bases; o índice preserva o ano-base observado e registra essa diferença.

As ressalvas centrais são três. Primeiro, unidades consumidoras e famílias não são a mesma unidade estatística, o que limita a interpretação direta de cobertura TSEE. Segundo, o cálculo de normalização usa corte superior no percentil 99, sem truncamento inferior adicional, de modo que extremos altos não dominam a escala. Terceiro, há não causalidade entre favelas, baixa renda, qualidade do fornecimento e sinais comerciais: as variáveis descrevem contexto municipal e regulatório, não conduta individual.

## Top 20

| ranking | município | IPEM |
|---|---|---:|
| 1 | Bagre (PA) | 81,38 |
| 2 | Maués (AM) | 81,08 |
| 3 | Acará (PA) | 75,42 |
| 4 | Cametá (PA) | 74,81 |
| 5 | Afuá (PA) | 74,07 |
| 6 | Boa Vista do Ramos (AM) | 73,81 |
| 7 | Viseu (PA) | 72,96 |
| 8 | Melgaço (PA) | 72,91 |
| 9 | Igarapé-Miri (PA) | 72,80 |
| 10 | Tonantins (AM) | 72,62 |
| 11 | Carazinho (RS) | 72,34 |
| 12 | Ipixuna (AM) | 71,93 |
| 13 | Prainha (PA) | 71,68 |
| 14 | Anori (AM) | 71,44 |
| 15 | Barreirinha (AM) | 70,86 |
| 16 | Santo Antônio do Içá (AM) | 70,80 |
| 17 | Cutias (AP) | 70,28 |
| 18 | Ipixuna do Pará (PA) | 70,28 |
| 19 | Coari (AM) | 69,51 |
| 20 | Urucará (AM) | 68,25 |

## Baixada Fluminense

A Baixada Fluminense aparece como recorte de leitura regional, não como validação causal. Nesta execução, Japeri, Belford Roxo, Seropédica, Queimados, Itaguaí, Nova Iguaçu, São João de Meriti, Duque de Caxias, Mesquita, Magé, Paracambi, Nilópolis e Guapimirim foram identificados no CSV processado. O resultado indica heterogeneidade interna do recorte, com maior severidade relativa em Japeri e menor em Guapimirim, conforme os dados lidos nesta execução.

## IDHM

A correlação com IDHM permanece não testada porque `data/raw/atlas/idhm.csv` não foi incorporado nesta fase. O teste automatizado reconhece essa ausência e registra a validação como pendente, sem usar valor substituto.
