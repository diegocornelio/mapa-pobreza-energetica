# Limites

Esta lista é parte do resultado, não ressalva de rodapé. Um número entregue sem os seus
limites transfere ao leitor um risco que quem calculou já conhecia.

---

## Ausências declaradas

Quando uma fonte não cobre um município, o campo diz que não sabe. Nenhum deles recebe
zero.

| | municípios | o que significa |
|---|---|---|
| Sem apuração de DEC/FEC | **14** | não há conjunto consumidor vinculado ao município na base de continuidade de 2024 |
| Subsídio indisponível | **32** | a CDE ficou líquida negativa no mês de referência; nenhuma cifra em reais é exibida |
| Sobrecobertura | **80** | há mais benefícios ativos que famílias elegíveis |
| Sem favela identificada | **4.915** | o Censo 2022 percorreu o território e não identificou nenhuma — este zero é medição, não ausência |

---

## Limites que atravessam todas as medidas

**Não identifica ninguém.** Todas as bases são agregadas por município e assim
permanecem. Nada aqui permite chegar a uma família, a um endereço ou a uma unidade
consumidora. O arquivo da CDE traz o CPF mascarado na origem, o que inclusive impede a
deduplicação de beneficiários.

**Não estabelece causa.** As medidas descrevem contexto municipal. Nenhuma explica por
que uma família não é atendida, e nenhuma autoriza inferência sobre conduta de qualquer
pessoa ou sobre furto de energia.

**A ausência do benefício pode ser cadastral.** Parte da diferença entre elegíveis e
beneficiários pode ser defasagem de cadastro, e não privação. Os dados não separam as
duas coisas. A primeira ação que eles sustentam é verificação local, não campanha.

**As bases têm 20 meses de defasagem entre si.** O CECAD é de agosto de 2026; a CDE, de
dezembro de 2024. A contagem de não atendidas compara dois estoques em datas diferentes.

**Unidade consumidora não é família.** Os 80 municípios com sobrecobertura são a prova
empírica disso. Onde uma família tem mais de uma unidade consumidora, ou onde um
beneficiário deixou de ser elegível sem sair da base, a contagem se desloca.

---

## Limites da conta de energia

**O valor é subestimado.** A tarifa homologada não inclui ICMS nem PIS/COFINS, e o ICMS
varia entre estados, tipicamente de 17% a 30%. A tarifa serve para comparar municípios;
não serve para dizer quanto alguém paga.

**O peso da conta é cenário, e o cenário domina o resultado.** A faixa é larga:

| consumo | peso mediano na faixa de pobreza | municípios acima de 10% |
|---|---|---|
| 30 kWh | 3,66% | 0 |
| **80 kWh** | **9,75%** | **2.392** |
| 100 kWh | 12,19% | 5.031 |

Os 80 kWh são o limiar da Lei 15.235/2025 e a única das três hipóteses com ancoragem
externa. A 30 kWh o problema desaparece; a 100 kWh é quase universal.

**O consumo de referência é conservador.** Invertendo o desconto legal contra o subsídio
que a CDE efetivamente pagou, o consumo mediano de quem já recebe a Tarifa Social é de
cerca de **98 kWh**, não 80. Famílias ainda não atendidas podem consumir de outro modo, e
o dado não separa as duas populações.

**Os vieses do peso da conta apontam em direções opostas e não se cancelam de forma
conhecida.**

| direção | causa |
|---|---|
| subestima | a tarifa não inclui tributos |
| subestima | o cálculo usa o teto da faixa de renda; quem está abaixo sente mais |
| superestima | usa o tamanho médio de domicílio do município, e domicílios pobres tendem a ser maiores |

**Consequência prática: a ordenação entre municípios é confiável; o nível não é.** A
ordenação vem da tarifa real, com 2,53× de amplitude observada.

**O desconto da Tarifa Social é aplicação de regra, não leitura de dado.** É o único
ponto do cálculo em que isso acontece. Se a regra estiver errada, os valores em reais e o
peso com benefício caem junto. A validação está em `docs/VALIDACAO.md`.

---

## Limites da qualidade do fornecimento

**A agregação envolve escolha, e a escolha muda o número.** Ponderando por consumidores,
2.082 municípios estão acima do limite. Pelo critério do pior conjunto, 3.199. Ambos os
valores são publicados, e o ponderado é o adotado.

**A média municipal esconde desigualdade interna.** Um município pode estar dentro do
limite na média e ter um conjunto muito acima. A coluna `d3_max` existe para isso.

**Compensações de DEC/FEC não podem ser somadas.** São valor de conjunto consumidor
replicado entre os municípios que ele atende, sem rateio: 770 valores aparecem em mais de
um município, envolvendo 2.071 municípios. Somar nacionalmente infla 1,20×. Por isso elas
não entram em nenhuma medida — apenas como atributo do conjunto.

**Violação coletiva e compensação individual são coisas distintas.** Os indicadores de
pagamento com prefixo `PG` remetem a indicadores individuais (DIC, FIC, DMIC), apurados
por unidade consumidora. Podem existir sem que o indicador coletivo do conjunto ultrapasse
o limite, e vice-versa. Cruzá-los não produz evidência de prestação de contas.

---

## Limites do território

**A ausência de correlação é entre municípios, não entre domicílios.** A participação de
favela não tem associação detectável com nenhuma medida energética na escala municipal —
nenhuma correlação de ordem passa de 0,09. Isso diz que municípios com mais favela não
têm pior situação energética média. **Não diz nada** sobre a situação de um domicílio
dentro de uma favela comparado a outro fora dela. Concluir o contrário seria falácia
ecológica, e a pergunta exige microdado que estas fontes não fornecem.

---

## Limites das comparações agregadas

**A comparação de cobertura entre estados é hipótese.** Supõe que a defasagem de data e a
diferença de unidade afetam os estados de modo parecido. É plausível — a diferença entre
a melhor e a pior cobertura é grande demais para ser só isso — mas não foi verificada.

**O subsídio não acessado é projeção.** Multiplica o número de não atendidas pelo subsídio
médio pago no próprio município, supondo que a família marginal receberia esse mesmo
valor. Serve para ordem de grandeza orçamentária, não para previsão. Não é calculado para
os 32 municípios com subsídio indisponível.

---

## O que os dados de 2024 ainda podem fazer

A base da CDE é de dezembro de 2024, anterior à gratuidade instituída pela Lei
15.235/2025. Isso costuma ser lido como desatualização; é o contrário.

Todas as fontes permanecem públicas e o cálculo é reprodutível. Repetir o procedimento
com a CDE de 2026 mede, município a município, quantas dessas famílias a lei efetivamente
alcançou — e onde não alcançou. Não existe hoje nada público que faça essa avaliação na
escala municipal.
