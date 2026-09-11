# Dicionário de dados

`reconstrucao/dados/municipios_corrigido.csv` — 5.570 linhas, 35 colunas, uma por
município. Chave: `cod_ibge`. Codificação UTF-8, separador vírgula, decimal ponto.

Campo vazio significa ausência de dado, nunca zero. Ver `docs/LIMITES.md`.

## Identificação

| coluna | tipo | descrição |
|---|---|---|
| `cod_ibge` | inteiro | código municipal IBGE de 7 dígitos |
| `nome` | texto | nome do município na malha IBGE 2022 |
| `uf` | texto | sigla da unidade da federação |
| `distribuidora` | texto | distribuidora com mais unidades consumidoras ativas no município, INDGER 2024 |

## Cadastro Único e Tarifa Social

Fonte: painel municipal do CECAD (ago/2026) e beneficiários da CDE (dez/2024).

| coluna | tipo | descrição |
|---|---|---|
| `familias_cadastradas` | inteiro | famílias no CadÚnico do município |
| `familias_pobreza` | inteiro | famílias na faixa de pobreza, até R$ 218 por pessoa (Decreto 11.566/2023, vigente na data da leitura) |
| `familias_baixa_renda` | inteiro | famílias na faixa de baixa renda, até meio salário mínimo por pessoa (R$ 810,50 em março de 2026) |
| `familias_elegiveis` | inteiro | soma das duas faixas acima, que são as que dão direito à Tarifa Social |
| `beneficiarios_tsee` | inteiro | linhas de benefício `SubsBaixaRenda` na CDE; são unidades consumidoras, não famílias |
| `cobertura` | número | `100 × beneficiarios_tsee ÷ familias_elegiveis` |
| `lacuna_pos` | inteiro | famílias não atendidas: `familias_elegiveis − beneficiarios_tsee`, com piso zero |
| `sobrecobertura` | 0 ou 1 | 1 quando há mais benefícios que famílias elegíveis; 80 municípios |

## Subsídio da CDE

Valores mensais, referência dezembro de 2024. Ver `docs/CORRECOES.md` § C4.

| coluna | tipo | descrição |
|---|---|---|
| `subs_liquido` | número | subsídio bruto menos estornos, em reais; pode ser negativo |
| `subsidio_familia_liq` | número | `subs_liquido ÷ beneficiarios_tsee` |
| `rs_nao_acessado` | número | cenário: `lacuna_pos × subsidio_familia_liq`. Projeção, não medição |
| `subsidio_indisponivel` | 0 ou 1 | 1 quando `subs_liquido` é negativo; 32 municípios. Nenhuma cifra em reais deve ser usada |

## Tarifa e conta

Tarifa B1 residencial convencional, base "Tarifa de Aplicação", vigente em dez/2024,
ponderada por unidades consumidoras ativas. **Sem ICMS e sem PIS/COFINS.**

| coluna | tipo | descrição |
|---|---|---|
| `tarifa_municipal` | número | tarifa da subclasse Residencial, em reais por kWh |
| `tarifa_baixa_renda` | número | tarifa da subclasse Baixa Renda. É a **base** sobre a qual o desconto incide, não a conta final |
| `rank_tarifa` | inteiro | posição nacional por `tarifa_municipal`, 1 é a mais cara |
| `conta_cheia80` | número | `tarifa_municipal × 80` |
| `conta_social80` | número | `tarifa_baixa_renda × 80 × 0,50625`, com o desconto escalonado da Lei 12.212/2010 |
| `econ_mes` | número | `conta_cheia80 − conta_social80`: economia mensal da família |

## Renda e peso da conta

Renda: SIDRA 10296 do Censo 2022, média aproximada por pontos médios das faixas.

| coluna | tipo | descrição |
|---|---|---|
| `renda_referencia` | número | rendimento nominal mensal domiciliar **por pessoa**, em reais |
| `moradores_por_domicilio` | número | moradores (SIDRA 10296) ÷ domicílios (SIDRA 4712) |
| `peso_pob80_cheia` | número | fração da renda domiciliar no teto da faixa de pobreza que a conta de 80 kWh consome, sem benefício |
| `peso_social_ef` | número | o mesmo, com o desconto escalonado aplicado |

Denominador dos dois pesos: `LINHA_POBREZA × moradores_por_domicilio`, com a linha de
pobreza em `_paths.py` e publicada no payload como `lp`, junto da data `lpv` em que
passou a valer. É valor nominal, não indexado: ver a ressalva em `docs/METODO.md`.

## Qualidade do fornecimento

DEC e FEC de 2024 somados nos doze meses, sobre o limite anual do conjunto, agregados ao
município pela ponte IndQual e ponderados por consumidores.

| coluna | tipo | descrição |
|---|---|---|
| `dec_h_ano` | número | horas de interrupção por unidade consumidora no ano, ponderado |
| `d3_corr` | número | razão entre o apurado e o limite; valor 1,00 é a fronteira regulatória |
| `d3_max` | número | mesma razão no pior conjunto que atende o município |
| `n_conj` | inteiro | conjuntos consumidores que atendem o município |
| `violacao` | 0 ou 1 | 1 quando `d3_corr ≥ 1`. Vazio nos 14 municípios sem apuração |

Quando `d3_corr < 1` e `d3_max ≥ 1`, há desigualdade interna: o município está dentro do
limite na média, mas ao menos um conjunto está acima.

## Território

Censo 2022, na espécie particular permanente ocupado nos dois lados da divisão.

| coluna | tipo | descrição |
|---|---|---|
| `dom_favela` | inteiro | domicílios em favelas e comunidades urbanas, SIDRA 9887 variável 9909 |
| `dom_total_mun` | inteiro | domicílios do município, SIDRA 4712 variável 381 |
| `d4_corr` | número | `dom_favela ÷ dom_total_mun` |
| `favela_mapeada` | booleano | verdadeiro nos 655 municípios com favela identificada pelo Censo |

Onde `favela_mapeada` é falso, o zero é medição: o IBGE percorreu o território e não
identificou favela. **Esta medida não é dimensão de vulnerabilidade energética** — ver
`docs/METODO.md` § 5.

---

## Colunas que existiram e foram removidas

| coluna | por quê |
|---|---|
| `peso_pob80_social` | usava a tarifa Baixa Renda sem o desconto escalonado, subestimando o benefício. Superada por `peso_social_ef` |
| `ipem`, `ranking`, `faixa`, `n_d1`…`n_d4` | pertenciam ao índice composto, rejeitado. Ver `docs/METODO.md` |
| `compensacoes_decfec_reais` | valor de conjunto replicado sem rateio entre municípios; somar infla 1,20× |
| `tarifa_flag_estimativa`, `distribuidoras_usadas` | descreviam a tarifa constante nacional, substituída pela tarifa municipal real |

As colunas do dataset anterior permanecem em `data/processed/ipem_municipios.csv`, para
que a comparação entre as duas versões seja auditável.
