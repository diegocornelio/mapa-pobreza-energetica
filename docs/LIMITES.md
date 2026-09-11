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
| Com conjunto consumidor exclusivo | **47** | nos outros 5.509, o indicador de continuidade é da rede e se repete em outros municípios: mediana de 15 coirmãos, máximo 110 |
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

**A leitura do presente casa as datas; a comparação temporal não pode casar tudo.** O
CadÚnico e a CDE do presente são ambos de março de 2026. A série do CadÚnico é mensal, mas a
da CDE não é utilizável mês a mês: dos cinco meses de 2026 publicados, só março traz as 103
distribuidoras. Por isso o benefício entra na série como pontos, e não como linha.

**Um município do país fica fora do mapa.** A malha do Censo 2022 tem 5.570 municípios e o
CadÚnico atual cobre 5.571. O excedente é Boa Esperança do Norte (MT, IBGE 5101837),
instalado depois do Censo, com 297 famílias elegíveis em agosto de 2026. Ele não aparece em
nenhuma tela.

**Unidade consumidora não é família.** Os 80 municípios com sobrecobertura são a prova
empírica disso. Onde uma família tem mais de uma unidade consumidora, ou onde um
beneficiário deixou de ser elegível sem sair da base, a contagem se desloca.

---

## Limites da conta de energia

**O valor é subestimado, por três exclusões.** A tarifa homologada não inclui ICMS nem
PIS/COFINS, e o ICMS varia entre estados, tipicamente de 17% a 30%. Também **não inclui
bandeira tarifária**: o filtro seleciona a linha `DscDetalhe = "Não se aplica"`, e a
bandeira é adicional cobrado por fora. A tarifa serve para comparar municípios; não serve
para dizer quanto alguém paga.

**A bandeira é o caminho curto entre hidrologia e conta, e está fora da medição.** Sobre a
conta mediana de 80 kWh, que é de R$ 65,76 sem bandeira, o adicional publicado pela ANEEL
leva a R$ 67,27 na amarela, R$ 69,33 na vermelha patamar 1 e **R$ 72,06 na vermelha
patamar 2**, ou 9,6% a mais. O aplicativo publica esse cenário à parte, na página da
conta, e nenhum número do mapa o incorpora.

**Há um repasse hidrológico que o projeto carrega e não consegue separar.** Seria errado
concluir, do parágrafo acima, que a tarifa medida é limpa de hidrologia. O reajuste
tarifário anual transfere ao consumidor a variação dos itens da Parcela A pelo mecanismo da
CVA, Conta de Compensação de Variação de Valores de Itens da "Parcela A", criada pela
Portaria Interministerial MF/MME nº 25, de 24 de janeiro de 2002:

> **Art. 3º** O saldo da CVA deverá ser compensado nas tarifas de fornecimento de energia
> elétrica da concessionária nos 12 (doze) meses subseqüentes à data de reajuste tarifário
> anual, sendo eventual diferença considerada no cálculo do reajuste tarifário seguinte.
>
> **§ 1º** Durante o período de que trata o *caput*, o saldo da CVA não compensado será
> remunerado com base na taxa de juros SELIC para o período, até a data de sua efetiva
> compensação.

**Dois itens registrados na CVA são o canal hidrológico direto.** Os encargos de serviços
de sistema, art. 1º, VII, que sobem quando a estiagem força despacho térmico fora da ordem
de mérito; e os custos de aquisição de energia elétrica, art. 1º, IX, na redação da
Portaria Interministerial nº 361/2004. A compensação financeira pela utilização dos
recursos hídricos, art. 1º, VI, é um terceiro.

**E um quarto item fecha um círculo que interessa diretamente a este trabalho.** A quota de
recolhimento à **Conta de Desenvolvimento Energético**, art. 1º, IV, na redação da Portaria
Interministerial nº 116/2003, é item da CVA. É a mesma CDE que financia o desconto da
Tarifa Social medido neste projeto: a variação do que as distribuidoras recolhem ao fundo
retorna à tarifa de fornecimento em doze meses.

**A consequência para a leitura dos números.** Parte do aumento de 7,36% na tarifa mediana
entre dezembro de 2024 e março de 2026 tem origem hidrológica, e parte tem origem na
própria política de subsídio. **O projeto não decompõe nenhuma das duas.** Quem quiser essa
decomposição precisa dos processos tarifários de cada distribuidora, que não estão aqui.

> **Estado de leitura.** A Portaria Interministerial MF/MME nº 25/2002 foi **lida**, em
> texto consolidado que registra as alterações das Portarias nº 116/2003 e nº 361/2004 e que
> declara não substituir o publicado no D.O. de 25/01/2002. O Submódulo 4.2 do PRORET,
> versão 1.3, que hoje operacionaliza o mecanismo, foi *identificado* na página da ANEEL e
> **não lido**. Nenhum número publicado por este projeto depende desses textos: eles
> sustentam apenas a ressalva de que existe repasse não decomposto.

**O nível do peso da conta é cenário; a ordenação não é.** A faixa do nível é larga:

| consumo | peso mediano na faixa de pobreza | municípios acima de 10% |
|---|---|---|
| 30 kWh | 3,94% | 0 |
| **80 kWh** | **10,50%** | **3.233** |
| 100 kWh | 13,12% | 5.440 |

A coluna da direita está aqui para mostrar por que ela **não é publicada**: uma contagem
que vai de zero a quase todos conforme uma hipótese é função da hipótese, e não do dado.
A coluna do meio, ao contrário, muda de escala mas não de ordem: a correlação de posto
entre o peso a 30 kWh e o peso a 100 kWh é **1,0000**, e nenhum município troca de
posição. O aplicativo publica a ordenação e a faixa; não afirma que um município cruza
um limiar de renda.

Os 80 kWh são o limiar da Lei 15.235/2025 e a única das três hipóteses com ancoragem
externa. A medida de manchete do projeto, a economia em reais, também usa os 80 kWh, mas
não usa renda: não depende da linha de pobreza nem do tamanho do domicílio, e por isso
escapa de dois dos três vieses listados acima.

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
ordenação vem da tarifa real, com 2,32× de amplitude observada.

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

---

## Limites da comparação entre 2024 e 2026

**O arquivo aberto da CDE tem cobertura variável de distribuidoras entre meses, e o dataset
não avisa.** Dos cinco meses de 2026 publicados, apenas março traz as 103 concessionárias:
janeiro tem 99, fevereiro 100, abril 99 e maio 94. Em maio faltam a distribuidora do Distrito
Federal, as de Mato Grosso, Mato Grosso do Sul e Paraíba, e parte do Rio de Janeiro. Quem
comparar dois meses sem conferir a lista de agentes conclui que houve queda de benefícios onde
houve apenas ausência de reporte, e o erro tem direção previsível, porque ausência sempre
parece queda. A comparação publicada usa março de 2026 por essa razão.

**O mesmo vale para a continuidade.** Em 2026, agosto foi reportado por apenas três conjuntos
consumidores e julho por 3.035 de 3.177. A janela comparável entre os três anos é de janeiro a
junho, com 2.995 conjuntos. Uma comparação de janeiro a agosto daria o resultado de três
conjuntos apresentado como nacional.

**A conferência de base precisa preceder qualquer comparação temporal.** Não é acaso: ocorreu
em duas fontes distintas, ANEEL e continuidade, e em mais de um mês.

**A comparação de benefícios é sólida; a de cobertura depende do denominador.** A contagem de
benefícios mede a mesma coisa nas duas pontas. A cobertura usa o CadÚnico de cada data, o que
resolve a defasagem, mas continua sujeita à diferença entre unidade consumidora e família.

**A atribuição de causa à Lei 15.235/2025 é inferência.** Está medido que a parcela da conta
coberta subiu de 58% para 88% e que o número de famílias atendidas não subiu. A magnitude, a
universalidade entre municípios e o patamar de 88% são compatíveis com a gratuidade instituída
pela lei, e é assim que a página apresenta a leitura. Não foi testado contrafactual, nem
descartada mudança de critério contábil da CDE.

**A explicação por melhora de renda foi testada e não se sustenta, o que também tem limite.**
O universo elegível variou −0,19% entre as duas datas, e as 940.860 famílias que saíram da
faixa de pobreza entraram em baixa renda, que preserva o direito. Isso afasta a hipótese no
agregado. Não afasta que ela opere em municípios específicos.

**O teste dos 56 municípios com duas concessionárias indica direção, não magnitude.** São
municípios de fronteira entre concessões, e em geral uma permissionária pequena divide
território com uma grande. A amostra não é aleatória, e a decomposição de variância atribui
96% à distribuidora e 39% ao município, somando mais de 100 porque os dois fatores são
correlacionados: distribuidoras atendem regiões específicas.

---

## O que os dados de 2024 ainda podem fazer

A comparação entre dezembro de 2024 e março de 2026 já foi feita, e está publicada na página
"O que mudou desde 2024". O que permanece aberto é a continuação: a CDE é mensal, e cada nova
competência completa permite estender a série sem trabalho adicional de método.
