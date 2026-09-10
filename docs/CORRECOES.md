# Correções

Seis defeitos estruturais foram encontrados na versão anterior deste trabalho, ao
auditá-la contra os arquivos brutos. Todos os seis alteravam o resultado, e três
alteravam a conclusão.

Cada correção traz a prova que a sustenta. A prova está sempre no dado, não no
argumento — é essa a diferença entre corrigir e trocar de opinião.

---

## C1 — A interrupção era comparada na periodicidade errada

**Defeito.** O DEC e o FEC apurados eram divididos pelo limite regulatório na
periodicidade errada: média mensal sobre limite anual.

**Prova.** No arquivo `indicadores-continuidade-coletivos-2020-2029.parquet`, a coluna
`NumPeriodoIndice` assume **apenas os valores 1 a 12** — são meses, e não existe registro
anual. Todas as 6.264 séries de DEC e FEC de 2024 têm exatamente 12 períodos. Já o
`VlrLimite`, no arquivo de limites, vem indexado por `AnoLimiteQualidade`: é anual, com
mediana de 10 h para DEC e 7 para FEC.

**Efeito.** O indicador ficava comprimido por volta de um doze avos, e a razão nunca
passava de 0,49 em nenhum dos 5.570 municípios — ou seja, o cálculo anterior concluía
que **nenhum município do Brasil descumpria o limite de continuidade**.

| | antes | depois |
|---|---|---|
| DEC apurado mediano | — | 9,30 h/ano |
| razão mediana sobre o limite | 0,0715 | 0,8583 |
| conjuntos violando o limite de DEC | **0** | **952 de 3.132** |
| conjuntos violando o limite de FEC | **0** | **432** |

**Correção adicional, na agregação.** A ponte conjunto→município usa o IndQual, e a
agregação passou a ser **ponderada pelo número de consumidores** de cada conjunto
(`SigIndicador = NumCon`, 91,1 milhões de unidades no total, compatível com o parque
nacional). A escolha importa: o Rio de Janeiro é atendido por 78 conjuntos, e o pior
deles está a 6,19× o limite enquanto a média ponderada fica em 0,93×. Pelo critério do
pior conjunto seriam 3.199 municípios em violação; ponderando, são 2.082. O valor do
pior conjunto continua publicado como coluna auxiliar, porque identifica desigualdade
interna ao município.

---

## C2 — A tarifa era uma constante nacional

**Defeito.** Todos os 5.570 municípios recebiam a mesma tarifa, R$ 0,695701 por kWh,
descrita como mediana nacional.

**Prova.** A coluna `conta_estimada` do CSV anterior é constante. Logo o peso da conta
na renda era `69,5701 ÷ renda`: uma função estritamente decrescente da renda, com
correlação de ordem de **−1,000000** e erro absoluto máximo **zero**. Nenhuma informação
tarifária entrava na comparação entre municípios.

Consequência colateral: como a normalização min-max satisfaz min-max(k·x) = min-max(x),
mudar o consumo de referência de 100 para 80 ou 150 kWh **não alterava nenhuma posição
do ranking**. A análise de sensibilidade prometida era matematicamente vazia.

**Correção.** Tarifa B1 residencial convencional, subclasse Residencial, base "Tarifa de
Aplicação", vigente em dezembro de 2024 — 103 distribuidoras. A ponte para o município
usa o INDGER, casando **por `NumCNPJ` e não por `SigAgente`**: pelo nome do agente casam
560 municípios; pelo CNPJ, os 5.570. Média ponderada por `QtdUCAtiva`, já que 9,9% dos
municípios têm mais de uma distribuidora.

**Efeito.** Tarifa municipal de **R$ 0,4241 a R$ 1,0738 por kWh, amplitude de 2,53×**.

---

## C3 — A participação de favela media outra coisa

**Defeito.** O denominador não era o município.

**Prova.** No SIDRA 9887, a variável **1009909** chama-se "Domicílios em favelas e
comunidades urbanas — percentual do total geral", e esse total geral é o universo **das
favelas**, repartido por espécie de domicílio. O pipeline anterior recuperava esse total
a partir do percentual e depois dividia um pelo outro, de modo que o indicador
**reproduzia literalmente a variável 1009909**: a fração dos domicílios de favela que são
"particular permanente ocupado". Daí o valor girar em torno de 0,84 em toda parte —
mediana de 0,842, com 98,5% dos casos acima de 0,5 — e São Paulo aparecer com 89,8% dos
seus domicílios em favela.

Somado a isso, um `fillna(0)` atribuía zero a 4.915 municípios (88,2%), misturando "não
tem favela" com "não foi medido". Como era a única dimensão com preenchimento, a coluna
`n_dimensoes_validas` era constante igual a 4 e a trava das quatro dimensões nunca atuava.

**Correção.** Denominador da tabela **SIDRA 4712, variável 381** — domicílios
particulares permanentes ocupados, mesma espécie do numerador, disponível para os 5.570
municípios.

| | antes | depois |
|---|---|---|
| Rio de Janeiro | 0,880 | **0,208** |
| São Paulo | 0,898 | **0,136** |
| Belo Horizonte | 0,883 | **0,120** |
| Brasília | 0,843 | **0,063** |
| Belém | 0,815 | **0,556** |
| Manaus | 0,870 | **0,539** |

Nos 655 municípios com favela mapeada: mediana de 4,19%, máximo de 69,6%. Os valores
passam a ser compatíveis com o que o IBGE divulgou. Com o denominador certo, o zero dos
demais 4.915 municípios torna-se um zero legítimo, porque o Censo 2022 percorreu todo o
território e identificou favela em 655.

---

## C4 — O subsídio negativo era zerado

**Defeito.** A coluna de subsídio da CDE era clipada em zero.

**Prova.** O clip zerava 32 municípios, entre eles **11 dos 13 da Baixada Fluminense** —
o recorte-piloto do projeto anterior — e o **Rio de Janeiro**, que é o maior contingente
de famílias não atendidas do país.

Processando as 18,3 milhões de linhas da CDE de dezembro de 2024 (17.883.087 delas com
`DscTipoSubsidio = SubsBaixaRenda`), verifica-se que os valores negativos são estornos e
aparecem em **3.383 municípios**, não apenas na área de uma concessionária.

**Efeito.**

| | valor |
|---|---|
| bruto positivo | R$ 532.269.488,83 |
| estornos | −R$ 29.526.873,15 |
| líquido | R$ 502.742.615,68 |
| total que o clip produzia | R$ 528,5 mi, **R$ 25,8 mi acima do real** |

**Correção.** Bruto, estornos e líquido em colunas separadas. Onde o líquido é negativo,
o campo recebe `subsidio_indisponivel` e nenhuma cifra em reais é exibida para o
município — o aplicativo escreve "indisponível", não "zero".

---

## C5 — A renda usada não era a que paga a conta

**Defeito.** A conta de energia era dividida pela renda **per capita**.

**Prova.** A conta é paga pelo domicílio, não por indivíduo. O tamanho médio do
domicílio varia de **2,29 a 5,87 moradores** entre municípios brasileiros — amplitude
de 2,56× —, e é maior justamente no Norte. Dividir a conta pela renda por pessoa
penalizava sistematicamente as regiões de domicílio grande.

**Correção.** Renda domiciliar = renda per capita × moradores por domicílio, com o
tamanho do domicílio calculado como moradores (SIDRA 10296) ÷ domicílios (SIDRA 4712).

**Efeito colateral que mudou a leitura.** Com o denominador correto, a média municipal
do peso da conta cai para 2,32% e **nenhum município cruza o limiar de 10%**. Isso não é
um resultado menor: significa que **média municipal não detecta pobreza energética**,
porque o fenômeno é intradomiciliar e desaparece na agregação. O que revela alguma coisa
é o cálculo sobre a faixa de renda elegível, usando os tetos oficiais do CadÚnico.

---

## C6 — A tarifa social publicada é a base, não a conta

**Defeito.** A conta com Tarifa Social usava a tarifa da subclasse Baixa Renda tal como
publicada, que está apenas 14,1% abaixo da residencial.

**Prova.** O desconto legal da Tarifa Social a 80 kWh é de 49,4%, não de 14,1%. As linhas
"Residencial Tarifa Social – faixa 01" e "faixa 02" do arquivo de tarifas são
**idênticas** à linha "Baixa Renda", o que confirma que a ANEEL publica a **base
tarifária** da subclasse, e não a tarifa efetiva. O desconto escalonado incide sobre ela
na fatura.

**Correção.** Desconto da Lei 12.212/2010, aplicado por faixa e de forma cumulativa:
65% nos primeiros 30 kWh, 40% de 31 a 100, 10% de 101 a 220.

```
conta social = tarifa Baixa Renda × (30×0,35 + 50×0,60) , para 80 kWh
```

**Esta é a única aplicação de regra normativa em todo o cálculo.** Todo o resto é
leitura de dado. Por isso ela recebeu validação própria, descrita em `docs/VALIDACAO.md`.

**Efeito.**

| | antes | depois |
|---|---|---|
| conta de 80 kWh com o benefício, mediana | R$ 52,02 | **R$ 26,33** |
| peso na faixa de pobreza, mediana | 8,50% | **4,30%** |
| municípios acima de 10% com o benefício | 489 | **0** |

A leitura de política pública muda com isso: **sem o benefício, a conta cruza o limiar
de 10% em 2.392 municípios; com ele, em nenhum.** O instrumento funciona onde chega, e o
problema é a cobertura.

---

## Um argumento de validação que foi descartado

Registrado aqui porque a auditoria vale para o próprio trabalho.

Para sustentar C6, chegou-se a argumentar que a economia calculada (R$ 33,20 por família
ao mês) convergia com o subsídio observado na CDE (R$ 30,03), e que essa proximidade
entre fontes independentes validaria a regra.

**O argumento é inválido.** São grandezas diferentes. A CDE reembolsa o desconto
escalonado, que a 80 kWh vale R$ 25,68; a economia total da família inclui também a
mudança de subclasse tarifária, R$ 7,51. Os dois números ficaram próximos porque dois
erros se cancelaram parcialmente: o consumo suposto de 80 kWh é baixo demais — o consumo
implícito real é de cerca de 98 kWh — e a economia incluía uma parcela que a CDE não
cobre.

O argumento foi substituído pelo teste de inversão descrito em `docs/VALIDACAO.md`, que
compara as grandezas certas.
