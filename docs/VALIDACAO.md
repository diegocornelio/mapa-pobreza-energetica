# Validação

Três camadas: números de referência para conferir qualquer reexecução, validações contra
fontes externas independentes, e a validação específica da única regra normativa aplicada.

---

## 1. Números de referência

Confira qualquer reexecução contra esta tabela. Todos são calculados no aplicativo a
partir do payload, não escritos à mão.

| medida | valor |
|---|---|
| Famílias não atendidas | 9.968.144 |
| Cobertura nacional da Tarifa Social | 64,3% |
| Municípios acima do limite de DEC/FEC | 2.082 de 5.556 com dado |
| DEC anual mediano, ponderado | 12,13 h |
| Tarifa residencial, faixa | R$ 0,4241 a R$ 1,0738 por kWh |
| Peso da conta a 80 kWh, faixa de pobreza, sem benefício | mediana 9,75%, acima de 10% em 2.392 |
| Peso da conta a 80 kWh, com Tarifa Social | mediana 4,30%, acima de 10% em nenhum |
| Economia mediana por família | R$ 33,20 por mês |
| Municípios com favela mapeada | 655 |
| Sem apuração de DEC/FEC | 14 |
| Subsídio indisponível | 32 |
| Sobrecobertura | 80 |
| Encaminhamentos por município | 4 a 7, com 191 assinaturas distintas |

---

## 2. Validações contra fontes externas

Cada uma compara um resultado do pipeline com um valor publicado de forma independente.
Nenhuma delas passava antes das correções.

| resultado do pipeline | referência externa |
|---|---|
| DEC anual ponderado mediano de **12,13 h** | média nacional publicada, cerca de 12 h/ano |
| **91,1 milhões** de consumidores em `NumCon` | parque nacional de unidades consumidoras, cerca de 92 milhões |
| **202,0 milhões** de moradores no SIDRA 10296 | população do Censo 2022, excluídos pensionistas e empregados domésticos |
| favela no Rio em **20,8%** e em São Paulo em **13,6%** | valores divulgados pelo IBGE para o Censo 2022 |
| **17.883.087** linhas de `SubsBaixaRenda` | 17.882.926 contadas pelo pipeline anterior, com 3 municípios filtrados |

---

## 3. Validação do desconto da Tarifa Social

O desconto escalonado da Lei 12.212/2010 é a **única aplicação de regra normativa** em
todo o cálculo. Se a regra estiver errada, os valores em reais e o peso com benefício
caem junto. Por isso ela recebeu teste próprio.

### Teste por inversão

Partindo do subsídio que a CDE efetivamente pagou por família em cada município, e da
tarifa da subclasse Baixa Renda, resolve-se para o consumo que a regra implica.

| | valor |
|---|---|
| consumo implícito, mediana | **97,7 kWh** |
| p05 · p25 · p75 · p95 | 79,9 · 90,0 · 119,0 · 147,8 kWh |
| fração entre 40 e 150 kWh | **95,8%** |
| municípios fora do intervalo resolvível | 14 de 5.538 |

O resultado é fisicamente plausível para consumo residencial de baixa renda. Uma regra
errada por um fator produziria consumo implícito absurdo — algo como 300 kWh ou 15 kWh.

### Teste de escala

Se a regra vale, o subsídio deve ser proporcional à tarifa, e a razão entre os dois deve
ser aproximadamente constante entre municípios — ela é o equivalente em kWh descontados.

| | valor |
|---|---|
| Spearman(subsídio por família, tarifa Baixa Renda) | **+0,755** |
| coeficiente de variação do subsídio bruto | 0,143 |
| coeficiente de variação do subsídio ÷ tarifa | **0,093** |
| razão mediana, em kWh-equivalente descontado | 46,6 |

Normalizar pela tarifa reduz a dispersão entre municípios em **35%**, o que só acontece
se a tarifa for de fato um fator multiplicativo do subsídio, como a regra prevê.

E o fecho interno: a 97,7 kWh a regra prevê 0,65 × 30 + 0,40 × 67,7 = **46,6** kWh
descontados — exatamente a razão mediana observada.

### Um argumento anterior, descartado

Chegou-se a argumentar que a economia calculada (R$ 33,20 por família ao mês) convergia
com o subsídio observado na CDE (R$ 30,03), e que isso validaria a regra. **O argumento é
inválido:** são grandezas diferentes. A CDE reembolsa o desconto escalonado, R$ 25,68 a
80 kWh; a economia da família inclui também a mudança de subclasse tarifária, R$ 7,51. Os
números ficaram próximos porque dois erros se cancelaram parcialmente — o consumo suposto
era baixo demais e a economia incluía parcela que a CDE não cobre.

O registro fica porque um erro de raciocínio corrigido é informação para quem vier
depois.

---

## 4. Testes de coerência interna

**As quatro medidas são independentes entre si.** Testado explicitamente, porque é o que
justifica não haver índice composto.

| par | Spearman |
|---|---|
| não atendidas × qualidade do fornecimento | −0,098 |
| participação de favela × não atendidas | −0,011 |
| participação de favela × peso da conta | −0,033 |
| participação de favela × razão DEC/FEC | +0,014 |
| participação de favela × DEC anual | −0,086 |

A sobreposição dos piores quartis de não atendidas e de qualidade fica em **0,86 vez** o
que o acaso produziria — ou seja, ligeiramente abaixo da independência.

**Estabilidade do índice composto que foi rejeitado.** Retirando duas das quatro
dimensões, apenas **7 dos 100** primeiros colocados permaneciam no topo, com deslocamento
mediano acima de mil posições.

**Granularidade dos encaminhamentos.** Um desenho baseado em regras de exceção produzia
caixa vazia em 1.322 municípios e mediana de 1 item — foi descartado. O desenho por
bandas produz 4 a 7 encaminhamentos por município, com 191 assinaturas distintas e maior
grupo em 15,3%.

---

## 5. Scripts de validação

Em `reconstrucao/pipeline/`, fora do encadeamento principal:

| script | o que verifica |
|---|---|
| `valida_desconto.py` | teste por inversão e teste de escala, seção 3 |
| `valida_decomposicao.py` | decomposição da economia da família em subclasse e desconto |
| `valida_territorio.py` | correlações da participação de favela, seção 4 |
| `valida_granularidade.py` | distribuição das combinações de encaminhamento |

---

## Pendências

**Correlação com IDHM.** Nunca incorporada. Permanece declarada como pendente, sem valor
substituto.

**Reexecução completa a partir de `reconstrucao/pipeline/`.** Os scripts foram
parametrizados e compilam, mas nunca foram executados de ponta a ponta a partir daquela
pasta. A primeira reexecução deve conferir contra a seção 1 desta página, e qualquer
divergência é bug de porte, não de dado.
