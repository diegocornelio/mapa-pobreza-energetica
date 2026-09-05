# Dicionário

| coluna | descrição |
|---|---|
| `cod_ibge` | Código municipal IBGE com 7 dígitos. |
| `nome` | Nome do município conforme malha IBGE usada na espinha. |
| `uf` | Sigla da unidade da federação. |
| `nome_uf` | Nome municipal com UF entre parênteses. |
| `familias_cadastradas` | Famílias cadastradas no CECAD municipal. |
| `familias_pobreza` | Famílias no CECAD em situação de pobreza. |
| `familias_baixa_renda` | Famílias no CECAD em situação de baixa renda. |
| `familias_acima_meio_sm` | Famílias no CECAD acima de meio salário mínimo per capita. |
| `familias_elegiveis` | Soma de `familias_pobreza` e `familias_baixa_renda`. |
| `source_id` | Identificador da fonte principal da linha CECAD. |
| `data_referencia` | Data de referência da linha CECAD. |
| `renda_referencia` | Renda nominal mensal domiciliar per capita estimada por faixas do Censo 2022. |
| `renda_fonte` | Descrição da fonte e do tratamento usado para renda. |
| `beneficiarios_tsee` | Contagem de linhas de benefício TSEE no arquivo CDE de dezembro de 2024. |
| `subsidio_tsee_reais` | Soma municipal do subsídio TSEE em reais. |
| `source_id_tsee_municipio` | Identificador da fonte da tabela TSEE municipal. |
| `data_referencia_tsee_municipio` | Data de referência da tabela TSEE municipal. |
| `tarifa_municipal_estimada` | Tarifa estimada em R$/kWh para o consumo de referência. |
| `tarifa_flag_estimativa` | Indica que a tarifa municipal é estimada. |
| `distribuidoras_usadas` | Regra ou distribuidora usada na estimativa tarifária. |
| `dec_apurado` | DEC anual apurado associado ao município. |
| `fec_apurado` | FEC anual apurado associado ao município. |
| `dec_limite` | Limite regulatório de DEC associado ao município. |
| `fec_limite` | Limite regulatório de FEC associado ao município. |
| `dec_rel` | Razão entre DEC apurado e DEC limite. |
| `fec_rel` | Razão entre FEC apurado e FEC limite. |
| `compensacoes_decfec_reais` | Compensações de continuidade agregadas a partir da fonte DEC/FEC. |
| `dom_favela` | Domicílios em favelas e comunidades urbanas no Censo 2022. |
| `dom_total` | Total estimado de domicílios usado como denominador territorial. |
| `lacuna_bruta` | Diferença entre famílias elegíveis e beneficiários TSEE. |
| `d1_lacuna_tsee` | Dimensão 1, lacuna proporcional da Tarifa Social. |
| `conta_estimada` | Conta estimada para 100 kWh. |
| `d2_peso_conta_renda` | Dimensão 2, peso da conta estimada na renda de referência. |
| `d3_qualidade` | Dimensão 3, maior razão entre `dec_rel` e `fec_rel`. |
| `d4_vulnerabilidade_territorial` | Dimensão 4, proporção de domicílios em favela. |
| `n_d1_lacuna_tsee` | Dimensão 1 normalizada em 0 a 100. |
| `n_d2_peso_conta_renda` | Dimensão 2 normalizada em 0 a 100. |
| `n_d3_qualidade` | Dimensão 3 normalizada em 0 a 100. |
| `n_d4_vulnerabilidade_territorial` | Dimensão 4 normalizada em 0 a 100. |
| `n_dimensoes_validas` | Número de dimensões disponíveis para o município. |
| `ipem` | Índice final, calculado como média das quatro dimensões normalizadas quando todas estão presentes. |
| `ipem_dois_piores` | Média das duas dimensões normalizadas de maior severidade. |
| `dois_piores_indicadores` | Rótulos curtos das duas dimensões de maior severidade. |
| `ranking` | Posição nacional, com 1 para maior IPEM. |
| `faixa` | Faixa ordinal do IPEM: Baixa, Média, Alta ou Muito alta. |
| `subsidio_por_familia` | Subsídio TSEE médio por beneficiário registrado. |
