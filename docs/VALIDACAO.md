# Validação

Quatro camadas: números de referência para conferir qualquer reexecução, validações contra
fontes externas independentes, testes de coerência interna, e a validação específica da
única regra normativa aplicada.

Os números desta página foram recalculados por caminho independente e comparados com o que
o aplicativo publica. Onde as duas contas divergiram, a divergência está explicada.

---

## 1. Números de referência

Confira qualquer reexecução contra esta tabela. Todos são calculados no navegador a partir
do payload publicado, e nenhum está escrito à mão no código.

### Tarifa Social

| medida | valor |
|---|---|
A leitura do presente casa CadÚnico e CDE na **mesma data**, março de 2026. Os valores de
dezembro de 2024 existem para a comparação temporal, e não para o presente.

| medida | mar/2026 | dez/2024 |
|---|---|---|
| Famílias elegíveis (CadÚnico do próprio mês) | **27.829.478** | 27.883.284 |
| Benefícios ativos (CDE do próprio mês) | **17.403.015** | 17.882.926 |
| **Não atendidas** | **10.440.849** | 10.028.764 |
| Cobertura nacional | **62,53%** | 64,13% |
| Municípios com sobrecobertura | **35** | — |

A contagem de não atendidas soma as diferenças positivas por município; pelo saldo líquido
o valor de mar/2026 seria 10.426.463, e a diferença é o excesso dos 35 municípios com mais
benefícios que famílias elegíveis. Ver `docs/METODO.md`, item 01b.

**Por que a base mudou.** Até uma versão anterior, a leitura do presente cruzava o CadÚnico
de agosto de 2026 com a CDE de dezembro de 2024, vinte meses de defasagem, enquanto a página
de comparação afirmava que cada data usa o CadÚnico do seu próprio mês. As duas coisas não
podiam ser verdade ao mesmo tempo, e a contradição aparecia na tela: o mesmo município exibia
64,9% numa tabela e 81,8% no cartão ao lado. Casar as datas também reduziu a sobrecobertura de
80 para 35 municípios, o que mostra que mais da metade daquela anomalia era artefato da
defasagem, e não a diferença entre unidade consumidora e família.

O CadÚnico nacional do SAGI em março de 2026 soma 27.829.708, que excede a soma municipal em
**230**: o SAGI cobre 5.571 municípios, um a mais que a malha do Censo 2022. O excedente é
Boa Esperança do Norte (MT, IBGE 5101837), instalado depois do Censo.

### Conta de energia

| medida | valor |
|---|---|
| Tarifa residencial, faixa nacional | R$ 0,4241 a R$ 1,0738 por kWh |
| Amplitude | 2,53× |
| Conta de 80 kWh, tarifa cheia, mediana | R$ 59,53 |
| Conta de 80 kWh com Tarifa Social, mediana | R$ 26,33 |
| Peso na faixa de pobreza a 80 kWh, sem benefício | mediana 9,75%, acima de 10% em 2.392 municípios |
| Fração da conta coberta, dez/2024 | 58,19% |
| Fração da conta coberta, mar/2026 | 88,11% |
| Municípios com ganho | 5.427 de 5.441, ou 99,74% |

A fração da conta coberta entra apenas nos municípios com subsídio positivo nas duas datas.
Os 129 restantes têm CDE líquida negativa em ao menos uma delas, e o valor não é utilizável.

### Continuidade do fornecimento

| medida | valor |
|---|---|
| Municípios acima do limite em 2024 | 2.082 de 5.555 |
| Municípios acima do limite em 2025 | 1.787 |
| **Acima do limite nos dois anos** | **1.412** |
| Deixaram de passar do limite | 670 |
| Passaram a ficar acima | 375 |
| Dentro do limite nos dois anos | 3.098 |
| DEC anual mediano, 2024 | 12,13 h |
| DEC acumulado jan a jun, ponderado | 5,16 h em 2024, 4,63 em 2025, 4,36 em 2026 |
| Tendência 2024 a 2026 | 3.303 melhoraram, 860 estáveis, 1.172 pioraram |
| Sem apuração de continuidade | 15 municípios |

### CadÚnico e comparação temporal

| medida | dez/2024 | mar/2026 |
|---|---|---|
| Famílias em situação de pobreza | 20.298.905 | 19.358.045 |
| Famílias em baixa renda | 7.584.379 | 8.471.663 |
| Famílias até meio salário mínimo por pessoa | 27.883.284 | 27.829.708 |
| CadÚnico total | 41.539.082 | 42.242.445 |

Saíram da faixa de pobreza: **940.860**. Variação do universo elegível: **−0,19%**.

### Distribuidoras

| medida | valor |
|---|---|
| Grupo Enel, variação de benefícios | −736.756 |
| Grupo EDP | −68.029 |
| Demais 98 distribuidoras | +325.021 |
| Municípios atendidos por duas concessionárias | 56 |
| Destes, com uma subindo e outra caindo | 29 |

A variação nacional somada por distribuidora dá −479.764; somada por município, −479.911.
A diferença de 147 vem de códigos municipais da CDE fora da malha do IBGE de 2022.

### Território

| medida | valor |
|---|---|
| Municípios com favela mapeada | 655 |
| Participação mediana nesses municípios | 4,19% |
| Participação no Rio de Janeiro | 20,8% |
| Participação em São Paulo | 13,6% |

---

## 2. Validações contra fontes externas

Cada uma compara um resultado do pipeline com um valor publicado de forma independente.
Nenhuma delas passava antes das correções.

| resultado do pipeline | referência externa |
|---|---|
| DEC anual ponderado mediano de **12,13 h** | média nacional publicada, cerca de 12 h/ano |
| **91,1 milhões** de consumidores em `NumCon` | parque nacional, cerca de 92 milhões |
| **202,0 milhões** de moradores no SIDRA 10296 | população do Censo 2022, excluídos pensionistas e empregados domésticos |
| favela no Rio em **20,8%** e em São Paulo em **13,6%** | valores divulgados pelo IBGE para o Censo 2022 |
| **17.883.087** linhas de `SubsBaixaRenda` em dez/2024 | 17.882.926 pelo pipeline, com 3 municípios filtrados |
| CadÚnico do SAGI contra o painel CECAD, ago/2026 | **idênticos nos 5.570 municípios**, nas quatro variáveis |

A última merece nota. O painel CECAD é raspado em 5.598 arquivos HTML; a série do SAGI vem
por uma requisição de API. As duas coincidem em cada município, o que valida a substituição
da raspagem pela API e habilita a série histórica.

---

## 3. Coerência interna

Catorze invariantes verificados sobre o payload publicado, todos passando:

- cobertura e parcela descoberta somam 100 em cada município
- não atendidas é igual a elegíveis menos benefícios, onde a diferença é positiva
- as quatro situações de continuidade somam o total de municípios com dado
- municípios acima do limite em 2024 é igual a reincidentes mais os que saíram
- municípios acima do limite em 2025 é igual a reincidentes mais os que entraram
- pobreza mais baixa renda é igual a elegíveis, nas duas datas
- saíram da pobreza é igual à queda da faixa entre as datas
- Enel mais EDP mais demais é igual à variação nacional, com folga de malha
- melhoraram, estáveis e pioraram somam os municípios com dado de tendência
- a fração da conta coberta é reproduzível a partir do payload
- a conta com Tarifa Social é menor que a conta cheia em todos os municípios
- a economia é igual à conta cheia menos a conta social
- o peso com benefício é menor que o peso sem benefício em todos os municípios
- as medidas são independentes entre si, conforme a tabela abaixo

### Independência entre as medidas

Testada explicitamente, porque é o que justifica não haver índice composto.

| par | Spearman |
|---|---|
| não atendidas × qualidade do fornecimento | −0,098 |
| participação de favela × não atendidas | −0,011 |
| participação de favela × peso da conta | −0,033 |
| participação de favela × razão DEC/FEC | +0,014 |
| participação de favela × DEC anual | −0,086 |
| renda × taxa de suspensão por inadimplência | −0,086 |

A sobreposição dos piores quartis de não atendidas e de qualidade fica em **0,86 vez** o que
o acaso produziria.

### Estabilidade do índice composto rejeitado

Retirando duas das quatro dimensões, apenas **7 dos 100** primeiros colocados permaneciam no
topo, com deslocamento mediano acima de mil posições.

### Granularidade dos encaminhamentos

Um desenho baseado em regras de exceção produzia caixa vazia em 1.322 municípios e mediana de
um item. O desenho por bandas produz 4 a 7 encaminhamentos por município, com 191 assinaturas
distintas e maior grupo em 15,3%.

---

## 4. Validação do desconto da Tarifa Social

O desconto escalonado da Lei 12.212/2010 é a **única aplicação de regra normativa** em todo o
cálculo. Se a regra estiver errada, os valores em reais e o peso com benefício caem junto.

### Teste por inversão

Partindo do subsídio que a CDE efetivamente pagou por família em cada município, e da tarifa
da subclasse Baixa Renda, resolve-se para o consumo que a regra implica.

| | valor |
|---|---|
| consumo implícito, mediana | **97,7 kWh** |
| p05 · p25 · p75 · p95 | 79,9 · 90,0 · 119,0 · 147,8 kWh |
| fração entre 40 e 150 kWh | **95,8%** |
| municípios fora do intervalo resolvível | 14 de 5.538 |

O resultado é fisicamente plausível para consumo residencial de baixa renda. Uma regra errada
por um fator produziria consumo implícito absurdo, algo como 300 kWh ou 15 kWh.

### Teste de escala

Se a regra vale, o subsídio deve ser proporcional à tarifa, e a razão entre os dois deve ser
aproximadamente constante entre municípios.

| | valor |
|---|---|
| Spearman(subsídio por família, tarifa Baixa Renda) | **+0,755** |
| coeficiente de variação do subsídio bruto | 0,143 |
| coeficiente de variação do subsídio ÷ tarifa | **0,093** |
| razão mediana, em kWh-equivalente descontado | 46,6 |

Normalizar pela tarifa reduz a dispersão entre municípios em **35%**, o que só acontece se a
tarifa for de fato um fator multiplicativo do subsídio, como a regra prevê. E o fecho interno:
a 97,7 kWh a regra prevê 0,65 × 30 mais 0,40 × 67,7, que dá **46,6** kWh descontados,
exatamente a razão mediana observada.

### Um argumento anterior, descartado

Chegou-se a argumentar que a economia calculada, de R$ 33,20 por família ao mês, convergia com
o subsídio observado na CDE, de R$ 30,03, e que isso validaria a regra. **O argumento é
inválido:** são grandezas diferentes. A CDE reembolsa o desconto escalonado, que a 80 kWh vale
R$ 25,68; a economia da família inclui também a mudança de subclasse tarifária, R$ 7,51. Os
números ficaram próximos porque dois erros se cancelaram parcialmente, já que o consumo suposto
era baixo demais e a economia incluía parcela que a CDE não cobre.

O registro fica porque um erro de raciocínio corrigido é informação para quem vier depois.

---

## 5. Divergências encontradas na auditoria

Cinco, todas corrigidas. Nenhuma alterou conclusão; todas eram de reprodutibilidade ou de
coerência interna.

| | o que era | como ficou |
|---|---|---|
| Fração coberta não reproduzível | o número publicado vinha de base filtrada em 5.441 municípios, e o payload trazia 5.569 | o aplicativo calcula ao vivo, com o filtro declarado e a base visível |
| Definição de não atendidas | saldo líquido e soma das positivas divergiam em 30.058 sem que a escolha estivesse escrita | declarada em `docs/METODO.md`, item 01b |
| Variação nacional de benefícios | −479.764 por distribuidora e −479.911 por município | declarada em `docs/LIMITES.md` |
| Precisão do payload | três casas decimais não reproduziam a mediana de 88,11% | cinco casas |
| Saíram da pobreza | 940.966 pela soma municipal | 940.860 pelo agregado direto do SAGI |

Havia ainda uma inconsistência de tela: o título da página inicial trazia o valor de março de
2026 e a linha logo abaixo trazia o de dezembro de 2024, sem que a diferença de data estivesse
dita. As duas foram unificadas na data mais recente.

---

## 6. Scripts de validação

Em `reconstrucao/pipeline/`, fora do encadeamento principal:

| script | o que verifica |
|---|---|
| `valida_numeros.py` | recalcula os números de referência por caminho independente |
| `valida_desconto.py` | teste por inversão e teste de escala, seção 4 |
| `valida_decomposicao.py` | decomposição da economia em subclasse e desconto |
| `valida_territorio.py` | correlações da participação de favela, seção 3 |
| `valida_granularidade.py` | distribuição das combinações de encaminhamento |

---

## Pendências

**Correlação com IDHM.** Nunca incorporada. Permanece declarada como pendente, sem valor
substituto.

**Reexecução completa a partir de `reconstrucao/pipeline/`.** Os scripts foram parametrizados
e compilam, e produziram os números desta página em execução ad hoc. A execução de ponta a
ponta a partir daquele diretório ainda não foi feita. A primeira deve conferir contra a seção
1, e qualquer divergência é defeito de porte, não de dado.
