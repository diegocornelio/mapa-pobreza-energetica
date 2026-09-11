# Método

Quatro medidas, calculadas separadamente sobre os 5.570 municípios. Não há índice
composto, e a ausência dele é decisão metodológica, não omissão — a justificativa está
na última seção.

Cada medida abaixo traz a fórmula, a fonte e a razão da escolha. Os defeitos corrigidos
em relação à versão anterior estão em `docs/CORRECOES.md`; os limites de cada medida, em
`docs/LIMITES.md`.

---

## 1. Famílias não atendidas pela Tarifa Social

```
não atendidas = (famílias em pobreza + famílias em baixa renda) − linhas de benefício TSEE
```

O minuendo vem do painel municipal do CECAD, nas duas faixas que dão elegibilidade à
Tarifa Social. O subtraendo vem do arquivo de beneficiários da CDE, filtrado por
`DscTipoSubsidio = SubsBaixaRenda` e agregado por `CodIbgeMunicipio`.

**Por que linhas de benefício e não pessoas.** O `NumCPFCNPJCliente` vem mascarado no
arquivo aberto, o que impede deduplicação. A contagem usa linhas, e cada linha
corresponde a uma unidade consumidora beneficiária no mês de referência.

**A contagem tem sinal de erro conhecido e publicado.** Em 80 municípios há mais
benefícios ativos que famílias elegíveis. Isso não é ruído: é a evidência empírica de
que unidade consumidora não equivale a família. Esses municípios recebem
`sobrecobertura = 1` em vez de serem zerados.

A leitura do presente casa as duas pontas em março de 2026: o CadÚnico vem da competência
202603 do SAGI e os benefícios do arquivo da CDE de 01mar2026, o único mês de 2026 que traz
as 103 distribuidoras. Uma versão anterior cruzava CadÚnico de agosto de 2026 com CDE de
dezembro de 2024, e a defasagem de vinte meses aparecia como contradição na própria tela.

## 2. Peso da conta na faixa de pobreza

```
peso = (tarifa × 80 kWh) ÷ (R$ 218 × moradores por domicílio)
```

**Por que não a média municipal.** Testada, ela fica em torno de 2,3% e nenhum município
cruza o limiar de 10%. Pobreza energética é fenômeno intradomiciliar e desaparece na
agregação por município. O cálculo só diz algo quando feito sobre a faixa de renda
elegível.

**Por que o teto da faixa.** R$ 218 por pessoa é o teto da faixa de pobreza do CadÚnico,
valor fixado pelo Decreto 11.566/2023 e ainda vigente na data desta leitura. Usar o teto,
e não a renda média da faixa, torna o resultado conservador: quem está abaixo do teto
sente peso maior.

**A linha não é indexada e a tarifa é.** Os R$ 218 são valor nominal que só muda por novo
ato do Executivo, enquanto a tarifa é reajustada todo ano. O peso, portanto, sobe entre
duas leituras sem que nenhuma família tenha empobrecido. Foi o que aconteceu aqui: com a
tarifa de dezembro de 2024 a mediana nacional era 9,75% e 2.392 municípios passavam de
10%; com a de março de 2026, sem que o denominador mudasse, a mediana é 10,50% e são
3.233. A variação mede reajuste tarifário contra linha parada, e não mudança de condição
de vida.

**Por que multiplicar pelo tamanho do domicílio.** O teto é por pessoa, mas a conta é do
domicílio. O tamanho médio vem de moradores (SIDRA 10296) ÷ domicílios (SIDRA 4712) e
varia de 2,29 a 5,87 entre municípios.

**Por que 80 kWh.** É o limiar adotado pela Lei 15.235/2025. É a única das hipóteses de
consumo com ancoragem externa — e o resultado depende inteiramente dela, como
`docs/LIMITES.md` detalha.

## 3. Conta com Tarifa Social

```
conta social = tarifa Baixa Renda × (30 × 0,35 + 50 × 0,60) , para 80 kWh
```

A ANEEL publica a tarifa da subclasse Baixa Renda, que é a **base** sobre a qual o
desconto incide, não a conta final. O desconto da Lei 12.212/2010 é aplicado por faixa e
de forma cumulativa: 65% nos primeiros 30 kWh, 40% de 31 a 100, 10% de 101 a 220. Num
consumo de 80 kWh isso equivale a 49,4%.

**Esta é a única aplicação de regra normativa em todo o cálculo.** Todo o resto é leitura
de dado. Por isso recebeu validação própria, em `docs/VALIDACAO.md`.

## 4. Qualidade do fornecimento

```
razão = (soma dos 12 meses de DEC) ÷ limite anual do conjunto
```

DEC e FEC são publicados por conjunto consumidor, mês a mês — a coluna
`NumPeriodoIndice` assume apenas os valores 1 a 12, e não existe registro anual. O valor
do ano é a soma dos doze meses, comparada ao `VlrLimite` do mesmo conjunto para o mesmo
ano.

**Agregação para o município.** A ponte é o IndQual, e a agregação é **ponderada pelo
número de consumidores** de cada conjunto (`SigIndicador = NumCon`). Um município grande
é atendido por dezenas de conjuntos de tamanhos muito diferentes, e a média simples ou o
pior caso distorcem: o Rio de Janeiro tem 78 conjuntos, com o pior a 6,19× o limite e a
média ponderada em 0,93×.

O valor do pior conjunto continua publicado como coluna auxiliar. Quando a média está
dentro do limite mas o pior conjunto está acima, o município tem desigualdade interna — o
problema tem endereço de bairro, e a média municipal o esconde.

## 5. Território

```
participação = domicílios em favela ÷ domicílios do município
```

Numerador: SIDRA 9887, variável 9909. Denominador: SIDRA 4712, variável 381, na mesma
espécie de domicílio — particular permanente ocupado — nos dois lados da divisão.

**Esta medida não é dimensão de vulnerabilidade energética, e o dado diz por quê.** A
participação de favela foi cruzada com todas as outras medidas e não há associação
detectável: nenhuma correlação de ordem passa de 0,09 nos 5.570 municípios. Municípios
com favela mapeada têm interrupção **menor** (10,3 h contra 12,3 h), porque favela é
fenômeno urbano e rede urbana tem melhor continuidade.

A medida entra como **contexto operacional** — dimensionamento de campo, endereçamento,
vínculo entre domicílio e unidade consumidora — e o resultado nulo é publicado, com a
ressalva de que um nulo entre municípios não é um nulo entre domicílios.

**A nomenclatura é a do IBGE.** "Favelas e comunidades urbanas" é o termo que o instituto
adotou no Censo 2022 em substituição a "aglomerados subnormais". Renomear a variável para
algo como "comunidade vulnerável à pobreza energética" foi avaliado e recusado: afirmaria
relação que o dado contradiz, e quebraria a rastreabilidade até a fonte. Os critérios da
classificação são territoriais e de infraestrutura — irregularidade fundiária, ausência
de serviços públicos, padrão de urbanização — e não critérios de renda nem de energia.

---

## Normalização

As medidas são publicadas em suas unidades próprias — famílias, reais por kWh, horas por
ano, razão sobre o limite, percentual. **Não há normalização min-max nem escala 0 a 100**,
porque não há composição a fazer.

Os mapas usam faixas fixas e declaradas, não quantis, para que a mesma cor signifique o
mesmo valor entre municípios e entre execuções. A razão DEC/FEC usa escala divergente com
o neutro exatamente em 1,00, porque ali está a fronteira regulatória: abaixo é
cumprimento, acima é violação. As demais usam escala sequencial de um só matiz.

## Por que não há índice composto

Um índice das quatro dimensões, com normalização min-max e pesos iguais, foi construído e
testado. **Retirando duas das quatro dimensões, apenas 7 dos 100 primeiros colocados
permaneciam no topo**, com deslocamento mediano acima de mil posições. Um número que muda
tanto conforme a escolha de quem o monta não sustenta decisão de gestão.

Há também razão substantiva, e ela é mais forte que a estatística. As famílias não
atendidas e a qualidade do fornecimento são independentes: a correlação de ordem entre as
duas é de **−0,098**, e a sobreposição dos piores quartis fica em 0,86 vez o que o acaso
produziria. São problemas distintos, em municípios distintos, sob responsabilidades
distintas — assistência social de um lado, regulação de outro. Somá-los num único número
apaga exatamente a informação de que o gestor precisa.

O produto é, por isso, um mapa de medidas separadas, e não um ranking.

## Encaminhamentos por município

O aplicativo apresenta, para cada município, de quatro a sete encaminhamentos. Cada um é
selecionado por um limiar sobre um valor medido daquele município e carrega o número que
o produziu. São classificados em três graus:

| grau | significado |
|---|---|
| **aritmética** | o efeito decorre da definição do indicador ou de tarifa publicada; só estes trazem efeito quantificado |
| **processo** | a ação instaura procedimento previsto em norma, e o resultado depende do procedimento |
| **verificação** | resolve ambiguidade do dado antes de qualquer decisão |

**Nenhum texto afirma que uma ação melhora um indicador por via causal.** O que os itens
de grau "aritmética" afirmam é que cadastrar famílias elegíveis eleva a cobertura por
definição — porque o que se conta é elegíveis menos beneficiários — e que a conta cai de
uma tarifa publicada para outra.

Um desenho anterior, baseado apenas em regras de exceção, deixava 1.322 municípios sem
nenhum encaminhamento e foi descartado. O desenho atual produz 191 assinaturas distintas,
com o maior grupo em 15,3% dos municípios.
