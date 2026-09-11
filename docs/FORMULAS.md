# Fórmulas

Toda conta que produz um número publicado: a expressão, o código literal que a
executa, por que ela é válida, a alternativa que foi descartada, a aplicação com
números reais de um município, como ler o resultado e o que a tornaria errada.

## Como este documento se defende

Descrever um cálculo com palavras é fácil, e descrever errado é mais fácil ainda.
Pior: documentação de cálculo envelhece em silêncio, porque alguém corrige uma linha,
o número publicado muda, e o texto continua descrevendo a versão antiga com a mesma
confiança de antes.

Por isso cada bloco de código aqui é precedido de um marcador de origem, e existe um
verificador que compara caractere a caractere com o arquivo:

```
python reconstrucao/pipeline/valida_formulas.py
```

Enquanto ele passar, o que está escrito aqui é o que roda. Se alguém mexer no código
sem mexer no documento, ele falha e diz onde.

## O município de exemplo

Os exemplos usam **São João de Meriti (RJ), IBGE 3305109**, porque ele exercita quase
todas as ramificações: tem contingente grande, cobertura acima da mediana, conta que
peso da conta bem acima da mediana nacional, economia mensal acima da mediana,
continuidade dentro do limite, e favela mapeada. Onde ele não serve, o exemplo diz qual município usa e por
quê.

Nenhum número dos exemplos foi digitado à mão: todos saem dos arquivos intermediários
do próprio pipeline.

---

# 1. Quantos benefícios existem, e quanto a CDE pagou

## A conta

$$\text{benefícios}(m)=\#\{\text{linhas com DscTipoSubsidio}=\texttt{SubsBaixaRenda}\ \wedge\ \text{CodIbgeMunicipio}=m\}$$

$$\text{subsídio}^{+}(m)=\sum_{v>0} v \qquad \text{subsídio}^{-}(m)=\sum_{v<0} v \qquad \text{líquido}(m)=\sum v$$

## O código que a executa

<!-- fonte: reconstrucao/pipeline/01_cde.py 12-21 -->
```python
        c=ch[ch.DscTipoSubsidio.astype(str).str.strip()=="SubsBaixaRenda"].copy()
        if not len(c): continue
        c["v"]=pd.to_numeric(c.VlrSubsidio.astype(str).str.replace(".","",regex=False).str.replace(",",".",regex=False),errors="coerce")
        c["m"]=pd.to_numeric(c.CodIbgeMunicipio,errors="coerce")
        c=c.dropna(subset=["m"]); c["m"]=c.m.astype(int)
        g=c.groupby("m").agg(linhas=("v","size"), pos=("v",lambda s:s[s>0].sum()), neg=("v",lambda s:s[s<0].sum()),
                             n_neg=("v",lambda s:(s<0).sum()), liq=("v","sum"))
        for m,r in g.iterrows():
            a=acc.setdefault(m,[0,0.0,0.0,0,0.0])
            a[0]+=r.linhas; a[1]+=r.pos; a[2]+=r.neg; a[3]+=r.n_neg; a[4]+=r.liq
```

## Por que ela é válida

A pergunta é quantos benefícios da Tarifa Social estão ativos em cada município. O
arquivo da CDE traz uma linha por benefício pago, com o código IBGE do município e o
tipo de subsídio. Contar as linhas do tipo `SubsBaixaRenda` responde exatamente isso,
sem intermediação.

O valor monetário vem em formato brasileiro, com ponto de milhar e vírgula decimal.
As duas substituições convertem para o formato que o `to_numeric` entende. Sem elas,
`1.234,56` viraria nulo e o subsídio do município desapareceria em silêncio.

A leitura é feita em blocos porque o CSV tem 2,3 GB e não cabe na memória; o
dicionário `acc` acumula entre blocos, e é por isso que um município que aparece no
primeiro e no último bloco soma certo.

## A alternativa descartada

Contar **famílias distintas** em vez de linhas. Não é possível: o arquivo traz o CPF
mascarado na origem. A consequência de contar linhas está declarada e é verificável:
onde uma família tem mais de uma unidade consumidora, ela conta mais de uma vez, e é
isso que produz municípios com mais benefícios que famílias elegíveis.

Guardar só o valor líquido também foi descartado. A CDE tem lançamentos de estorno, e
o líquido sozinho esconderia que houve movimento.

## Aplicação: São João de Meriti

| grandeza | valor |
|---|---|
| linhas `SubsBaixaRenda` em dez/2024 | **39.113** |
| soma dos valores positivos | R$ 6.504,66 |
| soma dos valores negativos | −R$ 1.058.493,02 |
| líquido | **−R$ 1.051.988,36** |

## Como ler o resultado

São 39.113 **benefícios ativos**, não 39.113 famílias. A distinção não é
preciosismo: ela é a razão pela qual 35 municípios do país aparecem com mais
benefícios que famílias elegíveis.

E o líquido negativo tem consequência direta na tela. Onde ele fica menor ou igual a
zero, o aplicativo **se recusa a exibir qualquer cifra em reais** daquele município e
emite um encaminhamento pedindo a abertura dos lançamentos antes de usar o valor em
peça orçamentária. São João de Meriti caía nessa situação em dezembro de 2024.

Em março de 2026 o mesmo município tem subsídio de **+R$ 1.602.410,44**. Casar as
datas, portanto, não mudou só a contagem: devolveu a este município uma cifra que
antes não podia ser mostrada.

## O que a tornaria errada

Se a ANEEL renomear `SubsBaixaRenda`, o filtro devolve zero linhas e o município soma
zero benefícios, sem erro nenhum na execução: a ausência apareceria como cobertura
zero, que é indistinguível de um município realmente descoberto. Se o separador
decimal mudar, o valor vira nulo e o subsídio some. Se o código IBGE vier fora da
malha de 2022, o município é descartado no `dropna` e não aparece em lugar algum.

---

# 2. A tarifa que vale em cada município

## A conta

$$\text{tar}_c=\frac{\text{TUSD}_c+\text{TE}_c}{1000} \qquad
\text{tarifa}(m)=\frac{\sum_{c} \text{tar}_c \cdot \text{UC}_{m,c}}{\sum_c \text{UC}_{m,c}}$$

## O código que a executa

<!-- fonte: reconstrucao/pipeline/02_tarifa.py 11-11 -->
```python
b["tar"]=(num(b.VlrTUSD)+num(b.VlrTE))/1000.0
```

<!-- fonte: reconstrucao/pipeline/02_tarifa.py 14-14 -->
```python
tc = v.dropna(subset=["cnpj"]).groupby("cnpj").tar.median().reset_index()
```

<!-- fonte: reconstrucao/pipeline/02_tarifa.py 27-27 -->
```python
wm=jj.groupby("cod_ibge").apply(lambda x: np.average(x.tar,weights=x.uc) if x.uc.sum()>0 else x.tar.mean(), include_groups=False).rename("tarifa_municipal").reset_index()
```

## Por que ela é válida

A tarifa é homologada por distribuidora, não por município. Para responder quanto
custa o kWh em um lugar, é preciso saber quem atende aquele lugar e com que peso.

**A soma TUSD mais TE** é a tarifa cheia: uso do sistema de distribuição mais energia.
A divisão por mil converte R$/MWh em R$/kWh, e está isolada numa linha justamente
porque é o tipo de erro que passa despercebido por um fator de mil.

**A mediana por CNPJ** existe porque uma distribuidora publica várias linhas na mesma
vigência. A mediana resiste a linha atípica melhor que a média.

**A média ponderada por unidades consumidoras** existe porque um município atendido
por duas concessionárias tem tarifa efetiva dominada por quem atende mais gente.

## A alternativa descartada

**Casar pelo nome do agente em vez do CNPJ.** Foi testado: pelo nome casam **560
municípios**; pelo CNPJ casam os **5.570**. O INDGER usa razão social (`AMPLA ENERGIA
E SERVIÇOS S.A.`) e a CDE usa sigla (`LIGHT`). A escolha da chave é a diferença entre
uma cobertura de 10% e uma cobertura completa.

**Média simples entre distribuidoras.** Daria o mesmo peso a uma permissionária com
trezentos clientes e a uma concessionária com trezentos mil.

## Aplicação: São João de Meriti

| grandeza | valor |
|---|---|
| tarifa residencial | **R$ 0,823560/kWh** |
| tarifa da subclasse Baixa Renda | R$ 0,684600/kWh |
| unidades consumidoras casadas a alguma tarifa | 100,00% |

## Como ler o resultado

R$ 0,82/kWh é a tarifa **sem tributos**. A conta real da família é maior, porque o
ICMS varia entre 17% e 30% conforme o estado e não entra aqui.

Por isso a tarifa serve para **comparar municípios**, e não para dizer quanto alguém
paga. A amplitude nacional observada é de **2,32×**, de R$ 0,4862 a R$ 1,1268 por
kWh: a mesma conta de 80 kWh custa mais que o dobro dependendo de onde a família
mora, e essa ordenação é confiável mesmo com o nível subestimado.

Uma leitura que a tabela do aplicativo torna explícita: como a tarifa é da
concessionária, todo município atendido pela mesma empresa tem o mesmo valor. Em
Autazes, o ranking mostra "1ª de 62, empatado com 61" — os 62 municípios do Amazonas
dividem a mesma tarifa.

## O que a tornaria errada

Se `QtdUCAtiva` vier vazia em todas as linhas de um município, a soma dos pesos é
zero e o código cai na média simples, que é uma medida diferente sem que nada avise.
Se a data de vigência não cobrir a data de referência, o município fica sem tarifa e
sai como nulo. E o corte de qualidade de 90% de unidades casadas é calculado, mas
**não é aplicado** ao arquivo exportado: ele serve à conferência impressa.
---

# 3. A energia falta mais do que a ANEEL permite?

## A conta

$$\text{rel}(c)=\frac{\sum_{t=1}^{12}\text{indicador}_{c,t}}{\text{Limite}^{\text{anual}}_c}
\qquad
\text{pior}(c)=\max\bigl(\text{rel}^{\text{DEC}}_c,\ \text{rel}^{\text{FEC}}_c\bigr)$$

$$\text{rel}(m)=\frac{\sum_{c\in m}\text{pior}(c)\cdot \text{NumCon}_c}{\sum_{c\in m}\text{NumCon}_c}
\qquad
\text{viol}(m)=\mathbb{1}\bigl[\text{rel}(m)\ge 1\bigr]$$

## O código que a executa

<!-- fonte: reconstrucao/pipeline/03c_continuidade_2024_2025.py 14-18 -->
```python
    ser = x.groupby(["IdeConjUndConsumidoras","SigIndicador"]).agg(soma=("VlrIndiceEnviado","sum"), n=("VlrIndiceEnviado","size")).reset_index()
    ser = ser[ser.n==12]
    lim = L[(L.AnoLimiteQualidade==a)&(L.SigIndicador.isin(["DEC","FEC"]))][["IdeConjUndConsumidoras","SigIndicador","VlrLimite"]].drop_duplicates(["IdeConjUndConsumidoras","SigIndicador"])
    m = ser.merge(lim, on=["IdeConjUndConsumidoras","SigIndicador"])
    m["rel"] = m.soma/m.VlrLimite
```

<!-- fonte: reconstrucao/pipeline/03c_continuidade_2024_2025.py 22-22 -->
```python
    p["pior"] = p[["rel_DEC","rel_FEC"]].max(axis=1)
```

<!-- fonte: reconstrucao/pipeline/03c_continuidade_2024_2025.py 25-28 -->
```python
    g = j.groupby("cod_ibge").apply(lambda x: pd.Series({
        "rel": np.average(x.pior, weights=x.w) if x.w.sum()>0 else x.pior.mean(),
        "dec_h": np.average(x.soma_DEC, weights=x.w) if x.w.sum()>0 else x.soma_DEC.mean(),
        "nconj": x.IdeConjUndConsumidoras.nunique()}), include_groups=False).reset_index()
```

## Por que ela é válida

A ANEEL publica os indicadores **mês a mês** e o limite **por ano**. Comparar as duas
coisas exige colocá-las na mesma unidade de tempo, e a única forma correta é somar os
doze meses antes de dividir pelo limite anual.

**Esta é a correção mais grave que o projeto fez.** A versão anterior comparava o
valor mensal contra o limite anual e concluía que **nenhum município do Brasil**
descumpria o limite de continuidade. Somando os doze meses, são 2.082 municípios
acima em 2024 e **1.412 acima nos dois anos seguidos**.

**O `max` entre DEC e FEC** existe porque a norma fixa limite para cada um, e eles
medem coisas distintas: duração total das interrupções e quantidade delas. Estourar
qualquer um é descumprimento.

**A ponderação por consumidores** na agregação ao município faz um trecho de rede
grande e ruim pesar mais que um pequeno e ruim.

## A alternativa descartada

**O critério do pior conjunto**, em que o município é marcado se qualquer conjunto que
o atende estourar. Também foi calculado: dá **3.199 municípios** em vez de 2.082. Os
dois valores são publicados, e o ponderado é o adotado, porque marcar um município
inteiro pelo pior trecho de rede superestima o alcance do problema.

**Extrapolar o ano incompleto.** O filtro `n==12` descarta o conjunto que não
reportou os doze meses em vez de estimar o que falta. É conservador: reduz a contagem
de violações em vez de inflá-la.

## Aplicação: dois municípios, porque um só não basta

São João de Meriti fica **dentro** do limite, então serve para mostrar o caso comum:

| grandeza | valor |
|---|---|
| razão sobre o limite em 2024 | 0,874229× |
| razão sobre o limite em 2025 | 0,786777× |
| DEC anual ponderado, 2024 | 5,92 h |
| conjuntos que atendem | 7 |
| violou? | não, nos dois anos |

**Pedras Altas (RS), IBGE 4314175**, é o pior caso do país e mostra a outra ponta:

| grandeza | valor |
|---|---|
| razão sobre o limite em 2024 | **7,3347×** |
| razão sobre o limite em 2025 | 1,6450× |
| DEC anual, 2024 | **110,02 h sem energia** |
| conjuntos que atendem | 1 |
| violou? | **sim, nos dois anos** |

## Como ler o resultado

Um valor de 7,33× quer dizer que a interrupção apurada foi **sete vezes e um terço o
máximo que a ANEEL permite** para aquele trecho de rede. São 110 horas sem energia no
ano, contra um limite de cerca de 15.

Estar acima do limite em dois anos seguidos afasta a hipótese de evento climático
isolado, e é o critério que fundamenta representação à agência estadual conveniada ou
ao Ministério Público. É a lista dos 1.412.

**A ressalva que a ficha municipal declara na tela.** A ANEEL apura por **conjunto
consumidor**, e um conjunto atravessa vários municípios. Pedras Altas é servida por um
único conjunto, **dividido com outros 6 municípios**: o 7,33× é o número da rede que
passa ali, idêntico nesses outros seis lugares. Ele diz que a energia falta, não que
falta *neste* município mais que no vizinho.

No país inteiro, apenas **47 municípios (0,8%)** têm conjuntos exclusivos seus. A
mediana divide a rede com outros 15, e o máximo com 110.

## O que a tornaria errada

Se um conjunto reportar mais de doze registros num ano, por duplicidade de agente, a
soma infla e o `n==12` deixa de proteger. Se o limite vier com a parte inteira
ausente, o que ocorre em 12 registros do arquivo, a razão sai absurda. E o
`np.average` não ignora nulo: basta um conjunto do município sem DEC apurado para que
a média ponderada inteira vire nulo, ainda que os outros vinte tenham valor.

---

# 4. Território: a participação de favela

## A conta

$$\text{favela}(m)=\frac{\text{domicílios em favela}(m)}{\text{domicílios particulares permanentes ocupados}(m)}$$

## O código que a executa

<!-- fonte: reconstrucao/pipeline/04_territorio.py 15-15 -->
```python
m["d4_corr"]=m.dom_favela/m.dom_total_mun
```

## Por que ela é válida

Numerador e denominador vêm do mesmo Censo 2022, usam o mesmo código municipal e a
**mesma espécie de domicílio**, o que torna a divisão direta e comparável entre
municípios.

## A alternativa descartada

A tabela 9887 do SIDRA publica uma variável chamada "percentual do total geral". Esse
total geral é o universo **das favelas**, repartido por espécie de domicílio, e não o
total do município. Usá-la como participação municipal produzia valores em torno de
**84% em toda parte**, e São Paulo aparecia com 89,8% dos seus domicílios em favela.

Com o denominador certo, da tabela 4712, São Paulo fica em **13,6%** e o Rio de
Janeiro em **20,8%**, compatíveis com o que o IBGE divulgou. É a correção mais
constrangedora do projeto e está publicada.

## Aplicação: São João de Meriti

$$\frac{14.058}{168.771}=0{,}083296 \;\to\; \mathbf{8{,}33\%}$$

## Como ler o resultado

8,33% dos domicílios do município estão em favelas ou comunidades urbanas segundo o
Censo 2022.

**E aqui o resultado publicado é nulo, de propósito.** A participação de favela **não
tem associação detectável** com nenhuma medida energética na escala municipal:
nenhuma correlação de ordem passa de 0,09 em módulo. Municípios com mais favela não
têm pior situação energética média.

Isso **não diz nada** sobre a situação de um domicílio dentro de uma favela comparado
a outro fora dela. Concluir o contrário seria falácia ecológica, e a pergunta exige
microdado que estas fontes não fornecem.

Onde o Censo percorreu o território e não identificou favela, o valor é zero, e esse
zero é **medição, não ausência**. São 4.915 municípios nessa condição.

## O que a tornaria errada

Se o numerador vier de uma espécie de domicílio e o denominador de outra, a razão
perde sentido sem que nada acuse. Foi exatamente o que aconteceu na versão anterior.

---

# 5. A renda de referência

## A conta

$$\text{renda do domicílio na faixa de pobreza}(m)=218 \times \text{moradores por domicílio}(m)$$

$$\text{moradores por domicílio}(m)=\frac{\text{moradores}(m)}{\text{domicílios}(m)}$$

## O código que a executa

<!-- fonte: reconstrucao/pipeline/05_domicilio.py 18-18 -->
```python
m["moradores_por_domicilio"]=m.moradores/m.dom_total_mun
```

<!-- fonte: reconstrucao/pipeline/06c_faixas_cadunico.py 21-23 -->
```python
SM=SALARIO_MINIMO; TETO_BR=SM/2; TETO_POB=LINHA_POBREZA
df["renda_dom_teto_br"]=TETO_BR*df.moradores_por_domicilio
df["renda_dom_teto_pob"]=TETO_POB*df.moradores_por_domicilio
```

## Por que ela é válida

A pergunta é quanto a conta de luz pesa **para quem está na faixa de pobreza**, não
para o morador médio do município. Por isso a renda usada não é a renda observada: é
o **teto da faixa** do CadÚnico, R$ 218 por pessoa ao mês, multiplicado pelo tamanho
médio do domicílio daquele município.

O tamanho do domicílio varia muito entre municípios, e é ele que transforma uma renda
per capita numa renda de domicílio, que é a unidade em que a conta de luz chega.

## A alternativa descartada

**Usar a renda média municipal do Censo.** Diluiria justamente a população que
interessa: num município onde a maioria não é pobre, a média esconderia o peso sobre
quem é.

**Usar denominador per capita em vez de domiciliar.** Foi calculado e comparado: o
deslocamento mediano no ranking passa de mil posições entre as duas escolhas, e a
sobreposição dos cem piores cai. O domiciliar é o correto, porque a conta de luz
chega por domicílio e não por pessoa.

## Aplicação: São João de Meriti

| passo | valor |
|---|---|
| moradores por domicílio | 2,611764 |
| renda do domicílio no teto da faixa | 218 × 2,611764 = **R$ 569,3645** |

## Como ler o resultado

R$ 569,36 é a renda mensal de um domicílio de 2,61 pessoas no **teto** da faixa de
pobreza. Não é a renda média do município, nem a renda observada de ninguém: é o
limite superior da faixa, usado como referência.

**O viés é conhecido em direção:** quem está abaixo do teto sente a conta mais do que
o calculado. O número subestima o peso.

**O denominador não é indexado, e o numerador é.** Os R$ 218 são valor nominal fixado
pelo Decreto 11.566/2023 e não foram reajustados até a data de referência desta
leitura; a tarifa, ao contrário, é reajustada todo ano. Daí decorre que o peso da
conta na renda sobe entre duas leituras sem que nenhuma família tenha empobrecido:
é o efeito de comparar um preço corrigido com uma linha parada. Quem ler a variação
do peso entre duas datas está lendo isso, e não mudança de condição de vida.

## O que a tornaria errada

A tabela 10296 do SIDRA conta **pessoas** excluindo pensionistas e empregados
domésticos, então o tamanho do domicílio sai levemente subestimado, e com ele a renda
do domicílio. Se o valor da linha de pobreza do CadÚnico mudar, a constante
precisa mudar junto. Ela vive em `_paths.py`, com a data em que passou a valer, e é
lida de lá pelo pipeline e publicada no payload para o cálculo ao vivo na tela; antes
estava escrita à mão em nove lugares, e nada garantia que todos dissessem o mesmo.
---

# 6. Quanto pesa a conta de luz

## A conta

$$\text{peso}(m)=\frac{\text{tarifa}(m)\times 80}{218 \times \text{moradores por domicílio}(m)}$$

## O código que a executa

<!-- fonte: reconstrucao/pipeline/06e_distribuidora.py 15-16 -->
```python
df["peso_pob80_cheia"]=(df.tarifa_municipal*80)/df.renda_dom_teto_pob
df["peso_pob80_social"]=(df.tarifa_baixa_renda*80)/df.renda_dom_teto_pob
```

## Por que ela é válida

É a definição direta de peso orçamentário: o gasto dividido pela renda. O gasto é a
tarifa do município multiplicada por um consumo de referência; a renda é a do
domicílio no teto da faixa de pobreza.

## A alternativa descartada

**Outros consumos de referência.** O cenário domina o resultado, e por isso os três
foram calculados e publicados:

| consumo | peso mediano | municípios acima de 10% |
|---|---|---|
| 30 kWh | 3,94% | 0 |
| **80 kWh** | **10,50%** | **3.233** |
| 100 kWh | 13,12% | 5.440 |

A coluna da direita é a razão pela qual ela não é publicada: vai de zero a quase todos
conforme a hipótese. A do meio muda de escala e não de ordem, e isso foi verificado: a
correlação de posto entre o peso a 30 kWh e a 100 kWh é 1,0000.

A 30 kWh o problema desaparece; a 100 kWh é quase universal. Os 80 kWh foram
escolhidos porque são o limiar da Lei 15.235/2025, e são a **única das três hipóteses
com ancoragem externa**. A escolha não é neutra, e por isso está declarada com as
outras duas ao lado.

## Aplicação: São João de Meriti

$$\frac{0{,}823560 \times 80}{569{,}3645}=\frac{65{,}8848}{569{,}3645}=0{,}115713 \;\to\; \mathbf{11{,}57\%}$$

## Como ler o resultado

Uma conta de 80 kWh consome 11,57% da renda de um domicílio no teto da faixa de
pobreza em São João de Meriti, contra uma mediana nacional de 10,50%. O número a ler é
a **posição**: o município está acima da mediana do país. O nível depende do consumo
suposto e se move com ele; a posição não.

**Três vieses conhecidos, em direções opostas, que não se cancelam de forma
conhecida:**

| direção | causa |
|---|---|
| subestima | a tarifa não inclui ICMS nem PIS/COFINS |
| subestima | o cálculo usa o teto da faixa; quem está abaixo sente mais |
| superestima | usa o tamanho médio de domicílio do município, e domicílios pobres tendem a ser maiores |

**A consequência prática é a regra de leitura deste número: a ordenação entre
municípios é confiável; o nível não é.** A ordenação vem da tarifa real, com 2,32× de
amplitude observada. O nível depende de um consumo suposto e de uma renda de
referência.

## O que a tornaria errada

Se a tarifa ou o tamanho do domicílio vierem nulos, o peso vira nulo e o município
sai do cálculo em silêncio. E o número é **cenário, não medição**: nenhuma família
específica foi observada consumindo 80 kWh.

---

# 7. A única regra normativa: o desconto escalonado

Este é o único ponto de todo o cálculo em que se aplica uma **regra jurídica** em vez
de ler um dado. Se ela estiver errada, todos os valores em reais caem junto. Por isso
tem os dois testes independentes ao final desta seção.

## A conta

$$F(k)=\frac{0{,}35\min(k,30)+0{,}60\max(0,\min(k,100)-30)+0{,}90\max(0,\min(k,220)-100)+1{,}00\max(0,k-220)}{k}$$

## O código que a executa

<!-- fonte: reconstrucao/pipeline/07_tarifa_social.py 6-11 -->
```python
def fator(k):
    f1=min(k,30)*0.35
    f2=max(0,min(k,100)-30)*0.60
    f3=max(0,min(k,220)-100)*0.90
    f4=max(0,k-220)*1.0
    return (f1+f2+f3+f4)/k
```

<!-- fonte: reconstrucao/pipeline/07_tarifa_social.py 13-17 -->
```python
F80=fator(80)
d["conta_cheia80"]=d.tarifa_municipal*80
d["conta_social80"]=d.tarifa_baixa_renda*80*F80
d["econ_mes"]=d.conta_cheia80-d.conta_social80
d["peso_social_ef"]=d.conta_social80/(218*d.moradores_por_domicilio)
```

## Por que ela é válida

A função é escrita como fator de **pagamento**, e não de desconto. Cada faixa de
consumo tem o seu percentual, e o desconto é **cumulativo por faixa**, não aplicado
de uma vez sobre o total:

| faixa de consumo | fator no código | desconto implicado |
|---|---|---|
| 0 a 30 kWh | 0,35 | 65% |
| 31 a 100 kWh | 0,60 | 40% |
| 101 a 220 kWh | 0,90 | 10% |
| acima de 220 kWh | 1,00 | 0% |

Os `min` e `max` encadeados são o que implementa o escalonamento: cada faixa recebe
apenas a parte do consumo que cai dentro dela.

## A alternativa descartada

**Aplicar 40% sobre os 80 kWh inteiros**, por o consumo cair na segunda faixa. Daria
fator 0,60 em vez de 0,50625, uma conta 18,5% mais cara, e estaria errado: os
primeiros 30 kWh têm desconto de 65%, não de 40%.

## Aplicação: São João de Meriti

$$F_{80}=\frac{30(0{,}35)+50(0{,}60)}{80}=\frac{10{,}5+30{,}0}{80}=\mathbf{0{,}506250}$$

| passo | conta |
|---|---|
| conta cheia | 0,823560 × 80 = **R$ 65,8848** |
| conta com Tarifa Social | 0,684600 × 80 × 0,506250 = **R$ 27,7263** |
| economia | 65,8848 − 27,7263 = **R$ 38,1585 por mês** |
| peso sem o benefício | 11,57% |
| peso com o benefício | **4,87%** |

## Como ler o resultado

A família paga 50,625% do que pagaria sem a regra, o que corresponde a um desconto
efetivo de 49,4% a 80 kWh.

**A economia tem duas componentes, não uma.** A troca de subclasse tarifária, de
Residencial (R$ 0,8236) para Baixa Renda (R$ 0,6846), e o desconto escalonado sobre
ela. **A CDE reembolsa apenas a segunda.** Confundir as duas produziu um argumento de
validação que depois foi descartado em público, e o registro está em
`docs/VALIDACAO.md`.

**E aqui está a leitura que o aplicativo transforma em encaminhamento:** em São João de
Meriti a Tarifa Social devolve à família mais do que a mediana do país devolve, porque a
tarifa local é das mais altas. A mesma família, elegível, recupera esse valor por mês se
estiver dentro do benefício e não recupera nada se estiver fora. Não é caso de discutir
tarifa: o instrumento que resolve é o cadastro. O encaminhamento é dito em reais, e não
em fração da renda, justamente para não depender de hipótese sobre a renda.

## Os dois testes que a regra passou

**Teste por inversão.** Partindo do subsídio que a CDE efetivamente pagou por família
em cada município, e da tarifa da subclasse Baixa Renda, resolve-se para o consumo
que a regra implica:

| | valor |
|---|---|
| consumo implícito, mediana | **97,7 kWh** |
| p05 · p25 · p75 · p95 | 79,9 · 90,0 · 119,0 · 147,8 kWh |
| fração entre 40 e 150 kWh | **95,8%** |

É fisicamente plausível para consumo residencial de baixa renda. Uma regra errada por
um fator produziria consumo implícito absurdo, algo como 300 kWh ou 15 kWh.

**Teste de escala.** Se a regra vale, o subsídio é proporcional à tarifa, e a razão
entre os dois deve ser aproximadamente constante entre municípios:

| | valor |
|---|---|
| Spearman(subsídio por família, tarifa Baixa Renda) | **+0,755** |
| coeficiente de variação do subsídio bruto | 0,143 |
| coeficiente de variação do subsídio ÷ tarifa | **0,093** |
| razão mediana, em kWh-equivalente descontado | 46,6 |

Normalizar pela tarifa reduz a dispersão em **35%**, o que só acontece se a tarifa
for de fato um fator multiplicativo do subsídio. E o fecho é interno: a 97,7 kWh a
regra prevê $0{,}65 \times 30 + 0{,}40 \times 67{,}7 = 46{,}6$ kWh descontados,
exatamente a razão mediana observada. Não foi ajustado.

## O que a tornaria errada

Uma mudança legal nos percentuais ou nos limites de faixa. A regra aparece em três
arquivos (`07_tarifa_social.py`, `valida_desconto.py` e, em forma fechada,
`valida_decomposicao.py`), e nenhum teste acusa se apenas um for atualizado.

A função também aceita `k` negativo sem reclamar: para qualquer k menor que zero ela
devolve exatamente 0,35, porque o sinal cancela na divisão final e as três faixas
superiores são zeradas pelo `max`. Nada no código impede essa entrada; ela só não
ocorre porque `k` é a constante 80.

---

# 8. A leitura do presente, casada por data

## A conta

$$\text{não atendidas}(m)=\max\bigl(0,\ \text{elegíveis}^{\text{mar}26}_m - \text{benefícios}^{\text{mar}26}_m\bigr)$$

$$\text{cobertura}(m)=100 \times \frac{\text{benefícios}^{\text{mar}26}_m}{\text{elegíveis}^{\text{mar}26}_m}$$

## O código que a executa

<!-- fonte: reconstrucao/pipeline/06d_concentracao.py 52-62 -->
```python
df["familias_elegiveis_mar26"] = df.eleg_mar26
df["beneficiarios_mar26"] = df.ben_mar26
df["lacuna_bruta_casada"] = df.familias_elegiveis_mar26 - df.beneficiarios_mar26
df["lacuna_pos"] = df.lacuna_bruta_casada.clip(lower=0)
df["cobertura"] = 100 * df.beneficiarios_mar26 / df.familias_elegiveis_mar26.replace(0, np.nan)

# subsidio por familia na MESMA data do contingente, para que o valor em reais
# nao volte a cruzar a quantidade de uma data com o preco de outra
df["subsidio_familia_mar26"] = df.subs_mar26 / df.beneficiarios_mar26.replace(0, np.nan)
df["subsidio_familia_liq"] = df.subs_liquido / df.linhas_tsee.replace(0, np.nan)   # dez/2024, preservado
df["rs_nao_acessado"] = df.lacuna_pos * df.subsidio_familia_mar26
```

## Por que ela é válida

É a subtração que dá nome ao trabalho: quem tem direito menos quem recebe. O CadÚnico
diz quem tem direito, a CDE diz quem recebe, e **as duas pontas são da mesma data**.

**O `clip(lower=0)` não é cosmético, é definição.** A soma nacional usa as diferenças
positivas por município porque excesso num lugar não supre falta em outro: se um
município tem mais benefícios que famílias elegíveis, isso não alcança ninguém no
município vizinho. Pelo saldo líquido o valor nacional seria 10.426.463; a diferença
é o excesso dos 35 municípios com sobrecobertura.

**O `replace(0, np.nan)`** evita divisão por zero e faz o município sem elegíveis sair
como nulo em vez de infinito.

## A alternativa descartada

**Cruzar CadÚnico de agosto de 2026 com CDE de dezembro de 2024**, que é o que a
versão anterior fazia. Vinte meses de defasagem, enquanto a página de comparação
afirmava que cada data usa o CadÚnico do seu próprio mês. As duas coisas não podiam
ser verdade ao mesmo tempo, e a contradição aparecia na tela: o mesmo município
exibia **64,9%** de cobertura numa tabela e **81,8%** no cartão ao lado.

O efeito de casar as datas, no agregado nacional:

| medida | base cruzada | base casada |
|---|---|---|
| não atendidas | 9.968.144 | **10.440.849** |
| cobertura nacional | 64,28% | **62,53%** |
| **sobrecobertura** | **80 municípios** | **35** |

A queda da sobrecobertura pela metade é evidência, não conveniência: **mais da metade
daquela anomalia era artefato da defasagem**, e não a diferença entre unidade
consumidora e família.

## Aplicação: São João de Meriti

| passo | valor |
|---|---|
| famílias elegíveis, mar/2026 | 58.526 |
| benefícios ativos, mar/2026 | 47.860 |
| não atendidas | 58.526 − 47.860 = **10.666** |
| cobertura | 100 × 47.860 / 58.526 = **81,78%** |
| subsídio por família | 1.602.410,44 / 47.860 = R$ 33,4812 |
| subsídio não acessado | 10.666 × 33,4812 = **R$ 357.110,53/mês** |

## Como ler o resultado

10.666 famílias de São João de Meriti estão no CadÚnico, na faixa de renda que dá o
direito, e não constam como beneficiárias na base da ANEEL de março de 2026.

**O que esse número não diz.** Ele não separa privação de defasagem de cadastro.
Parte da diferença pode ser família que mudou de endereço, unidade consumidora em
nome de terceiro, ou cadastro desatualizado. Por isso a primeira ação que o dado
sustenta é **verificação local**, e não campanha: cruzar a relação de unidades
consumidoras da distribuidora com o CadÚnico, do qual o município já é gestor.

Os R$ 357 mil por mês são **projeção**, não previsão: supõem que a família marginal
receberia o mesmo subsídio médio das que já recebem naquele município. Servem para
ordem de grandeza orçamentária.

## O que a tornaria errada

Se o código do SAGI, que tem seis dígitos, for casado com o da CDE, que tem sete, sem
o ajuste, nenhum município casa e tudo vira nulo. Se a competência da CDE escolhida
não tiver todas as distribuidoras, a ausência de reporte aparece como queda de
benefícios: **só março de 2026 traz as 103 concessionárias** entre os meses de 2026
publicados.
---

# 9. A série mensal do CadÚnico

## A conta

Guardar o primeiro valor absoluto e, depois, apenas a diferença para o mês anterior:

$$d_1=v_1 \qquad d_t=v_t-v_{t-1}\ \ (t>1) \qquad\text{e, na leitura, } v_t=\sum_{j\le t} d_j$$

## O código que a executa

<!-- fonte: reconstrucao/pipeline/10d_payload_serie.py 56-61 -->
```python
    "comp": comp,
    "falhas": sorted(VAZIAS),
    "pob": delta(serie("pob")),
    "bxr": delta(serie("bxr")),
    "eleg": delta(serie("eleg")),
}
```

## Por que ela é válida

O número de famílias num município muda pouco de um mês para o outro. Guardar a
diferença em vez do valor absoluto produz números pequenos, e número pequeno ocupa
menos caracteres em JSON. A soma acumulada reconstrói o valor original **sem perda**,
porque são inteiros.

Medido sobre 31 competências e 5.570 municípios: de 2,37 MB para 1,64 MB crus, e de
0,93 MB para 0,59 MB depois da compressão que o servidor aplica.

## A alternativa descartada

**Guardar os valores absolutos**, que custaria 0,34 MB a mais por carregamento.
**Buscar a série sob demanda por requisição**, que quebraria a propriedade de a página
funcionar sem internet.

## Aplicação: São João de Meriti

| passo | valor |
|---|---|
| competências utilizáveis | 31, de jan/2024 a ago/2026 |
| famílias em pobreza, primeiro mês | 46.321 |
| famílias em pobreza, último mês | 47.043 |
| variação no período | **+722** |

## Como ler o resultado

A linha mostra a trajetória mensal, e não dois pontos ligados. Isso importa porque
uma comparação de duas datas não distingue tendência de oscilação.

**Duas competências foram excluídas, e a razão é o achado mais importante desta
seção.** Abril de 2025 e setembro de 2026 voltam do SAGI com **5.571 documentos e
todos os campos ausentes**. O `numFound` diz que estão completas; só a leitura dos
valores revela o vazio. Se fossem plotadas, o gráfico mostraria o CadÚnico despencando
a zero em dois meses. Elas entram em `falhas` e a linha é **interrompida** nelas.

É a segunda vez que essa armadilha aparece, em duas fontes federais distintas: a outra
é a cobertura variável de distribuidoras nos arquivos mensais da CDE. A lição é
operacional: **a conferência de base precisa preceder qualquer comparação temporal**,
e contar registros não é conferir.

**Por que os benefícios entram como pontos e não como linha.** A ANEEL publica a CDE
mês a mês desde 2018, mas cada arquivo tem 330 MB e, dos cinco meses de 2026
publicados, apenas março traz as 103 distribuidoras. Uma linha contínua ali seria
invenção.

## O que a tornaria errada

Se um município tiver valor num mês e nulo no seguinte, a soma acumulada precisa
retomar do último valor conhecido, e não de zero. O decodificador trata nulo como
interrupção, não como zero. Se essa distinção se perder, a série cai a zero em vez de
interromper.

---

# 10. O indicador é do município ou da rede?

## A conta

$$\text{coirmãos}(m)=\left|\ \bigcup_{c\,\in\,\text{conjuntos}(m)} \text{municípios}(c)\ \right| - 1$$

## O código que a executa

<!-- fonte: reconstrucao/pipeline/10e_payload_conjuntos.py 45-51 -->
```python
    vizinhos = set()
    for c in cs:
        vizinhos |= por_conj.get(c, set())
    vizinhos.discard(cod)
    ncj.append(len(cs))
    nviz.append(len(vizinhos))
    excl.append(1 if len(vizinhos) == 0 else 0)
```

## Por que ela é válida

A ANEEL apura continuidade por **conjunto consumidor**, que é um trecho de rede, e um
conjunto atravessa vários municípios. A união dos municípios de todos os conjuntos que
atendem um lugar, menos ele próprio, é exatamente com quantos outros ele divide o
número.

Sem isso, a ficha apresentaria como medição daquele município algo que é medição de
uma rede compartilhada.

## A alternativa descartada

**Contar quantos municípios têm o mesmo valor de DEC/FEC.** Foi o primeiro caminho
tentado, e é enganoso: valor igual pode ser coincidência de arredondamento, e valor
diferente não prova infraestrutura diferente. Compartilhar o **conjunto** é o fato;
compartilhar o número é consequência.

## Aplicação: dois casos

| município | conjuntos | coirmãos | leitura |
|---|---|---|---|
| São João de Meriti (RJ) | 7 | vários | valor é média ponderada de sete trechos |
| **Pedras Altas (RS)** | **1** | **6** | o 7,33× é da rede, idêntico em outros seis municípios |
| Autazes (AM) | 1 | 13 | o 1,055× aparece em catorze municípios do estado |

## Como ler o resultado

No país inteiro, apenas **47 municípios (0,8%)** têm conjuntos exclusivos seus. A
mediana divide a rede com **15** outros municípios, e o máximo com **110**.

A consequência para a leitura é direta: quando o município é servido por um único
conjunto compartilhado, o indicador **não distingue** aquele lugar dos vizinhos. Ele
diz que a energia falta naquele trecho de rede, e não que falta mais ali do que no
município ao lado.

É por isso que o ranking marca empate. Sem isso, catorze municípios do Amazonas
apareceriam como "1º do estado" cada um, como se cada um fosse o pior.

## O que a tornaria errada

O IndQual traz 5.574 códigos municipais distintos para 5.570 municípios, e ao menos um
deles, o 4314530, vem com nome e UF vazios. A junção não valida o código contra a
malha do projeto.

---

# 11. Cartografia

## A conta

Simplificação de Douglas-Peucker com tolerância em metros, aplicada **no plano
projetado**, e arredondamento das coordenadas geográficas a três casas decimais.

## O código que a executa

<!-- fonte: reconstrucao/pipeline/08_geometria.py 42-45 -->
```python
def arred(c):
    if isinstance(c[0], (int, float)):
        return [round(c[0], CASAS), round(c[1], CASAS)]
    return [arred(x) for x in c]
```

## Por que ela é válida

Tolerância em metros só faz sentido num plano projetado, e por isso a simplificação
acontece em SIRGAS 2000 / Policônica antes da conversão para coordenada geográfica.
A malha vai em WGS84 e quem projeta para a tela é a biblioteca de mapa, conforme o
nível de zoom.

Três casas decimais valem cerca de **111 m**, bem abaixo da distância entre vértices
que uma simplificação de 2 km deixa. O arredondamento, portanto, não remove nada
visível e corta o arquivo pela metade.

## A alternativa descartada

**Gravar caminho SVG já projetado, com coordenada inteira**, que é o que a versão
anterior fazia. Tinha três defeitos:

1. o enquadramento era sequestrado pelo extremo leste da malha, que é o arquipélago
   de **Trindade e Martim Vaz**, dentro do polígono de Vitória, a cerca de 1.100 km da
   costa. O envelope ficava com 4.819 km de largura contra os 4.326 km do continente:
   **11% da tela era Atlântico vazio**;
2. o arredondamento para inteiro dava **3,44 km por unidade**, grosseiro para qualquer
   aproximação;
3. não havia zoom contínuo, pinça no toque nem deslocamento de verdade, porque não
   havia mapa: havia um desenho.

## Aplicação: a camada estadual

| tentativa | vértices | tamanho |
|---|---|---|
| dissolve simples, simplify 4 km com topologia preservada | 162.993 | 3,31 MB |
| o mesmo, simplify 35 km | ~162.000 | 3,26 MB |
| **sem as lascas, simplify 3 km sem preservar topologia** | **4.949** | **0,09 MB** |

## Como ler o resultado

O dissolve de 5.570 municípios em 27 estados produz **898 partes**, com área mediana
de **0,014 km²**: são lascas nas frestas de ponto flutuante entre polígonos vizinhos.
Pior, com `preserve_topology` a simplificação **se recusa a agir** sobre essa
geometria, e por isso aumentar a tolerância de 4 km para 35 km quase não mudava o
tamanho.

Descartadas as partes abaixo de 20 km² e liberada a simplificação, a camada estadual
cai de 3,31 MB para 0,09 MB sem diferença visível num contorno que é apenas uma linha
branca de separação.

O mapa é **índice visual, não instrumento cartográfico**: serve para localizar e
comparar, não para medir distância nem área.

## O que a tornaria errada

Se a ordem das feições deixar de corresponder à ordem do payload, cada município seria
pintado com o dado de outro, sem erro nenhum na execução. O alinhamento é garantido
por reindexação explícita pela ordem de `app_dados.csv`.

---

# 12. O que é calculado ao vivo, no navegador

Os agregados nacionais **não são gravados prontos**: a página os recalcula a partir do
payload publicado, a cada carregamento. Isso é deliberado. Uma cifra escrita à mão no
código continuaria sendo publicada mesmo depois de o dado mudar, e foi exatamente esse
defeito que a auditoria encontrou em dezesseis agregados, hoje derivados.

| agregado | o que calcula |
|---|---|
| `NAT` | elegíveis, benefícios, não atendidas e cobertura em cada data, cada uma com o CadÚnico do seu próprio mês |
| `AGG` | somas nacionais, medianas e os extremos de tarifa |
| `COB` | mediana da fração da conta coberta, só nos municípios com subsídio positivo **nas duas datas** |
| `QCOB` | quartis de cobertura, que definem a banda de gravidade dos encaminhamentos |
| `CONC` | por estado, o conjunto mínimo de municípios que soma metade das famílias não atendidas |
| `IDX` | índices por estado e por macrorregião, para o ranking em três escalas |
| `posicao` | posição e **empate** de um município dentro de um conjunto declarado |

## Uma diferença de convenção que vale registrar

A mediana em JavaScript é o elemento na posição `floor(n/2)` do vetor ordenado; o
`.median()` do pandas faz a média dos dois centrais quando `n` é par. Os dois
resultados divergem apenas em vetor de tamanho par, e a tolerância dos scripts de
validação absorve isso.

## Uma armadilha de linguagem que a auditoria encontrou

Em JavaScript, `null` é coagido a `0` em contexto numérico. Uma soma que encontra nulo
não produz `NaN`: produz um total silenciosamente menor. E uma comparação como
`cob < QCOB[0]` com `cob` nulo avalia como verdadeira, o que classificaria o município
na banda mais grave por ausência de dado. Os agregados tratam nulo explicitamente.

---

# Apêndice: o inventário completo

As 793 operações do projeto que foram extraídas e **verificadas**. As doze que
produzem os números publicados têm tratamento completo no corpo do documento; este
índice existe para que nenhuma das outras fique fora, e para que se possa pular
direto para a linha.

**O que foi verificado, e como.** A transcrição de cada entrada foi comparada
caractere a caractere com as linhas que ela declara no arquivo, e só entrou aqui o
que bateu. O inventário saiu de varreduras com verificação adversarial, uma por
arquivo, em que um agente extrai e outro tenta derrubar a extração abrindo o
arquivo. Nas 90 operações de `valida_numeros.py`, auditado depois de reescrito, o
arquivo de transcrições se perdeu: o código foi relido das linhas reais, o que o
torna correto por construção, e a conferência mecânica recaiu sobre as faixas
declaradas, que estão dentro do arquivo, em ordem e sem sobreposição.

**Reancoragem.** 134 entradas apontavam para linhas que se deslocaram quando o
código acima delas mudou. Cada uma foi reancorada só quando o bloco transcrito
aparecia exatamente uma vez no arquivo de hoje: a verificação por transcrição
continua valendo, e o que mudou foi a posição, não o conteúdo. Onde o bloco não
aparecia, ou aparecia mais de uma vez, a entrada saiu.

**O que não está aqui.** 30 operações de seis arquivos foram retiradas porque o
código que elas descreviam mudou depois da auditoria e ainda não foi reauditado:
15 em `mapa.template.html`, 4 em `06c_faixas_cadunico.py`, 4 em
`06e_distribuidora.py`, 4 em `09_payload.py`, 2 em `02_tarifa.py` e 1 em
`07_tarifa_social.py`. São as passagens tocadas pela troca do indicador de manchete
e pela centralização das constantes de renda. Ficam declaradas como lacuna em vez de
entrarem com descrição não conferida.

Em todos os casos, o que nenhuma máquina conferiu é se a descrição corresponde ao
que o código faz: a transcrição é verificável, a leitura do que ela significa não é.

## Ingestão das fontes

112 operações em 8 arquivos.

### `reconstrucao/pipeline/01_cde.py`

| linhas | operação | espécie | o que faz, e o que a tornaria errada |
|---|---|---|---|
| `4-5` | Selecao do primeiro membro do zip | leitura | O pipeline le exatamente um membro do zip, escolhido pela posicao 0 da lista de entradas, e nao pelo nome nem por filtro de extensao. O codigo nao re… **Risco:** Se a ANEEL publicar o zip com mais de um membro (por exemplo um README, um dicionario de dados ou o CSV particionado em partes), infolist()[0] pode a… |
| `6` | Inicializacao dos acumuladores em zero | agregação | Define o estado que atravessa os chunks: acc mapeia codigo IBGE para um vetor de cinco acumuladores, ntot conta linhas lidas e tipos conta ocorrencia… **Risco:** Municipio que nunca aparece no arquivo nao entra em acc e portanto nao aparece no CSV de saida: a ausencia e representada por linha faltante, nao por… |
| `8-9` | Leitura em streaming por blocos de 2 milhoes de linhas | leitura | Chunk de 2.000.000 de linhas com apenas 4 colunas e dtype=str e o que mantem o consumo de memoria limitado sobre um CSV de 2,3 GB. dtype=str evita qu… **Risco:** latin-1 nunca falha: qualquer byte e decodificado para algum caractere. Se o arquivo de fato for UTF-8, nomes acentuados viram mojibake sem erro. Com… |
| `10` | Contagem total de linhas lidas | agregação | Conta todas as linhas do CSV, de qualquer tipo de subsidio, antes de qualquer filtro. Serve de denominador de conferencia contra o total de linhas de… **Risco:** len(ch) conta linhas do DataFrame apos o parsing, nao registros fisicos do arquivo. Linhas com aspas nao fechadas ou quebra de linha dentro de campo … |
| `11` | Histograma de tipos de subsidio acumulado entre chunks | agregação | E a auditoria do filtro da linha 12: imprime quais valores de DscTipoSubsidio existem no arquivo e quantas linhas cada um tem, de modo que a escolha … **Risco:** value_counts() ignora NaN por padrao: linhas com DscTipoSubsidio vazio nao aparecem em tipos, entao a soma de tipos.values() pode ser menor que ntot … |
| `12` | Filtro da subclasse de baixa renda | regra normativa | A CDE custeia varios subsidios; so o de baixa renda corresponde a Tarifa Social de Energia Eletrica. docs/METODO.md registra explicitamente que o sub… **Risco:** Comparacao literal, sem normalizacao de caixa nem de acento: se a ANEEL grafar 'SubsBaixaRenda ' com espaco interno, 'SUBSBAIXARENDA' ou renomear a c… |
| `13` | Curto-circuito do chunk sem linhas de baixa renda | limiar | Evita executar groupby e iterrows sobre um DataFrame vazio, o que em pandas pode produzir agregacao de tipo indefinido. Nao altera nenhum total, porq… **Risco:** Nao distingue 'este bloco nao tem baixa renda' de 'o filtro parou de casar'. Se o filtro da linha 12 quebrar, todos os chunks caem aqui, o script imp… |
| `14` | Conversao do valor monetario no formato pt-BR | aritmética | O campo VlrSubsidio vem no padrao brasileiro, com ponto separando milhar e virgula separando decimal; a remocao de todos os pontos seguida da troca d… **Risco:** A remocao de todos os pontos e incondicional. Se alguma safra publicar o valor no padrao americano (1234.56), o ponto decimal e apagado e o valor vir… |
| `15` | Conversao do codigo IBGE para numero | cartografia | CodIbgeMunicipio foi lido como texto por dtype=str na linha 9; a conversao para numero e o que torna a chave comparavel com o codigo IBGE usado no re… **Risco:** A conversao para numero destroi zero a esquerda: um codigo gravado como '0150010' viraria 150010 e nao casaria com nenhum municipio. Como o resultado… |
| `16` | Descarte de municipio invalido e truncamento para inteiro | cartografia | Linha sem codigo IBGE valido nao pode ser atribuida a nenhum municipio e e removida do universo agregado. docs/VALIDACAO.md registra o efeito: contra… **Risco:** O descarte e silencioso: nao ha contagem de quantas linhas nem de quanto subsidio saiu do universo, e a diferenca de 161 linhas contra a referencia e… |
| `17-18` | Agregacao por municipio dentro do chunk, com separacao de bruto, esto… | agregação | Sao cinco agregacoes sobre a mesma coluna v, agrupadas por codigo IBGE. A separacao entre pos, neg e liq existe porque os valores negativos da CDE sa… **Risco:** Assimetria deliberada mas nao documentada no codigo entre size e sum: uma linha com VlrSubsidio ilegivel entra em linhas mas nao em pos, neg nem liq,… |
| `19-21` | Acumulacao dos cinco agregados entre chunks | agregação | Como o mesmo municipio aparece em varios chunks, o total municipal so existe somando os agregados parciais. As cinco quantidades escolhidas sao aditi… **Risco:** O vetor e posicional: a correspondencia entre os indices 0..4 e os nomes das colunas so e restabelecida na linha 23, longe daqui, e uma troca de posi… |
| `23` | Montagem do quadro municipal a partir do acumulador posicional | agregação | Reata os nomes das colunas as posicoes do vetor acumulado. docs/DICIONARIO.md define os campos resultantes: beneficiarios_tsee sao 'linhas de benefic… **Risco:** A ordem das linhas segue a ordem de insercao do dicionario, isto e, a ordem em que cada municipio apareceu pela primeira vez no CSV: o arquivo nao sa… |
| `26` | Totais nacionais de municipios e de linhas de beneficio | agregação | E a conferencia do resultado contra a referencia externa: docs/VALIDACAO.md compara 17.883.087 linhas de SubsBaixaRenda em dez/2024 com 17.882.926 ob… **Risco:** int() trunca em direcao a zero em vez de arredondar: como linhas_tsee e float por causa do iterrows, um acumulo de erro de ponto flutuante que deixas… |
| `27-29` | Totais nacionais em reais, bruto, estornos e liquido | agregação | Reproduz os tres numeros da tabela de efeito do item C4 de docs/CORRECOES.md: bruto positivo R$ 532.269.488,83, estornos -R$ 29.526.873,15, liquido R… **Risco:** Somar por municipio ja agregado nao e igual a somar as 17,9 milhoes de parcelas originais em ponto flutuante: as duas ordens de soma diferem nos ulti… |
| `30` | Contagem de municipios com ao menos um estorno | limiar | Mede a extensao geografica dos estornos. docs/CORRECOES.md item C4 usa exatamente esse resultado para afirmar que os valores negativos 'aparecem em 3… **Risco:** Limiar estrito em zero. Como n_negativos foi contaminado para float pelo iterrows, a comparacao > 0 depende de a contagem nunca cair em algo como 0.9… |
| `31` | Contagem de municipios com liquido negativo | limiar | Identifica os municipios em que os estornos superam o subsidio do mes, isto e, aqueles para os quais nenhuma cifra em reais e publicavel. docs/CORREC… **Risco:** O limiar aqui e estrito (< 0), mas o consumidor a jusante usa um limiar diferente: reconstrucao/pipeline/06e_distribuidora.py linha 20 escreve subsid… |

### `reconstrucao/pipeline/01b_cde_2026.py`

| linhas | operação | espécie | o que faz, e o que a tornaria errada |
|---|---|---|---|
| `4-5` | Parametrizacao do arquivo e da etiqueta da safra | leitura | TAG nao e so rotulo: entra na formacao dos nomes de coluna ben_{TAG} e subs_{TAG} (linha 36) e do nome do arquivo de saida (linha 37). O default 2026… **Risco:** Z e TAG sao independentes. Passar o zip de uma safra com a etiqueta de outra gera um CSV com nome e colunas mentindo sobre a referencia, sem erro. O … |
| `17` | Tamanho do arquivo baixado em megabytes decimais | aritmética | Confirma que o download do portal da ANEEL trouxe um arquivo de tamanho plausivel. Divide por 1e6, ou seja, megabyte decimal (10^6), e nao mebibyte (… **Risco:** So mede tamanho, nao integridade: um download truncado ou uma pagina de erro HTML salva com o nome do zip passam por aqui sem serem detectados; a fal… |
| `19-20` | Tamanho descompactado do CSV em gigabytes decimais | aritmética | file_size e o tamanho descompactado declarado no cabecalho do zip, nao o tamanho comprimido, e e o que dimensiona a leitura em streaming das linhas 2… **Risco:** file_size vem do cabecalho do zip e e um valor declarado: um zip corrompido pode declarar um tamanho que nao corresponde ao conteudo real. z.infolist… |
| `21` | Inicializacao dos acumuladores e do conjunto de referencias | agregação | Versao reduzida do acumulador de 01_cde.py: o vetor por municipio tem dois elementos em vez de cinco (so linhas e liquido), e entra um conjunto ref p… **Risco:** Como pos, neg e n_negativos nao sao acumulados aqui, o CSV de 2026 nao permite reproduzir a analise de estornos que docs/CORRECOES.md C4 fez para 202… |
| `23-25` | Leitura em streaming da safra de 2026 | leitura | Mesmo chunk de 2.000.000 e mesmo encoding latin-1 de 01_cde.py, com uma troca de coluna: SigAgente sai e AnmReferencia entra. AnmReferencia e usada n… **Risco:** Os mesmos de 01_cde.py: latin-1 nunca falha e pode mascarar mojibake; usecols com nomes fixos quebra se a ANEEL renomear coluna; chunksize fixo assum… |
| `26` | Contagem total e uniao dos meses de referencia | agregação | A uniao de conjuntos e o que torna a coleta de referencias independente da ordem e do numero de chunks. O resultado e impresso na linha 38 e serve pa… **Risco:** dropna() remove referencias ausentes: se parte das linhas vier sem AnmReferencia, ref parece limpo e a ausencia nao e reportada. O conjunto registra … |
| `27` | Filtro da subclasse de baixa renda na safra de 2026 | regra normativa | Identico ao filtro da linha 12 de 01_cde.py, o que e o que torna as duas safras comparaveis: mesma categoria, mesma normalizacao por strip, mesma com… **Risco:** Mesmos riscos do filtro de 01_cde.py, agravados por uma ausencia: aqui nao ha o histograma de DscTipoSubsidio (linha 11 de 01_cde.py). Se a ANEEL ren… |
| `28` | Curto-circuito do chunk sem linhas de baixa renda (2026) | limiar | Mesma guarda de 01_cde.py linha 13: evita groupby e iterrows sobre DataFrame vazio. Nao altera totais, porque um bloco vazio contribuiria zero. **Risco:** Igual ao de 01_cde.py: um filtro quebrado produz todos os chunks vazios, o loop imprime o progresso normalmente e o script termina com acc vazio e CS… |
| `29` | Conversao do valor monetario pt-BR (2026) | aritmética | Caractere por caractere igual a linha 14 de 01_cde.py, o que preserva a comparabilidade entre as duas safras: qualquer vies introduzido pelo parsing … **Risco:** Os mesmos da linha 14 de 01_cde.py: remocao incondicional do ponto multiplica por cem valores em formato americano; errors="coerce" cria NaN silencio… |
| `30` | Conversao do codigo IBGE para numero (2026) | cartografia | Igual a linha 15 de 01_cde.py. A chave geografica e o codigo IBGE convertido para numero, para casar com as demais bases do pipeline. **Risco:** Os mesmos: zero a esquerda e destruido na conversao; codigo nao numerico vira NaN e sera descartado na linha seguinte sem contagem. Se a malha munici… |
| `31` | Descarte de municipio invalido e truncamento para inteiro (2026) | cartografia | Identico a linha 16 de 01_cde.py. Linha sem codigo IBGE utilizavel sai do universo agregado; o cast para int fixa o tipo da chave do dicionario acc. **Risco:** Descarte silencioso e nao contado, como em 01_cde.py, mas aqui sem o equivalente da conferencia registrada em docs/VALIDACAO.md para 2024: nao ha ref… |
| `32` | Agregacao por municipio no chunk, apenas linhas e liquido | agregação | Duas agregacoes sobre a mesma coluna v por codigo IBGE. "size" conta todas as linhas do grupo, inclusive aquelas cujo v virou NaN no parsing; "sum" e… **Risco:** Mesma assimetria entre size e sum de 01_cde.py: uma linha com valor ilegivel entra na contagem de beneficiarios e nao na soma de subsidio. Como pos e… |
| `33-34` | Acumulacao dos dois agregados entre chunks (2026) | agregação | Contagem e soma sao aditivas entre blocos, o que e a condicao que torna a acumulacao por chunk equivalente a um groupby sobre o arquivo inteiro. setd… **Risco:** Como em 01_cde.py, g tem coluna inteira (linhas) e coluna float (liq); iterrows converte a linha para Series float64, entao r.linhas chega como float… |
| `36-37` | Montagem do quadro municipal com colunas nomeadas pela safra | agregação | Os nomes de coluna carregam a etiqueta da safra, o que e o que permite juntar varias safras lado a lado sem colisao; 08b_nacional_2026.py linha 12 le… **Risco:** Se TAG contiver caractere invalido para nome de arquivo, o to_csv falha so aqui, depois de todo o processamento dos 2 GB. A ordem das linhas segue a … |
| `38-39` | Totais finais da safra: municipios, linhas e subsidio | agregação | Fecha a execucao com os tres numeros que permitem conferir a safra: quais meses de referencia o arquivo continha, quantos municipios entraram e quant… **Risco:** int() trunca em direcao a zero sobre uma soma que e float por causa do iterrows. O subsidio impresso e a soma dos liquidos municipais, ja com estorno… |

### `reconstrucao/pipeline/02_tarifa.py`

| linhas | operação | espécie | o que faz, e o que a tornaria errada |
|---|---|---|---|
| `5-5` | Normalizacao numerica de decimal em formato brasileiro | leitura | O CSV e lido inteiro como texto (dtype=str, linha 6), entao qualquer valor precisa ser convertido antes de somar. A rotina assume a convencao brasile… **Risco:** Se algum registro ja vier com ponto decimal (ex.: '0.695'), a remocao do ponto transforma 0.695 em 695 -- erro silencioso de fator 1000, sem excecao.… |
| `7-10` | Filtro do segmento tarifario B1 residencial convencional | regra normativa | Sao seis igualdades exatas de string, combinadas por conjuncao logica, que isolam um unico segmento do cadastro tarifario: baixa tensao B1, modalidad… **Risco:** Comparacao por igualdade literal, inclusive de acentuacao ('Tarifa de Aplicação', 'Não se aplica'): qualquer mudanca de grafia, acento, encoding ou c… |
| `11-11` | Tarifa residencial em R$/kWh: soma TUSD+TE dividida por 1000 | aritmética | A tarifa cheia de aplicacao e a soma das duas parcelas publicadas separadamente pela ANEEL: TUSD (uso do sistema de distribuicao) e TE (energia). A s… **Risco:** Se a coluna de origem ja estiver em R$/kWh, a divisao por 1000 subestima a tarifa em tres ordens de grandeza sem erro. Se num() tiver removido um pon… |
| `13-13` | Chave CNPJ da distribuidora convertida para numero | leitura | Esta e a metade tarifaria da ponte CNPJ: o CNPJ e convertido para numero para poder casar com o NumCNPJ do INDGER (linha 18), que passa pela mesma co… **Risco:** A conversao para numero descarta zeros a esquerda -- inofensivo se ambos os lados passam por to_numeric, destrutivo se algum dia um lado for comparad… |
| `14-15` | Mediana das tarifas por CNPJ | estatística | Apos os filtros de segmento e vigencia, um mesmo CNPJ ainda pode ter mais de uma linha (vigencias que se tocam na data de corte, ou registros repetid… **Risco:** Com numero par de registros no grupo, a mediana do pandas devolve a media dos dois centrais -- um valor que pode nao corresponder a nenhuma tarifa ho… |
| `18-18` | Unidades consumidoras ativas com ausente convertido em zero | leitura | uc e o peso da media ponderada da linha 27 e o denominador da cobertura da linha 23; cnpj e a outra ponta da ponte com a tarifa. O fillna(0) e uma de… **Risco:** fillna(0) trata 'nao informado' como 'zero unidades consumidoras'. Isso e invisivel na cobertura da linha 23 (numerador e denominador ambos zerados n… |
| `19-20` | Codigo IBGE numerico e truncado para inteiro | cartografia | cod_ibge e a chave geografica de toda a saida do arquivo (agrupamentos das linhas 21, 23, 27 e o CSV final). A conversao para inteiro padroniza a cha… **Risco:** astype(int) trunca em direcao a zero: se algum codigo vier com parte fracionaria por erro de digitacao, o municipio muda silenciosamente. astype(int)… |
| `21-21` | Soma de UC ativas por municipio e distribuidora | agregação | O INDGER reporta por data de referencia; o groupby colapsa todas as datas de 2024 em um unico registro por par municipio-distribuidora, que e a granu… **Risco:** QtdUCAtiva e um estoque, nao um fluxo: somar o estoque ao longo dos periodos de 2024 produz UC-periodo, nao UC. Como peso relativo dentro de um mesmo… |
| `22-22` | Ponte CNPJ: juncao a esquerda entre par municipio-distribuidora e tar… | leitura | Esta e a ponte propriamente dita: o CNPJ e o unico campo comum entre a base tarifaria e a base comercial, e o how='left' preserva todos os pares muni… **Risco:** A juncao supoe que tc tem no maximo uma linha por CNPJ; isso e garantido pelo groupby da linha 14, mas se deixasse de ser, o merge multiplicaria linh… |
| `23-23` | Cobertura municipal: fracao das UC casadas a uma tarifa | aritmética | Mede que parcela do parque consumidor do municipio ficou associada a uma tarifa pela ponte CNPJ. O numerador soma apenas os pares com tarifa; o denom… **Risco:** A guarda max(soma,1) nao e neutra: se 0 < soma_uc < 1 o denominador e inflado para 1 e a cobertura sai subestimada. Como uc e uma soma de UC-periodo … |
| `24-25` | Contagem e percentual de municipios acima do limiar de cobertura | estatística | Diagnostico da ponte: soma de uma serie booleana conta os municipios aprovados, media da mesma serie booleana devolve a proporcao, multiplicada por 1… **Risco:** O percentual e calculado sobre os municipios que chegaram ate cob; municipios perdidos por CNPJ ou codigo IBGE ilegivel nao entram no denominador e o… |
| `26-26` | Descarte dos pares sem tarifa antes da ponderacao | limiar | Separa o conjunto usado para medir cobertura (j, com os nao casados) do conjunto usado para calcular a media (jj, so os casados). A media ponderada d… **Risco:** A media resultante e representativa apenas na medida em que cob for alto; sem o corte da linha 29, um municipio com 5% das UC casadas receberia uma t… |
| `27-28` | Tarifa municipal: media ponderada por UC ativas com recuo para media … | estatística | Um municipio pode ser atendido por mais de uma distribuidora; a ponderacao por unidades consumidoras ativas faz a tarifa municipal refletir a distrib… **Risco:** A media ponderada supoe pesos nao negativos e soma de pesos estritamente positiva. A guarda cobre apenas a soma nula; nao cobre pesos negativos (QtdU… |
| `29-31` | Corte de cobertura de 90% para o conjunto reportado | limiar | Define o conjunto sobre o qual as estatisticas das linhas 32-33 sao calculadas: apenas municipios em que pelo menos 90% das UC ficaram associadas a u… **Risco:** O corte e aplicado apenas ao que se imprime. O arquivo gravado na linha 34 e wm, nao ok: o CSV contem todos os municipios, inclusive os de cobertura … |
| `32-32` | Estatisticas descritivas da tarifa municipal | estatística | Resumo de cinco numeros usado como conferencia de ordem de grandeza da tarifa construida, com quatro casas decimais. Os quantis usam a interpolacao l… **Risco:** A distribuicao e sobre municipios, nao sobre consumidores nem sobre domicilios: cada municipio pesa igual, entao a mediana impressa nao e a tarifa me… |
| `33-34` | Amplitude como razao entre maximo e minimo | aritmética | Razao entre extremos, exibida como multiplo, para contrastar a dispersao da tarifa entre municipios com a constante unica 0.695701 impressa ao lado. … **Risco:** Divisao por zero se o minimo for zero; o filtro tar>0 da linha 12 e a ponderacao com pesos nao negativos tornam isso improvavel, mas nao ha guarda ex… |

### `reconstrucao/pipeline/03a_decfec_conjunto.py`

| linhas | operação | espécie | o que faz, e o que a tornaria errada |
|---|---|---|---|
| `6-7` | Leitura seletiva da serie de continuidade coletiva | leitura | A tabela e longa: a mesma coluna VlrIndiceEnviado carrega DEC, FEC e NumCon, distinguidos so por SigIndicador. A restricao de colunas e necessaria pa… **Risco:** VlrIndiceEnviado e o valor declarado pela distribuidora. Todo o subsistema herda o auto-reporte sem nenhuma checagem contra valor homologado. NumPeri… |
| `8` | Filtro de ano e de indicadores DEC/FEC | leitura | 2024 e fixado literalmente no codigo, sem constante nem parametro. O codigo nao registra por que 2024 e o ano de referencia; o script 03c, que roda a… **Risco:** Ano codificado em literal em tres lugares distintos deste arquivo (linhas 8 e 15 e a mensagem da linha 11). Se apenas um for atualizado, a serie do a… |
| `9-10` | Apuracao anual por conjunto: soma, media e contagem dos periodos | agregação | DEC e FEC mensais sao grandezas de fluxo acumulavel: horas de interrupcao no mes e numero de interrupcoes no mes. Somar os doze meses produz a grande… **Risco:** size conta LINHAS, nao meses distintos. Uma serie com o mesmo periodo duplicado dá meses=12 sem cobrir doze meses. Nada aqui exige meses==12: uma ser… |
| `11` | Distribuicao do numero de periodos por serie | estatística | E o unico diagnostico de completude da serie neste script. Serve para ver se as series tem mesmo doze periodos, mas o resultado nao alimenta nenhum f… **Risco:** Diagnostico sem consequencia. Se a distribuicao mostrar muitas series com n diferente de 12, nada no script reage; o operador precisa ler o console p… |
| `14` | Conversao do limite de texto em formato brasileiro para numero | leitura | O CSV bruto grava o limite com virgula decimal e ponto de milhar, conforme conferido no cabecalho e nas primeiras linhas do arquivo. Remover o ponto … **Risco:** A remocao incondicional do ponto e destrutiva se algum registro vier em convencao anglo-saxa: "8.00" vira 800, cem vezes maior, sem erro nenhum. Tamb… |
| `15` | Selecao dos limites do ano e dos indicadores DEC/FEC | regra normativa | O arquivo de limites e historico: contem linhas de 1990, 1996 e demais anos, conforme verificado no proprio CSV. Sem o filtro por ano o merge multipl… **Risco:** O ano 2024 e literal e independente do literal da linha 8: nada garante que os dois sejam o mesmo ano. Se um conjunto nao tiver linha de limite para … |
| `16` | Deduplicacao dos limites por conjunto e indicador | leitura | Garante que o merge seja um-para-um e nao infle o numero de linhas. O codigo nao registra se ha de fato duplicidade no arquivo nem quantas linhas for… **Risco:** drop_duplicates mantem a PRIMEIRA ocorrencia na ordem fisica do CSV, que nao e ordenacao semantica nenhuma. Se houvesse mais de um limite valido para… |
| `18` | Juncao interna entre serie apurada e limite | leitura | So faz sentido calcular razao onde existe limite. O inner impoe isso. **Risco:** O inner descarta silenciosamente conjuntos com serie mas sem limite 2024, e limites sem serie. A perda nao e contada nem impressa: o print da linha 2… |
| `19` | Razao da media mensal sobre o limite anual (criterio ATUAL, descartad… | aritmética | O nome ATUAL e o proprio codigo indicam que esta e a formula que estava em uso antes e que o script foi escrito para questionar: ele calcula as duas … **Risco:** Incompatibilidade de unidade: horas/mes dividido por horas/ano. O resultado nao tem interpretacao normativa e subestima violacao por um fator de cerc… |
| `20` | Razao da soma anual sobre o limite anual (criterio CORRIGIDO) | regra normativa | O limite do arquivo da ANEEL e indexado por AnoLimiteQualidade e nao tem coluna de periodicidade, o que e consistente com ser limite anual. Dividir a… **Risco:** Sem protecao contra VlrLimite igual a zero (inf) ou ausente (NaN). Se soma12 vier de serie incompleta (meses<12, permitido pelas linhas 9-10), a raza… |
| `23-24` | Medianas de apuracao e de limite por indicador | estatística | Mediana e usada aqui, e nao media, sem que o codigo registre a razao; e coerente com distribuicoes de DEC muito assimetricas a direita, em que a medi… **Risco:** A mediana da soma dividida pela mediana do limite NAO e a mediana da razao. Ler as duas linhas impressas como se dessem a razao tipica e um erro de i… |
| `25` | Contagem de violacoes pelo criterio da media | limiar | O limiar 1 marca o ponto em que o apurado iguala o limite. O comparador e >= e nao >, ou seja, estar exatamente no limite ja e contado como violacao. **Risco:** Aplicar o limiar 1 a uma razao com unidades incompativeis (mes sobre ano) torna a contagem quase sempre zero: um conjunto so apareceria aqui se a med… |
| `26` | Contagem e percentual de violacoes pelo criterio da soma | limiar | Media de uma serie booleana e a proporcao de True; multiplicada por 100 vira percentual. O denominador e o numero de conjuntos COM limite 2024 para a… **Risco:** Percentual calculado sobre a base pos-merge-inner: conjuntos sem limite nao entram nem no numerador nem no denominador, o que muda o percentual sem q… |
| `27` | Gravacao da apuracao por conjunto | leitura | Este arquivo e a unica entrada de 03b (linha 10 de 03b), logo a fronteira entre os dois scripts. As duas razoes concorrentes sao gravadas juntas. **Risco:** A coluna meses e gravada mas 03b nunca a le, entao a informacao de completude da serie existe no disco e nao e usada: series incompletas atravessam a… |

### `reconstrucao/pipeline/04_territorio.py`

| linhas | operação | espécie | o que faz, e o que a tornaria errada |
|---|---|---|---|
| `4-4` | Leitura da SIDRA 4712 e descarte do primeiro elemento | leitura | O endpoint /values do SIDRA devolve o primeiro elemento como linha de rotulos das dimensoes, nao como dado; o corte [1:] o remove. docs/FONTES.md ide… **Risco:** Busca online sem snapshot: diferente do arquivo de favelas (lido de data/raw de 2026-09-05 na linha 8), o denominador depende do estado da API no mom… |
| `5-5` | Selecao da categoria 381 e conversao do total de domicilios | leitura | Mantem so as linhas da categoria 381 da segunda dimensao e converte o valor para numero. O arquivo nao registra o que 381 designa; docs/FONTES.md e q… **Risco:** int(r["D1C"]) levanta ValueError se vier codigo nao numerico (linhas de agregado, se aparecerem). errors="coerce" transforma os marcadores de indispo… |
| `6-6` | Eliminacao de nulos e deduplicacao do denominador | leitura | Remove linhas com valor nao convertido e garante um registro por municipio antes do merge da linha 13. **Risco:** dropna() sem subset elimina a linha inteira se qualquer coluna for NaN. drop_duplicates mantem a PRIMEIRA ocorrencia, que depende da ordem de chegada… |
| `7-7` | Contagem de municipios com total de domicilios | agregação | Diagnostico de cobertura do denominador. O CSV final tem 5.570 linhas, o que corresponde ao conjunto de municipios brasileiros. **Risco:** E so impressao: nao ha assert contra 5.570, entao uma queda de cobertura da API nao interrompe o pipeline e propaga um universo menor para 05 e 06a. |
| `10-11` | Extracao de domicilios em favela (tabela 9887, variavel 9909) | leitura | Seleciona a variavel 9909 da tabela 9887 e le a serie de 2022. docs/FONTES.md descreve essa variavel como 'domicilios em favelas e comunidades urbana… **Risco:** b["resultados"][0] pega apenas o primeiro bloco de resultados: se o JSON trouxer mais de um cruzamento de classificacao, os demais sao ignorados sem … |
| `12-12` | Contagem de municipios com favela mapeada | agregação | Diagnostico do numerador. Nao e o mesmo conjunto que a linha 16 marca: len(fav) conta linhas do arquivo de favelas, e favela_mapeada conta os que sob… **Risco:** Se o arquivo de favelas tiver municipios ausentes da tabela 4712, len(fav) sera maior que a soma de favela_mapeada e os dois numeros impressos diverg… |
| `13-13` | Juncao a esquerda do numerador sobre o denominador | agregação | O universo do resultado passa a ser o da tabela 4712: todo municipio com total de domicilios entra, com ou sem favela. **Risco:** how='left' descarta municipios que existam so no arquivo de favelas, sem contagem nem aviso. Se a API do 4712 vier incompleta numa rodada, o municipi… |
| `14-14` | Imputacao de zero para municipio sem favela mapeada | regra normativa | Quem nao aparece no arquivo de favelas passa a contar como zero domicilio em favela. A distincao entre 'nao mapeado' e 'zero' fica apenas na coluna c… **Risco:** A imputacao nao e neutra a jusante: em 06a_indice_corrigido.py a coluna d4_corr entra numa normalizacao min-max (linhas 11-15 daquele arquivo), e no … |
| `15-15` | Participacao de favela sobre domicilios do municipio (D4 corrigido) | aritmética | Participacao dos domicilios em favela no total de domicilios do municipio, como o proprio titulo impresso na linha 17 declara. Substitui a variavel a… **Risco:** Numerador e denominador vem de tabelas diferentes do Censo 2022 (9887 e 4712); a compatibilidade dos universos e afirmada em docs/FONTES.md, nao veri… |
| `16-16` | Marcacao de municipio com favela efetivamente mapeada | regra normativa | Preserva a informacao que o fillna(0) da linha 14 apagou: distinguir zero medido de ausencia de levantamento. A coluna e propagada ate o app (09_payl… **Risco:** A marca vem da presenca em fav DEPOIS do dropna da linha 11: um municipio cujo valor foi suprimido pelo IBGE e classificado como nao mapeado e recebe… |
| `18-19` | Estatisticas de d4 sobre o subconjunto com favela mapeada | estatística | Restringe as estatisticas aos municipios com levantamento, o que evita que os zeros imputados na linha 14 puxem a mediana para zero. E coerente com a… **Risco:** O rotulo '656' esta escrito a mao dentro da f-string e nao vem de len(x): no CSV gerado favela_mapeada soma 655, entao o texto impresso e o subconjun… |
| `21-22` | Juncao com a base original para comparar antes e depois | agregação | Aproxima a variavel antiga e a nova no mesmo municipio para as comparacoes impressas nas linhas 23-27. **Risco:** merge sem how usa inner: municipios ausentes de ipem_municipios.csv saem da comparacao sem contagem. Isso afeta so o que e impresso — m, salvo na lin… |
| `23-25` | Leitura pontual de nove capitais por codigo fixo | leitura | Amostra de conferencia manual. O codigo nao registra o criterio de escolha das nove cidades. **Risco:** .iloc[0] levanta IndexError se o codigo nao estiver em cmp — por exemplo se a rodada da API perder um municipio ou se ele faltar na base original. A … |
| `27-27` | Oito maiores participacoes | estatística | Mostra o extremo superior da distribuicao ao lado da variavel antiga. **Risco:** nlargest desempata pela ordem de ocorrencia das linhas, o que e arbitrario se houver valores iguais. round(3) e so exibicao e nao altera o CSV. O rec… |
| `28-28` | Gravacao do D4 corrigido | leitura | Define o contrato consumido por 05_domicilio.py (linha 16) e por 06a_indice_corrigido.py (linha 6). O denominador dom_total_mun sai daqui e vira base… **Risco:** Salva m, e nao cmp: o arquivo mantem municipios ausentes da base original. favela_mapeada e gravado como texto 'True'/'False' e relido como booleano … |

### `reconstrucao/pipeline/05_domicilio.py`

| linhas | operação | espécie | o que faz, e o que a tornaria errada |
|---|---|---|---|
| `6-7` | Varredura dos 27 arquivos de renda por UF | leitura | A tabela 10296 foi baixada por UF; docs/FONTES.md registra '27 arquivos, um por UF'. Diferente do 04, aqui a leitura e de snapshot local e nao da API. **Risco:** glob nao garante ordem, o que importa por causa do drop_duplicates da linha 14. Se um arquivo de UF faltar, os municipios daquele estado simplesmente… |
| `9-11` | Selecao do bloco cuja ultima classificacao e a categoria Total | regra normativa | A tabela 10296 e cruzada por classes de rendimento nominal mensal domiciliar por pessoa; manter so a categoria 'Total' da ultima classificacao pega o… **Risco:** Depende da ordem das classificacoes no JSON: cats[-1] supoe que a classe de rendimento e a ultima. Se o IBGE reordenar ou acrescentar outra classific… |
| `12-13` | Leitura dos moradores por municipio (SIDRA 10296) | leitura | A unidade da tabela 10296 e pessoas, nao domicilios — docs/FONTES.md registra isso explicitamente como ressalva ('unidade e pessoas, nao domicilios')… **Risco:** Se o universo do numerador exclui moradores que o denominador conta como residentes do domicilio (pensionistas e empregados domesticos), o tamanho me… |
| `14-14` | Deduplicacao dos moradores por municipio | leitura | Garante um registro por municipio antes do merge da linha 17. **Risco:** Com 27 arquivos por UF, duplicata so apareceria se um municipio constasse de dois arquivos ou de dois blocos de resultado aceitos pelo filtro da linh… |
| `15-15` | Soma nacional de moradores | agregação | Conferencia de ordem de grandeza contra a populacao do Censo 2022. docs/VALIDACAO.md cita 202,0 milhoes e explica a diferenca para a populacao total … **Risco:** sum() ignora NaN, mas os NaN ja foram eliminados na linha 14, entao a soma e sobre os municipios sobreviventes: uma perda de cobertura aparece como t… |
| `16-17` | Juncao dos moradores com o total de domicilios | agregação | O denominador do tamanho do domicilio e reaproveitado do arquivo do 04, e nao lido de novo da API. **Risco:** merge sem how usa inner: o universo vira a intersecao e municipios presentes em so uma das fontes desaparecem sem contagem. Ha acoplamento por arquiv… |
| `18-18` | Tamanho medio do domicilio | aritmética | Razao de dois totais municipais, exatamente como docs/METODO.md linha 51 descreve: 'moradores (SIDRA 10296) / domicilios (SIDRA 4712)'. E o fator que… **Risco:** E razao de totais, nao media do tamanho dos domicilios: as duas coincidem apenas se o universo de pessoas do numerador for exatamente o de moradores … |
| `20-20` | Distribuicao do tamanho do domicilio | estatística | Diagnostico da dispersao entre municipios, que e o argumento do arquivo 06b: se o tamanho variasse pouco, trocar o denominador per capita pelo domici… **Risco:** quantile usa interpolacao linear (padrao do pandas) e ignora NaN, entao o percentil pode ser de um subconjunto menor sem que a impressao diga. Estati… |
| `21-21` | Amplitude do tamanho do domicilio | aritmética | Quantifica em quantas vezes o fator de conversao varia entre municipios. Nos dados gerados da 2,5608, que e o '2,56x' citado em docs/CORRECOES.md e n… **Risco:** Razao entre dois extremos: um unico municipio atipico em qualquer das pontas move o numero inteiro, e o valor sustenta uma afirmacao publicada. Minim… |
| `22-22` | Gravacao do tamanho do domicilio | leitura | Contrato consumido por 06b_renda_domiciliar.py (linha 5) e, por heranca, por 06c, 06e e pelo payload do app (campo 'hh'). **Risco:** O arquivo guarda numerador e denominador ao lado da razao, o que permite auditoria; nenhuma checagem de faixa plausivel e gravada junto. Um valor abs… |

### `reconstrucao/pipeline/05b_cadunico_serie.py`

| linhas | operação | espécie | o que faz, e o que a tornaria errada |
|---|---|---|---|
| `10-18` | Paginacao cumulativa da API do SAGI | leitura | A API do SAGI responde em blocos; o codigo desloca o offset somando a quantidade de documentos efetivamente recebidos e para quando o offset alcanca … **Risco:** Se a API repetir documentos entre paginas, start avanca alem do conjunto real e ha perda; se numFound mudar durante a coleta, ha perda ou duplicacao … |
| `20-20` | Coercao do codigo municipal do SAGI | leitura | O SAGI devolve codigo_ibge com seis digitos, sem digito verificador: verificavel no proprio produto do script, reconstrucao/dados/cadunico_sagi.csv, … **Risco:** O campo gravado como cod_ibge NAO e o codigo IBGE de 7 digitos usado no resto do pipeline. Qualquer merge direto por cod_ibge com as demais tabelas d… |
| `21-21` | Coercao numerica das cinco contagens de familias | leitura | F[2:] e o fatiamento que pula codigo_ibge e anomes e alcanca exatamente os cinco campos de contagem declarados nas linhas 6-8. docs/FONTES.md linhas … **Risco:** df.get(c) devolve None quando a coluna nao veio na resposta daquela competencia; nesse caso a coluna nao recebe dado real e o total nacional da compe… |
| `24-27` | Empilhamento das tres competencias | agregação | Tres competencias fixadas no proprio codigo. docs/FONTES.md linha 31 as identifica como dez/2024, mar/2026 e ago/2026, e diz que a serie historica e … **Risco:** pd.concat sem ignore_index preserva indices repetidos das tres fatias; qualquer operacao posterior por indice se torna ambigua. Se um municipio exist… |
| `31-35` | Somas nacionais por faixa e por competencia | agregação | Agregacao simples por competencia. O cabecalho impresso na linha 30 ('NACIONAL: familias ate 1/2 SM per capita (criterio TSEE)') declara que a primei… **Risco:** Series.sum() ignora NaN: municipio ausente ou coercao falha reduz o total nacional sem sinalizar. O groupby('anomes') supoe que anomes chegou com tip… |

### `reconstrucao/pipeline/05c_serie_mensal.py`

| linhas | operação | espécie | o que faz, e o que a tornaria errada |
|---|---|---|---|
| `15-15` | Contexto TLS com verificacao desligada | leitura | Todo valor deste arquivo vem de uma unica origem remota, e esta linha define sob que garantia essa origem e aceita. O codigo nao registra por que a v… **Risco:** Sem verificacao de cadeia nem de nome, qualquer resposta que chegue no endereco e aceita como se fosse do MDS. Um intermediario, um proxy corporativo… |
| `17-21` | Lista de campos pedidos ao indice misocial | leitura | A selecao de campos e o que fixa a definicao operacional de cada serie: pobreza aqui e a contagem de familias cadastradas em pobreza pelo criterio do… **Risco:** Os nomes sao literais do indice remoto. Se o SAGI renomear, aposentar ou zerar um campo, a consulta continua valida e o campo simplesmente deixa de v… |
| `23-28` | Geracao das competencias mensais | aritmética | A comparacao de tuplas (a, m) <= fim equivale a comparar ano e, em empate, mes, o que so descreve a ordem cronologica porque m permanece no intervalo… **Risco:** Os limites estao fixos no codigo como valores padrao e nada os liga a uma data de referencia do restante do pipeline. Se a fonte for atualizada, a se… |
| `33-33` | Montagem da URL de consulta com paginacao | leitura | O tamanho de pagina 2000 e menor que os 5.571 municipios por competencia, o que torna a paginacao obrigatoria e nao opcional: sao tres requisicoes po… **Risco:** anomes entra na consulta sem escape; como e gerado internamente com digitos apenas, isso nao e explorado aqui, mas a construcao por concatenacao de s… |
| `36-38` | Acumulo das paginas e criterio de parada | agregação | O deslocamento avanca pelo numero de documentos efetivamente recebidos, e nao por rows fixo, de modo que uma pagina curta nao abre buraco na sequenci… **Risco:** numFound conta documentos, nao valores: uma competencia pode declarar 5.571 documentos e trazer todos os campos vazios, caso que este bloco nao disti… |
| `40-40` | Tabela a partir dos documentos JSON | leitura | A construcao infere as colunas dos proprios documentos. Como o indice omite chaves ausentes em vez de devolve-las nulas, o conjunto de colunas varia … **Risco:** Se docs vier vazio, df fica sem colunas e a linha 41 falha ao acessar df.codigo_ibge, o que dispara a excecao capturada no laco de tentativas e leva … |
| `41-41` | Chave do municipio convertida para numero | aritmética | A docstring afirma que o codigo do SAGI tem seis digitos, sem digito verificador, e que a juncao com a malha do IBGE exige esse ajuste. O consumidor … **Risco:** O nome ibge6 e uma afirmacao que o codigo nao verifica: nada testa que o valor tem seis digitos. Se a fonte passar a devolver o codigo de sete digito… |
| `42-42` | Contadores convertidos para numero com coercao | aritmética | O df.get evita erro quando a competencia volta sem o campo, e o coerce evita erro quando o valor nao e numerico. Sao duas decisoes que convertem ause… **Risco:** Este e o ponto onde uma competencia vazia passa a parecer uma competencia presente: sem o campo, a coluna vira inteiramente nula e o script segue, im… |
| `47-55` | Tres tentativas por competencia | agregação | A captura e de Exception, isto e, qualquer erro, e nao apenas falha de rede. Isso inclui o KeyError de uma resposta com formato diferente e o Attribu… **Risco:** Tratar erro de conteudo como erro transitorio faz o script repetir tres vezes uma consulta que nunca vai funcionar e depois seguir adiante. A mensage… |
| `56-57` | Descarte da competencia falha e acumulo | agregação | A falha de uma competencia nao interrompe a execucao: a serie sai mais curta e o arquivo final nao guarda nenhum registro da lacuna, apenas a mensage… **Risco:** Uma lacuna no meio da serie fica indistinguivel de uma competencia que nunca existiu. Quem ler o CSV adiante vera meses ausentes sem saber se a fonte… |
| `58-58` | Contagem impressa por competencia | apresentação | E a unica conferencia de cobertura durante a coleta, e corresponde ao numero que a docstring afirma ter sido verificado antes, 5.571 municipios por c… **Risco:** O numero imprime 5.571 tanto para uma competencia cheia quanto para uma em que todos os quatro contadores vieram ausentes, porque as linhas existem d… |
| `60-60` | Empilhamento das competencias | agregação | Empilhar em formato longo preserva a chave de tempo em coluna, o que e o formato que o pivot de 10d_payload_serie.py consome. O ignore_index descarta… **Risco:** Se uma competencia trouxer colunas diferentes das demais, a uniao cria colunas com nulos em vez de falhar; isso e absorvido pela selecao da linha 66,… |
| `61-65` | Renomeacao dos quatro contadores | serialização | E aqui que a definicao da fonte e substituida por um rotulo curto. O nome eleg em particular e uma interpretacao: a fonte diz renda familiar per capi… **Risco:** O rotulo eleg afirma elegibilidade a algum beneficio sem que o arquivo diga a qual, e sem que o criterio de meio salario minimo seja necessariamente … |
| `66-66` | Selecao de colunas e descarte de codigo invalido | limiar | O filtro incide apenas sobre a chave do municipio, escolha coerente com o uso adiante, em que ibge6 vira indice do pivot. Os quatro contadores mantem… **Risco:** O descarte e silencioso e nao contado: nada informa quantas linhas cairam nem de quais competencias. Se a fonte mudar o formato do codigo e todos vir… |
| `67-67` | Chave do municipio truncada para inteiro | aritmética | A conversao existe para que o CSV grave 110001 e nao 110001.0, e para que a comparacao de conjuntos com a malha em 10d_payload_serie.py, que usa c //… **Risco:** astype(int) trunca em vez de arredondar. Aqui os valores vem de codigos inteiros e o ponto flutuante de dupla precisao os representa exatamente nessa… |
| `68-68` | Gravacao da serie em CSV | serialização | OUT e definido em _paths.py como a pasta dados dentro de reconstrucao, criada se nao existir, e e a mesma pasta lida por 10a_payload_comparacao.py e … **Risco:** As quatro colunas de contagem estao em ponto flutuante por causa da coercao da linha 42, de modo que o CSV grava 1234.0 onde o dado e uma contagem in… |
| `71-71` | Contagem de competencias e de municipios | estatística | Sao contagens de valores distintos, nao de linhas, e por isso nao detectam duplicata. Servem para confrontar com o esperado da docstring, 33 competen… **Risco:** Uma competencia cujos quatro contadores vieram todos vazios entra nessa contagem como presente, pois as linhas existem. O numero de municipios e a un… |
| `72-72` | Totais nacionais por competencia | agregação | Somar contagens municipais para chegar ao total nacional so e valido porque cada municipio aparece uma vez por competencia e os conjuntos sao disjunt… **Risco:** Como nulo soma como zero, uma competencia em que todos os quatro contadores vieram ausentes aparece como total zero, e nao como total desconhecido. E… |
| `73-74` | Conversao para milhoes e arredondamento | apresentação | A divisao por um milhao e a mudanca de unidade declarada na linha 76, e o arredondamento a duas casas fixa a resolucao da leitura em dez mil familias… **Risco:** A resolucao de dez mil familias esconde variacoes menores entre meses consecutivos, que e justamente a escala de movimento esperada em serie mensal d… |
| `76-76` | Declaracao de unidade e de definicao | apresentação | E o unico ponto do arquivo em que a unidade da tabela impressa e a definicao de eleg ficam escritas. A afirmacao corresponde ao nome do campo de orig… **Risco:** A legenda vive no terminal e nao no CSV, de modo que o arquivo publicado em reconstrucao/dados sai sem unidade nem definicao. O texto tambem esta des… |

## Continuidade do fornecimento

48 operações em 3 arquivos.

### `reconstrucao/pipeline/03b_decfec_municipio.py`

| linhas | operação | espécie | o que faz, e o que a tornaria errada |
|---|---|---|---|
| `7` | Filtro do ano de referencia na serie bruta | leitura | Aqui o filtro NAO restringe SigIndicador, porque o script precisa de NumCon, que nao e DEC nem FEC. **Risco:** O literal 2024 tem de coincidir com o ano usado em 03a para gerar decfec_conj_2024.parquet. Nada verifica: se divergirem, os pesos de consumidores de… |
| `8` | Consumidores por conjunto: media dos periodos de NumCon | agregação | NumCon e estoque, nao fluxo: o numero de unidades consumidoras existentes naquele periodo. Somar os doze meses daria doze vezes o parque. A media dos… **Risco:** A media supoe que o conjunto existiu o ano inteiro: um conjunto criado em outubro tem media sobre 3 periodos, nao sobre 12, e portanto nao e subestim… |
| `9` | Cobertura e parque total de consumidores | agregação | Serve de conferencia de ordem de grandeza contra o parque nacional conhecido. O codigo nao compara com nenhum valor de referencia: quem le e que deci… **Risco:** Soma de medias anuais por conjunto: se um mesmo consumidor estiver em dois conjuntos em momentos distintos do ano, ele e contado duas vezes. O total … |
| `11-12` | Chave conjunto para municipio, deduplicada | cartografia | As duas fontes da ANEEL grafam a chave de forma diferente (IdeConjUnidConsumidoras no indqual, IdeConjUndConsumidoras no parquet); o rename existe so… **Risco:** A relacao e MUITOS-PARA-MUITOS, verificada no proprio arquivo: o conjunto 3 aparece ligado a sete municipios do Piaui. Isso significa que o merge adi… |
| `13-14` | Pivotagem de soma anual e limite por indicador | agregação | Passar de formato longo para largo e o que permite comparar DEC e FEC do mesmo conjunto na mesma linha (o criterio do pior, linha 16). aggfunc="first… **Risco:** Se houvesse duplicidade de (conjunto, indicador), "first" escolheria arbitrariamente pela ordem da tabela, silenciosamente. O script 03c faz a mesma … |
| `15` | Razoes DEC e FEC sobre limite, por conjunto | regra normativa | Normalizar cada indicador pelo seu proprio limite e o que torna DEC (horas) e FEC (contagem) comparaveis entre si, porque as duas razoes passam a viv… **Risco:** Divisao sem guarda: limite zero produz inf; limite ausente produz NaN. Recalcula o que 03a ja calculou na coluna rel_CORRIGIDO_soma_sobre_limite, ent… |
| `16` | Criterio do pior indicador por conjunto | regra normativa | Tomar o maximo faz a violacao de QUALQUER um dos dois indicadores marcar o conjunto: rel >= 1 equivale a (rel_dec >= 1 OU rel_fec >= 1). E um criteri… **Risco:** max com skipna padrao do pandas IGNORA NaN: um conjunto que so tem DEC devolve rel = rel_dec, indistinguivel de um conjunto avaliado nos dois indicad… |
| `17` | Juncao conjunto-municipio e descarte de razao ausente | cartografia | E aqui que a apuracao sai do dominio da distribuidora (conjunto) e entra no dominio territorial (municipio). Como a relacao e muitos-para-muitos, a l… **Risco:** O inner descarta municipios cujos conjuntos nao tem apuracao e conjuntos sem municipio mapeado, sem contabilizar a perda. A replicacao carrega o cons… |
| `18` | Peso do conjunto com ausente tratado como zero | aritmética | np.average rejeita NaN no vetor de pesos; preencher com zero e o que permite chamar a funcao. O efeito e excluir da media ponderada, sem excluir da b… **Risco:** fillna(0) nao e neutro: e uma afirmacao de que o conjunto nao tem consumidores. O conjunto continua contando em d3_max (que ignora o peso) e em n_con… |
| `19-20` | Soma dos pesos do municipio | agregação | E calculada uma vez por municipio para servir de guarda das tres medias ponderadas abaixo (o teste w>0) e tambem como valor exportado na coluna consu… **Risco:** Essa soma NAO e a populacao de consumidores do municipio: e a soma dos parques dos conjuntos que tocam o municipio, incluindo a parcela desses conjun… |
| `21` | Pior conjunto do municipio (d3_max) | regra normativa | Mede a pior situacao existente dentro do municipio, independente de quantas pessoas ela atinge. E usada em valida_granularidade.py (linha 21) em conj… **Risco:** Ignora completamente o peso: um conjunto com 30 consumidores define o indicador de uma capital. E um estimador de maximo, portanto sobe monotonicamen… |
| `22` | Media das razoes ponderada por consumidores (d3_pond) | agregação | Ponderar pelo numero de consumidores faz a razao municipal refletir a experiencia do consumidor tipico do municipio, e nao a do conjunto tipico. Essa… **Risco:** Media ponderada supoe pesos nao negativos e soma de pesos diferente de zero; so a segunda condicao e testada. O fallback quando W=0 muda a DEFINICAO … |
| `23` | DEC anual em horas, ponderado por consumidores | agregação | Diferente de d3_pond, esta coluna preserva a unidade fisica (horas sem energia no ano), o que permite comunicar o resultado sem depender do limite re… **Risco:** soma12_DEC pode vir de serie com menos de 12 meses, porque 03a nao filtra completude; nesse caso o valor em horas subestima o ano e e comunicado como… |
| `24-25` | Contagem de conjuntos e parque exportado | agregação | nunique protege contra dupla contagem caso o par (conjunto, municipio) apareca repetido. n_conj e usado em valida_granularidade.py (linha 21) para se… **Risco:** n_conj mede fragmentacao administrativa da distribuidora, nao do territorio; municipio com n_conj=1 pode estar dentro de um conjunto enorme que cobre… |
| `28` | Estatisticas de violacao por d3_max | limiar | Quantifica em quantos municipios existe PELO MENOS UM conjunto fora do limite. O comparador >= inclui o municipio exatamente no limite. **Risco:** Percentual sobre os municipios que sobreviveram aos dois inner joins, nao sobre os 5570 do pais; o print nao diz qual e o denominador em relacao ao u… |
| `29` | Estatisticas de violacao por d3_pond | limiar | Impressa lado a lado com a de d3_max para expor a diferenca entre o criterio do pior conjunto e o criterio do consumidor medio. O script existe, pelo… **Risco:** Aplicar limiar 1 a uma MEDIA de razoes nao tem o mesmo significado normativo que aplicar a uma razao: um municipio com metade dos consumidores a 1,9 … |
| `30` | Distribuicao do DEC anual ponderado | estatística | Mediana, p95 e maximo descrevem a cauda direita de uma distribuicao assimetrica. O codigo nao registra por que p95 e nao p90 ou p99. **Risco:** quantile usa interpolacao linear por padrao, entao o p95 impresso nao e necessariamente um valor observado. O maximo e um unico municipio e pode ser … |
| `34` | Gravacao do agregado municipal | leitura | E o ponto de entrega deste subsistema ao indice: 06a_indice_corrigido.py (linha 6) le esse CSV e renomeia d3_pond para d3_corr e dec_h_pond para dec_… **Risco:** O CSV nao carrega nenhuma marca de qualidade: nao registra quantos conjuntos do municipio tinham serie incompleta, nem quais municipios caíram no fal… |

### `reconstrucao/pipeline/03c_continuidade_2024_2025.py`

| linhas | operação | espécie | o que faz, e o que a tornaria errada |
|---|---|---|---|
| `7-8` | Parse do limite em formato brasileiro (replicado) | leitura | Identica a de 03a linha 14; o codigo repete a conversao em vez de compartilhar funcao. **Risco:** Duplicacao literal da regra de parse em dois arquivos: uma correcao em um nao alcanca o outro. Mesma fragilidade da remocao incondicional do ponto: "… |
| `12-13` | Recorte anual da serie DEC/FEC dentro da funcao ano | leitura | Aqui o ano vira parametro, ao contrario de 03a e 03b, onde e literal. E o que permite rodar a mesma apuracao para 2024 e 2025 e comparar. **Risco:** Nenhuma checagem de que o ano pedido existe na base com cobertura comparavel: se 2025 tiver menos conjuntos com doze meses enviados que 2024, a compa… |
| `14` | Soma anual e contagem de periodos por conjunto | agregação | Mesma apuracao de 03a linhas 9-10, sem a coluna media12 porque este script nao compara o criterio antigo. A contagem n aqui e usada de fato, na linha… **Risco:** size conta linhas, nao periodos distintos, entao duplicidade de periodo passa no teste n==12 da linha seguinte e infla a soma. |
| `15` | Exigencia de serie completa de doze periodos | limiar | Comparar soma anual contra limite anual so e legitimo se os doze periodos estiverem presentes; este filtro impoe isso. E a diferenca de politica mais… **Risco:** O filtro exige 12 LINHAS, nao 12 meses distintos: um conjunto com o mes 3 enviado duas vezes e o mes 11 ausente passa. Tambem introduz selecao: conju… |
| `16` | Limites do ano com deduplicacao | regra normativa | Aqui o ano do limite e o MESMO parametro a usado na serie, o que elimina o risco de descasamento que existe em 03a (dois literais independentes). **Risco:** Se o ano a nao tiver limites publicados (caso plausivel para o ano corrente), lim vem vazia e o merge da linha seguinte devolve tabela vazia, e o scr… |
| `17-18` | Juncao serie-limite e razao anual | regra normativa | Numerador e denominador na mesma unidade anual, e aqui com a garantia de 12 periodos dada pela linha 15. merge sem how explicito usa inner por padrao… **Risco:** Sem guarda contra VlrLimite zero (inf) ou NaN. O inner implicito (how omitido) descarta pares sem limite sem que isso esteja escrito no codigo, o que… |
| `19` | Consumidores por conjunto no ano | agregação | NumCon e estoque e por isso e promediado, nao somado, igual a 03b linha 8. Aqui o peso acompanha o ano da apuracao, ao contrario de 03d, que congela … **Risco:** NumCon nao passa pelo filtro de 12 periodos da linha 15: a media pode vir de um unico mes. Peso ausente vira NaN e depois zero na linha 24. |
| `20-21` | Pivotagem de razao e soma por indicador (aggfunc padrao) | agregação | Mesmo objetivo da pivotagem de 03b (colocar DEC e FEC na mesma linha), mas aqui o aggfunc nao e informado, de modo que o pandas aplica a media. O cod… **Risco:** Divergencia silenciosa entre dois scripts que calculam a mesma coisa: com duplicidade de (conjunto, indicador), 03b pegaria a primeira e 03c a media.… |
| `22` | Criterio do pior indicador (pior) | regra normativa | Mesmo criterio disjuntivo de 03b linha 16, escrito de novo com outro nome de coluna. pior >= 1 equivale a violar duracao ou frequencia. **Risco:** Mesma regra implementada em dois arquivos com nomes diferentes (rel em 03b, pior em 03c): um ajuste em um nao alcanca o outro. max ignora NaN, entao … |
| `23-24` | Juncao municipal e peso com ausente igual a zero | cartografia | Igual a 03b linhas 17-18. A replicacao do conjunto em cada municipio e inerente a relacao muitos-para-muitos da fonte. **Risco:** O peso continua sendo o parque do conjunto inteiro aplicado a cada municipio; nenhum rateio. dropna remove NaN mas nao inf. fillna(0) afirma zero con… |
| `25-28` | Agregacao municipal ponderada da razao e do DEC | agregação | Mesma definicao de d3_pond e dec_h_pond de 03b, reimplementada em lambda. A guarda x.w.sum()>0 evita a divisao por zero de np.average. **Risco:** Media ponderada supoe pesos nao negativos: peso negativo por erro de envio passaria e poderia produzir soma de pesos positiva com media distorcida, o… |
| `29-30` | Conjuntos violando DEC no ano | limiar | Contagem no nivel de conjunto, antes da agregacao municipal, o que permite separar violacao do conjunto de violacao do municipio. O rename por ano e … **Risco:** Denominador e a base ja filtrada por n==12 e por existencia de limite; nao e o universo de conjuntos. Contagem por conjunto, sem ponderar por consumi… |
| `33-34` | Juncao interna dos dois anos | leitura | O inner e o que garante painel balanceado: so municipios com apuracao completa nos dois anos entram na comparacao, condicao necessaria para que as tr… **Risco:** Municipio que perdeu cobertura em 2025 (por exemplo, conjunto que deixou de enviar doze meses) desaparece da comparacao inteira, inclusive da contage… |
| `35` | Indicadores binarios de violacao por ano | limiar | Binarizar em torno de 1 e o que permite as contagens de transicao. O comparador >= trata o municipio exatamente no limite como violador. **Risco:** Binarizar descarta a magnitude: um municipio a 0,99 e outro a 0,10 ficam identicos, e um municipio que caiu de 3,0 para 1,01 aparece como 'violava no… |
| `38-39` | Contagem e percentual de municipios acima do limite por ano | agregação | Como viol e 0/1, a media e a proporcao. Os dois anos usam o mesmo denominador \\|M\\| por construcao do inner join, o que torna a comparacao entre anos… **Risco:** O percentual e sobre o painel balanceado, nao sobre os municipios do pais nem sobre os municipios apurados em cada ano isoladamente. Contagem de muni… |
| `42-45` | Matriz de transicao entre os dois anos | agregação | E a tabela de contingencia 2x2 completa; as quatro celulas somam o total do painel, o que permite conferir consistencia com os totais da linha 38-39. **Risco:** Transicao medida sobre um limiar duro: um municipio que vai de 1,001 para 0,999 e contado como 'deixou de violar' embora nao tenha mudado praticament… |
| `48` | Variacao percentual da mediana do DEC entre anos | estatística | Razao de medianas menos um e a variacao relativa entre os dois valores centrais. O codigo nao registra por que compara medianas em vez da mediana das… **Risco:** A variacao da mediana NAO e a mediana das variacoes, e as duas podem ter ate sinais diferentes; o print nao distingue. Divisao sem guarda: mediana de… |
| `49` | Medianas da razao por ano | estatística | Mediana e escolhida sem justificativa registrada no codigo; e coerente com a assimetria da distribuicao de razoes, em que a media seria puxada por ca… **Risco:** Comparar medianas de dois anos supoe que o limite regulatorio nao mudou entre eles; se a ANEEL revisou limites de 2024 para 2025, parte da variacao d… |
| `50-51` | Municipios que pioraram entre os anos | limiar | Comparacao estrita, sem faixa de tolerancia: qualquer aumento, por menor que seja, conta como piora. Contrasta com 03d linha 44, que usa banda de +-5… **Risco:** Sem banda morta, o resultado tende a aproximadamente metade dos municipios por ruido puro quando nao ha tendencia real; o numero impresso nao disting… |

### `reconstrucao/pipeline/03d_continuidade_semestre.py`

| linhas | operação | espécie | o que faz, e o que a tornaria errada |
|---|---|---|---|
| `9` | Janela semestral fixada em seis periodos | limiar | Define a janela janeiro a junho, usada tanto como filtro (NumPeriodoIndice<=K) quanto como criterio de completude (nunique==K). E o que torna 2026 co… **Risco:** Assume que NumPeriodoIndice e mensal e comeca em 1 em janeiro. O codigo nunca verifica essa hipotese. Se algum agente usar periodicidade diferente (t… |
| `10-15` | Base comum de conjuntos com semestre completo nos tres anos | agregação | Aqui a completude e medida com nunique, ou seja, periodos DISTINTOS, e nao com size como em 03a e 03c: este e o unico dos quatro scripts imune a dupl… **Risco:** A intersecao e restritiva: basta um ano com envio incompleto para o conjunto sair dos tres. Se o envio incompleto correlacionar com qualidade ruim de… |
| `16` | Peso congelado no parque de 2025 | agregação | Usar um unico vetor de pesos para os tres anos faz a variacao entre anos refletir so a mudanca do DEC, e nao a mudanca da composicao do parque. 2025 … **Risco:** Peso congelado e uma escolha com efeito mensuravel: se um conjunto crescer muito entre 2024 e 2026, sua importancia real muda e o calculo nao acompan… |
| `17-21` | DEC acumulado de janeiro a junho por conjunto e ano | agregação | DEC mensal e acumulavel, portanto a soma dos seis primeiros periodos e a duracao total de interrupcao no semestre. Restringir a base comum e o que to… **Risco:** A soma usa todas as linhas com periodo <= 6, enquanto a checagem de completude usou periodos distintos: se houver periodo duplicado, o conjunto passa… |
| `22-23` | Painel largo de conjuntos e vetor de pesos | agregação | concat com axis=1 alinha pelo indice (o identificador do conjunto). Como os tres vetores vem todos da mesma base comum, o alinhamento e completo por … **Risco:** fillna(0) aplicado ao vetor de pesos afirma zero consumidores para conjunto sem NumCon em 2025, excluindo-o silenciosamente das medias ponderadas nac… |
| `26-27` | DEC semestral nacional ponderado e mediana por conjunto | agregação | A media ponderada estima as horas sem energia do consumidor tipico; a mediana por conjunto estima as do conjunto tipico. Imprimir as duas expoe a dif… **Risco:** Media ponderada supoe peso nao negativo e soma nao nula, nenhuma das duas testada aqui. O peso e o parque de 2025 aplicado aos tres anos. Se algum de… |
| `29-34` | Variacoes percentuais interanuais do DEC semestral | aritmética | Como os tres anos usam a mesma base de conjuntos, o mesmo vetor de pesos e a mesma janela de seis periodos, a razao entre eles isola a variacao do DE… **Risco:** Divisao sem guarda: DEC_pond do ano base igual a zero daria inf. Variacao percentual de uma media ponderada e dominada pelos conjuntos grandes; um un… |
| `36-40` | DEC semestral municipal ponderado por consumidores | agregação | Mesmo padrao de agregacao municipal de 03b e 03c: media das grandezas dos conjuntos que tocam o municipio, ponderada pelo parque do conjunto, com fal… **Risco:** Aqui nao ha dropna antes do groupby (diferente de 03b e 03c): um municipio cujos conjuntos tenham dec NaN produz s_a NaN silencioso. Peso e o parque … |
| `41-43` | Mediana municipal por ano | estatística | Mediana entre municipios, cada municipio contando uma vez, complementa a media ponderada nacional das linhas 26-27, que conta cada consumidor uma vez… **Risco:** Mediana de municipios da peso igual a um municipio de mil habitantes e a uma capital, e como DEC rural e sistematicamente maior, a mediana municipal … |
| `44` | Classificacao de tendencia municipal com banda de 5 por cento | limiar | A banda de +-5% cria uma zona morta para nao classificar flutuacao como mudanca. E o oposto da politica de 03c linha 50, que usa comparacao estrita s… **Risco:** O 5% e arbitrario e nao esta ligado a nenhuma medida de variabilidade dos dados: o mesmo municipio pode mudar de categoria se o limiar for 3% ou 10%.… |
| `46-48` | Contagem de municipios por tendencia e gravacao | agregação | Fecha o script com a distribuicao das tres categorias. O CSV gravado contem cod_ibge, s2024, s2025, s2026 e tend. **Risco:** A contagem por categoria nao pondera por consumidores nem por populacao: 'melhorou' em contagem de municipios pode conviver com piora para a maioria … |

## Consolidação municipal

156 operações em 7 arquivos.

### `reconstrucao/pipeline/06a_indice_corrigido.py`

| linhas | operação | espécie | o que faz, e o que a tornaria errada |
|---|---|---|---|
| `5-6` | Leitura das fontes corrigidas e renomeacao de d3 | leitura | O rename apenas troca os nomes vindos de 03b (d3_pond = razao apurado/limite ponderada por consumidores; dec_h_pond = DEC anual ponderado) pelos nome… **Risco:** O sufixo 'corr' sugere uma correcao aritmetica que nao existe: e o mesmo numero de 03b. DataFrame.rename nao levanta erro se a coluna nao existir, en… |
| `7-9` | Junção das dimensoes por codigo IBGE | leitura | O left join preserva a lista de municipios do arquivo base e admite ausencia nas fontes corrigidas; essas ausencias sao exatamente o que a contagem n… **Risco:** Nenhuma verificacao de cardinalidade (validate= nao e usado): se cod_ibge se repetir em tar, d3 ou d4, o merge multiplica linhas e todo o resto do sc… |
| `10` | D2 — peso da conta de 100 kWh sobre a renda per capita | aritmética | O fator 100 e o consumo mensal suposto em kWh, nao conversao percentual: 06b_renda_domiciliar.py escreve a mesma conta como df["conta"]=df.tarifa_mun… **Risco:** Parece percentual por causa do *100 e nao e; multiplicar por 100 de novo na leitura dobraria a escala. renda_referencia igual a zero produz inf, ause… |
| `11-13` | Normalizacao min-max com winsorizacao no percentil 99 (funcao wmm) | estatística | Winsorizacao superior antes do min-max: o clip no percentil 99 impede que o maior outlier defina sozinho o denominador e comprima todos os demais mun… **Risco:** Depois do clip, cerca de 1% dos municipios fica empatado no maximo e perde ordem entre si — o indice nao distingue o pior do centesimo pior. O minimo… |
| `14-16` | Aplicacao da normalizacao as quatro dimensoes e escala 0-100 | aritmética | O fator 100 e apenas mudanca de escala de leitura; nao altera ordem nem a media relativa entre dimensoes, ja que e aplicado igualmente as quatro. **Risco:** As quatro dimensoes medem coisas de dominios distintos (cobertura de beneficio, preco/renda, continuidade do fornecimento, territorio) e so ficam som… |
| `17` | Contagem de dimensoes disponiveis por municipio | agregação | Conta quantas dimensoes normalizadas existem para o municipio; e a condicao usada na linha seguinte para admitir ou nao o municipio no indice. **Risco:** Mede disponibilidade, nao qualidade: uma dimensao presente mas medida com cobertura ruim (por exemplo d3 apurado em um unico conjunto consumidor, com… |
| `18` | IPEM v2 — indice composto por media aritmetica simples das quatro dim… | agregação | Nenhum vetor de pesos e declarado no arquivo: .mean(axis=1) sobre quatro colunas atribui 1/4 a cada dimensao. A mascara np.where exige as quatro dime… **Risco:** Pesos iguais so seriam neutros se as quatro dimensoes fossem comensuraveis apos o min-max — nada no arquivo testa isso, e a escala de cada uma depend… |
| `20` | Cobertura do indice: municipios com as quatro dimensoes | agregação | Quantifica a perda de base imposta pela mascara da linha 18. **Risco:** len(df) so equivale ao numero de municipios se os merges das linhas 7-9 nao tiverem duplicado linhas — nada verifica isso. |
| `21` | Faltantes por dimensao | agregação | Atribui a perda de base a cada dimensao, separando quem falta por continuidade, por tarifa/renda ou por territorio. **Risco:** Conta faltantes da coluna normalizada, nao da bruta; se wmm devolvesse NaN por span zero, a dimensao inteira apareceria como faltante e o diagnostico… |
| `22` | Ranking do indice antigo e do indice v2 | estatística | ascending=False faz 'posicao 1' significar o pior caso segundo o indice, coerente com o uso de nsmallest nas linhas 25 e 32 para listar o topo. **Risco:** method='min' deixa buracos na sequencia (tres empatados em 1 fazem o proximo ser 4). NaN recebe rank NaN, entao rk_new so existe para quem tem as qua… |
| `23-24` | Deslocamento mediano de posicao entre o indice antigo e o v2 | estatística | Mede quanto a troca de metodo reordena os municipios; e uma das evidencias de instabilidade do indice composto registradas em docs/VALIDACAO.md. **Risco:** int() trunca em vez de arredondar, e a mediana de um numero par de observacoes pode terminar em ,5. rk_old foi calculado sobre toda a base e rk_new s… |
| `25-26` | Sobreposicao dos 100 primeiros colocados | estatística | Testa se o topo do ranking — a parte que teria uso pratico — se mantem quando o metodo muda. **Risco:** Com method='min' ha empates, e nsmallest corta o excedente pela ordem das linhas do DataFrame, escolha arbitraria que altera a composicao exata do co… |
| `27` | Correlacao de Spearman entre o indice antigo e o v2 | estatística | Pearson aplicado sobre postos e, por definicao, o coeficiente de Spearman; a conversao previa a postos torna as duas escalas comparaveis. **Risco:** Este rank usa o default method='average', diferente do method='min' da linha 22 — duas convencoes de empate convivem no mesmo arquivo. O coeficiente … |
| `28-29` | Correlacao de cada dimensao bruta com o indice | estatística | Usa a dimensao bruta, e nao a normalizada n_dj; para a correlacao de postos isso so difere no trecho winsorizado. Mede quanto de cada dimensao sobrev… **Risco:** E auto-correlacao: cada dimensao entra no proprio indice com peso 1/4, entao o valor tem piso positivo por construcao e nao serve como validacao exte… |
| `30-32` | Listagem dos 20 primeiros e arredondamento de exibicao | leitura | round(3) atua so na copia impressa; o CSV da linha 33 guarda os valores nao arredondados. **Risco:** d2_corr e d4_corr sao fracoes pequenas e, com 3 casas, municipios distintos aparecem com o mesmo numero na tela; a impressao sugere precisao que o va… |
| `33` | Persistencia do indice rejeitado | leitura | 06b, 06c, 06d e 06e leem essa cadeia (ipem_v2 → ipem_v3 → ipem_v4 → ipem_v5) por causa das outras colunas; o indice em si nao e usado adiante — 06e n… **Risco:** O indice rejeitado continua gravado em quatro arquivos intermediarios com nomes que sugerem versoes sucessivas de um produto valido; qualquer consumi… |

### `reconstrucao/pipeline/06b_renda_domiciliar.py`

| linhas | operação | espécie | o que faz, e o que a tornaria errada |
|---|---|---|---|
| `4-6` | Anexacao do tamanho do domicilio ao indice | agregação | Traz o fator de conversao para o arquivo onde a renda per capita vira renda domiciliar. **Risco:** how='left' preserva todos os municipios do ipem_v2; quem faltar em domicilio_tamanho.csv fica com moradores_por_domicilio NaN e propaga NaN para rend… |
| `7-7` | Renda domiciliar a partir da renda de referencia per capita | aritmética | Converte renda por pessoa em renda da casa multiplicando pelo tamanho medio do domicilio do municipio. O argumento explicito do arquivo esta no comen… **Risco:** O produto de duas medias so e a media do produto se renda per capita e tamanho do domicilio forem independentes dentro do municipio. O proprio projet… |
| `8-8` | Conta mensal hipotetica de 100 kWh | aritmética | Despesa mensal de energia supondo consumo de 100 kWh, com a tarifa da distribuidora que atende o municipio. O titulo impresso na linha 11 declara as … **Risco:** Os 100 kWh sao suposicao escrita no codigo, nao medicao: o proprio pipeline usa 80 kWh adiante (06e_distribuidora.py linha 15, ancorado na Lei 15.235… |
| `9-9` | Peso da conta com denominador per capita | aritmética | Reproduz o denominador do indice original para servir de termo de comparacao; o comentario na propria linha declara que essa e a formula em uso no pr… **Risco:** Divide uma despesa do domicilio por uma renda de individuo: as duas grandezas nao se referem a mesma unidade de consumo e o quociente nao e fracao de… |
| `10-10` | Peso da conta com denominador domiciliar | aritmética | Poe numerador e denominador na mesma unidade de consumo: despesa do domicilio sobre renda do domicilio. O comentario chama de 'peso real', o que e ju… **Risco:** Herda tudo que afeta renda_domiciliar: a hipotese de independencia entre renda e tamanho do domicilio e a aproximacao por pontos medios das faixas. P… |
| `12-13` | Mediana, p90 e maximo dos dois pesos, em pontos percentuais | estatística | Multiplicacao por 100 converte fracao em ponto percentual. Os rotulos 'atual' e 'correto' sao do autor, nao decorrem do calculo. **Risco:** median, quantile e max ignoram NaN, entao as estatisticas podem ser de um subconjunto menor que o total de municipios sem que a impressao diga quanto… |
| `14-14` | Contagem de municipios acima de 10% da renda domiciliar | limiar | Aplica o limiar de 10% da renda, atribuido no texto impresso a Boardman. O codigo nao traz referencia bibliografica nem distingue limiar absoluto de … **Risco:** Comparacao com NaN devolve False: municipio sem dado e contado como abaixo do limiar em vez de ausente, e a contagem nao revela isso. Limiar estrito … |
| `15-15` | Contagem e participacao acima de 5% | limiar | Segundo corte, mais baixo, para mostrar alguma variacao onde o limiar de 10% nao seleciona ninguem. A linha seguinte contrapoe a referencia da POF 20… **Risco:** O .mean() de uma serie booleana divide pelo numero TOTAL de linhas do DataFrame, incluindo aquelas cujo d2_domiciliar e NaN (que comparam como False)… |
| `18-18` | Ranking por cada denominador | estatística | ascending=False faz a posicao 1 ser o maior peso da conta, isto e, a situacao pior. **Risco:** rank() sem method usa 'average': empates recebem posicao fracionaria, diferente do method='min' usado em 06a_indice_corrigido.py linha 22 para os ran… |
| `19-19` | Deslocamento mediano absoluto de posicao | estatística | Mede em quantas posicoes o municipio tipico se move quando o denominador muda. Como d2_domiciliar = d2_percap / moradores_por_domicilio, o deslocamen… **Risco:** %d trunca o float em vez de arredondar. abs() descarta o sinal, entao um deslocamento simetrico (tantos subindo quanto descendo) aparece igual a um d… |
| `20-21` | Sobreposicao dos 100 piores | agregação | nsmallest sobre a coluna de POSTO seleciona as melhores posicoes, ou seja, os 100 municipios de maior peso da conta em cada criterio; a intersecao do… **Risco:** Com ranks 'average', empates geram valores fracionarios e nsmallest corta arbitrariamente no limite dos 100. Se houver menos de 100 linhas validas, n… |
| `23-23` | Tamanho medio do domicilio por UF | agregação | Identifica quais UFs seriam mais penalizadas pelo denominador per capita, que e a tese do arquivo: onde o domicilio e maior, dividir pela renda por p… **Risco:** Media simples entre municipios da UF, nao ponderada por domicilios nem por populacao: um estado com muitos municipios pequenos tem o perfil dominado … |
| `24-25` | Cinco maiores e cinco menores UFs | estatística | Extremos da ordenacao por UF. tail(5) sobre serie decrescente devolve as cinco menores, em ordem crescente de posicao — ou seja, a ultima impressa e … **Risco:** Nao ha teste de significancia nem intervalo: duas UFs separadas por 0,01 pessoa por domicilio aparecem como ordens distintas. O arredondamento de exi… |
| `26-26` | Gravacao do ipem_v3 | leitura | Contrato consumido por 06c_faixas_cadunico.py (linha 19). De tudo que este arquivo calcula, o que sobrevive rio abaixo e moradores_por_domicilio: 06c… **Risco:** As colunas d2_percap e d2_domiciliar ficam gravadas no arquivo sem marca de que sao diagnostico e nao entram no indice publicado; quem ler o CSV sem … |

### `reconstrucao/pipeline/06c_faixas_cadunico.py`

| linhas | operação | espécie | o que faz, e o que a tornaria errada |
|---|---|---|---|
| `4-4` | Caminho base dos dados brutos da ANEEL | leitura | Fixa a raiz de onde vem tarifa e INDGER. O codigo nao registra por que a pasta aneel e a fonte, apenas a usa. **Risco:** Se RAW apontar para outra copia dos dados brutos, ou se a pasta for movida, todas as leituras seguintes falham ou leem outra versao sem aviso. Concat… |
| `5-5` | Conversor de decimal brasileiro para numero | leitura | O CSV da ANEEL vem em formato brasileiro, com ponto como separador de milhar e virgula como separador decimal. Remover o ponto antes de trocar a virg… **Risco:** Se algum campo ja vier em formato ingles, com ponto decimal, a remocao do ponto multiplica o valor por uma potencia de dez sem erro visivel. errors="… |
| `6-6` | Leitura da tabela de tarifas homologadas | leitura | dtype=str evita que o pandas adivinhe tipo e estrague os decimais brasileiros antes da conversao controlada da linha 5. A data 2026-09-05 no caminho … **Risco:** Caminho e data estao fixos no codigo. Se a ANEEL republicar o arquivo com outras colunas ou outra codificacao, a leitura quebra ou muda o resultado s… |
| `7-9` | Selecao da tarifa da subclasse Baixa Renda | regra normativa | Recorte por igualdade exata nos cinco campos descritivos que isolam a tarifa de aplicacao da subclasse Baixa Renda no grupo B1 convencional. E o mesm… **Risco:** Comparacao por igualdade exata de textos acentuados ('Tarifa de Aplicação', 'Não se aplica'): qualquer mudanca de grafia, caixa ou codificacao no arq… |
| `7-7` | Normalizador de texto das colunas de classificacao | leitura | Permite comparar os descritores da ANEEL por igualdade exata sem que espaco acidental derrube a linha. O codigo nao registra ter observado tais espac… **Risco:** Limpa so as bordas. Diferenca de acentuacao, de caixa, espaco duplo interno ou caractere nao separavel continua fazendo a comparacao falhar, e a linh… |
| `8-8` | Filtro normativo da tarifa B1 subclasse Baixa Renda | regra normativa | Seleciona a tarifa aplicavel ao consumidor de baixa tensao residencial de baixa renda, excluindo tarifa de referencia e modalidades horarias. E o mes… **Risco:** Depende de os cinco rotulos virem escritos exatamente assim, com acento. A ausencia de filtro por DscClasse aqui, que em 02_tarifa.py exige Residenci… |
| `9-9` | Recorte das linhas de tarifa e conversao das datas de vigencia | leitura | A vigencia precisa ser data para permitir o corte temporal da linha 11. O codigo nao informa o formato esperado, confia na deteccao automatica do pan… **Risco:** Sem format explicito, o pandas infere o padrao e pode trocar dia por mes em datas ambiguas. errors="coerce" transforma data ilegivel em NaT, e NaT fa… |
| `10-10` | Tarifa Baixa Renda em reais por kWh, soma TUSD mais TE | aritmética | A tarifa aplicada ao consumidor e a soma da parcela de uso do sistema de distribuicao com a parcela de energia. A divisao por mil converte a unidade … **Risco:** Se um dos dois componentes vier ausente, a soma vira NaN e a distribuidora perde a tarifa. O valor resultante e sem tributos, ICMS, PIS e COFINS nao … |
| `12-12` | Tarifa Baixa Renda por distribuidora, mediana das vigencias | estatística | Uma mesma distribuidora pode aparecer com mais de uma linha vigente na data, por posto tarifario ou por desdobramento de registro. A mediana escolhe … **Risco:** Se as multiplas linhas representarem grandezas diferentes, e nao repeticoes da mesma tarifa, a mediana mistura coisas distintas e produz um numero qu… |
| `13-13` | Leitura do INDGER comercial, unidades consumidoras por municipio | leitura | Essa tabela e o que permite saber qual distribuidora atende qual municipio e com que peso, insumo da ponderacao da linha 18. Ler so quatro colunas re… **Risco:** Caminho e data fixos no codigo, sem verificacao de que o arquivo existe ou de que as colunas mudaram de nome. Se o parquet trouxer mais de um registr… |
| `15-16` | Unidades consumidoras com ausente tratado como zero | leitura | uc e o peso da media ponderada da linha 18. fillna(0) faz o registro sem informacao contribuir com peso nulo em vez de propagar NaN para a media do m… **Risco:** fillna(0) afirma 'nenhuma unidade consumidora' onde o dado e 'nao informado' - e uma decisao, nao uma leitura. Se todos os registros de um municipio … |
| `15-15` | Conversao do CNPJ e das unidades consumidoras, com ausente tratado co… | leitura | O CNPJ precisa virar numero para casar com o CNPJ da tabela de tarifas, convertido do mesmo modo na linha 10. O fillna(0) faz o registro sem quantida… **Risco:** fillna(0) confunde ausencia de informacao com ausencia de consumidor. Um municipio onde a distribuidora dominante nao reportou quantidade fica com pe… |
| `16-16` | Codigo IBGE numerico, descarte de chave ausente e conversao para inte… | leitura | O dropna antes do astype(int) e necessario, porque converter NaN para inteiro levanta erro. Sem chave de municipio ou de distribuidora a linha nao se… **Risco:** Registro sem municipio ou sem CNPJ e descartado sem contagem, entao a cobertura do universo nunca e verificada neste script. astype(int) trunca, enta… |
| `17-17` | Unidades consumidoras por par municipio e distribuidora, cruzadas com… | agregação | Consolida os doze meses de 2024 em um peso unico por par e anexa a tarifa da distribuidora. O dropna final remove pares sem tarifa Baixa Renda casada… **Risco:** O descarte silencioso e o ponto sensivel. Diferente de 02_tarifa.py, que calcula uma cobertura por municipio e depois filtra por cobertura de pelo me… |
| `18-18` | Tarifa Baixa Renda municipal, media ponderada por unidades consumidor… | estatística | Municipio atendido por mais de uma distribuidora recebe uma tarifa unica ponderada pelo numero de consumidores de cada uma, de modo que a distribuido… **Risco:** O ramo de media simples e acionado exatamente nos municipios onde a informacao de quantidade falhou, por ausencia virada zero na linha 15, e ali a ta… |
| `19-20` | Juncao com o indice municipal e contagem de cobertura | agregação | O left join preserva todos os municipios do indice e deixa NaN onde nao houve tarifa Baixa Renda; a contagem impressa e a unica medida do alcance des… **Risco:** Todo indicador 'social' derivado herda o NaN, e as estatisticas da linha 32 aplicam dropna, de modo que as linhas 'tarifa cheia' e 'tarifa social' da… |
| `19-19` | Juncao com o indice v3 e anexacao da tarifa Baixa Renda | leitura | A juncao a esquerda preserva todos os municipios de ipem_v3, mesmo os sem tarifa Baixa Renda apurada, que ficam nulos e serao excluidos linha a linha… **Risco:** Municipio presente em mb e ausente de ipem_v3 e descartado sem contagem. A chave cod_ibge precisa ter o mesmo tipo dos dois lados, aqui inteiro em am… |
| `20-20` | Contagem de municipios com tarifa Baixa Renda apurada | apresentação | Unica verificacao de cobertura do script. Mostra quantos municipios receberam tarifa, mas nao quanto do universo isso representa nem qual fracao de u… **Risco:** O numero e impresso, nao gravado nem comparado a limiar. Se a cobertura despencar entre execucoes, nada no arquivo de saida registra o fato e o pipel… |
| `22-23` | Renda domiciliar no teto da faixa Baixa Renda | aritmética | Os tetos do CadUnico sao definidos por pessoa e a conta de energia e paga por domicilio, entao a passagem de um para o outro exige multiplicar pelo t… **Risco:** O produto de um teto por pessoa pelo tamanho MEDIO do domicilio do municipio nao e o teto do domicilio tipico da faixa, porque domicilios de baixa re… |
| `24-27` | Peso da conta de 100 kWh sobre a renda no teto da faixa | aritmética | O cabecalho impresso nas linhas 28-29 declara exatamente a construcao: 'PESO DA CONTA DE 100 kWh SOBRE A RENDA DO DOMICILIO (teto da faixa CadUnico x… **Risco:** O peso e diretamente proporcional ao consumo suposto: 100 kWh e hipotese fixada nesta linha, e o proprio projeto adota 80 kWh como consumo de referen… |
| `24-24` | Peso da conta de 100 kWh na faixa Baixa Renda, tarifa cheia | aritmética | Multiplicar a tarifa em R$/kWh por 100 kWh produz o valor mensal de uma conta de consumo de referencia, e dividir pela renda do teto da faixa da a pa… **Risco:** O resultado e uma fracao, nao percentual; quem ler a coluna crua sem multiplicar por cem interpreta errado, e a linha 32 de fato multiplica por cem a… |
| `25-25` | Peso da conta de 100 kWh na faixa Baixa Renda, tarifa da subclasse so… | aritmética | Mesma conta da linha anterior, trocando a tarifa cheia pela tarifa da subclasse Baixa Renda apurada nas linhas 8 a 18. O codigo nao explica a diferen… **Risco:** A tarifa da subclasse e aplicada de forma plana aos 100 kWh, sem o desconto escalonado por faixa de consumo da Tarifa Social. O proprio pipeline trat… |
| `26-26` | Peso da conta de 100 kWh na faixa de pobreza, tarifa cheia | aritmética | Repete a conta da linha 24 sobre a faixa mais restrita, de renda per capita ate 218 reais, produzindo o peso na populacao mais pobre. Como o denomina… **Risco:** Os mesmos da linha 24. Alem disso, a razao entre peso_pob e peso_br e constante e igual a 706 dividido por 218 em todos os municipios, entao as duas … |
| `27-27` | Peso da conta de 100 kWh na faixa de pobreza, tarifa da subclasse soc… | aritmética | Combina a tarifa da subclasse Baixa Renda com o teto da faixa de pobreza, o caso mais severo das quatro combinacoes. O codigo nao registra por que as… **Risco:** Acumula a ressalva da linha 25, tarifa plana sem o desconto escalonado da Tarifa Social, com a da linha 26, denominador proporcional ao da outra faix… |
| `28-29` | Declaracao impressa da definicao e das unidades do peso | apresentação | E o unico lugar do arquivo onde ficam escritas tres decisoes de definicao: o consumo de referencia de 100 kWh, o uso do teto da faixa multiplicado pe… **Risco:** Essa documentacao existe apenas no que e impresso no terminal durante a execucao. Nao acompanha o CSV gravado na linha 33, entao quem consumir ipem_v… |
| `30-32` | Estatisticas de distribuicao dos quatro pesos e contagem acima de dez… | estatística | A multiplicacao por cem converte a fracao das linhas 24 a 27 em percentual so na apresentacao, mantendo a coluna gravada como fracao. O corte em 0,10… **Risco:** Cada uma das quatro linhas pode estar calculada sobre um conjunto diferente de municipios, porque o dropna e por coluna e tarifa_baixa_renda tem cobe… |
| `32-32` | Estatisticas dos pesos e contagem acima de 10% da renda | estatística | As multiplicacoes por 100 convertem a fracao em porcentagem para exibicao. O limiar 0,10 e aplicado sobre a fracao, logo corresponde a 10% da renda d… **Risco:** O dropna muda o conjunto de municipios entre as quatro linhas impressas: as linhas com tarifa_baixa_renda cobrem menos municipios que as com tarifa_m… |
| `33-33` | Gravacao do indice v4 | serialização | Passa adiante a base com tarifa_baixa_renda, as duas rendas de teto e os quatro pesos, insumo dos scripts seguintes do pipeline. index=False evita cr… **Risco:** Sobrescreve o arquivo sem verificacao. Grava em CSV sem tipos, entao o consumidor seguinte reinfere tudo. As colunas de peso vao gravadas como fracao… |
| `34-38` | Sobreposicao dos piores quartis de D1 e D3 contra o acaso | estatística | Sob independencia entre as duas ordenacoes, a probabilidade de um municipio estar simultaneamente no quarto superior de ambas e 0.25 * 0.25 = 0.0625,… **Risco:** O 0.0625 supoe que cada quartil contenha exatamente 25% da amostra, o que empates e o uso de >= (em vez de >) podem violar: com empates no quantil, c… |
| `34-35` | Recorte dos municipios com D3 corrigido definido | leitura | Toda a comparacao das linhas 36 a 41 exige d3_corr definido, entao o recorte e feito uma vez. O recorte NAO exige d1_lacuna_tsee definido, embora ess… **Risco:** Se d1_lacuna_tsee tiver nulos dentro de w, o quantil da linha 36 os ignora mas as comparacoes das linhas 37 e 41 tratam nulo como falso, entao o muni… |
| `35-36` | Corte no quartil superior de D1 e de D3 | estatística | Define os cortes do quarto superior de cada dimensao para testar se os piores municipios das duas coincidem. Os quantis sao calculados sobre w, ou se… **Risco:** O nome q1 designa o percentil 75, nao o primeiro quartil - nomenclatura enganosa que nao altera o calculo, mas confunde a leitura. Os cortes vem de w… |
| `36-36` | Limiares do pior quartil de D1 e de D3 | estatística | Define o pior quartil de cada dimensao de forma relativa ao proprio conjunto analisado, em vez de por valor absoluto. Isso torna o corte independente… **Risco:** O quantil e calculado sobre w, nao sobre a base completa, entao os limiares mudam se a cobertura de d3_corr mudar. O metodo de interpolacao e o padra… |
| `37-38` | Coincidencia dos piores quartis contra a hipotese de independencia | estatística | Sob independencia entre os dois ordenamentos, a probabilidade de um municipio estar ao mesmo tempo no quarto superior de D1 e no quarto superior de D… **Risco:** O valor 1/16 so vale se cada corte selecionar exatamente 25% da amostra. Com o operador >= e empates no valor do quantil - frequentes em indices norm… |
| `37-37` | Intersecao dos dois piores quartis | limiar | Conta a sobreposicao entre carencia de acesso a Tarifa Social e violacao de qualidade, que e a pergunta enunciada no titulo impresso na linha 34. O u… **Risco:** Comparacao com nulo devolve falso, entao municipio com d1_lacuna_tsee ausente e tratado como se estivesse fora do pior quartil, e nao como ausencia. … |
| `38-38` | Razao entre sobreposicao observada e sobreposicao esperada sob indepe… | estatística | Sob independencia entre as duas dimensoes, a probabilidade de um municipio estar no quartil superior de ambas e o produto das duas probabilidades mar… **Risco:** A constante 0,0625 so vale se cada corte realmente separar um quarto do conjunto. Com empates, ou com nulos em d1_lacuna_tsee tratados como falso na … |
| `39-39` | Correlacao de postos entre D1 e D3 corrigido | estatística | Correlacionar os postos, e nao os valores, mede associacao monotona sem depender da escala nem da forma da distribuicao de cada indicador, o que e ap… **Risco:** rank() atribui posto medio aos empates, e o padrao de corr e Pearson, entao o resultado equivale a spearman com correcao de empates, mas nada disso e… |
| `40-41` | Contagem de municipios em violacao do limite e cruzamento com o pior … | limiar | d3_corr e construido como razao entre indicador de continuidade observado e o limite regulatorio, entao o valor um e a fronteira: igual ou acima sign… **Risco:** O limiar 1 esta escrito diretamente no codigo, em mais de um arquivo, sem constante compartilhada. Nulo em d1_lacuna_tsee vira falso na conjuncao e r… |

### `reconstrucao/pipeline/06d_concentracao.py`

| linhas | operação | espécie | o que faz, e o que a tornaria errada |
|---|---|---|---|
| `29-29` | Leitura da base municipal v4 | leitura | O passo parte da base ja consolidada pelos passos anteriores. O codigo nao registra verificacao de integridade, contagem de linhas esperada ou chave … **Risco:** Se ipem_v4.csv tiver cod_ibge duplicado, todos os merges seguintes multiplicam linhas e as somas nacionais inflam sem qualquer aviso. Se cod_ibge for… |
| `32-33` | Anexo da CDE de dezembro de 2024 | leitura | O cabecalho do arquivo declara que as colunas de dezembro de 2024 sao preservadas porque a pagina de comparacao entre as duas datas depende delas. O … **Risco:** Municipio sem linha na CDE fica com linhas_tsee e subs_liquido nulos, e o subsidio por familia de dez/2024 sai nulo em vez de zero. Se cde_municipal.… |
| `36-38` | Anexo da CDE de marco de 2026 com renomeacao | leitura | O cabecalho justifica a escolha do arquivo: 01mar2026 e apontado como o unico mes de 2026 com as 103 distribuidoras presentes. O renomear e apenas de… **Risco:** A afirmacao sobre as 103 distribuidoras esta no comentario, nao e verificada em codigo aqui; se o arquivo de origem mudar de cobertura, nada nesta et… |
| `40-43` | Extracao dos elegiveis do SAGI na competencia 202603 | leitura | A definicao de elegivel adotada e a faixa de renda per capita ate meio salario minimo do CadUnico, criterio que o codigo escolhe por nome de campo. O… **Risco:** Se nenhuma linha tiver anomes igual a 202603, sg fica vazio, o merge devolve eleg_mar26 todo nulo e a cobertura sai integralmente nula, sem erro. Se … |
| `44-44` | Reducao do codigo IBGE de sete para seis digitos | aritmética | O cabecalho registra a razao: o codigo do SAGI tem seis digitos, sem digito verificador, e o da CDE tem sete. A divisao inteira por 10 descarta o ult… **Risco:** A operacao so e valida se cod_ibge for inteiro de 7 digitos. Com cod_ibge lido como float, o resultado ainda e float e o merge por ibge6 pode nao cas… |
| `45-45` | Casamento dos elegiveis por codigo de seis digitos | leitura | Junta o contingente do SAGI a base municipal pela chave de seis digitos construida na linha 44. O join a esquerda mantem os municipios sem correspond… **Risco:** Se sg tiver ibge6 duplicado, por exemplo por mais de uma competencia escapando ao filtro da linha 42, o join multiplica as linhas de df e infla todas… |
| `46-48` | Contagem de municipios sem o par casado | agregação | Verificacao de cobertura do casamento entre as duas pontas. A soma e de duas contagens independentes, nao de municipios distintos: um municipio nulo … **Risco:** A mensagem afirma que os ausentes ficam como nulo e nao como zero, mas a linha seguinte converte ben_mar26 nulo em zero. A mensagem nao descreve o qu… |
| `49-49` | Imputacao de zero nos beneficios ausentes de marco de 2026 | aritmética | Trata ausencia na CDE como ausencia de beneficio concedido no municipio. O codigo nao registra a razao dessa equivalencia entre dado faltante e valor… **Risco:** Se a ausencia for falha de reporte da distribuidora, e nao ausencia real de beneficiarios, o municipio aparece com cobertura zero e lacuna igual ao c… |
| `52-53` | Definicao das colunas da leitura do presente | aritmética | Copia de valor sem transformacao, para fixar os nomes que o restante do pipeline e o aplicativo passam a usar. O codigo nao registra por que duplica … **Risco:** As duas colunas de origem continuam em df e sao gravadas no CSV final, o que permite que um consumidor a jusante leia eleg_mar26 ou ben_mar26 acredit… |
| `54-54` | Lacuna bruta casada | aritmética | Diferenca direta entre contingente potencial e beneficios efetivos na mesma competencia. A versao bruta preserva o sinal, o que permite contar na lin… **Risco:** A subtracao pressupoe que uma familia elegivel corresponde a um beneficio, ou seja, que unidade consumidora e familia sao a mesma unidade de contagem… |
| `55-55` | Truncagem da lacuna em zero | limiar | Escolha de definicao: excesso de beneficios sobre elegiveis nao compensa deficit de outro municipio. Sem o corte, a soma nacional de nao atendidas se… **Risco:** O corte descarta informacao sobre a magnitude da sobrecobertura, que so sobrevive como contagem na linha 70. Se a sobrecobertura for erro sistematico… |
| `56-56` | Cobertura municipal em marco de 2026 | aritmética | Razao entre beneficios concedidos e contingente elegivel, ambos em marco de 2026, que e o ponto do passo segundo o cabecalho. O replace de zero por n… **Risco:** Municipio com elegiveis zero mas beneficios positivos vira nulo, e some dos mapas e ordenacoes em vez de aparecer como anomalia. A cobertura pode pas… |
| `60-60` | Subsidio por familia em marco de 2026 | aritmética | O comentario das linhas 58 e 59 registra a razao: manter quantidade e preco na mesma data, para que o valor em reais nao cruze o contingente de um me… **Risco:** Municipio com beneficios zero e subsidio positivo vira nulo. Se subs_mar26 vier liquido de estornos, o valor por familia pode ser negativo, o que a l… |
| `61-61` | Subsidio por linha de dezembro de 2024, preservado | aritmética | O comentario na propria linha marca que se trata de dezembro de 2024 e que e preservado, coerente com o cabecalho, que diz manter as colunas de 2024 … **Risco:** O nome subsidio_familia_liq sugere familia, mas o divisor e linhas_tsee. Quem consumir a coluna como reais por familia mede outra coisa. subs_liquido… |
| `62-62` | Reais nao acessados por municipio | aritmética | Estimativa do valor mensal que deixaria de ser transferido, obtida multiplicando a quantidade de familias nao atendidas pelo subsidio medio por benef… **Risco:** A hipotese implicita e forte: as familias fora do beneficio teriam o mesmo consumo, a mesma faixa de desconto e a mesma tarifa das ja atendidas. Se o… |
| `65-65` | Totais nacionais casados | agregação | Soma simples sobre todos os municipios da base. O sum do pandas ignora nulos por padrao, de modo que e soma apenas os municipios com elegiveis conhec… **Risco:** Assimetria com a linha 49: beneficiarios_mar26 ja teve nulo convertido em zero e entra completo, enquanto familias_elegiveis_mar26 nulo e simplesment… |
| `66-67` | Formatacao dos totais nacionais com separador de milhar | apresentação | Formatacao apenas de exibicao. O especificador .0f arredonda para o inteiro mais proximo; o separador usado e o da localidade padrao do Python, a vir… **Risco:** O arredondamento a zero casas pode fazer o valor impresso diferir do valor gravado. O separador com virgula nao segue a convencao brasileira de ponto… |
| `68-68` | Cobertura nacional casada | aritmética | Razao dos totais, nao media das coberturas municipais, o que da peso proporcional ao tamanho do municipio. O cabecalho declara o valor esperado desta… **Risco:** Nao ha protecao contra e igual a zero; se o filtro da linha 42 nao casar nada, a divisao levanta erro ou devolve nulo. O valor herda a assimetria de … |
| `69-69` | Soma nacional de familias nao atendidas | agregação | Soma das lacunas ja truncadas em zero, como o proprio rotulo declara. E diferente de max(e - b, 0) no agregado: somar positivos por municipio nao com… **Risco:** O total depende do corte da linha 55 e da imputacao de zero da linha 49; municipio sem dado de beneficio entra com lacuna igual ao contingente inteir… |
| `70-70` | Contagem de municipios em sobrecobertura | agregação | Indicador de anomalia do pareamento. O cabecalho usa essa contagem como evidencia do efeito da troca de base: 80 municipios contra 35, atribuindo mai… **Risco:** A comparacao com nulo devolve falso, entao municipios com lacuna nula sao contados como nao anomalos e nao como desconhecidos. A contagem nao informa… |
| `73-73` | Totais nacionais da base cruzada antiga | agregação | Mantido apenas para conferencia, como diz o cabecalho da secao impressa na linha 72. Permite comparar o efeito da troca de base sem reexecutar o pass… **Risco:** Os dois totais vem de datas diferentes, agosto de 2026 e dezembro de 2024, que e exatamente a defasagem que o passo pretende eliminar. Qualquer uso d… |
| `74-75` | Cobertura e nao atendidas da base cruzada antiga | agregação | Reproduz, com a mesma regra de truncagem em zero usada na linha 55, o resultado da leitura anterior, para que a mudanca de numero seja atribuivel so … **Risco:** Mede quantidade e beneficio em datas separadas por vinte meses, o que o proprio arquivo aponta como o defeito a corrigir. Sem protecao para ev igual … |
| `77-77` | Descarte de nulos para a distribuicao do subsidio | estatística | Remove os municipios sem beneficios ou sem subsidio informado antes de calcular minimo, mediana e maximo, que ficariam indefinidos com nulos. O codig… **Risco:** O tamanho de s nao e impresso, entao as estatisticas da linha 80 descrevem um subconjunto de tamanho desconhecido. Se muitos municipios cairem por au… |
| `80-80` | Estatisticas de posicao e contagem de negativos do subsidio | estatística | Mediana e nao media, escolha que reduz o efeito de caudas; o codigo nao registra a razao dessa escolha. A contagem de negativos e um teste de sanidad… **Risco:** Com s vazio, min, median e max devolvem nulo e a formatacao imprime nan sem erro. A mediana e simples, sem ponderacao por quantidade de beneficios, d… |
| `81-81` | Total nacional de reais nao acessados, com corte em zero | agregação | O corte em zero impede que municipios com subsidio por familia negativo reduzam o total nacional, tratando estorno como ausencia de valor a acessar e… **Risco:** O corte aparece so aqui; a coluna rs_nao_acessado gravada no CSV conserva os negativos, de modo que outro consumidor que some a coluna sem clip obtem… |
| `85-85` | Particao por unidade da federacao | agregação | O cabecalho da secao, na linha 83, registra a razao do recorte estadual: e o universo que um gestor estadual opera. A concentracao e medida dentro de… **Risco:** groupby descarta silenciosamente linhas com uf nula, que nao aparecem em nenhum grupo nem em nenhuma linha da tabela final. Variacao de grafia ou de … |
| `86-86` | Ordenacao decrescente pela lacuna e total da UF | agregação | A ordenacao decrescente e condicao para a leitura de concentracao da linha 88: a soma acumulada so responde quantos municipios concentram metade da l… **Risco:** Empates sao desempatados pela ordem original da base, o que torna n50 sensivel a ordem de leitura do arquivo quando ha muitos municipios com a mesma … |
| `87-87` | Descarte de UF sem lacuna | limiar | Evita a divisao por zero na linha 88, onde tot e denominador da fracao acumulada. Como lacuna_pos ja foi truncada em zero na linha 55, tot menor que … **Risco:** A UF descartada some da tabela sem qualquer registro, e o leitor nao distingue UF sem lacuna de UF ausente da base. Se tot for nulo, por todas as lac… |
| `88-88` | Fracao acumulada da lacuna dentro da UF | estatística | Curva de concentracao no estilo de uma curva de Lorenz invertida: com os municipios ordenados do maior para o menor, c mede que parcela do total esta… **Risco:** Um unico nulo em lacuna_pos faz cumsum propagar nulo a partir dali; como os nulos foram para o fim da ordenacao, isso afeta a cauda da curva, onde a … |
| `89-89` | Numero de municipios para cobrir metade da lacuna | limiar | Conta quantos pontos da curva ainda estao abaixo de metade e soma um, o que devolve a posicao do primeiro municipio que leva o acumulado a atingir ou… **Risco:** Nulos em c contam como falso na comparacao e nao incrementam a contagem, o que pode subestimar n50 se houver nulo antes de o acumulado cruzar a metad… |
| `90-91` | Montagem da linha da UF e percentual de municipios | agregação | Normaliza n50 pelo tamanho da UF, para que estados com poucos municipios sejam comparaveis a estados com muitos. int(tot) trunca em direcao a zero, n… **Risco:** len(g) inclui municipios com lacuna nula, que nao entraram em tot nem em c, de modo que o denominador do percentual pode ser maior que o universo efe… |
| `92-92` | Ordenacao da tabela de concentracao | apresentação | Ordena por n50 absoluto, nao pelo percentual, de modo que a primeira linha e a UF onde menos municipios bastam para cobrir metade da lacuna. O codigo… **Risco:** Se out ficar vazio, por todas as UFs terem sido descartadas na linha 87, o DataFrame nao tem a coluna mun_para_50pct e sort_values levanta erro. A or… |
| `93-93` | Impressao da tabela de concentracao | apresentação | to_string imprime todas as linhas, sem a truncagem que o pandas aplica na representacao padrao. O resultado nao e gravado em arquivo. **Risco:** Toda a analise de concentracao por UF existe apenas no console. Se a execucao nao for capturada em log, o resultado se perde e nao pode ser conferido… |
| `95-95` | Gravacao da base v5 sem a chave auxiliar | serialização | Remove a chave de seis digitos criada na linha 44, que era instrumental ao merge e nao e informacao do municipio. Grava sem indice para que o CSV ten… **Risco:** As colunas intermediarias eleg_mar26, ben_mar26, subs_mar26, lacuna_bruta_casada e rs_nao_acessado com valores negativos permanecem no arquivo, sem q… |

### `reconstrucao/pipeline/06e_distribuidora.py`

| linhas | operação | espécie | o que faz, e o que a tornaria errada |
|---|---|---|---|
| `4-4` | Montagem do caminho base da ANEEL | leitura | Define a raiz das bases brutas da ANEEL usadas adiante. O codigo nao registra por que RAW aponta para onde aponta; isso vem de _paths.py, importado n… **Risco:** Se RAW apontar para outra copia do acervo, o arquivo lido na linha 6 pode ser outra versao sem que nada falhe na execucao. |
| `5-5` | Leitura da base municipal consolidada v5 | leitura | Este passo e o ultimo da cadeia 06 e parte do produto ja consolidado pelos passos anteriores (06a a 06d), que trazem tarifa, D3, lacuna casada e subs… **Risco:** Se ipem_v5.csv for de uma execucao anterior, todas as colunas derivadas abaixo (peso, violacao, sobrecobertura) saem consistentes entre si porem defa… |
| `6-6` | Leitura dos dados comerciais INDGER com selecao de colunas | leitura | A base INDGER e o unico vinculo disponivel no acervo entre agente distribuidor e municipio, com contagem de unidades consumidoras ativas. A projecao … **Risco:** SigAgente e lido e nunca usado. Se o parquet mudar de esquema de colunas, o read falha na leitura. Se o snapshot 2026-09-05 nao contiver mais registr… |
| `8` | Conversao de UC ativas com preenchimento por zero | aritmética | O valor so e usado como criterio de ordenacao para escolher o agente dominante; zero mantem a linha na base sem lhe dar peso. **Risco:** fillna(0) trata 'nao informado' como 'zero UC ativas': um agente que deixou de reportar alguns meses e rebaixado em vez de excluido da comparacao. Se… |
| `8-8` | Numerizacao das unidades consumidoras ativas com nulo tratado como ze… | aritmética | A coluna e usada como peso de dominancia na linha 10; um peso nao numerico impediria a soma. O fillna(0) faz registro ilegivel valer como ausencia de… **Risco:** Se QtdUCAtiva estiver sistematicamente ilegivel para uma distribuidora (formato com separador de milhar, por exemplo), ela entra com peso zero e perd… |
| `9` | Normalizacao da chave municipal | leitura | Alinha o tipo da chave ao cod_ibge inteiro usado no restante do pipeline, sem o que o merge da linha 13 nao casaria. **Risco:** astype(int) trunca parte decimal em vez de arredondar, se houver. Linhas sem codigo valido somem sem contagem, e com elas as UC do agente naquele mun… |
| `9-9` | Numerizacao do codigo IBGE, descarte de faltantes e conversao a intei… | leitura | O merge da linha 13 exige o mesmo tipo de chave dos dois lados; df traz cod_ibge inteiro do CSV. O dropna e obrigatorio antes do astype(int), porque … **Risco:** Registro sem codigo de municipio some sem contagem. O astype(int) trunca em vez de arredondar: um codigo lido como 3550308.0 vira 3550308, mas qualqu… |
| `10-12` | Distribuidora dominante do municipio por UC ativas somadas em 2024 | agregação | drop_duplicates apos sort descendente mantem a primeira linha de cada municipio, isto e, o agente de maior soma. DICIONARIO.md descreve o campo como … **Risco:** A soma acumula snapshots mensais: o numero somado nao e um estoque de UC e vale multiplas vezes o valor medio do ano — serve para ordenar, nao para c… |
| `10-10` | Eleicao da distribuidora dominante por municipio | agregação | Municipio pode ser atendido por mais de uma distribuidora; a escolha adotada e a de maior numero de unidades consumidoras ativas somadas no periodo f… **Risco:** A soma ocorre sobre todas as competencias de 2024 que sobreviveram ao filtro da linha 7; se duas distribuidoras do mesmo municipio reportarem numeros… |
| `11-11` | Renomeacao e reducao as colunas de saida | serialização | Descarta a coluna uc para que o merge da linha 13 nao injete o total de unidades consumidoras em df. O nome final e o usado no app. **Risco:** Ao descartar uc, perde-se o unico registro do quanto a distribuidora vencedora domina o municipio; o consumidor da tabela final nao consegue distingu… |
| `12-12` | Normalizacao do nome da distribuidora | serialização | Evita que espacos de borda gerem rotulos distintos na contagem da linha 14 e na apresentacao. O astype(str) garante texto mesmo se a coluna vier com … **Risco:** A limpeza acontece DEPOIS do groupby da linha 10: nomes que so diferem por espaco nas bordas ja foram tratados como agentes distintos na eleicao da d… |
| `13-14` | Anexacao da distribuidora ao painel municipal | agregação | Left join preserva todos os municipios do painel e marca com NaN os que nao aparecem no INDGER 2024. **Risco:** nunique ignora NaN, entao 'distribuidoras distintas' nao inclui os municipios sem nome; a contagem de distintos depende da grafia de NomAgente, ja qu… |
| `13-13` | Juncao da distribuidora na base municipal | agregação | O left join preserva todos os municipios de df mesmo sem par no INDGER; a ausencia vira nulo em vez de perda de linha. Como dom tem no maximo uma lin… **Risco:** Municipio ausente do INDGER de 2024, ou cujo codigo nao casa por tipo, sai com distribuidora nula e segue ate o CSV final; a linha 14 imprime essa co… |
| `14-14` | Diagnostico impresso de cobertura da distribuidora | apresentação | Expoe quantos rotulos distintos resultaram e quantos municipios ficaram sem atribuicao, para conferencia manual. nunique ignora nulos por padrao. **Risco:** E apenas impressao: nenhum limite e verificado e nenhuma execucao e interrompida por cobertura baixa. Se a linha 12 tiver convertido faltantes no tex… |
| `15` | Peso da conta de 80 kWh na renda domiciliar do teto da faixa de pobre… | aritmética | Conta mensal de 80 kWh dividida pelo teto de renda domiciliar da faixa de pobreza do CadUnico. Este arquivo nao registra por que 80 kWh; docs/DECISOE… **Risco:** E fracao e nao percentual. O denominador e o teto da faixa, nao a renda observada: quem esta abaixo do teto tem peso maior, logo o valor e um piso. D… |
| `15-15` | Peso da conta de 80 kWh a tarifa cheia sobre a renda domiciliar no te… | aritmética | Mede quanto do orcamento mensal de um domicilio no teto da faixa de pobreza do CadUnico consome uma conta de 80 kWh a tarifa plena do municipio. A ta… **Risco:** O consumo de 80 kWh e imposto igual para todo o pais e nao vem de dado observado. A tarifa e sem tributos, entao o peso real da conta e maior que o c… |
| `16` | Peso da conta de 80 kWh com a tarifa da subclasse Baixa Renda | aritmética | Usa a tarifa da subclasse Baixa Renda como preco. O desconto escalonado da Lei 12.212/2010 nao e aplicado nesta linha: DICIONARIO.md registra que tar… **Risco:** Se o valor for lido como 'conta com beneficio', superestima o que a familia paga em cerca de duas vezes — a conta social a 80 kWh e tarifa_baixa_rend… |
| `16-16` | Peso da conta de 80 kWh a tarifa de baixa renda sobre a mesma renda | aritmética | Mesma conta da linha 15 trocando a tarifa cheia pela tarifa homologada da subclasse Baixa Renda, calculada em 06c como media ponderada por unidades c… **Risco:** Interpretar esta coluna como conta efetivamente paga por familia beneficiaria da Tarifa Social subestima ou superestima o alivio, porque o desconto l… |
| `21` | Indicador de violacao do limite de continuidade | limiar | d3_corr e razao entre apurado e limite regulatorio, entao 1,00 e a fronteira; o np.where preserva vazio para os municipios sem apuracao em vez de os … **Risco:** Sem o np.where, (d3_corr>=1) com NaN daria False e transformaria 'sem dado' em 'sem violacao' — a escolha e justamente evitar isso, e o mesmo cuidado… |
| `21` | Bandeira de violacao do limite de continuidade | limiar | d3_corr vem de 03b como media, ponderada por conjunto eletrico, da razao entre o indicador de continuidade apurado e o respectivo limite regulatorio;… **Risco:** Como d3_corr e media ponderada entre conjuntos, um municipio pode ficar abaixo de 1 no agregado tendo conjuntos individualmente violados (a coluna d3… |
| `22-25` | Bandeira de sobrecobertura na mesma base da lacuna | limiar | lacuna_bruta_casada e definida em 06d linha 54 como familias_elegiveis_mar26 menos beneficiarios_mar26, e lacuna_pos e a mesma diferenca truncada em … **Risco:** O comparador < 0 trata valor nulo como falso, de modo que municipio sem lacuna_bruta_casada sai com sobrecobertura igual a zero, indistinguivel de mu… |
| `26` | Bandeira de subsidio indisponivel | limiar | subs_mar26 e o valor de subsidio da competencia de marco de 2026, renomeado em 06d linha 37 a partir de subs_2026_03, e serve de denominador em 06d l… **Risco:** O comparador <= 0 e falso para nulo, entao municipio sem subs_mar26 sai com a bandeira em zero, isto e, como se o subsidio estivesse disponivel. A co… |
| `27-33` | Definicao das colunas da tabela final | serialização | Fixa quais grandezas saem para o app e em que ordem, descartando as demais colunas intermediarias de ipem_v5. A lista mistura deliberadamente as duas… **Risco:** Qualquer nome ausente em df derruba o script com KeyError na linha 31, que e o unico mecanismo de verificacao do contrato. Colunas usadas no calculo … |
| `34` | Materializacao da tabela de saida | serialização | Seleciona e copia, para que a tabela exportada seja independente de df. A selecao por lista e o ponto em que a ausencia de qualquer coluna esperada s… **Risco:** A copia nao valida tipos nem intervalos; colunas nulas passam intactas ate o CSV. Se cols contiver nome repetido, a coluna sai duplicada no arquivo. |
| `35` | Diagnostico impresso de numero de linhas | apresentação | Permite conferir a olho se a contagem bate com o universo de municipios esperado. **Risco:** Nenhuma comparacao automatica com o numero esperado de municipios; o script segue e grava mesmo se a contagem estiver errada. |
| `36` | Diagnostico impresso de nulos por coluna | apresentação | Lista somente as colunas com faltantes, encurtando a saida e expondo onde o casamento de bases falhou. isna().sum() e calculado duas vezes na mesma e… **Risco:** E somente impressao: nenhum limite de nulos e imposto e a gravacao ocorre em seguida de qualquer forma. Colunas cujo faltante foi convertido em zero … |
| `37` | Gravacao do CSV consumido pelo app | serialização | index=False evita uma coluna extra de indice sem significado. O arquivo e a entrada dos passos de payload e validacao (09_payload.py e os scripts val… **Risco:** Sobrescreve a saida anterior sem versionar nem checar se os diagnosticos impressos acima eram aceitaveis. A gravacao usa o padrao do pandas para sepa… |
| `38` | Mensagem final de conclusao | apresentação | Sinaliza o fim do passo para o orquestrador e para quem le o log. **Risco:** O OK indica apenas que nenhuma excecao ocorreu; nao afirma nada sobre cobertura da distribuidora, quantidade de nulos ou coerencia temporal entre as … |

### `reconstrucao/pipeline/07_tarifa_social.py`

| linhas | operação | espécie | o que faz, e o que a tornaria errada |
|---|---|---|---|
| `4-4` | Leitura da base municipal consolidada | leitura | Todo o calculo deste arquivo opera sobre colunas ja produzidas a montante: tarifa_municipal (02_tarifa.py), tarifa_baixa_renda (06c_faixas_cadunico.p… **Risco:** Nao ha verificacao de existencia do arquivo nem de presenca das colunas usadas; qualquer mudanca de nome a montante quebra o script com AttributeErro… |
| `5-11` | Regra completa do desconto escalonado da Lei 12.212/2010 (funcao fato… | regra normativa | O comentario da linha 5 declara a escolha central: o desconto e CUMULATIVO por faixa, isto e, cada bloco de kWh recebe o percentual da sua propria fa… **Risco:** Funcao escalar: nao aceita Series (max(0, Series) levantaria ValueError). Nao valida dominio de k (zero divide por zero, negativo devolve numero sem … |
| `7-7` | Faixa 1 do desconto TSEE: primeiros 30 kWh | regra normativa | 0.35 e a fracao PAGA, complemento de um desconto de 65% na primeira faixa. O codigo nunca escreve 0,65; escreve o que resta. O comentario da linha 5 … **Risco:** min(k,30) com k escalar Python funciona; com uma Series pandas, min() compara de forma nao definida e o max() da linha seguinte levantaria ValueError… |
| `8-8` | Faixa 2 do desconto TSEE: de 31 a 100 kWh | regra normativa | 0.60 e a fracao paga, complemento de desconto de 40% na segunda faixa; valida_desconto.py usa 0.40 como desconto para o mesmo intervalo. O max(0, ...… **Risco:** O max(0, ...) supoe que o piso da faixa (30) e exatamente o teto da faixa anterior; se um dos dois for editado sem o outro, abre-se um vao ou uma sob… |
| `9-9` | Faixa 3 do desconto TSEE: de 101 a 220 kWh | regra normativa | 0.90 e a fracao paga, complemento de desconto de 10% na terceira faixa; valida_desconto.py usa 0.10 como desconto para o intervalo 100-220. Esta parc… **Risco:** O corte de 220 kWh e um limite que, na norma citada, tem regra propria para parte dos beneficiarios (por exemplo populacao indigena e quilombola). O … |
| `10-10` | Faixa 4 do desconto TSEE: acima de 220 kWh | regra normativa | 1.0 significa desconto zero acima de 220 kWh: o excedente e cobrado integralmente. A multiplicacao por 1.0 e aritmeticamente inerte e existe para man… **Risco:** Multiplicar por 1.0 converte o resultado para float mesmo quando k e inteiro; irrelevante aqui, mas e o unico efeito real da operacao. A regra implic… |
| `11-11` | Normalizacao: fator medio de fatura por kWh | aritmética | A divisao por k converte a soma das faixas (expressa em kWh cobrados a preco cheio) em um multiplicador adimensional aplicavel a uma fatura inteira. … **Risco:** Divisao por zero: fator(0) levanta ZeroDivisionError, sem tratamento. Para k negativo o retorno e um numero sem significado, nao ha guarda. O fator s… |
| `12-12` | Impressao do fator e do desconto percentual nas faixas de referencia | aritmética | Converte a fracao paga em desconto percentual pelo complemento (1 - fator) e multiplica por 100. Os pontos escolhidos sao os limites de faixa, onde o… **Risco:** Somente imprime: se o fator estiver errado, nada aqui falha, apenas sai um numero errado no log. O arredondamento .1f esconde diferencas menores que … |
| `13-13` | Fator fixado no consumo de referencia de 80 kWh | limiar | Fixa um unico consumo de referencia para todos os municipios, o que torna o calculo comparavel entre eles: a variacao dos resultados passa a vir so d… **Risco:** Consumo uniforme de 80 kWh e hipotese forte: municipios com clima, renda e posse de equipamentos diferentes consomem de forma diferente, e o desconto… |
| `14-14` | Conta cheia de 80 kWh (sem tributos) | aritmética | Multiplicacao direta tarifa x consumo. A tarifa vem das tarifas homologadas da ANEEL, subgrupo B1, modalidade convencional, ja convertida de R$/MWh p… **Risco:** Nao inclui ICMS, PIS/COFINS, bandeira tarifaria, contribuicao de iluminacao publica nem custo de disponibilidade; a conta real emitida e maior, em pr… |
| `15-15` | Conta com beneficio da Tarifa Social, 80 kWh | aritmética | Esta e a correcao central do arquivo. A tarifa publicada da subclasse Baixa Renda e uma tarifa propria, mas NAO embute o desconto escalonado da lei; … **Risco:** Se F80 fosse aplicado a um consumo diferente de 80, a identidade algebrica se quebraria e a conta ficaria errada; o acoplamento entre o 80 desta linh… |
| `16-16` | Economia mensal por familia | aritmética | Diferenca entre a conta sem beneficio e a conta com beneficio, no mesmo consumo de 80 kWh. Os dois termos usam tarifas DIFERENTES: o minuendo usa tar… **Risco:** Nao ha clip(lower=0): se em algum municipio tarifa_baixa_renda*0,50625 superar tarifa_municipal, econ_mes fica negativo e e mantido, entrando com sin… |
| `20-20` | Estatisticas descritivas da conta cheia | estatística | Resumo de posicao e amplitude da conta sem beneficio entre municipios. Mediana e nao media, o que reduz a influencia de caudas; o codigo nao registra… **Risco:** median(), min() e max() do pandas ignoram NaN por padrao, entao os tres numeros descrevem apenas os municipios com tarifa disponivel, sem que o log d… |
| `21-21` | Estatisticas descritivas da conta com beneficio | estatística | Mesmo resumo aplicado a conta com desconto, para leitura lado a lado com a linha 20. Nao ha calculo novo alem das tres estatisticas. **Risco:** O conjunto de municipios por tras desta mediana pode ser MENOR que o da linha 20, porque conta_social80 depende de tarifa_baixa_renda, que tem cobert… |
| `22-22` | Economia mediana e anualizacao por familia | estatística | Mediana da economia mensal entre municipios, depois multiplicada por 12. Como multiplicar por 12 e transformacao linear crescente, 12*mediana e igual… **Risco:** Anualizar supoe doze meses identicos: mesma tarifa (ignora o reajuste tarifario anual de cada distribuidora), mesmo consumo (ignora sazonalidade) e b… |
| `25-25` | Peso da conta cheia na faixa de pobreza: mediana e contagem acima de … | limiar | Aplica o limiar de 10% da renda domiciliar como marcador de esforco excessivo com energia e conta quantos municipios o ultrapassam na hipotese sem be… **Risco:** A comparacao NaN > 0.10 devolve False, entao municipios sem tarifa entram na contagem como se estivessem abaixo do limiar, deflacionando o numero sem… |
| `26-26` | Peso com tarifa Baixa Renda SEM desconto (calculo rotulado ERRADO) | limiar | Impresso deliberadamente para contraste, com o rotulo ERRADO cravado na propria string. O defeito que o codigo aponta e preciso: peso_pob80_social us… **Risco:** Manter a coluna defeituosa no arquivo gravado permite que outro script a use sem ver o rotulo, que existe apenas nesta string de impressao e nao no d… |
| `27-27` | Peso com beneficio efetivo: mediana e contagem acima de 10% | limiar | Terceira linha do bloco comparativo: peso da conta sobre a renda quando o desconto escalonado e efetivamente aplicado. Junto com as linhas 25 e 26 fo… **Risco:** Herda todos os riscos de peso_social_ef (teto da faixa como renda, media municipal de moradores, conta sem tributos) e da comparacao com NaN, que con… |
| `30-30` | Alivio mensal agregado de fechar a lacuna de cobertura | agregação | Produto familia a familia dentro de cada municipio, somado nacionalmente: quanto as familias hoje fora do beneficio deixariam de pagar se entrassem. … **Risco:** sum() do pandas ignora NaN por padrao, entao municipios sem tarifa_baixa_renda contribuem zero em vez de contribuir um valor desconhecido: o total e … |
| `31-31` | Anualizacao do alivio agregado | aritmética | Multiplicacao por 12 para expressar o mesmo agregado em base anual, mantendo a lacuna constante ao longo do ano. **Risco:** Supoe lacuna estavel por doze meses, tarifa sem reajuste e consumo sem sazonalidade. Como tot ja e um piso por causa dos NaN descartados na soma, o v… |
| `32-32` | Subsidio observado por familia na CDE (mediana) | estatística | Contraponto empirico ao calculo teorico: quanto a CDE de fato aporta por familia beneficiaria, ao lado da economia calculada pela regra. O rotulo imp… **Risco:** O denominador linhas_tsee teve zeros convertidos em NaN a montante, entao municipios sem beneficiarios saem da mediana. 06d informa que subsidio_fami… |
| `33-33` | Persistencia das colunas derivadas | leitura | Grava a base com as quatro colunas novas. E o arquivo consumido por 09_payload.py (que publica peso_social_ef como 'ps' e peso_pob80_cheia como 'pc')… **Risco:** Sobrescreve sem versionar e sem registrar data de geracao; index=False descarta o indice, inocuo aqui porque a chave e cod_ibge. Como o CSV e texto, … |

### `reconstrucao/pipeline/07b_municipio_agente.py`

| linhas | operação | espécie | o que faz, e o que a tornaria errada |
|---|---|---|---|
| `5-8` | Leitura do ZIP de beneficiarios em blocos de 2,5 milhoes de linhas | leitura | O ZIP de beneficiarios da CDE nao cabe em memoria de uma vez, entao a leitura e feita em blocos e a agregacao e incremental em um dicionario (acc). S… **Risco:** z.infolist()[0] pega o primeiro membro do ZIP sem verificar nome ou quantidade: se o arquivo passar a conter mais de um membro, ou se a ordem mudar, … |
| `9-10` | Filtro do tipo de subsidio baixa renda | regra normativa | O arquivo de beneficiarios da CDE reune varios tipos de subsidio; a igualdade exata isola a Tarifa Social de Energia Eletrica (rotulo 'SubsBaixaRenda… **Risco:** Igualdade literal e sensivel a qualquer mudanca de rotulo na base da ANEEL entre snapshots; como o script compara duas fotografias de datas diferente… |
| `11-12` | Normalizacao da sigla do agente e do codigo IBGE | cartografia | Define as duas chaves do produto do script. A sigla do agente e normalizada apenas por strip nas bordas; o codigo IBGE e numerificado e linhas sem co… **Risco:** A chave de agente aqui e SigAgente (sigla), enquanto o arquivo 02_tarifa.py faz a ponte por CNPJ: as duas saidas do subsistema usam identificadores d… |
| `13-17` | Contagem de registros por par municipio-agente acumulada entre blocos | agregação | size() conta linhas de cada par dentro do bloco e o dicionario acc soma as contagens parciais entre blocos, reproduzindo um groupby global sem carreg… **Risco:** O que se conta e linhas do arquivo, nao beneficiarios distintos: se um mesmo beneficiario aparecer em mais de uma linha (por competencia, por unidade… |
| `18-22` | Uniao externa das duas fotografias e preenchimento de ausente com zero | agregação | As duas fotografias -- 01/12/2024 e 01/03/2026 -- sao contadas pela mesma funcao e unidas por par municipio-agente com how='outer', preservando pares… **Risco:** O fillna(0) e a decisao central: funde 'este par nao existia nesta data' com 'este par tinha zero beneficiarios'. Se um dos dois arquivos estiver tru… |

## Comparação entre as duas datas

120 operações em 4 arquivos.

### `reconstrucao/pipeline/08b_nacional_2026.py`

| linhas | operação | espécie | o que faz, e o que a tornaria errada |
|---|---|---|---|
| `5-7` | Parametrizacao do mes de referencia | leitura | REF nao e so rotulo: ele e a data usada adiante para escolher a vigencia tarifaria (linha 46), logo o mes escolhido define simultaneamente o arquivo … **Risco:** Qualquer TAG fora das duas chaves levanta KeyError antes de qualquer calculo. REF e fixado no dia 1 do mes: se nenhuma vigencia tarifaria de uma dist… |
| `8-8` | Reapontamento do diretorio bruto para a ANEEL | leitura | Converte o Path importado em string e o especializa para o subdiretorio da ANEEL, que e a origem das tarifas e do indger lidos adiante. O codigo nao … **Risco:** A reatribuicao destroi o Path original; se alguma linha posterior esperasse o objeto Path ou a raiz sem "/aneel", o caminho sairia errado. Como _path… |
| `9-9` | Conversor numerico de formato brasileiro | aritmética | Os CSVs tarifarios da ANEEL sao publicados com ponto como separador de milhar e virgula como decimal; a lambda desfaz essa convencao antes de convert… **Risco:** Se o arquivo mudar para o padrao anglo-saxao, "1,234.56" vira "1,23456" e depois 1.23456, ou seja, erro silencioso de tres ordens de grandeza sem ger… |
| `11-12` | Leitura da base municipal e do agregado CDE do mes novo | leitura | O renome apaga o sufixo do mes e fixa nomes genericos ben26 e subs26, o que permite ao restante do script tratar marco e abril de 2026 com o mesmo co… **Risco:** Tratar ben26 como numero de familias sobrestima a cobertura sempre que houver mais de uma linha por unidade consumidora no mes. Se os nomes ben_TAG o… |
| `13-13` | Juncao a esquerda do painel com o mes de 2026 | agregação | O how="left" preserva o universo de municipios de app_dados2.csv como denominador: municipios presentes so no arquivo de 2026 sao descartados, e muni… **Risco:** Se cod_ibge tiver tipos ou granularidades diferentes nos dois lados (por exemplo codigo de 7 digitos contra 6 digitos sem digito verificador), o casa… |
| `14-15` | Contagem de cobertura do arquivo do mes novo | estatística | Mede quantos municipios do painel encontraram correspondencia no arquivo de 2026, diagnostico do join da linha 13. A contagem e feita antes do fillna… **Risco:** A contagem nao distingue ausencia por municipio sem beneficiario de ausencia por falha de casamento de codigo. Um municipio presente no arquivo com v… |
| `16-16` | Imputacao de zero para municipios ausentes em 2026 | aritmética | Converte ausencia de registro em ausencia de beneficio, o que e o que permite somar a coluna inteira nas linhas 19 e 65 sem propagar NaN. O codigo na… **Risco:** A imputacao e indistinguivel de um dado real. Se parte dos municipios ficou de fora por falha de casamento de codigo ou por recorte incompleto do arq… |
| `19-19` | Totais nacionais de elegiveis e beneficios | agregação | Soma simples sobre todos os municipios do painel, sem ponderacao e sem filtro. As tres grandezas vem de fontes e datas distintas: familias_elegiveis … **Risco:** Somar contagens de linhas da CDE (b24 e b26) contra um universo de familias do CECAD (ele) mistura unidades: a razao so e interpretavel como cobertur… |
| `22-22` | Formatacao do total de familias elegiveis | apresentação | Apenas formata; o arredondamento para zero casas nao altera a variavel usada nas divisoes seguintes, que continua em ponto flutuante. **Risco:** O separador de milhar usado e o anglo-saxao (virgula), divergente da convencao brasileira do restante do projeto, o que pode induzir leitura errada s… |
| `23-24` | Cobertura nacional e familias nao atendidas nas duas datas | aritmética | A lacuna e definida como diferenca aritmetica entre o universo elegivel do CECAD e a contagem de beneficios da CDE, com o mesmo denominador nas duas … **Risco:** A subtracao nao tem clip inferior: se b26 exceder ele em algum cenario, o resultado sai negativo e seria impresso como tal. Divisao por ele sem prote… |
| `27-28` | Leitura das tarifas homologadas | leitura | dtype=str preserva o formato original dos numeros para que a conversao seja feita pela lambda num da linha 9, e evita inferencia de tipo divergente e… **Risco:** A data 2026-09-05 esta fixa no codigo: uma reexecucao com dados atualizados exige editar o caminho, e uma tarifa revisada apos essa data nao entra. e… |
| `29-33` | Selecao da tarifa B1 Baixa Renda convencional de aplicacao | regra normativa | Cinco igualdades exatas sobre campos de texto do cadastro de tarifas homologadas da ANEEL, com strip previo. A combinacao isola a linha de tarifa de … **Risco:** Comparacao literal com acento ("Tarifa de Aplicação", "Não se aplica") e sensivel a mudanca de grafia, de encoding ou de dominio da ANEEL: qualquer a… |
| `29-29` | Normalizacao textual das colunas de classificacao | aritmética | Os filtros da linha 30 usam igualdade exata; o strip evita que espaços acidentais no arquivo eliminem linhas validas. **Risco:** O strip nao normaliza caixa, acentuacao nem espacos internos. Uma grafia "Tarifa de Aplicacao" sem cedilha, ou "Baixa Renda" com dois espacos, sairia… |
| `30-33` | Selecao normativa da tarifa B1 Baixa Renda convencional | regra normativa | Reproduz, por filtros no dicionario de dados da ANEEL, o recorte do consumidor residencial de baixa renda atendido em baixa tensao na modalidade conv… **Risco:** Os cinco filtros sao igualdades literais com acento; qualquer alteracao de nomenclatura no arquivo da ANEEL esvazia b e propaga NaN ate frac24 e frac… |
| `34-34` | Conversao das datas de vigencia tarifaria | aritmética | As datas delimitam o intervalo em que cada tarifa esteve homologada, usado como criterio de vigencia na linha 42. O coerce evita interrupcao diante d… **Risco:** A conversao e feita sem format explicito, entao o pandas infere: uma serie ambigua entre dia e mes primeiro pode ser lida ao contrario e deslocar vig… |
| `35-35` | Tarifa total por distribuidora em R$/kWh | aritmética | A tarifa de aplicacao e a soma das duas parcelas homologadas, TUSD (uso do sistema de distribuicao) e TE (energia); a divisao por 1000 converte de R$… **Risco:** Se o arquivo passar a publicar em R$/kWh, a divisao por 1000 subestima a conta em tres ordens de grandeza e a fracao coberta explode para valores abs… |
| `36-37` | Leitura do cadastro comercial por municipio | leitura | O indger e a fonte que liga CNPJ de distribuidora a municipio, ligacao que o arquivo tarifario nao possui; QtdUCAtiva sera o peso da media ponderada … **Risco:** Snapshot fixo na data 2026-09-05, como no arquivo tarifario. Se qualquer uma das quatro colunas mudar de nome, a leitura falha de imediato. A cobertu… |
| `38-38` | Conversao da data de referencia do indger | aritmética | Necessaria para o recorte anual da linha 43, que seleciona registros pelo ano de dt. **Risco:** Registros com data invalida viram NaT e nunca casam com nenhum ano, saindo do calculo de peso sem contagem. Inferencia de formato sem format explicit… |
| `39-39` | Conversao de CNPJ e unidades consumidoras | aritmética | O CNPJ numerico e a chave de juncao com a tabela tarifaria, que sofreu a mesma conversao na linha 35. O fillna(0) garante que a soma de pesos da linh… **Risco:** O fillna(0) faz um registro sem quantidade informada ter peso nulo na media ponderada, ou seja, a distribuidora correspondente e ignorada no municipi… |
| `40-40` | Codigo IBGE inteiro e descarte de registros sem chave | aritmética | O dropna precede o astype(int) porque a conversao para inteiro falharia com NaN presente; a ordem das tres operacoes na mesma linha e portanto necess… **Risco:** O descarte e silencioso: nao ha contagem de quantos registros do indger sao perdidos por codigo ou CNPJ ausente, e cada perda retira peso de um munic… |
| `41-42` | Tarifa mediana vigente por distribuidora na data de referencia | estatística | Uma distribuidora pode ter mais de uma linha tarifaria vigente na mesma data (postos, subclasses detalhadas, revisoes sobrepostas). O codigo resolve … **Risco:** Com numero par de linhas vigentes a mediana interpola entre duas tarifas e produz um valor que nao consta do cadastro. Se a vigencia estiver com fim … |
| `42-42` | Tarifa mediana vigente por distribuidora na data de referencia | estatística | Uma distribuidora pode ter mais de uma linha vigente na mesma data, por posto tarifario, bandeira ou revisao sobreposta; a mediana e uma escolha de r… **Risco:** Se duas vigencias se sobrepoem na data ref, por exemplo tarifa antiga ainda nao encerrada e tarifa nova ja iniciada, a mediana mistura os dois regime… |
| `43-43` | Unidades consumidoras por municipio e distribuidora no ano | agregação | Soma as unidades consumidoras do ano inteiro para obter um peso estavel da presenca de cada distribuidora em cada municipio, e o dropna em t retira p… **Risco:** O recorte e por ano civil enquanto ref e uma data especifica: para 2026 o ano inteiro ainda pode estar incompleto no snapshot, e para 2024 o peso acu… |
| `44-44` | Tarifa municipal como media ponderada por unidades consumidoras | estatística | Municipios atendidos por mais de uma distribuidora precisam de um valor unico; o peso por unidades consumidoras aproxima a tarifa media enfrentada po… **Risco:** O peso e o numero de UCs totais, nao o de UCs de baixa renda; se a distribuidora com tarifa mais alta concentrar proporcionalmente menos familias de … |
| `45-46` | Juncao das tarifas municipais das duas datas | agregação | Fixa a data de 2024 em 1 de dezembro, coerente com a CDE de dez/2024 usada em beneficiarios_tsee e subs_liquido, e usa REF para a ponta de 2026. O le… **Risco:** A data de 2024 esta escrita no codigo enquanto a de 2026 vem do parametro TAG, entao as duas pontas nao sao configuraveis do mesmo modo. Municipios s… |
| `48-48` | Subsidio por beneficiario em dez/2024 | aritmética | Divide o subsidio liquido municipal pelo numero de linhas de beneficio para obter o valor medio por beneficio. O replace(0, np.nan) evita divisao por… **Risco:** subs_liquido, conforme 01_cde.py, e a soma algebrica de valores positivos e negativos (estornos), de modo que um municipio com muitos estornos pode t… |
| `49-49` | Subsidio por beneficiario no mes de 2026 | aritmética | Mesma definicao aplicada a ponta de 2026, condicao para que a comparacao das linhas 50 e 51 seja entre grandezas construidas do mesmo modo. **Risco:** Como a linha 16 imputou zero aos municipios ausentes, o denominador zerado vira NaN aqui e esses municipios saem do bloco 2, mas permanecem no bloco … |
| `50-50` | Fracao da conta de 80 kWh coberta em 2024 | aritmética | O denominador e o custo de 80 kWh a tarifa municipal de baixa renda: R$/kWh multiplicado por kWh resulta em reais, mesma unidade do numerador, de mod… **Risco:** O denominador ignora tributos e bandeiras, entao a conta real e maior e frac24 superestima a cobertura. Se tar24 for zero ou nulo, o resultado e infi… |
| `51-51` | Fracao da conta de 80 kWh coberta em 2026 | aritmética | Mesma construcao de frac24 com os insumos de 2026, o que e a condicao para que a diferenca da linha 58 isole a variacao de politica e de tarifa em ve… **Risco:** Os mesmos de frac24, com um adicional: tar26 vem de uma vigencia apurada em REF enquanto o peso de UCs vem do ano de 2026 possivelmente incompleto, e… |
| `52-53` | Mascara do conjunto comparavel | limiar | Restringe a comparacao aos municipios em que as duas pontas sao calculaveis, requisito para que a diferenca da linha 58 seja pareada no mesmo conjunt… **Risco:** A selecao e dependente do resultado: municipios com subsidio liquido negativo, tipicamente os com mais estornos, sao removidos, o que enviesa a media… |
| `55-57` | Quartis da fracao coberta nas duas datas | estatística | Quantis descrevem a distribuicao municipal sem ponderacao por populacao ou por numero de beneficiarios: cada municipio conta como uma observacao. A m… **Risco:** A mediana municipal nao e a mediana das familias: municipios pequenos, que sao maioria, dominam a estatistica, e o resultado pode divergir do agregad… |
| `56-57` | Quartis da fracao coberta nas duas datas | estatística | Resumo da distribuicao por municipio, nao ponderado: cada municipio pesa igual, independentemente do numero de beneficiarios. A multiplicacao por 100… **Risco:** Media ou mediana nao ponderada por municipio da o mesmo peso a um municipio de mil habitantes e a uma capital; o numero nacional resultante nao e a f… |
| `58-59` | Ganho de cobertura da conta entre as duas datas | aritmética | Diferenca simples entre as duas fracoes, municipio a municipio, reportada em pontos percentuais. A proporcao de municipios com ganho e calculada como… **Risco:** A mediana de g nao e a diferenca das medianas impressas na L57: mediana de diferencas e diferenca de medianas sao grandezas distintas, e o texto que … |
| `58-58` | Ganho municipal em fracao coberta | aritmética | Diferenca pareada dentro do mesmo municipio, o que elimina o efeito de nivel entre municipios e isola a variacao temporal. Depende de v ter as duas c… **Risco:** A diferenca absoluta trata igualmente um ganho de 10 para 20 por cento e de 60 para 70 por cento, embora o significado economico seja distinto. Como … |
| `59-59` | Mediana do ganho e proporcao de municipios com ganho | estatística | A mediana resume a variacao tipica sem ser puxada por outliers, e a proporcao de g>0 mede a difusao do ganho independentemente de sua magnitude, duas… **Risco:** O limiar estrito g>0 classifica como ausencia de ganho qualquer valor exatamente zero e tambem variacoes positivas despreziveis contam como ganho, se… |
| `60-60` | Reajuste tarifario municipal mediano | estatística | A razao de tarifas separa o efeito tarifario do efeito de subsidio dentro da variacao de frac: se a tarifa subiu mais que o subsidio por beneficiario… **Risco:** A razao e nominal, sem deflacionamento: um fator maior que 1 pode ser apenas inflacao do periodo, e o codigo nao registra indice de precos nem o inte… |
| `65-65` | Agregacao por unidade da federacao | agregação | A agregacao usa m, o painel completo, e nao v: o bloco 3 cobre todos os municipios, inclusive aqueles com ben26 imputado em zero pela linha 16, ao co… **Risco:** Municipios que nao casaram no join da linha 13 entram na UF com b26 igual a zero e deprimem a cobertura de 2026 daquela UF, produzindo um delta negat… |
| `66-66` | Cobertura estadual nas duas datas e variacao em pontos percentuais | aritmética | Usa o mesmo denominador ele nas duas datas, de modo que dpp e proporcional a variacao absoluta do numero de beneficios: dpp = 100 * (b26 - b24) / ele… **Risco:** Divisao sem protecao: uma UF com ele igual a zero produz infinito ou NaN, que seria impresso. Se ben26 estiver subcontado por falha de cobertura do a… |
| `67-68` | Ordenacao e arredondamento da tabela por UF | leitura | Apresentacao: ordena da maior para a menor variacao e arredonda para uma casa. O arredondamento e aplicado apenas na exibicao; u mantem os valores ch… **Risco:** dpp arredondado pode nao ser igual a diferenca entre cob26 e cob24 arredondados (erro de ate 0,1 pp), o que faz a tabela impressa parecer inconsisten… |
| `67-67` | Ordenacao das UFs por ganho de cobertura | apresentação | Coloca no topo as UFs com maior avanco de cobertura, ordenacao por magnitude do ganho e nao por tamanho da UF ou por nivel de cobertura. **Risco:** Ordenar por ganho absoluto favorece UFs que partiam de cobertura baixa, e a lista nao mostra o nivel de partida no criterio de ordem, apenas nas colu… |
| `68-68` | Arredondamento e impressao da tabela por UF | apresentação | O arredondamento ocorre em copias via assign e nao altera u, entao nenhuma etapa posterior herda a perda de precisao. O recorte de colunas oculta ele… **Risco:** dpp e arredondado de forma independente de cob24 e cob26, entao a diferenca entre as duas colunas exibidas pode divergir do dpp exibido em uma decima… |
| `69-69` | Gravacao do painel comparativo | serialização | Persiste o painel municipal com todas as colunas derivadas (ben26, subs26, tar24, tar26, spb24, spb26, frac24, frac26) para consumo a jusante; o nome… **Risco:** Grava o painel apos os fillna(0) da linha 16, entao o CSV nao distingue municipio sem beneficiarios de municipio ausente do arquivo CDE: essa informa… |

### `reconstrucao/pipeline/09a_painel_municipal.py`

| linhas | operação | espécie | o que faz, e o que a tornaria errada |
|---|---|---|---|
| `4-4` | Codigo IBGE do CadUnico convertido a numero | leitura | errors='coerce' transforma qualquer valor nao numerico em NaN em vez de interromper. E a chave do join com o lado da CDE. **Risco:** Silencia o erro: linhas com codigo invalido viram NaN, nao entram no indice e desaparecem do painel sem contagem nem aviso. O codigo nao verifica qua… |
| `8-10` | Recorte de cada data e sufixo de periodo | agregação | As duas datas sao dezembro/2024 e marco/2026, as pontas da comparacao publicada. str(am)[2:] extrai '2412' e '2603' por fatiamento de texto, nao por … **Risco:** set_index('ibge6') sem verificar unicidade: se a SAGI trouxer mais de uma linha por municipio e mes, o join posterior multiplica linhas. Se um dos do… |
| `11-11` | Interseccao das duas datas do CadUnico | agregação | O inner join garante que todo municipio do painel tenha as duas pontas da comparacao; sem isso, d_cob seria calculado contra um lado ausente. **Risco:** Municipios presentes em so uma das datas somem da comparacao sem contagem. O script nao imprime quantos foram perdidos nem compara len(w[202412]), le… |
| `14-14` | Reducao do codigo IBGE de 7 para 6 digitos | aritmética | O setimo digito do codigo IBGE e verificador; a divisao inteira por 10 o descarta para casar com a chave de 6 digitos usada pela SAGI. Verifiquei que… **Risco:** E uma hipotese sobre o formato do outro arquivo, nao uma verificacao. Se cadunico_sagi.csv trouxer 7 digitos, o merge da linha 15 nao casa nada e o p… |
| `15-15` | Juncao a esquerda do lado CDE com o CadUnico | agregação | how='left' preserva a lista de municipios da CDE como universo do painel; o CadUnico entra como atributo. E o que permite que o painel tenha o mesmo … **Risco:** Municipios sem correspondencia ficam com todas as colunas do CadUnico em NaN, o que propaga NaN para cob_2412, cob_2603, d_cob, saiu_pobreza e d_eleg… |
| `18-18` | Cobertura de dezembro de 2024 | aritmética | O comentario da linha 17 declara a decisao: cada data usa o denominador do seu proprio mes. replace(0,np.nan) evita divisao por zero convertendo o re… **Risco:** Numerador e denominador tem unidades diferentes: beneficio da CDE e por unidade consumidora, elegibilidade da SAGI e por familia. Se uma familia tive… |
| `19-19` | Cobertura de marco de 2026 | aritmética | Espelha a linha 18 com a outra ponta temporal. A simetria e o que torna a diferenca da linha 20 interpretavel como variacao e nao como troca de metod… **Risco:** Mesmas hipoteses da linha 18. Alem disso, 08b_nacional_2026.py registra defasagens de apuracao diferentes entre as duas datas (20 meses contra 5 mese… |
| `20-20` | Variacao de cobertura em pontos percentuais | aritmética | Diferenca de dois percentuais, portanto pontos percentuais e nao percentual de variacao. E o valor que vira D.dcob no payload (10a_payload_comparacao… **Risco:** Como cada ponta usa denominador proprio, d_cob muda quando so o denominador muda: um municipio que mantem exatamente os mesmos beneficios e ve o CadU… |
| `21-21` | Variacao absoluta de beneficiarios | aritmética | Diferenca bruta entre as duas apuracoes da CDE, sem denominador. E a unica das variacoes desta secao que nao depende do CadUnico. **Risco:** d_ben e calculado e gravado no painel_municipal.csv, mas nao e lido por 10a nem pelo template — o template recalcula o mesmo numero no navegador (map… |
| `22-22` | Saldo da faixa de pobreza | aritmética | E um saldo entre dois estoques, nao um fluxo: mede a diferenca de tamanho da faixa entre duas fotografias. O proprio template declara isso ao usuario… **Risco:** O nome da variavel afirma um movimento ('sairam') que o calculo nao consegue observar: entradas e saidas ocorrem no periodo e so o liquido aparece. U… |
| `23-23` | Variacao do universo elegivel | aritmética | Isola a variacao do denominador da cobertura. E a grandeza testada na segunda correlacao (linha 49) contra d_cob, justamente para separar movimento d… **Risco:** O sinal e invertido em relacao a saiu_pobreza (aqui positivo = universo cresceu; la positivo = faixa encolheu), o que facilita erro de leitura ao com… |
| `24-24` | Nao atendidas em marco de 2026 com piso em zero | aritmética | O clip(lower=0) e uma escolha de definicao: excesso de beneficios sobre elegiveis nao vira credito negativo. Isso torna a soma nacional uma soma de f… **Risco:** O clip apaga a informacao de sobrecobertura: um municipio com -3000 e um com 0 ficam identicos no campo publicado (D.na26). A flag que preserva esse … |
| `26-33` | Rotulo da variacao de cobertura (bandas de -5, -1, 1, 5 pp) | limiar | Cortes em 1 e 5 pontos percentuais, simetricos entre queda e alta, com a faixa central [-1, 1] chamada 'estavel'. O codigo nao registra de onde vem 1… **Risco:** As fronteiras sao tratadas de modo assimetrico: -5 exato cai em 'caiu muito' (<=) e -1 exato cai em 'estavel' (nao e < -1), enquanto +1 exato e 'esta… |
| `36-36` | Distribuicao dos rotulos de cobertura em ordem fixa | agregação | reindex fixa a ordem de leitura do pior para o melhor, em vez da ordem por frequencia que value_counts devolve. **Risco:** Se algum rotulo mudar de grafia na funcao rot, o reindex devolve NaN naquela linha em vez de erro — a contagem some da impressao silenciosamente. A s… |
| `37-37` | Percentis e mediana da variacao de cobertura | estatística | quantile e median do pandas ignoram NaN por padrao, de modo que estes tres numeros descrevem apenas os municipios com as duas datas. Isso e coerente … **Risco:** O quantil do pandas usa interpolacao linear entre observacoes, enquanto o quantil equivalente no template (QCOB, mapa.template.html:622) usa selecao … |
| `38-38` | Municipios com queda de cobertura: contagem e proporcao | estatística | A comparacao NaN < 0 e falsa em pandas, entao municipios sem dado contam como 'sem queda' no numerador e permanecem no denominador da media. **Risco:** O percentual impresso e a fracao de queda sobre o universo inteiro, incluindo os municipios sem CadUnico nas duas datas — nao e a fracao entre os mun… |
| `41-41` | Total nacional do saldo da faixa de pobreza | agregação | Soma simples, com compensacao entre municipios: saldo negativo em um municipio abate saldo positivo em outro. Isso e o oposto da regra adotada para n… **Risco:** Como sum() ignora NaN, o total nacional e a soma apenas dos municipios presentes nas duas datas, mas e rotulado 'nacional'. O numero nao e comparavel… |
| `42-42` | Municipios com saida liquida da pobreza | estatística | Mesmo padrao da linha 38: comparacao estrita > 0 e media booleana sobre o DataFrame inteiro. **Risco:** NaN conta como falso no numerador e permanece no denominador, subestimando o percentual. O limiar e > 0 em familias absolutas: um municipio com saldo… |
| `43-43` | Percentis do saldo da pobreza por municipio | estatística | Descreve a dispersao do saldo em valores absolutos de familias, sem normalizar pelo tamanho do municipio. **Risco:** Quantis de uma grandeza absoluta em uma distribuicao municipal fortemente assimetrica (capitais x municipios pequenos) sao dominados pela escala popu… |
| `44-44` | Variacao nacional do universo elegivel e contagem de quedas | agregação | Da a ordem de grandeza do movimento do denominador que a linha 49 tenta relacionar com d_cob. **Risco:** Soma com compensacao entre municipios: um total nacional proximo de zero e compativel com grande movimentacao em sentidos opostos. NaN contam como na… |
| `47-47` | Filtro de municipios para as correlacoes | limiar | Restringe a correlacao aos municipios com as duas pontas medidas e com denominador acima de 500 familias elegiveis. O codigo nao registra por que 500. **Risco:** O corte de 500 e uma escolha que muda o resultado publicado da correlacao e nao esta documentada em lugar nenhum do arquivo. Nao ha analise de sensib… |
| `48-48` | Spearman entre saida relativa da pobreza e variacao de cobertura | estatística | Correlacao de postos obtida como Pearson sobre rank(), que e a definicao de Spearman com tratamento de empates por posto medio (rank padrao do pandas… **Risco:** Os postos sao calculados sobre o subconjunto k, entao o coeficiente nao e comparavel com outro rodado com filtro diferente. saiu_pobreza e d_cob comp… |
| `49-49` | Spearman entre variacao relativa do elegivel e variacao de cobertura | estatística | Testa diretamente a hipotese anunciada no cabecalho da secao (linha 46): se a queda de cobertura acompanha o crescimento do denominador. E a contrapa… **Risco:** O filtro k nao exige d_eleg notna — ele exige saiu_pobreza notna. Municipios com eleg_2603 ausente entram em k e sao descartados depois, dentro do co… |

### `reconstrucao/pipeline/10a_payload_comparacao.py`

| linhas | operação | espécie | o que faz, e o que a tornaria errada |
|---|---|---|---|
| `4-6` | Alinhamento do painel a ordem dos paths do mapa | cartografia | O payload e publicado como vetores posicionais (linhas 98-104): o indice do vetor precisa corresponder ao indice do path no SVG, e reindex(ordem) for… **Risco:** reindex cria linha inteiramente NaN para codigo presente em geo.json e ausente no painel, e descarta em silencio municipio do painel que nao esteja e… |
| `6-7` | Reindexacao do painel para a ordem dos paths do mapa | cartografia | Todos os vetores do payload sao listas posicionais lidas pelo SVG do mapa; o alinhamento posicional so e valido se a ordem das linhas for exatamente … **Risco:** O desalinhamento e silencioso por natureza: uma linha a mais ou a menos desloca TODOS os valores subsequentes para o municipio errado, e nada alem do… |
| `7-7` | Contagem de municipios sem correspondencia | apresentação | Mede quantas linhas o reindex criou sem dado, usando nome como sentinela de linha vazia. E diagnostico: nao interrompe a execucao nem altera o payloa… **Risco:** Se um municipio real tiver nome ausente no painel, ele e contado como faltante; se um codigo do painel estiver fora de geo.json, essa perda nao apare… |
| `9-10` | Carga do payload anterior e verificacao da ordem | leitura | Como o script escreve por cima do proprio dados.json (linha 110), os vetores novos so podem ser concatenados aos antigos se ambos seguirem a mesma or… **Risco:** Se dados.json nao tiver nem codes nem cod, a expressao levanta KeyError em vez da mensagem de assert; comparacao == entre listas exige tipo identico,… |
| `12-14` | Conversao de serie para lista JSON com nulo e arredondamento | serialização | Converte NaN do pandas, que json.dumps nao serializa como JSON valido, em null explicito, e decide a precisao publicada: sem dec o valor vira inteiro… **Risco:** int(x) trunca em direcao a zero e nao arredonda: 2,9 e publicado como 2; round de Python arredonda a metade exata para o par, entao 0,5 vira 0; valor… |
| `17-18` | Variacao nacional de beneficiarios por distribuidora | aritmética | Variacao percentual do numero de beneficiarios de cada agente entre dez/2024 e mar/2026. O replace(0,np.nan) evita divisao por zero, convertendo o ca… **Risco:** Nenhuma etapa do roda_tudo.py escreve por_agente.csv: o arquivo existe em reconstrucao/dados mas nao tem produtor no pipeline, entao esta linha conso… |
| `17-17` | Leitura do agregado por distribuidora | leitura | index_col=0 usa a primeira coluna (nome do agente) como indice, o que permite os testes de pertencimento por rotulo das linhas 72 a 74. O arquivo ja … **Risco:** Nome do agente e a chave: variacao de grafia, acento ou espaco entre execucoes cria linhas distintas para a mesma empresa; se houver rotulo repetido … |
| `18-18` | Variacao percentual nacional de beneficiarios por distribuidora | aritmética | replace(0, np.nan) troca a divisao por zero por NaN, de modo que agente sem beneficiario na base de 2024 produz valor nulo em vez de infinito; a linh… **Risco:** A conta sobrescreve a coluna var que ja vem no CSV, entao qualquer definicao diferente usada a montante e perdida sem aviso; sendo razao de estoques,… |
| `19-21` | Corte de porte e ordenacao das distribuidoras | limiar | O corte de 1000 beneficiarios em dez/2024 remove agentes pequenos, cuja variacao percentual e ruidosa. O valor 1000 e literal e o codigo nao registra… **Risco:** O limiar e arbitrario e nao documentado: mover de 1000 para 500 muda a lista publicada e qualquer afirmacao do tipo "todas as distribuidoras". Agente… |
| `19-19` | Corte de porte e ordenacao das distribuidoras | limiar | Elimina agentes pequenos, em que poucas familias produzem variacao percentual extrema (o CSV traz caso de 19 para 5 beneficiarios, -73,7%). O valor 1… **Risco:** O limiar aplica-se so a dez24; um agente que tinha menos de 1000 em 2024 e cresceu muito ate 2026 e excluido, o que enviesa a lista para quedas entre… |
| `20-21` | Montagem do bloco de distribuidoras do payload | serialização | np.isfinite descarta os NaN criados pelo replace da linha 18 e eventuais infinitos, de modo que so entra agente com variacao definida; int e round fi… **Risco:** int() trunca as contagens em vez de arredondar; iterrows converte a linha para uma Series unica, entao se houver coluna de texto no CSV os numeros vi… |
| `24-26` | Variacao por par municipio-distribuidora | aritmética | mun_agente.csv vem do 07b_municipio_agente.py, que conta linhas SubsBaixaRenda por par (municipio, agente) nas duas datas e aplica fillna(0) no merge… **Risco:** Por causa do fillna(0) do 07b, par que so existe em 2026 tem b24=0 e cai fora pelo replace/NaN e pelo corte; par que so existe em 2024 produz var=-10… |
| `24-24` | Leitura do cruzamento municipio x distribuidora | leitura | Fonte do bloco de municipios atendidos por mais de uma concessionaria. O arquivo contem linhas com cod_ibge igual a 0, isto e, registros da CDE sem m… **Risco:** cod_ibge 0 e um pseudo-municipio: se sobrevivesse aos filtros seguintes, agruparia agentes de lugares distintos num falso caso de dupla concessionari… |
| `25-25` | Variacao percentual por par municipio-distribuidora | aritmética | Mesma definicao da linha 18, agora no nivel municipio-agente, para permitir comparar duas concessionarias dentro do mesmo municipio. O replace evita … **Risco:** Pares que aparecem so em 2026 tem b24 ausente ou zero e saem como NaN, ou seja, entrada de distribuidora nova nunca e representada; a variacao nao se… |
| `26-26` | Corte de porte minimo do par municipio-distribuidora | limiar | Abaixo de 100 beneficiarios a variacao percentual e dominada por poucos casos. O numero 100 e literal e sem justificativa no arquivo; e um corte dife… **Risco:** O corte incide so sobre 2024, entao crescimento a partir de base pequena e sistematicamente excluido; exclui tambem o municipio inteiro quando uma da… |
| `27-29` | Selecao de municipios com duas ou mais concessionarias | agregação | Identifica municipios atendidos por mais de um agente para comparar a variacao de cada um dentro do mesmo territorio. A contagem e feita DEPOIS do fi… **Risco:** Contar depois do filtro faz um municipio com uma distribuidora grande e uma pequena aparecer como de agente unico, o que subestima o numero de munici… |
| `27-28` | Selecao dos municipios com duas ou mais distribuidoras | agregação | nunique conta agentes distintos, e nao linhas, de modo que duplicidade de registro do mesmo agente no municipio nao cria um falso par. A contagem e f… **Risco:** A condicao mede presenca de duas distribuidoras na base filtrada, nao atendimento simultaneo de fato; variacao de grafia do nome do agente conta como… |
| `29-29` | Anexacao de nome e UF aos pares selecionados | agregação | O merge a esquerda preserva todos os pares selecionados mesmo sem correspondencia no painel, o que mantem a contagem mun2dist estavel; o rotulo, pore… **Risco:** Codigo presente na CDE e ausente da malha do Censo 2022 (o comentario das linhas 44 a 48 declara esse tipo de residuo) produz nome e uf NaN, que a li… |
| `30-35` | Montagem e ordenacao dos pares por divergencia interna | estatística | Dentro do municipio, os agentes sao ordenados por variacao, e os municipios sao ordenados pela amplitude entre a maior e a menor variacao. Como g foi… **Risco:** A amplitude usa apenas os extremos: um municipio com tres agentes, dois estaveis e um extremo, ordena igual a um com dois agentes realmente opostos. … |
| `30-34` | Montagem dos pares de distribuidoras por municipio | serialização | A ordenacao por var crescente e o que torna d[0] o pior desempenho e d[-1] o melhor; as linhas 35 e 88 dependem dessa ordem para calcular amplitude e… **Risco:** Se a ordenacao for removida ou trocada, amplitude e contagem de sinais opostos passam a medir outra coisa sem erro visivel; iloc[0] adota como rotulo… |
| `35-35` | Ordenacao dos pares por amplitude de divergencia | agregação | A diferenca entre o extremo superior e o inferior mede quanto duas concessionarias divergiram no mesmo municipio, sob a premissa de que a lista d ja … **Risco:** Amplitude em pontos percentuais favorece municipios com distribuidora pequena e variacao extrema, mesmo apos o corte de 100 beneficiarios; nao ponder… |
| `49-49` | Leitura da serie mensal do CadUnico | leitura | O comentario das linhas 44 a 48 declara que o agregado nacional sai desta fonte, e nao da soma do painel, e registra a diferenca (940.860 contra 940.… **Risco:** A cobertura do arquivo (5.571 municipios em 202412) difere da malha publicada, entao o agregado nacional e a soma dos vetores municipais do payload n… |
| `50-53` | Agregado nacional do CadUnico por competencia | agregação | Soma simples de contagens municipais dentro de uma competencia; o assert exige apenas que a competencia exista e tenha ao menos um valor nao nulo em … **Risco:** sum do pandas ignora NaN, entao municipio sem valor entra como zero e o total sai subestimado sem aviso; nesta base a competencia 202412 tem uma linh… |
| `54-54` | Fixacao das duas competencias comparadas | leitura | Define dezembro de 2024 e marco de 2026 como as datas da comparacao publicada. Os dois codigos de competencia sao literais no arquivo; o codigo nao r… **Risco:** Uma atualizacao da serie nao move a comparacao: o script continua lendo 202603 mesmo com competencia mais recente presente; se uma das duas sumir do … |
| `55-59` | Bloco de fluxo do CadUnico e variacao do estoque em pobreza | aritmética | saiu_pob e a diferenca entre dois estoques nacionais na mesma fonte. O nome sugere fluxo de saida, mas a operacao e variacao liquida: entradas e said… **Risco:** Se o estoque cresceu, saiu_pob fica negativo e o rotulo passa a contradizer o sinal; a diferenca tambem absorve mudanca de cobertura municipal entre … |
| `62-62` | Totais nacionais de beneficiarios pela soma municipal | agregação | O comentario da linha 61 declara a escolha: para beneficios, a soma corre sobre a malha publicada, ao contrario do CadUnico, que vem do agregado da f… **Risco:** A soma ignora NaN, e ben26 ja chega preenchido com zero a montante (08b_nacional_2026.py aplica fillna(0)), de modo que municipio sem dado em 2026 e … |
| `68-69` | Definicao dos grupos economicos comparados | agregação | Agrupa concessionarias por controlador para a decomposicao da queda. O comentario das linhas 64 a 67 afirma que sao os dois grupos que concentram a q… **Risco:** Casamento por texto exato: se o rotulo mudar de grafia entre execucoes (por exemplo ENEL SP no lugar de ELETROPAULO), o grupo esvazia sem erro e o va… |
| `70-70` | Releitura do agregado por agente sem os cortes | leitura | Recarregar o arquivo devolve a tabela completa, porque ag foi reduzida na linha 19 ao subconjunto com dez24 acima de 1000. A decomposicao das linhas … **Risco:** Duas variaveis com conteudo parecido e escopo diferente (ag filtrada, agf completa) convidam a troca acidental numa edicao futura; se o corte da linh… |
| `71-71` | Variacao absoluta de beneficiarios por agente | aritmética | Diferenca absoluta, e nao relativa, porque as parcelas serao somadas entre agentes; variacoes percentuais nao sao aditivas. O codigo nao comenta essa… **Risco:** Agente presente em so uma das datas gera NaN, que nas somas seguintes vira zero e desaparece da decomposicao; se a carteira de um municipio migrou de… |
| `72-74` | Decomposicao da variacao em Enel, EDP e complemento | agregação | O terceiro termo e definido por negacao dos dois primeiros, o que garante que a soma das tres parcelas reproduza a variacao total por agente, conform… **Risco:** O fechamento vale contra a soma por agente, nao contra B26-B24 da linha 62: as duas bases tem universos diferentes e a diferenca nao e calculada aqui… |
| `79-79` | Mascara de municipios com fracao coberta utilizavel nas duas datas | limiar | O comentario das linhas 76 a 78 declara a regra: onde a CDE ficou liquida negativa a fracao nao e utilizavel, e misturar as duas populacoes moveria a… **Risco:** O filtro pareado descarta municipio utilizavel numa das datas, o que reduz a amostra e pode enviesa-la para municipios de subsidio estavel; a condica… |
| `80-80` | Selecao das duas series de fracao coberta | leitura | Extrair as duas series com a mesma mascara mantem o pareamento por municipio, necessario para a comparacao elemento a elemento da linha 81. A fracao … **Risco:** Se as duas series fossem selecionadas com mascaras distintas, a comparacao da linha 81 alinharia municipios diferentes pelo indice; qualquer reordena… |
| `81-81` | Contagem de municipios com ganho de fracao coberta | agregação | Comparacao estrita elemento a elemento entre municipios pareados; empate exato nao conta como ganho. A comparacao usa o alinhamento por indice do pan… **Risco:** Comparacao de floats sem tolerancia: diferenca de arredondamento na quinta casa ja classifica um municipio como ganho; a contagem nao pesa tamanho do… |
| `82-83` | Transporte dos totais de beneficios e da decomposicao para o payload | serialização | O comentario das linhas 38 a 42 declara a regra do arquivo: estes numeros eram literais no codigo e passaram a ser derivados, para que uma reexecucao… **Risco:** b24 e b26 vem da soma municipal e enel, edp e resto da tabela por agente: os dois conjuntos tem universos distintos, e o payload os publica lado a la… |
| `84-84` | Medianas nacionais da fracao coberta | estatística | Mediana, e nao media, sobre a distribuicao municipal da fracao coberta; o comentario das linhas 76 a 78 registra que as duas medianas sao calculadas … **Risco:** Mediana de municipios nao e a fracao coberta do pais: nao pondera por familias nem por consumo, entao um municipio minusculo pesa igual a uma capital… |
| `85-85` | Contagem de ganhos e tamanho da amostra | agregação | Publicar o denominador ao lado do numerador permite que quem le o payload saiba sobre quantos municipios a estatistica foi calculada, ja que o filtro… **Risco:** ganho_n e a contagem apos o filtro pareado, nao o total de municipios da malha; o payload nao publica quantos foram excluidos nem por que, entao a di… |
| `86-86` | Percentual de municipios com ganho | aritmética | Proporcao simples sobre a mesma populacao filtrada usada nas medianas; a divisao entre inteiros em Python 3 ja devolve float, entao nao ha truncament… **Risco:** Se o filtro k nao selecionar nenhum municipio, int(k.sum()) e zero e a linha levanta ZeroDivisionError, interrompendo o pipeline; o percentual conta … |
| `87-88` | Contagem de municipios com duas distribuidoras e com sinais opostos | agregação | A condicao encadeada exige que a menor variacao do municipio seja negativa e a maior positiva, ou seja, que duas concessionarias no mesmo municipio t… **Risco:** Se a ordenacao da linha 32 mudar, d[0] e d[-1] deixam de ser os extremos e a contagem passa a medir outra coisa sem erro; a contagem herda todos os c… |
| `91-93` | Diagnostico impresso dos totais e da decomposicao | apresentação | A soma das tres parcelas e impressa ao lado das parcelas justamente para tornar visivel o fechamento afirmado no comentario das linhas 64 a 67. Estes… **Risco:** O confronto entre a soma das tres parcelas e a diferenca B26-B24 fica a cargo de quem le o log; nada no codigo compara os dois numeros nem interrompe… |
| `94-94` | Variacao percentual nacional de familias elegiveis | aritmética | Mesma forma de variacao relativa usada nas linhas 18 e 25, agora sobre o total nacional de elegiveis do CadUnico. O resultado so aparece no log; a pa… **Risco:** Divide sem protecao: eleg de 2024 igual a zero levantaria ZeroDivisionError, e aqui nao ha replace por NaN como nas linhas 18 e 25; o numerador e o d… |
| `95-95` | Conversao da fracao coberta para percentual no log | apresentação | O payload guarda a fracao como numero entre 0 e 1 com cinco casas (linha 84) e a multiplicacao por 100 acontece so na exibicao, o que deixa a unidade… **Risco:** A multiplicacao por 100 e feita sobre o valor ja arredondado a cinco casas, entao o percentual impresso pode diferir na terceira casa do que se obter… |
| `98-104` | Serializacao das series municipais com precisao por campo | serialização | A escolha de casas decimais define o que a pagina consegue exibir e o tamanho do arquivo: cobertura e diferenca de cobertura vem de 09a como percentu… **Risco:** As series carregam decisoes tomadas a montante que o payload nao declara: cob_* ja e uma divisao com replace(0, NaN) sobre elegiveis, d_cob e diferen… |
| `105-108` | Anexacao dos blocos agregados ao payload | serialização | Reune no mesmo objeto os vetores posicionais e os agregados derivados, de modo que a pagina leia um unico arquivo. As chaves sao curtas, o que reduz … **Risco:** Nada verifica que os blocos agregados e as series vieram da mesma execucao dos mesmos insumos alem da ordem verificada na linha 10; se um bloco falha… |
| `109-110` | Fusao com o payload anterior e gravacao do JSON | serialização | update sobrescreve so as chaves presentes em novo e preserva o restante do payload produzido por etapas anteriores; separators sem espaco e ensure_as… **Risco:** Grava por cima da propria fonte lida na linha 9: uma falha no meio da escrita deixa dados.json truncado e a execucao seguinte quebra na leitura; o ar… |
| `111-111` | Tamanho do arquivo publicado em megabytes | aritmética | Divisao por 1e6, isto e, megabyte decimal, coerente com o que se mede em transferencia de rede; nao e MiB (1.048.576). O codigo nao registra a conven… **Risco:** Quem comparar esse numero com o tamanho mostrado pelo sistema de arquivos, que costuma usar potencia de dois, vera cerca de 5% de diferenca; o valor … |
| `112-113` | Contagens finais do payload impressas | apresentação | Le a contagem de sinais opostos de dentro do dicionario ja montado, e nao de uma variavel solta, de modo que o log reporta exatamente o que foi grava… **Risco:** Sao contagens apos todos os cortes (1000 beneficiarios por agente, 100 por par municipio-agente), entao nao descrevem o universo de distribuidoras ne… |

### `reconstrucao/pipeline/10c_payload_agente.py`

| linhas | operação | espécie | o que faz, e o que a tornaria errada |
|---|---|---|---|
| `4-4` | Alinhamento posicional a ordem do mapa | leitura | Os arrays cdei e cdev sao publicados sem chave: a correspondencia com o municipio e so a posicao no vetor, definida por geo['codes'] — o template le … **Risco:** Acoplamento implicito: regenerar geo.json com outra ordem sem regerar dados.json atribui a variacao ao municipio errado, sem erro nem aviso, porque o… |
| `7-8` | Agente dominante do municipio por beneficios de dezembro de 2024 | agregação | drop_duplicates apos ordenacao decrescente mantem, para cada municipio, a linha do agente com mais beneficios em dez/2024, e carrega o b26 do mesmo a… **Risco:** A dominancia e fixada na base de 2024: se o agente dominante mudou ate mar/2026, a variacao publicada e a do agente antigo. Empate em b24 e resolvido… |
| `9` | Reindexacao pela ordem do mapa | cartografia | Garante um elemento por municipio do mapa, na posicao correta, inclusive para municipios sem par municipio-agente na base CDE. **Risco:** reindex exige indice unico — garantido apenas pelo drop_duplicates da linha anterior; se ele falhar, reindex levanta erro. Codigos presentes em mun_a… |
| `10` | Variacao percentual dos beneficios do agente dominante entre dez/2024… | aritmética | Variacao relativa do estoque de beneficios do agente dominante entre os dois recortes. replace(0, np.nan) troca divisao por zero por ausencia: o resu… **Risco:** Quando b24 = 0 e b26 > 0 (agente que so aparece em 2026) a variacao fica indefinida e o municipio perde o valor apesar de ter crescimento — e esse ca… |
| `12-13` | Dicionario de agentes e codificacao por indice | agregação | Substitui o nome repetido em milhares de posicoes por um inteiro, reduzindo o tamanho do JSON publicado (a linha 20 imprime o tamanho do arquivo). **Risco:** sorted usa ordem de codigo de caractere sobre a string bruta: maiusculas, acentos e espacos afetam a ordenacao. O indice e posicional e nao estavel: … |
| `14-15` | Serializacao do indice do agente por municipio | cartografia | cdei e lido no template como D.cdeag[D.cdei[i]], ou seja, o nome do agente e recuperado por dupla indexacao a partir da posicao do municipio. **Risco:** Depende da posicao i coincidir com geo['codes'] e do par cdeag/cdei ser publicado junto; um payload parcialmente atualizado exibe o nome de outro age… |
| `16` | Arredondamento e filtro de valores nao finitos da variacao | aritmética | Uma casa decimal basta para exibicao no mapa e reduz o tamanho do JSON; null cobre tanto b24 = 0 quanto qualquer infinito residual. **Risco:** round() do Python usa arredondamento para o par mais proximo (half-even), entao −12,25 vira −12,2 e nao −12,3; o valor publicado nao e exatamente o c… |
| `18-19` | Escrita do payload e contagens de controle | agregação | O script le dados.json, acrescenta tres chaves e reescreve o mesmo arquivo; separators compactos e ensure_ascii=False reduzem o tamanho. **Risco:** Escrita sobre o proprio arquivo de entrada sem backup: se o processo falhar entre a abertura em modo 'w' e o write, dados.json fica vazio e os passos… |
| `20` | Tamanho do payload em MB decimais | aritmética | Controle do peso do arquivo que o mapa baixa; a divisao por 1e6 define MB como 10^6 bytes. **Risco:** 1e6 e MB decimal, nao MiB (2^20 = 1.048.576): o numero impresso e cerca de 4,9% maior que o exibido por ferramentas que usam base binaria. Mede o arq… |

## Geometria e publicação

119 operações em 6 arquivos.

### `reconstrucao/pipeline/08_geometria.py`

| linhas | operação | espécie | o que faz, e o que a tornaria errada |
|---|---|---|---|
| `30-33` | Constantes de arredondamento, tolerancia e corte de area | limiar | A docstring (linhas 16 a 20) registra a razao de duas delas: a simplificacao de 2 km e feita no plano projetado, que e onde tolerancia em metros faz … **Risco:** A equivalencia 3 casas decimais = 111 m so vale para latitude; em longitude o grau encolhe com o cosseno da latitude, de modo que no extremo sul do p… |
| `35-35` | Leitura da malha municipal e selecao de colunas | leitura | Carrega a malha de origem e descarta as demais colunas. O codigo nao registra qual versao ou ano da malha do IBGE esta no parquet, nem qual CRS vem g… **Risco:** Se o parquet vier sem CRS definido, to_crs na linha 40 levanta erro. Se o arquivo tiver sido gerado por outro passo com nomes de coluna diferentes, a… |
| `36-36` | Leitura da tabela de dados do aplicativo | leitura | Le a tabela ja produzida por passo anterior do pipeline para extrair dela o conjunto e a ordem dos municipios. O arquivo so e usado por cod_ibge; nen… **Risco:** Le o CSV inteiro (36 colunas, mais de 5 mil linhas) para usar uma coluna. Se app_dados.csv nao existir porque o passo anterior nao rodou, o passo fal… |
| `37-37` | Juncao que restringe a geometria aos municipios do payload | agregação | O merge sem parametro how usa o padrao inner, entao o resultado e a intersecao. O codigo nao registra por que a intersecao e nao um left join com geo… **Risco:** Falha silenciosa por tipo: se cod_ibge for texto de um lado e inteiro do outro, o resultado e vazio sem erro. Se d tiver cod_ibge duplicado, cada geo… |
| `38-38` | Reordenacao das geometrias na ordem do payload | agregação | O comentario do proprio autor registra a razao: ordem do payload. Isso e o que sustenta os passos seguintes, porque a lista codes gravada na linha 89… **Risco:** Todo o resto do arquivo passa a depender de alinhamento posicional, que e mudo quando quebra: qualquer reordenacao, filtro ou drop posterior sobre gd… |
| `40-40` | Reprojecao para SIRGAS 2000 Policonica (EPSG:5880) | cartografia | A docstring justifica a existencia de um plano projetado: a simplificacao de 2 km e feita no plano projetado, que e onde tolerancia em metros faz sen… **Risco:** A Policonica brasileira nao preserva area nem distancia longe do meridiano central; a comparacao de area da linha 68 e feita nesse plano, entao o lim… |
| `42-45` | Arredondamento recursivo das coordenadas para tres casas | aritmética | Reduz o tamanho do JSON cortando digitos. A docstring registra a razao e a ordem de grandeza: tres casas decimais valem cerca de 111 m, bem abaixo do… **Risco:** O ramo de folha devolve apenas c[0] e c[1]: se a geometria tiver coordenada Z, a terceira componente e descartada em silencio. Se algum vertice vier … |
| `47-48` | Simplificacao Douglas-Peucker e reprojecao para WGS84 | cartografia | A ordem importa e esta registrada na docstring: simplifica no plano projetado, onde a tolerancia em metros e interpretavel, e so depois converte para… **Risco:** Se a funcao receber geometria em outro CRS, o crs=5880 e aceito sem conferencia e a tolerancia passa a significar outra coisa. Com preserve_topology=… |
| `50-53` | Geometria ausente ou vazia vira feature com geometry nula | serialização | Preserva a cardinalidade e a ordem: em vez de omitir o municipio sem geometria, emite uma feature nula, de modo que a posicao no vetor de features co… **Risco:** zip trunca em silencio: se len(ids) e len(g) diferirem, o excedente e descartado sem erro e o alinhamento posicional com o payload quebra sem aviso. … |
| `54-57` | Montagem da feature GeoJSON com coordenadas arredondadas | serialização | properties fica vazio de proposito: o identificador viaja em id e todos os atributos ficam no payload de dados, ligados por posicao ou por codigo. Is… **Risco:** O consumidor precisa cruzar geometria e dado por id ou por posicao; se a biblioteca de mapa reordenar as features, a leitura por posicao quebra e so … |
| `59-59` | Camada municipal simplificada a 2 km | cartografia | Usa o padrao topologia=True, isto e, preserve_topology ligado para a camada municipal, ao contrario da camada estadual da linha 72. O comentario das … **Risco:** O alinhamento entre proj.geometry e gdf.cod_ibge e posicional; proj foi derivado de gdf na linha 40, entao vale enquanto ninguem reordenar um dos doi… |
| `67-67` | Decomposicao de MultiPolygon em partes | leitura | Normaliza o tratamento para que o filtro de area da linha seguinte opere sempre sobre uma lista. O teste e por nome de tipo exato, entao so MultiPoly… **Risco:** Se o dissolve devolver GeometryCollection ou Polygon com buracos problematicos, o ramo else embrulha a geometria inteira em lista de um elemento e o … |
| `68-68` | Descarte de lascas do dissolve por limiar de area | limiar | O comentario das linhas 60 a 65 registra a medida que motivou o corte: o dissolve produz 898 partes com mediana de 0,014 km2, frestas de ponto flutua… **Risco:** O limiar de 20 km2 e absoluto, entao ele nao distingue fresta numerica de ilha real: qualquer ilha costeira com menos de 20 km2 que forme parte separ… |
| `69-69` | Recomposicao do MultiPolygon e saneamento por buffer(0) | cartografia | buffer(0) e o idioma usual para forcar validade em geometria com auto-intersecao ou anel mal orientado, o que e provavel depois de um dissolve com fr… **Risco:** buffer(0) nao e neutro: pode remover microareas, eliminar aneis degenerados e, em geometria invalida de certo tipo, devolver poligono vazio ou trocar… |
| `71-71` | Dissolve das geometrias municipais por unidade da federacao | agregação | A camada estadual e derivada da propria malha municipal em vez de lida de um arquivo estadual, o que garante que os contornos coincidam exatamente co… **Risco:** O .values e exatamente o ponto fragil: se os indices de proj e gdf divergissem, o pandas normalmente alinharia ou acusaria; com .values a atribuicao … |
| `72-72` | Camada estadual simplificada a 3 km sem preservar topologia | cartografia | O comentario das linhas 62 a 65 registra a razao de desligar a preservacao de topologia: com ela ligada a simplificacao se recusa a agir sobre a geom… **Risco:** Com preserve_topology=False a simplificacao pode gerar poligono auto-intersectado ou invalido, e nada revalida depois. Como cada UF e simplificada de… |
| `74-74` | Contagem de municipios sem geometria | agregação | E a unica verificacao de sanidade do arquivo. Conta os casos produzidos pelo ramo das linhas 50 a 53 e o resultado e apenas impresso, nao comparado a… **Risco:** E diagnostico passivo: nenhum assert, nenhuma interrupcao. Se todos os municipios saissem sem geometria, o passo gravaria o geo.json mesmo assim e so… |
| `75-76` | Impressao das contagens das duas camadas | apresentação | Expoe no log os numeros que permitem conferir de fora se a malha cobriu o payload e se apareceram 27 unidades da federacao. Nao ha conferencia automa… **Risco:** Se a saida padrao nao for lida, a informacao se perde. Um numero de UF diferente de 27 nao interrompe nada. |
| `81-81` | Lista fixa de municipios excluidos do enquadramento | limiar | O comentario das linhas 78 a 80 registra a intencao: o enquadramento inicial e o continente, e as ilhas continuam no mapa, alcancaveis por deslocamen… **Risco:** A exclusao e do municipio inteiro, nao apenas da ilha: o territorio continental de Vitoria e de Recife tambem sai do calculo do envelope. Aqui isso e… |
| `82-82` | Filtro do continente e reprojecao para graus | cartografia | Parte de gdf, a malha original sem simplificar, e nao de mun, a malha ja simplificada. Isso significa que o enquadramento e calculado sobre os vertic… **Risco:** Como o envelope vem da geometria completa e o desenho vem da simplificada, os dois podem diferir por ate a tolerancia de 2 km na borda, diferenca irr… |
| `83-83` | Envelope do continente | estatística | total_bounds devolve a ordem (minx, miny, maxx, maxy), isto e, longitude primeiro, e o desempacotamento segue essa ordem. E o extremo absoluto, nao u… **Risco:** Por ser minimo e maximo puros, qualquer poligono espurio remanescente na malha continental dominaria o enquadramento inteiro. Se cont ficasse vazio, … |
| `84-84` | Foco do mapa em pares latitude e longitude | cartografia | Inverte deliberadamente a ordem em relacao ao GeoJSON: as coordenadas das features sao [lon, lat] e o foco e [lat, lon], que e a convencao de bounds … **Risco:** A inversao e muda: um consumidor que leia foco como [lon, lat] enquadraria o mapa em um ponto no oceano Indico, ja que as latitudes brasileiras sao n… |
| `85-85` | Envelope de toda a malha, com as ilhas | estatística | Existe apenas para a comparacao impressa nas linhas 86 e 87; nao entra no arquivo gravado. E o termo de contraste que quantifica quanto o enquadramen… **Risco:** Reprojeta a malha inteira uma segunda vez so para imprimir dois numeros, custo desnecessario mas sem efeito no resultado. Nao e gravado, entao a comp… |
| `86-87` | Impressao da largura dos dois enquadramentos em graus | aritmética | Mede em graus de longitude, nao em quilometros, apesar de a docstring apresentar o mesmo problema em quilometros (4.819 km contra 4.326 km). A difere… **Risco:** Grau de longitude nao e distancia constante: encolhe com o cosseno da latitude, entao esses numeros nao sao comparaveis diretamente aos quilometros c… |
| `89-89` | Montagem do payload geografico | serialização | codes repete a ordem fixada na linha 38, a mesma das features de mun, o que permite ao aplicativo indexar geometria e dado por posicao. int() e neces… **Risco:** codes e a lista de features de mun sao redundantes e podem divergir sem que nada detecte: se zip tivesse truncado nas linhas 50 e seguintes, codes te… |
| `90-91` | Serializacao compacta e gravacao do geo.json | serialização | separators=(",", ":") elimina os espacos que json.dumps insere por padrao, o que reduz o tamanho do arquivo, coerente com a preocupacao de custo decl… **Risco:** O arquivo e aberto sem contexto e nunca fechado explicitamente: depende da contagem de referencias do CPython para descarregar o buffer, o que nao e … |
| `92-92` | Tamanho do arquivo gravado em megabytes decimais | aritmética | Divide por 1e6, isto e, megabyte decimal, e nao por 2^20. E o numero que a docstring cita como custo medido, 2,30 MB crus, entao a convencao usada no… **Risco:** Quem interpretar MB como 2^20 bytes lera cerca de 5% a menos que o valor impresso. O numero medido e o do arquivo cru; o custo relevante para o usuar… |

### `reconstrucao/pipeline/09_payload.py`

| linhas | operação | espécie | o que faz, e o que a tornaria errada |
|---|---|---|---|
| `5` | Leitura da base municipal consolidada | leitura | O arquivo lido e a saida de 07_tarifa_social.py (linha 33, d.to_csv(str(OUT)+"/app_dados2.csv",index=False)), ou seja, a base ja com conta_cheia80, c… **Risco:** Nenhuma validacao de schema, de numero de linhas ou de dtypes; se 07 nao rodou, le uma versao antiga do CSV sem aviso. Colunas inteiras que contenham… |
| `6` | Lista ordenada de distribuidoras e indice posicional | serialização | Substituir a string da distribuidora por um inteiro reduz o tamanho do JSON, que e medido logo adiante na linha 26; a ordenacao alfabetica torna o in… **Risco:** dropna() remove os nulos da lista, mas a linha 10 indexa di[x] para todas as linhas: se algum municipio tiver distribuidora nula ou um valor que nao … |
| `7-8` | Conversao para inteiro sem arredondamento (col com dec=None) | aritmética | Aplicado aos campos que o projeto trata como contagem (cad, pob, bxr, ele, ben, lac, sob, sind, rkt, nc, vio, fav, dt). int() e truncamento, nao arre… **Risco:** Se alguma dessas colunas deixar de ser inteira por construcao (por exemplo, uma media ponderada de conjuntos em nc, ou uma lacuna calculada em fracao… |
| `7-9` | Funcao col: nulo explicito, truncamento a inteiro ou arredondamento d… | apresentação | E a unica conversao de NaN para null do arquivo: json.dumps emitiria NaN, que nao e JSON valido, entao o pd.isna e o que garante que o payload possa … **Risco:** int(x) trunca, nao arredonda: uma coluna float com valor 2,99 vira 2, e um valor negativo pequeno vira 0, o que muda contagens como lacuna e domicili… |
| `9` | Arredondamento decimal do payload (col com dec) | aritmética | Define a precisao publicada de cada campo e, por consequencia, o tamanho do arquivo. O round() do Python 3 desempata para o digito par e opera sobre … **Risco:** Arredondar ANTES de comparar muda classificacao no app: pc e ps sao publicados com 4 casas e o template testa pc>0.10 e ps<=0.10; d3x vai com 2 casas… |
| `18` | Contagens do CadUnico convertidas a inteiro | apresentação | Sao contagens de familias, portanto o ramo inteiro de col e coerente com a unidade. Nada aqui recalcula as tres colunas, que chegam prontas do CSV. **Risco:** Se a montante essas colunas tiverem virado float por merge com municipios sem CadUnico, o int() trunca em vez de arredondar, subestimando em ate uma … |
| `19-21` | Elegiveis e beneficiarios casados em marco de 2026 | apresentação | O comentario e a unica declaracao no arquivo do criterio de data: as duas pontas do indicador principal, elegiveis e beneficiarios, vem da mesma refe… **Risco:** O casamento temporal e afirmado pelo comentario, nao verificado pelo codigo: se o CSV trouxer colunas de outra data com esse nome, nada acusa. As cha… |
| `22` | Colunas de dezembro de 2024 preservadas para a pagina de comparacao | apresentação | Conforme o comentario das linhas 12 e 13, estes dois vetores existem para 10a_payload_comparacao.py e para a pagina de comparacao, nao para o indicad… **Risco:** Os nomes de coluna familias_elegiveis e beneficiarios_tsee nao carregam data; a associacao a dezembro de 2024 vem do comentario acima, nao de uma che… |
| `23` | Cobertura com uma casa, lacuna truncada e sobrecobertura binaria | apresentação | cobertura ja chega em escala de 0 a 100 de 06d_concentracao.py (100 * beneficiarios_mar26 / familias_elegiveis_mar26 com replace(0, np.nan) no denomi… **Risco:** Municipios sem elegiveis chegam com cobertura NaN por causa do replace(0, np.nan) a montante e saem como null; a pagina precisa distinguir null de ze… |
| `24` | Valor nao acessado, subsidio por familia e indicador de indisponibili… | apresentação | rs_nao_acessado vem de 06d como lacuna_pos * subsidio_familia_mar26, portanto um produto de familias por reais por familia, e zero casa decimal e coe… **Risco:** round(x, 0) devolve float, de modo que rs aparece no JSON como 12345.0, gastando bytes e podendo ser exibido com .0 se o front nao formatar. Onde ben… |
| `25` | Tarifas com quatro casas e posicao no ranking | apresentação | Quatro casas em R$/kWh e a ordem de grandeza com que as tarifas homologadas sao publicadas; como 07_tarifa_social.py multiplica a tarifa por 80 kWh p… **Risco:** O arredondamento acontece so no payload, nao no calculo, entao conta_cheia80 publicada na linha 21 pode nao ser exatamente tar * 80: a pagina que rec… |
| `32` | Contas de 80 kWh e economia mensal com duas casas | apresentação | As tres colunas sao valores monetarios formados em 07_tarifa_social.py (tarifa_municipal*80, tarifa_baixa_renda*80*F80 e a diferenca entre as duas), … **Risco:** Como cada um dos tres e arredondado de forma independente, a identidade ec = cc - cs pode falhar em um centavo no valor publicado. Se conta_social80 … |
| `33` | Indicadores de qualidade do servico e de conjuntos eletricos | apresentação | dec_h_ano e uma duracao anual de interrupcao, e uma casa decimal e um decimo de hora. d3_corr e a razao entre o DEC observado e o limite, usada em 06… **Risco:** d3 com tres casas e d3x com duas usam precisoes diferentes para grandezas da mesma familia, e o codigo nao registra por que. O arredondamento de d3 p… |
| `34` | Violacao, domicilios em favela, domicilios totais e proporcao d4 | apresentação | violacao vem de 06e como np.where(d3_corr.isna(), np.nan, (d3_corr>=1).astype(float)), isto e, um float com tres estados: 0, 1 ou NaN; passar pelo ra… **Risco:** O null de vio significa DEC indisponivel, nao ausencia de violacao; se a pagina tratar null como zero, conta como sem violacao um municipio sem dado.… |
| `35` | Booleano de favela mapeada convertido em 0/1 e renda de referencia se… | apresentação | favela_mapeada vem de 04_territorio.py como cod_ibge.isin(fav.cod_ibge), um booleano; a conversao para 0 e 1 e o formato usado pelos demais indicador… **Risco:** Este e o unico campo que nao passa por col, entao nao tem ramo de nulo: um NaN em favela_mapeada e falsy e vira 0, e a string "False", que apareceria… |
| `36` | Serializacao compacta do payload em JSON | serialização | separators=(",",":") remove os espacos que o json.dumps insere por padrao e ensure_ascii=False grava os acentos dos nomes de municipio como UTF-8 em … **Risco:** O arquivo e aberto sem context manager e sem fechamento explicito: em CPython o refcount fecha o objeto, mas em outra implementacao o conteudo pode n… |
| `37` | Tamanho do arquivo publicado em megabytes | aritmética | A divisao e por 1e6 e nao por 1048576, portanto o numero exibido e em megabytes decimais, a mesma convencao usada para tamanho de download; e a unica… **Risco:** Quem comparar o valor com o que o sistema de arquivos exibe em MiB vera cerca de 5% de diferenca. Nao ha limite nem alerta: se o payload crescer ate … |
| `39` | Selecao da linha de Nova Iguacu para a checagem | leitura | E uma conferencia manual de um municipio conhecido, impressa no log para inspecao visual apos a gravacao do payload; o codigo nao compara com valor e… **Risco:** iloc[0] levanta IndexError se o municipio nao estiver na base, por exemplo apos um filtro a montante, quebrando o script depois que dados.json ja foi… |
| `40` | Impressao da conta cheia, da conta social e da economia com duas casas | apresentação | Reproduz no log a mesma precisao de duas casas usada no payload na linha 21, de modo que o operador possa comparar o log com o que a pagina exibe. A … **Risco:** Se qualquer um dos tres for NaN, o formato :.2f imprime nan sem erro e a checagem passa despercebida. O log nao registra a data nem a versao dos dado… |
| `41` | Conversao dos pesos a percentual com uma casa | apresentação | A multiplicacao por 100 converte a fracao publicada em pc e ps na linha 20 para ponto percentual; e a mesma conversao que 07_tarifa_social.py faz nas… **Risco:** A seta sugere um antes e um depois do mesmo indicador, mas os dois pesos tem denominadores distintos: peso_pob80_cheia usa renda_dom_teto_pob e peso_… |

### `reconstrucao/pipeline/10b_payload_continuidade.py`

| linhas | operação | espécie | o que faz, e o que a tornaria errada |
|---|---|---|---|
| `7-8` | Alinhamento das bases de continuidade a ordem cartografica | cartografia | O template le todas as listas por indice posicional; reindex(ordem) e o que garante que a posicao i de 'sit' seja o mesmo municipio da posicao i de '… **Risco:** reindex silencia dois erros opostos: codigos do CSV que nao estao em ordem sao descartados sem contagem, e codigos de ordem ausentes no CSV viram NaN… |
| `10-11` | Conversao a inteiro no payload de continuidade | aritmética | Copia literal da funcao homonima de 09_payload.py:6-8 e de 10a:12-14. Neste arquivo o ramo dec=None nao chega a ser usado: todas as chamadas passam c… **Risco:** Tres copias independentes da mesma funcao em tres arquivos do pipeline; alterar a regra de arredondamento em um nao altera nos outros, e os tres escr… |
| `12-12` | Arredondamento decimal no payload de continuidade | aritmética | Define a precisao publicada de rel24/rel25 (3 casas), h24/h25 (1 casa) e s24/s25/s26 (2 casas). **Risco:** rel24 e rel25 sao publicados com 3 casas e exibidos com 2 (nf2 em mapa.template.html:881): um valor de 0.9996 aparece como '1,00x o limite' ao lado d… |
| `14-18` | Codificacao da situacao de continuidade 2024/2025 | regra normativa | Traduz o par de anos em quatro estados mutuamente exclusivos. viol24/viol25 vem de rel>=1, onde rel e o pior entre DEC e FEC do conjunto dividido pel… **Risco:** As quatro condicoes sao exaustivas para 0/1, entao a ordem em que aparecem nao importa aqui — mas se viol vier com outro valor (2, por exemplo), cai … |
| `21-22` | Precisao das razoes sobre o limite e das horas anuais | aritmética | 3 casas em rel preserva a distancia ao limite de 1 com resolucao de 0,1%; 1 casa em horas e a resolucao com que o template as exibe (nf1, mapa.templa… **Risco:** rel e uma media ponderada por consumidores de razoes de conjuntos: um municipio com um conjunto pequeno em descumprimento grave e um conjunto grande … |
| `23-23` | Conversao da situacao para inteiro do payload | aritmética | np.select com default=np.nan devolve array de float (0.0, 1.0, 2.0, 3.0, nan); a conversao a int e necessaria porque o template usa o valor como indi… **Risco:** Nao reusa col() — e a quarta variacao da mesma conversao no pipeline. Se sit ganhasse um quinto estado, SITROT e SITTOM (vetores de 4 posicoes) devol… |
| `24-24` | Precisao das horas do primeiro semestre | aritmética | Sao horas de semestre, nao de ano: 03d restringe NumPeriodoIndice<=6 e exige os 6 periodos presentes nos tres anos (base comum de conjuntos). Por iss… **Risco:** s24 e o denominador da tendencia calculada no template (100*(s26/s24-1)) e das bandas de +-5% da linha 36-38 deste arquivo. Arredondar a 2 casas ante… |
| `26-26` | Contagem de municipios acima do limite e base apurada | agregação | Como viol e 0/1, a soma e a contagem de municipios acima do limite. n e o denominador publicado, tomado do ano de 2024. **Risco:** n usa notna de viol24 apenas. Como decfec_2024_2025.csv vem de um merge inner entre 2024 e 2025 em 03c:34, viol24 e viol25 tem exatamente os mesmos n… |
| `27-30` | Transicoes de situacao entre 2024 e 2025 | agregação | Sao as mesmas quatro celulas da tabela 2x2 que a linha 15-18 codifica em sit — recontadas aqui por comparacao direta em vez de por np.select. Reprodu… **Risco:** Regra duplicada: a matriz de transicao existe em tres lugares (03c:42-45, 10b:15-18 e 10b:27-30) com tres implementacoes. Com NaN, (a.viol24==1) e fa… |
| `31-31` | Medianas nacionais das horas anuais | estatística | Mediana de municipios, cada municipio ja sendo uma media ponderada de seus conjuntos. Nao e a mediana nacional de consumidores nem a media nacional d… **Risco:** A mediana municipal trata Sao Paulo e um municipio de 800 habitantes como uma observacao cada; a horas medias por consumidor do pais seria outro nume… |
| `33-33` | Numero de conjuntos da base comum (constante cravada) e n municipal | leitura | conj e publicado como numero de conjuntos que formam a base comum dos tres semestres. Nao e lido de nenhum arquivo aqui: e um literal. n, ao lado, e … **Risco:** Constante cravada que descreve outro arquivo: se 03d for reexecutado com outra extracao da ANEEL e a base comum mudar, o payload continua publicando … |
| `34-34` | Medias nacionais ponderadas dos semestres (constantes cravadas) | leitura | Sao as medias por conjunto ponderadas por consumidores, ou seja, a leitura 'por consumidor do pais', distinta das medianas municipais das linhas 31 e… **Risco:** Tres constantes copiadas de uma saida de console para o payload. Nenhuma verificacao de coerencia com dec_semestre.csv e feita aqui; se a fonte mudar… |
| `35-35` | Medianas municipais dos semestres | estatística | Mediana por municipio, contraparte nao ponderada das constantes p24/p25/p26. Ter as duas leituras lado a lado permite ver a diferenca entre 'municipi… **Risco:** As tres medianas sao calculadas sobre o mesmo conjunto de municipios (reindex a ordem) mas cada coluna tem seus proprios NaN; se um municipio tiver s… |
| `36-38` | Bandas de tendencia do semestre: +-5% sobre 2024 | limiar | Banda relativa de 5% em torno do valor de 2024, replicando a regra ja aplicada em 03d:44 (np.where com os mesmos 0.95 e 1.05). O codigo nao registra … **Risco:** Qualquer comparacao com NaN e falsa, entao municipios sem dado nao entram em nenhuma das tres contagens e a soma e menor que n, sem que isso apareca … |
| `41-41` | Tamanho final do payload | aritmética | Mesma divisao decimal de 09_payload.py:23 e 10a:55, medida depois da terceira gravacao. **Risco:** Nao compara com o tamanho anterior; um update que tenha apagado chaves (por exemplo, 09 rodado fora de ordem) apareceria apenas como um numero menor,… |
| `42-43` | Distribuicao das situacoes de continuidade | agregação | value_counts ignora NaN por padrao, entao os municipios sem apuracao nao aparecem no dicionario impresso; sort_index ordena pelo codigo numerico, que… **Risco:** O total impresso e menor que o numero de municipios e a diferenca nao e mostrada; quem le a linha precisa somar as chaves para descobrir quantos fica… |

### `reconstrucao/pipeline/10d_payload_serie.py`

| linhas | operação | espécie | o que faz, e o que a tornaria errada |
|---|---|---|---|
| `16-16` | Exclusao fixa de competencias vazias | regra normativa | O docstring das linhas 3 a 6 afirma que abril de 2025 e setembro de 2026 retornam 5.571 documentos com todos os campos ausentes e que o numFound do S… **Risco:** Lista estatica. Se outra competencia passar a vir vazia, ou se o SAGI corrigir uma destas duas, o script nao percebe: no primeiro caso a serie recebe… |
| `18-19` | Leitura da serie mensal e do payload existente | leitura | cadunico_mensal.csv e escrito por 05c_serie_mensal.py, que renomeia os campos do indice misocial do SAGI para cad, pob, bxr e eleg. dados.json e o pa… **Risco:** O dtype de anomes depende do que o pandas inferir do CSV (inteiro aqui, mas texto se alguma linha vier suja), e todo o resto do script converte com i… |
| `20-20` | Conversao do codigo IBGE de 7 para 6 digitos | cartografia | O docstring de 05c_serie_mensal.py registra que o codigo do SAGI tem seis digitos, sem digito verificador, e que a juncao com a malha do IBGE exige e… **Risco:** Vale apenas se todo elemento de D["cod"] for inteiro de 7 digitos. Se algum vier como texto, o operador // levanta TypeError; se algum ja vier com 6 … |
| `22-22` | Eixo temporal do payload | agregação | comp define simultaneamente quais colunas entram na matriz (linha 36) e em que ordem, e a ordem e o que da sentido ao delta: cada valor codificado e … **Risco:** Se houver buraco no meio da serie (uma competencia que o SAGI nao devolveu e que 05c pulou com `continue`), comp fica sem essa posicao e o delta pass… |
| `23-24` | Relato da cobertura temporal | apresentação | E o unico ponto em que a diferenca entre competencias lidas e competencias publicadas aparece para quem roda o pipeline. O codigo nao compara os dois… **Risco:** comp[0] e comp[-1] levantam IndexError se comp ficar vazio. Como e print puro, uma cobertura menor que a esperada nao altera o codigo de saida do pro… |
| `26-26` | Municipios do SAGI ausentes da malha | cartografia | O reindex da linha 36 mantem apenas os municipios de malha; tudo que existe no SAGI e nao existe na malha do payload some do resultado. Esta linha ma… **Risco:** A diferenca e calculada em um so sentido. O caso inverso, municipio da malha ausente do SAGI, nao e medido aqui e nao gera aviso nenhum: ele vira uma… |
| `28-30` | Volume elegivel descartado com os municipios fora da malha | agregação | Quantifica o descarte da linha 26 na unidade que importa para o projeto, familias com renda familiar per capita ate meio salario minimo, e o faz na c… **Risco:** A comparacao t.anomes == comp[-1] compara a coluna com um int; se anomes tiver sido lido como texto, o filtro nao casa com nada, g fica vazio e sum()… |
| `32-37` | Matriz municipio por competencia na ordem do payload | agregação | Tres operacoes encadeadas fazem o alinhamento: pivot poe cada municipio numa linha e cada competencia numa coluna; reindex(malha) reordena as linhas … **Risco:** pivot levanta ValueError se houver par (ibge6, anomes) duplicado no CSV, ou seja, o script depende de o SAGI nao devolver o mesmo municipio duas veze… |
| `42-48` | Codificacao delta, tratamento do ausente | regra normativa | NaN vira None, que o json.dumps escreve como null, e o `continue` faz o ausente nao atualizar `ant`. A consequencia e que o proximo valor observado s… **Risco:** Quem reconstroi a serie (funcao reconstroi, linha 69) soma os deltas ignorando os nulls, o que reproduz o valor absoluto correto. Mas se alguem inter… |
| `49-53` | Codificacao delta, primeiro absoluto e diferencas seguintes | aritmética | O docstring do arquivo (linhas 8 a 10) registra o motivo: sobre 31 competencias e 5.570 municipios a codificacao reduz o payload de 2,37 MB para 1,64… **Risco:** int() trunca em direcao a zero, nao arredonda: se algum valor chegasse como 1234.9999 por qualquer conversao intermediaria, sairia 1234. Deltas podem… |
| `55-61` | Montagem do bloco de serie do payload | serialização | Os tres campos vem de 05c_serie_mensal.py: pob e cadun_qtd_familias_cadastradas_pobreza_pbf_i, bxr e cadun_qtd_familias_cadastradas_baixa_renda_i e e… **Risco:** As competencias de `falhas` nao aparecem em `comp`, entao o consumidor precisa inserir a lacuna no eixo por conta propria; se ele desenhar apenas com… |
| `63-65` | Escrita do payload no lugar | serialização | separators=(",", ":") remove os espacos que o json.dumps insere por padrao, e ensure_ascii=False mantem os acentos como UTF-8 em vez de escapes \u, a… **Risco:** Le e escreve o mesmo caminho: uma falha entre a abertura em modo "w" e o fim da escrita deixa dados.json truncado, e como as etapas anteriores nao sa… |
| `66-66` | Tamanho do payload em megabytes | aritmética | Usa 1e6, isto e, megabyte decimal, coerente com as cifras de 2,37 MB e 1,64 MB citadas no docstring. Mede o arquivo no disco depois da escrita, nao o… **Risco:** Se fosse comparado com um numero calculado em MiB (divisao por 2^20) a diferenca seria de cerca de 5 por cento. E apenas log: nao ha limite de tamanh… |
| `69-75` | Reconstrucao da serie a partir do delta | aritmética | E a inversa exata da funcao delta: o primeiro valor nao nulo e absoluto e cada seguinte soma a diferenca ao acumulado. Existe aqui para a conferencia… **Risco:** O None nao zera `ac`, entao a reconstrucao depois de uma lacuna continua a partir do ultimo valor conhecido, coerente com a codificacao. Um delta cor… |
| `77-78` | Total nacional de pobreza em dez/2024 reconstruido | agregação | Reconstroi a serie de cada um dos 5.570 municipios e soma a coluna de dezembro de 2024, que e a competencia com referencia publicada em docs/VALIDACA… **Risco:** `or 0` trata None e o inteiro 0 do mesmo modo; para uma soma o efeito numerico e identico, mas municipios sem valor entram como zero em vez de fazer … |
| `79-81` | Comparacao com a referencia de VALIDACAO.md | limiar | A referencia e um numero literal no codigo, atribuido a docs/VALIDACAO.md; o script nao le esse documento, de modo que um numero revisado no document… **Risco:** O resultado e apenas impresso. O processo termina com codigo 0 nos dois casos, e roda_tudo.py so verifica returncode (linha 37 daquele arquivo), enta… |

### `reconstrucao/pipeline/10e_payload_conjuntos.py`

| linhas | operação | espécie | o que faz, e o que a tornaria errada |
|---|---|---|---|
| `21-21` | Montagem do caminho base da ANEEL | leitura | RAW e definido em _paths.py como um caminho resolvido fora do repositorio, por modulo local ou variavel de ambiente, fora… **Risco:** Concatenacao textual em vez de Path: se RAW terminar com barra, o caminho fica com barra dupla. Como RAW aponta para uma pasta que nao acompanha o re… |
| `22-23` | Conjunto de conjuntos consumidores elegiveis | leitura | O parquet e produzido por 03a_decfec_conjunto.py, que agrega DEC e FEC de 2024 por conjunto e faz merge interno com os limites de 2024. Logo conj_ok … **Risco:** O docstring deste arquivo (linhas 14-15) afirma que o recorte e de conjuntos com apuracao completa de doze meses em 2024, mas 03a calcula a coluna me… |
| `24-24` | Relato da contagem de conjuntos elegiveis | apresentação | Contagem simples do conjunto construido na linha 23. O rotulo impresso descreve o numero como apuracao completa, atributo que o codigo nao verifica e… **Risco:** O texto do log afirma completude de doze meses que a montagem de conj_ok nao garante (ver 03a). Quem ler apenas o log conclui algo mais forte do que … |
| `26-27` | Leitura do cadastro conjunto-municipio do IndQual | leitura | Mesma leitura usada em 03b, 03c e 03d, com os mesmos parametros, o que mantem a base de juncao identica entre os passos. O codigo nao registra por qu… **Risco:** latin-1 nunca falha na decodificacao: se o arquivo estiver em utf-8, acentos viram mojibake silenciosamente. Como so as colunas de ID e codigo de mun… |
| `28-29` | Renomeacao de colunas, recorte e deduplicacao dos pares | agregação | O IndQual grafa Unid e o dataset de continuidade grafa Und; o rename alinha as duas grafias para que o isin da linha 30 compare a mesma chave. O drop… **Risco:** Se a ANEEL renomear qualquer das duas colunas, o rename vira no-op e o recorte por lista quebra com KeyError; nao ha checagem previa de presenca. Com… |
| `30-30` | Restricao aos conjuntos com apuracao em 2024 | limiar | Alinha a base de contagem a mesma populacao de conjuntos que gera o indicador d3 em 03b/03c, para que ncj e nviz descrevam exatamente os conjuntos cu… **Risco:** Se os tipos das chaves divergirem (inteiro no parquet e texto no CSV, ou vice-versa), o isin nao casa nada e q fica vazio, o que faria todos os munic… |
| `31-31` | Descarte de pares sem codigo de municipio | limiar | Remove linhas em que o CSV nao traz o codigo do municipio, que nao poderiam ser ligadas ao payload. O codigo nao registra quantas linhas caem nem avi… **Risco:** Descarte silencioso: se uma parcela relevante do IndQual vier sem CodMunicipio, os municipios afetados perdem conjuntos e aparecem como menos compart… |
| `32-32` | Conversao numerica do codigo de municipio | aritmética | A chave do payload e numerica (09_payload.py grava cod como d.cod_ibge.tolist()), entao a comparacao exige o mesmo tipo. errors="coerce" transforma v… **Risco:** coerce converte erro em ausencia: um codigo com espaco, ponto de milhar ou marcador textual vira NaN e some na linha seguinte, sem contagem nem aviso… |
| `33-33` | Segundo descarte de nulos e conversao para inteiro | aritmética | O dropna e necessario porque astype(int) sobre NaN levanta erro; a ordem das duas operacoes na mesma linha e o que evita a excecao. O inteiro e a for… **Risco:** astype(int) trunca em vez de arredondar; um codigo lido como 1300300.0 fica correto, mas 1300299.9 viraria 1300299 sem aviso. O codigo nao valida que… |
| `34-34` | Relato do volume de pares e de municipios | apresentação | Contagem de linhas e contagem de municipios distintos apos todos os filtros; e o unico ponto do script onde o efeito acumulado das linhas 30 a 33 fic… **Risco:** E um log, nao uma verificacao: nao ha comparacao com um valor esperado nem interrupcao se as contagens despencarem. Um filtro que zerar q passa por a… |
| `36-36` | Indice municipio para conjuntos que o atendem | agregação | Inverte a tabela de pares em um indice de adjacencia para consulta direta no laco da linha 41. O uso de set garante que \\|por_mun[m]\\| seja contagem … **Risco:** Materializa todo o indice em memoria; para uma tabela grande isso e pesado, mas nao muda o resultado. Municipios sem nenhum par apos os filtros simpl… |
| `37-37` | Indice conjunto para municipios atendidos | agregação | E o outro lado da mesma relacao, necessario para responder quais outros municipios dividem um conjunto. As duas linhas juntas transformam a relacao e… **Risco:** Herda os mesmos filtros de q: municipios que foram descartados por codigo nulo ou nao numerico nas linhas 31 a 33 nao aparecem como vizinhos de ningu… |
| `39-39` | Leitura do payload existente | leitura | O passo e incremental: le o payload ja montado pelos passos anteriores e acrescenta campos. A ordem de D["cod"] e o que define a posicao de cada valo… **Risco:** O arquivo e aberto sem with e sem close explicito; o fechamento depende da contagem de referencias do CPython. Como o mesmo arquivo e reaberto para e… |
| `40-44` | Inicializacao das listas e caso sem cobertura apurada | regra normativa | Gravar None, e nao zero, e a escolha que preserva a diferenca entre ausencia de apuracao e apuracao com valor zero: um municipio sem conjunto elegive… **Risco:** if not cs trata None e set vazio de forma identica, entao uma falha de casamento de chave (tipo divergente, IBGE de seis digitos) produz exatamente o… |
| `45-48` | Uniao dos municipios coirmaos e remocao do proprio | agregação | A uniao, e nao a soma, e o que impede contar duas vezes um municipio que divide mais de um conjunto com o municipio corrente. O discard remove o prop… **Risco:** O por_conj.get(c, set()) devolve conjunto vazio para um c ausente do indice, situacao que nao deveria ocorrer por construcao (cs vem do mesmo q) e qu… |
| `49-51` | Contagem de conjuntos, de vizinhos e marca de exclusividade | limiar | excl e derivado de nviz, nao calculado a parte: nenhum vizinho equivale a todos os conjuntos do municipio serem exclusivos dele, porque vizinhos e a … **Risco:** excl afirma exclusividade dentro do universo filtrado: conjuntos do municipio que ficaram fora de conj_ok (sem limite 2024) nao sao examinados, e mun… |
| `53-53` | Anexacao dos tres campos ao payload | serialização | O contrato do payload e de listas paralelas indexadas pela mesma posicao de D["cod"]; as tres listas foram construidas percorrendo D["cod"] na ordem,… **Risco:** Nao ha assert de comprimento igual ao de D["cod"] nem verificacao de que as chaves nao existiam antes. Se o passo for reexecutado apos outro passo re… |
| `54-55` | Reescrita compacta do dados.json | serialização | separators=(",", ":") remove os espacos que json.dumps insere por padrao e ensure_ascii=False grava acentos como UTF-8 em vez de escapes \u, duas esc… **Risco:** Escrita destrutiva no mesmo arquivo que foi lido na linha 39, em modo w e sem arquivo temporario nem with: se a serializacao falhar no meio, o dados.… |
| `57-57` | Indice dos municipios com apuracao | agregação | Define o denominador de todas as porcentagens das linhas 63 a 65: a base e o universo com apuracao, nao o total de municipios do payload. O teste e i… **Risco:** Se todos os municipios cairem no ramo nulo (por exemplo por falha de tipo de chave), tem fica vazio e as linhas 63 a 65 levantam ZeroDivisionError; e… |
| `58-58` | Municipios atendidos por um unico conjunto | limiar | Isola o caso descrito no docstring, em que o indicador municipal e o valor de um unico conjunto replicado, sem agregacao entre conjuntos. Comparacao … **Risco:** Contar um unico conjunto nao implica que o conjunto seja exclusivo do municipio; sao propriedades distintas, medidas separadamente em um e em exclusi… |
| `59-59` | Municipios com conjuntos exclusivos | limiar | Reaproveita o indicador binario calculado na linha 51, sem recomputar a vizinhanca, o que mantem log e payload coerentes por construcao. **Risco:** Herda a ressalva de excl: exclusividade dentro do universo filtrado por conj_ok e pelos descartes das linhas 31 a 33. |
| `60-62` | Cabecalho e contagem da base com apuracao | apresentação | Torna explicito o denominador antes das porcentagens que vem a seguir, o que permite reconstruir os numerados a partir do log. **Risco:** Somente log em stdout; nenhum desses numeros e gravado em arquivo, entao a auditoria depende de capturar a saida da execucao. |
| `63-63` | Percentual de municipios com conjunto unico | estatística | Proporcao simples sobre a base com apuracao, nao sobre o total de municipios do payload; e a leitura correta da pergunta quantos dos medidos dependem… **Risco:** Divisao por len(tem): levanta ZeroDivisionError se nenhum municipio tiver apuracao. O arredondamento para uma casa e apenas de exibicao. O percentual… |
| `64-64` | Percentual de municipios com conjuntos so deles | estatística | Mesma base de p1, o que torna as duas porcentagens comparaveis entre si. Mede quantos municipios tem indicador proprio, no sentido de nao compartilha… **Risco:** Mesma divisao por len(tem) sem protecao. O numerador depende do universo filtrado: quanto mais restritivo o conj_ok, maior tende a ser a fracao apare… |
| `65-65` | Complemento: municipios que dividem conjunto | estatística | O complemento e exato porque excl e binario e definido sobre todo k em tem, entao nao ha terceira categoria: quem nao tem excl=1 tem excl=0. Calcular… **Risco:** Divisao por len(tem) sem protecao. A identidade p3 = 100 - p2 so vale enquanto excl nunca for nulo dentro de tem, condicao garantida pela construcao … |
| `66-69` | Mediana e maximo do numero de coirmaos | estatística | O filtro if nviz[k] e truthy, nao is not None, entao exclui tambem os zeros: a estatistica descreve a distribuicao entre os municipios que efetivamen… **Risco:** Dois pontos alteram o numero. Primeiro, o rotulo diz mediana mas v[len(v)//2] e o elemento de posicao piso(n/2), que para n par e o valor superior do… |
| `70-72` | Localizacao e relato do caso de Autazes | apresentação | Codigo IBGE 1300300 fixo no fonte como caso de verificacao manual. O guard de pertinencia evita ValueError do index quando o municipio nao esta no pa… **Risco:** Se ncj[i] for None (municipio no payload mas sem conjunto elegivel), a linha imprime None conjunto, dividido com None outros municipios, sem sinaliza… |
| `73-73` | Tamanho final do payload em megabytes | apresentação | Divisao por 1e6 e megabyte decimal, a convencao usada por sistemas de arquivos e por medicoes de transferencia de rede, coerente com a preocupacao de… **Risco:** Se o leitor interpretar MB como mebibyte (1048576 bytes), o numero aparece cerca de 4,9 por cento maior do que o esperado. Mede o arquivo em disco, n… |

### `reconstrucao/pipeline/build_app.py`

| linhas | operação | espécie | o que faz, e o que a tornaria errada |
|---|---|---|---|
| `9-9` | Raiz do projeto por posicao do arquivo | leitura | Todo caminho posterior e derivado desta raiz, e nao do diretorio de trabalho corrente. Como build_app.py esta em reconstrucao/pipeline/, parents[1] s… **Risco:** Mover build_app.py um nivel na arvore desloca BASE silenciosamente e faz o script ler ou gravar em lugar errado sem erro imediato. resolve() resolve … |
| `10-10` | Leitura do template HTML | leitura | O template e carregado inteiro em memoria como uma unica string porque a montagem seguinte e feita por substituicao textual, nao por streaming. A cod… **Risco:** O descritor de arquivo nunca e fechado explicitamente: depende da contagem de referencias do CPython para liberar o objeto ao fim da expressao. Em le… |
| `11-12` | Leitura dos dois payloads de dados | leitura | Os dois arquivos sao tratados como texto opaco, nao como JSON: nao ha json.load, nao ha validacao de estrutura, nao ha reserializacao. Isso preserva … **Risco:** JSON sintaticamente invalido, truncado ou vazio passa sem qualquer aviso e so quebra no navegador, em tempo de execucao da pagina. Um arquivo remanes… |
| `14-16` | Guarda contra fechamento precoce de script nos payloads | limiar | Os dois payloads sao injetados dentro de blocos <script type="application/json"> do template (linhas 511 e 512 de mapa.template.html). O analisador d… **Risco:** O teste e um limiar binario: qualquer ocorrencia legitima da sequencia dentro de um campo de texto do JSON, por exemplo um nome de municipio ou uma n… |
| `21-23` | Leitura das bibliotecas vendorizadas | leitura | O comentario imediatamente acima, nas linhas 18 a 20, declara a razao: as bibliotecas vao embutidas em vez de carregadas de CDN para que a pagina sej… **Risco:** O script le os arquivos mas nao confere o hash declarado em PROVENIENCIA.txt: a garantia de procedencia e documental, nao verificada em tempo de mont… |
| `24-26` | Guarda contra fechamento precoce de script nas bibliotecas JS | limiar | Mesma regra de fechamento de bloco bruto aplicada aos dois arquivos JavaScript, que entram em <script> nas linhas 515 e 516 do template. A repeticao … **Risco:** Uma versao futura de qualquer das duas bibliotecas que contenha a sequencia em uma string literal derruba a etapa sem oferecer caminho de correcao au… |
| `27-28` | Guarda contra fechamento precoce de estilo no CSS | limiar | O CSS entra dentro de um bloco <style> do template, na linha 12 de mapa.template.html, e o conteudo bruto de <style> encerra na sequencia '</style', … **Risco:** A agulha tem sete caracteres, nao oito como nos testes de script; trocar uma pela outra por descuido em manutencao futura tornaria a guarda inerte se… |
| `30-34` | Substituicao encadeada dos cinco marcadores | serialização | A montagem e textual: cada marcador do template e trocado pelo conteudo integral do arquivo correspondente, produzindo um documento sem nenhuma refer… **Risco:** Por operar em cascata sobre o texto ja montado, uma ocorrencia literal de '__GEO__', '__CHARTJS__', '__LEAFLETJS__' ou '__LEAFLETCSS__' dentro de dad… |
| `35-37` | Verificacao de marcadores remanescentes | limiar | Confere depois da montagem que nenhum dos cinco marcadores sobrou no texto final, o que detecta a situacao em que o template foi alterado e um marcad… **Risco:** O teste e feito sobre o html ja montado, entao uma ocorrencia legitima de um dos cinco tokens dentro de dados.json, de geo.json ou do codigo das bibl… |
| `39-40` | Caminho de destino e criacao do diretorio | serialização | A saida vai para fora de reconstrucao/, em site/ na raiz do repositorio, porque esse e o diretorio publicado. BASE.parent desfaz um nivel da resoluca… **Risco:** Depende inteiramente de BASE estar correto: se o script for movido, a pagina e gravada em outro lugar da arvore e o diretorio errado e criado sem avi… |
| `41-41` | Gravacao do HTML com quebra de linha fixada em LF | serialização | newline="\n" desliga a traducao automatica de fim de linha que o modo texto faz no Windows, onde o padrao converteria cada '\n' em '\r\n'. Com isso o… **Risco:** O arquivo nao e fechado explicitamente nem aberto em bloco with: a descarga do buffer depende de o objeto de arquivo ser liberado pela contagem de re… |
| `42-42` | Tamanho do arquivo publicado em megabytes decimais | aritmética | A divisao por 1e6 adota o megabyte decimal, de 10 elevado a 6 bytes, e nao o mebibyte de 2 elevado a 20, que daria um numero cerca de 4,9 por cento m… **Risco:** Se a gravacao da linha 41 ainda nao tiver sido descarregada para o disco, a medida sai menor que o arquivo final e o log informa um numero falso. O v… |

## Cálculo ao vivo no navegador

116 operações em 1 arquivos.

### `reconstrucao/app/mapa.template.html`

| linhas | operação | espécie | o que faz, e o que a tornaria errada |
|---|---|---|---|
| `524-529` | Formatadores numericos pt-BR | apresentação | Arredondamento e separador decimal sao decisao de exibicao, aplicada uma unica vez para todas as telas. O tratamento de nulo e NaN e explicito e prod… **Risco:** pct nao multiplica por 100: quem chamar com uma fracao imprime um numero cem vezes menor sem aviso, e por isso METRICS.pc e METRICS.descob precisam m… |
| `536-541` | Selecao dos municipios com subsidio utilizavel nas duas datas | limiar | O comentario das linhas 534 e 535 registra a razao declarada: onde a CDE ficou liquida negativa o valor nao e utilizavel, entao so entram municipios … **Risco:** O teste !(x>0) descarta tambem zero exato e qualquer NaN, e nao apenas valores negativos, o que nao esta escrito no comentario. A exclusao nao e alea… |
| `542-542` | Mediana por indice do meio | estatística | Ordena uma copia, o que preserva o vetor original usado depois na contagem de ganho da linha 543. Para vetor de tamanho impar o resultado e a mediana… **Risco:** Se o vetor estiver vazio o retorno e undefined e a formatacao a jusante mostra travessao sem sinalizar erro. A comparacao p-q assume numeros: qualque… |
| `543-543` | Contagem de municipios onde a fracao coberta subiu | agregação | Conta pareado, municipio a municipio, e nao pela diferenca das medianas. E a contagem coerente com a afirmacao exibida na linha 2059, que fala em sub… **Risco:** Comparacao estrita: empate exato conta como nao ganho. Qualquer ruido de arredondamento na origem dos dados desloca casos de empate para um dos lados… |
| `544-545` | Retorno do bloco COB: excluidos e percentual de ganho | aritmética | O denominador de ganho_pct e \\|a\\|, o conjunto que passou pelo filtro, e nao N. Isso torna o percentual uma afirmacao sobre os municipios com subsidi… **Risco:** Se \\|a\\| for zero, ganho_pct e NaN e excluidos iguala N, sem tratamento explicito. fr24 e fr26 saem como fracao de 0 a 1, e o consumo nas linhas 1510… |
| `559-560` | Leitura por data com encadeamento de fontes de beneficiarios | leitura | O ?? converte ausencia em zero, o que permite somar sem propagar nulo. O encadeamento de B24 aceita duas nomenclaturas de campo para a mesma grandeza… **Risco:** Tratar ausencia como zero nao distingue municipio sem beneficiario de municipio sem dado. Um municipio com ele26 ausente entra no denominador com zer… |
| `561-561` | Acumulacao nacional de elegiveis e beneficiarios por data | agregação | Soma simples sobre os N municipios, sem ponderacao, porque as grandezas ja sao contagens de familias e sao aditivas entre municipios. **Risco:** A soma assume que cada municipio aparece uma unica vez em D e que nao ha dupla contagem de familia entre municipios. Se o payload trouxer valores em … |
| `562-562` | Contingente nao atendido como soma de diferencas positivas | aritmética | O comentario da linha 549 registra a razao: excesso num municipio nao supre falta em outro, entao a diferenca e truncada em zero antes de somar. E um… **Risco:** O truncamento em zero descarta informacao sobre o sentido oposto, isto e, beneficiarios acima do universo elegivel, que pode indicar defasagem cadast… |
| `564-565` | Cobertura nacional por data com denominador da propria data | aritmética | O comentario das linhas 552 a 556 registra a razao da escolha: usar o CadUnico de cada data em vez de um denominador unico, para que a variacao entre… **Risco:** Com denominadores diferentes, cob26 menos cob24 nao e uma variacao de cobertura a universo constante, e sim o efeito combinado de mudanca no numerado… |
| `570-571` | Somatorios nacionais do painel corrente | agregação | Soma direta das contagens municipais, aditivas por construcao. Diferente de NAT, aqui nao ha ?? nem max: o codigo assume que esses quatro campos vem … **Risco:** Um unico null em qualquer dos quatro vetores torna o acumulador NaN a partir daquele indice, e o NaN se propaga silenciosamente para AGG.cob na linha… |
| `572-572` | Contagem de municipios acima do limite de interrupcao e de municipios… | agregação | Separar o denominador dos que tem apuracao do total N e o que permite a linha 1777 afirmar uma proporcao sobre os que tem apuracao, e nao sobre os 5.… **Risco:** Se vio vier como booleano ou string, o teste ===1 falha e viol fica zero enquanto withD3 continua contando, produzindo proporcao zero sem erro. Munic… |
| `573-573` | Soma de restituicao apenas onde nao ha sindicancia aberta e o valor e… | agregação | Tres condicoes encadeadas restringem o total: ausencia de sindicancia, valor presente e valor estritamente positivo. O efeito e produzir um total con… **Risco:** O teste sind_i===0 exclui tambem o caso de sind nulo ou ausente, que cai fora do total sem ser contado em lugar nenhum. Nao existe contador de exclui… |
| `574` | Contagem de municipios com favela identificada | agregação | Le uma marca binaria do payload. A legenda da linha 716 explicita o significado do complemento: zero significa que o IBGE nao identificou favela no m… **Risco:** Igualdade estrita com 1 trata qualquer outro valor, inclusive null, como ausencia de favela, colapsando ausencia de dado e ausencia do fenomeno na me… |
| `576` | Mediana nacional com descarte de nulos | estatística | Aqui o filtro de nulo e explicito, ao contrario dos somatorios das linhas 570 e 571. O denominador da mediana passa a ser o numero de municipios com … **Risco:** Mediana nao ponderada por populacao: cada municipio vale um, entao a mediana nacional de tarifa descreve o municipio tipico e nao o consumidor tipico… |
| `594-598` | Ordenacao e posto denso por metrica | estatística | Filtra nulos antes de ordenar, entao o posto 1 e sempre um municipio com o dado e o vetor rank preserva null para quem nao tem. O posto e sequencial … **Risco:** Com valores empatados o posto exibido depende da estabilidade do sort e da ordem original do payload, ou seja, e arbitrario mas apresentado como rank… |
| `599-602` | Ordenacoes pre-computadas por metrica, com sentido invertido para cob… | estatística | A unica metrica com desc falso e cob, porque cobertura baixa e o caso grave enquanto nas demais o valor alto e o grave. Com isso o posto 1 significa … **Risco:** A convencao esta implicita no unico argumento false da linha 590. Acrescentar uma metrica onde menor e pior sem repetir o false produz um ranking inv… |
| `608-613` | Acumulacao por unidade da federacao | agregação | Repete no recorte estadual a mesma decisao do agregado nacional: separar d3n de mun para que a proporcao de violacao tenha denominador de municipios … **Risco:** o.dec recebe D.dec[i] sem checar se dec e nulo, apenas condicionado a vio nao ser nulo: se houver municipio com vio preenchido e dec nulo, entra um n… |
| `614` | Mediana estadual com guarda de vetor vazio | estatística | Diferente das medianas das linhas 542 e 577, esta devolve null explicito para vetor vazio em vez de undefined, o que faz a formatacao mostrar travess… **Risco:** Sem filtro de nulo, um null no vetor participa da ordenacao com comparacao NaN e pode deslocar o elemento central, produzindo uma mediana estadual er… |
| `615-616` | Derivados estaduais e ordenacao por cobertura ascendente | aritmética | A cobertura estadual e razao de somas e nao media das coberturas municipais, coerente com AGG.cob da linha 579. O teste o.d3n antes da divisao evita … **Risco:** O teste o.d3n usa veracidade e nao comparacao explicita, o que funciona para inteiro mas trataria zero e ausencia da mesma forma se d3n fosse outro t… |
| `621-622` | Agrupamento dos valores de familias nao atendidas por UF | leitura | Guarda os valores e nao os indices, ao contrario de CONC na linha 764, porque aqui o resultado desejado e apenas a contagem k e o total, nao a identi… **Risco:** Nenhum filtro de nulo: um lac nulo entra no vetor e afeta a ordenacao e o total da linha 614. Como UFCONC e CONC calculam o mesmo criterio por caminh… |
| `624-625` | Numero minimo de municipios que concentram metade das familias nao at… | agregação | E a definicao operacional de concentracao usada no texto da linha 906: o menor conjunto de municipios, tomados do maior para o menor, que reune metad… **Risco:** Se t_u for zero, a condicao c>=t/2 e satisfeita na primeira iteracao e k vale 1, afirmando concentracao onde nao ha contingente algum. Um lac nulo to… |
| `630-631` | Rampas de cor sequencial e divergente | cartografia | Sao sete classes porque cada metrica declara seis cortes, e seis cortes produzem sete intervalos. Guardar a cor como referencia a variavel CSS, e nao… **Risco:** O numero de cores esta amarrado ao numero de cortes de cada metrica sem verificacao: se uma metrica declarar cinco ou sete cortes, binner devolve und… |
| `632-636` | Classificador de valor em classe de cor | limiar | Classificacao por cortes fixos declarados por metrica, e nao por quantis calculados na hora, faz a legenda ser a mesma em qualquer recorte e a cor de… **Risco:** NaN falha em toda comparacao v<breaks[i] e nao e capturado pelo guarda de nulo, entao um NaN e pintado com a cor mais intensa da rampa, o extremo opo… |
| `676-680` | Metrica descob: complemento da cobertura | aritmética | Inverte a cobertura para que a cor mais escura corresponda ao problema maior, o que e a convencao usada por todas as metricas sequenciais do mapa. O … **Risco:** Assume que D.cob esta em pontos percentuais de 0 a 100; se vier como fracao, o resultado fica proximo de 100 para todo municipio. Se a base de benefi… |
| `681-685` | Metrica lac: contagem absoluta nao atendida | leitura | Leitura direta do payload, sem transformacao. Os cortes crescem por ordem de grandeza, o que e a escolha usual para uma contagem de cauda longa entre… **Risco:** Por ser contagem absoluta, o mapa reproduz o mapa de populacao: a classe mais escura tende a marcar as capitais independentemente da gravidade relati… |
| `686-690` | Metrica d3: razao em relacao ao limite regulatorio | regra normativa | O corte em 1,0 e o unico que tem sentido normativo: acima dele o valor apurado ultrapassou o limite que a ANEEL fixa para o conjunto. A rampa diverge… **Risco:** Como binner usa comparacao estritamente menor, o valor exatamente 1,00 cai na classe seguinte, ou seja, ja e pintado como fora do limite; o rotulo '0… |
| `711-715` | Metrica dcob: variacao em pontos percentuais | aritmética | Diferenca entre duas porcentagens e lida em pontos percentuais, e o rotulo usa essa palavra em vez de por cento. A rampa divergente e invertida com s… **Risco:** O intervalo de -1 a 1 e rotulado 'praticamente igual', um julgamento sem justificativa registrada no codigo. O prefixo '+' so aparece para v estritam… |
| `716-720` | Metrica sit: categoria de reincidencia acima do limite | regra normativa | O cruzamento de dois anos fechados transforma dois testes binarios contra o limite da ANEEL em quatro estados. A marcacao categorica:true desvia do b… **Risco:** fmt indexa o vetor sem verificar limite: qualquer codigo fora de 0 a 3 produz undefined no rotulo, e ramp[v] produz cor invalida, pintada como preto … |
| `721-726` | Metrica tend: variacao relativa entre semestres | aritmética | Variacao relativa em vez de diferenca absoluta, para comparar municipios de patamares muito diferentes de interrupcao. A condicao s24 <= 0 e o que im… **Risco:** Base pequena mas positiva gera variacao enorme sem que a magnitude absoluta importe: sair de 0,2 hora para 0,4 hora aparece como piora de 100%. NaN e… |
| `727-731` | Metrica pf: favela com zero explicito | limiar | O corte em 0,0001 existe para separar o zero verdadeiro de qualquer valor positivo por menor que seja, ja que binner usa comparacao estritamente meno… **Risco:** Ausencia de identificacao pelo IBGE e tratada como zero, e nao como sem dado, entao o mapa nao distingue municipio sem favela de municipio nao pesqui… |
| `733-736` | Atribuicao da funcao de cor a cada metrica | cartografia | Separa dois regimes de cor: na metrica categorica o proprio valor e o indice da cor, na continua o valor precisa passar pelos cortes. Escrever isso u… **Risco:** Na metrica categorica nao ha verificacao de intervalo: um codigo fora do tamanho da rampa devolve undefined, que o canvas pinta de preto em silencio,… |
| `774-775` | Quartis nacionais de cobertura municipal | estatística | Filtra nulos antes de ordenar, entao os cortes descrevem apenas municipios com cobertura apurada. Sao quantis por indice truncado, sem interpolacao, … **Risco:** Quantil por piso do indice e enviesado para baixo em relacao a definicao interpolada, e a diferenca cresce em amostras pequenas; para 5.570 municipio… |
| `778-779` | Agrupamento de indices municipais por UF para o conjunto de concentra… | leitura | Guarda indices, e nao valores, porque o resultado final e um conjunto de municipios pertencentes ao grupo de concentracao, testado por CONC.has(i) na… **Risco:** Duplica o agrupamento por UF ja feito em UFS na linha 599, em UFCONC na linha 612 e em IDX na linha 801, quatro passagens sobre os mesmos N elementos… |
| `781-785` | Conjunto dos municipios que concentram metade do contingente estadual | agregação | Mesmo criterio de UFCONC nas linhas 614 e 615, porem produzindo a pertinencia em vez da contagem. A insercao ocorre antes do teste de parada, entao o… **Risco:** A ordenacao e feita no proprio vetor de byUf com sort em vigor, o que muta a estrutura; como byUf e local ao bloco, o efeito nao vaza, mas o mesmo pa… |
| `788` | Corte dos dez por cento de tarifa mais alta | limiar | Define o limiar usado nas linhas 1010 e 1092 para classificar um municipio como estando entre as tarifas mais altas do pais. Ordena decrescente e ind… **Risco:** Nao filtra nulo, ao contrario de QCOB na linha 759: um null em D.tar produz comparacao NaN e ordem indefinida, e a posicao 10% pode devolver o propri… |
| `790-794` | Tabela GRAU: rotulo e explicacao do grau de certeza | apresentação | O codigo classifica cada encaminhamento em tres regimes de certeza e guarda aqui o texto que explica cada regime ao leitor. A escolha de tres categor… **Risco:** A tabela e consultada em boxLeitura (linha 1067) e na pagina de personas (linha 1382) como GRAU[x.grau].exp sem guarda: qualquer grau novo escrito em… |
| `817` | Inversao do mapa de regioes para consulta por UF | leitura | Inverte a lista das cinco macrorregioes declarada nas linhas 786 a 792, cuja fonte o comentario da linha 782 atribui ao IBGE. A inversao assume parti… **Risco:** Se uma UF aparecer em duas regioes na tabela de origem, a ultima atribuicao vence sem erro. Uma UF ausente da tabela devolve undefined, e o codigo a … |
| `820-826` | Indices de municipios por UF, por regiao e nacional | leitura | O comentario das linhas 781 a 785 registra a razao de existirem tres escopos: um ranking so tem sentido contra um conjunto declarado, e 41o entre 5.5… **Risco:** A guarda if(r) exclui do escopo regional qualquer municipio cuja UF nao esteja mapeada, silenciosamente: esse municipio ainda aparece em uf e em todo… |
| `836` | Guarda de municipio sem o dado na funcao de posicao | leitura | Usa ==null, que captura null e undefined mas nao NaN. Devolver null em vez de uma posicao arbitraria e o que permite a linha 849 filtrar a medida for… **Risco:** Um NaN em vals_i passa por esta guarda e segue para o laco, onde toda comparacao com NaN e falsa: o municipio recebe pos igual a 1, isto e, aparece c… |
| `837-844` | Contagem de piores, de elegiveis e de empates no conjunto | estatística | O comentario das linhas 807 a 811 registra as duas decisoes. Primeira: o denominador conta so quem tem o dado, entao de e o universo real da comparac… **Risco:** NaN em vals_i, ou em vals_k, escapa da guarda ==null e entra em de sem nunca satisfazer as comparacoes, inflando o denominador e empurrando todos os … |
| `845` | Percentil de posicao dentro do conjunto | aritmética | Normaliza a posicao para a faixa de 0 a 100, com o denominador de-1 para que o pior do conjunto, pos igual a 1, produza 100 e o melhor, pos igual a d… **Risco:** No caso degenerado de um unico municipio com dado, o codigo devolve 100, ou seja, afirma o extremo maximo de gravidade onde nao existe comparacao pos… |
| `864-869` | Montagem dos tres conjuntos de comparacao de um municipio | leitura | Materializa os tres escopos anunciados no comentario das linhas 781 a 785. Os operadores \\|\\| e o ternario garantem vetor vazio em vez de undefined q… **Risco:** Um conjunto vazio nao e sinalizado: posicao devolve pos igual a 1, de igual a zero e pct igual a 100 pela guarda da linha 822, isto e, o municipio ap… |
| `870-874` | Producao dos rankings por medida e por escopo, com descarte de medida… | serialização | O filtro final remove a medida inteira quando o municipio nao tem o valor, o que evita exibir tres escopos de posto nulo. valor sai cru, sem passar p… **Risco:** O filtro usa ==null e nao captura NaN, entao uma medida com valor NaN sobrevive ao descarte, e pela guarda da linha 813 tambem sobrevive dentro de po… |
| `883-898` | Lista PERSONAS: chave, nome e competencia de cada ator | leitura | O comentario imediatamente acima (linhas 852-857) registra a razao declarada: transformar o responsavel que ja aparecia no rodape de cada encaminhame… **Risco:** O conjunto de chaves aqui e o dominio implicito dos campos quem:[...] de leitura(i). Nao ha validacao cruzada: uma chave escrita em quem que nao cons… |
| `899` | PNOME: indice de chave para nome da persona | serialização | Converte a lista ordenada em mapa de consulta. O codigo nao registra por que a competencia (terceiro elemento) e descartada aqui; ela continua sendo … **Risco:** Chaves repetidas em PERSONAS seriam silenciosamente colapsadas, a ultima vencendo, sem erro. PNOME[k] para chave inexistente devolve undefined, que a… |
| `901-903` | Abertura de leitura(i): acumulador de encaminhamentos | serialização | O motor produz uma lista por acumulacao em ordem de avaliacao das regras, nao por selecao declarativa. A ordem de insercao e a ordem dos blocos 1 a 6… **Risco:** Nao ha deduplicacao nem limite de itens: se dois blocos disparassem para o mesmo assunto, os dois entrariam. D.uf[i] fora do intervalo devolve undefi… |
| `910` | Banda de gravidade por quartis nacionais de cobertura | limiar | A gravidade nao e fixada por limiar absoluto e sim pela posicao do municipio na distribuicao nacional de cobertura, calculada em QCOB sobre os munici… **Risco:** Por construcao, aproximadamente 25% dos municipios recebem 'crit' e 25% recebem 'ok' qualquer que seja o nivel absoluto de cobertura no pais: se a co… |
| `911-912` | Classificacao do encaminhamento A1 | serialização | pac define o pacote em que o item e agrupado por PACNOME (linha 1045); tom define a classe CSS e a ordem via TOMORD (linha 1046); quem define em que … **Risco:** Atribuir a unica persona 'social' a este item significa que a distribuidora nao o ve na sua visao, ainda que a acao descrita na linha 888 dependa de … |
| `913` | Meta do encaminhamento: numero de familias a cadastrar | apresentação | nf formata com separador de milhar pt-BR e devolve travessao para null ou NaN. O numero exibido e o mesmo lac usado nos limiares dos blocos seguintes… **Risco:** nf nao arredonda explicitamente: toLocaleString sem opcoes aplica no maximo 3 casas decimais, de modo que um lac fracionario (se a origem nao for int… |
| `914` | Situacao da cobertura contra a mediana nacional | limiar | Ancora o numero municipal na mediana do pais, que e o segundo elemento de QCOB. O comparador e estritamente menor, entao o municipio exatamente na me… **Risco:** D.cob[i] igual a null faz a comparacao ser falsa e imprime 'acima da mediana' junto de um travessao no lugar do valor, afirmacao que o dado ausente n… |
| `919-926` | Ramo A1 alternativo: nao ha contingente pelo dado disponivel | limiar | Em vez de afirmar cobertura de 100%, o item mostra os dois numeros e se rotula 'verif', o que e coerente com o caso ben > ele, que indica inconsisten… **Risco:** O tom 'ok' pinta de verde tambem o caso ben > ele, isto e, o caso suspeito, e TOMORD o joga para o fim da lista (linha 1051), onde e menos visto. A r… |
| `929-936` | Pertencimento ao conjunto que concentra metade do deficit estadual | limiar | A regra e de cobertura minima: escolhe o menor numero de municipios cuja soma de familias nao atendidas atinge metade do deficit estadual. Isso ident… **Risco:** O texto da linha 906 afirma que a operacao dimensionada para os k municipios alcanca UFCONC[uf].tot familias, mas tot e o deficit total do estado, na… |
| `937-943` | Limiar de mutirao: mil familias | limiar | Limiar absoluto de 1.000 familias separando o que o codigo chama de volume acima do atendimento de rotina. O codigo nao registra de onde vem 1.000: n… **Risco:** O corte e absoluto e nao relativo ao porte do municipio: 1.000 familias num municipio de 5.000 domicilios e um problema de outra ordem que 1.000 fami… |
| `944-950` | Limiar de rotina: cem familias | limiar | Segundo degrau da mesma escada de escala. Como o de 1.000, o valor 100 nao tem justificativa registrada no codigo nem referencia a fonte externa. **Risco:** Mesma descontinuidade absoluta do degrau anterior, agora em 99 contra 100. A escada tem tres degraus (1000, 100, 0) e o codigo nao registra por que a… |
| `951-958` | Limiar residual: contingente abaixo de cem | limiar | Fecha a escada. A cadeia if/else if garante exclusividade: exatamente um dos quatro ramos do bloco 2 dispara, ou nenhum quando lac <= 0 e i nao esta … **Risco:** Recebe tom 'ok' um municipio que ainda tem familias com direito nao exercido; a cor comunica ausencia de problema onde ha problema pequeno. Quando la… |
| `965-966` | Resolucao da sigla e do agregado de concessao na CDE | leitura | Dupla indirecao: do municipio para o indice de agente, do indice para a sigla, da sigla para o registro de variacao. O casamento e por igualdade estr… **Risco:** Se a sigla em D.cdeag divergir da sigla em D.agvar por espaco, acentuacao ou caixa, find devolve undefined, agCDE vira nulo e o encaminhamento das li… |
| `967-968` | Porta e tom do encaminhamento da distribuidora | limiar | Usa a mesma mediana nacional da linha 887, mas com escala de duas bandas em vez das quatro da linha 883: para a distribuidora o piso e 'warn', nunca … **Risco:** Um mesmo municipio pode exibir tom 'ok' no item A1 (linha 883, cobertura acima do terceiro quartil) e tom 'warn' neste item, sobre o mesmo indicador;… |
| `976-977` | Comparacao do municipio com a media da propria concessionaria | limiar | O parametro de comparacao nao e uma meta e sim o desempenho da propria concessionaria no conjunto de sua area, o que neutraliza efeitos de politica n… **Risco:** Comparacao de variacoes percentuais sem controlar a base: um municipio que saiu de 10 para 15 familias varia +50% e supera qualquer media de concessa… |
| `978-987` | Encaminhamento CDE: ramo de sustentacao ou de explicacao | apresentação | nf1 fixa uma casa decimal; o simbolo % e concatenado no template, o que confirma que os valores ja chegam em pontos percentuais. O ramo positivo nao … **Risco:** grau declarado 'arit' com efeito null: o selo 'aritmetica' aparece sem o calculo que, segundo a legenda de boxLeitura (linha 1058), ele deveria traze… |
| `1005-1011` | Municipio sem vinculo a conjunto consumidor no IndQual | limiar | Trata ausencia de dado como achado proprio, com acao propria, em vez de omitir a linha. O uso de == null (e nao === null) e o que faz undefined cair … **Risco:** A frase 'nenhum conjunto consumidor associado na base de 2024' e literal e nao derivada do payload: se a base de referencia mudar de ano, o texto con… |
| `1012-1018` | Descumprimento confirmado do limite de continuidade | limiar | O gatilho e igualdade estrita com 1, nao uma comparacao de d3 com 1,00, de modo que a decisao de violacao vem pronta do payload e nao e recalculada a… **Risco:** Se vio e d3 divergirem no payload (vio === 1 com d3 abaixo de 1, ou o inverso), a ficha exibe tom critico ao lado de um numero que nao o sustenta, e … |
| `1019-1025` | Media dentro do limite mas ao menos um conjunto acima | limiar | Captura o caso em que a agregacao municipal esconde violacao local: a media ponderada fica abaixo de 1 enquanto o pior conjunto esta em 1 ou acima. E… **Risco:** A condicao usa >= 1 enquanto a nota da linha 831 diz 'acima de 1,00x e descumprimento': o valor exatamente 1,00 e tratado aqui como problema e na not… |
| `1026-1033` | Todos os conjuntos dentro do limite: nao alocar fiscalizacao | limiar | Fecha a cadeia de quatro ramos do bloco 4, garantindo que toda ficha receba exatamente um item de continuidade. O texto declara explicitamente que sa… **Risco:** O ramo tambem recebe o caso d3x >= 1 com nc === 1 que nao tenha vio === 1, isto e, municipio de conjunto unico com maximo no limite: a frase 'Todos o… |
| `1046-1052` | Sinalizacao de sobrecobertura: beneficios acima de elegiveis | limiar | Registra as duas explicacoes possiveis (mais de uma unidade consumidora por familia, ou beneficiario que deixou de ser elegivel) sem escolher entre e… **Risco:** O item so aparece se o sinalizador vier no payload; este arquivo nao recalcula ben > ele, entao um payload sem sob deixa o caso invisivel enquanto o … |
| `1053-1059` | CDE liquida negativa: proibicao de citar cifra de subsidio | limiar | Um subsidio liquido negativo indica estorno ou lancamento retroativo no mes, e nao valor de politica; o item impede que o numero seja citado sem aber… **Risco:** A data 'marco de 2026' esta literal no texto e nao vem do payload: se o mes de referencia mudar, a instrucao passa a apontar para o mes errado. O ite… |
| `1060-1066` | Logistica de busca ativa em favela: tres limiares combinados | limiar | Conjuncao de tres condicoes: existencia de favela identificada, escala absoluta de domicilios e escala do deficit de cadastro. O texto registra expli… **Risco:** O limiar de 1.000 aqui repete o da linha 908, mas com comparador >= em ambos, enquanto fav usa > estrito: um municipio com exatamente 2.000 domicilio… |
| `1068` | Retorno da lista de encaminhamentos | serialização | A funcao e deterministica e sem efeito colateral fora de it: dado o mesmo i e o mesmo D, devolve sempre a mesma lista, o que e o que o comentario das… **Risco:** A lista pode ter tamanho variavel de 1 a cerca de 10 itens, e o contador de encaminhamentos exibido no cabecalho (linha 1056) usa items.length sem di… |
| `1109-1110` | semAcao: leitura dos insumos de continuidade | leitura | O comentario das linhas 1079-1082 registra a razao da funcao: quando uma persona nao tem encaminhamento, a razao e dita, porque saber onde nao agir e… **Risco:** As duas variaveis sao lidas mesmo quando p nao e 'fisc' nem 'agencia', trabalho inutil sem consequencia de resultado. A funcao cobre apenas quatro da… |
| `1111-1116` | Justificativa de nao acao para fiscalizacao e agencia | limiar | A condicao e construida como complemento das duas regras de disparo do bloco 4, de modo que a justificativa so aparece quando de fato nao houve item … **Risco:** Para a persona 'fisc', vio nulo produz null aqui e tambem nao produz item (o item 979-985 e de aneel e agencia), entao a persona Procon e Ministerio … |
| `1117-1120` | Justificativa de nao acao para o conselho de consumidores | limiar | Espelha o limiar do item 1010-1017 com o comparador invertido, de modo que persona com item nunca recebe justificativa e vice-versa. O texto nomeia o… **Risco:** O total 5.570 esta escrito literalmente no texto, enquanto o item equivalente da linha 1014 usa nf(N), o numero de municipios efetivamente carregados… |
| `1121-1124` | Justificativa de nao acao para a ANEEL | limiar | A ANEEL so recebe item quando falta o vinculo no IndQual (linhas 979-985); havendo vinculo, nao ha o que pedir a ela neste levantamento, e a justific… **Risco:** A frase afirma que o municipio e alcancavel por fiscalizacao pelo simples fato de ter vinculo, conclusao mais forte que o dado: vinculo a conjunto si… |
| `1125-1129` | Justificativa de nao acao para a coordenacao estadual | limiar | Espelha o gatilho do item 900-907 e repete os mesmos dois numeros (k e mun) para que a justificativa de exclusao use o mesmo criterio que a inclusao.… **Risco:** UFCONC[D.uf[i]] e acessado sem guarda: UF ausente ou desconhecida lanca TypeError e derruba a renderizacao da pagina de personas. A frase diz que uma… |
| `1160-1161` | Procedencia curta: exclusivo ou compartilhado, com plural | limiar | O corte e nv = 0, isto e, nenhum outro municipio compartilha os conjuntos. O comentario da linha 1130 registra que no pais apenas 47 municipios, 0,8%… **Risco:** nv negativo, impossivel por construcao mas nao impedido, cairia no ramo compartilhado com texto sem sentido. O sufixo so e anexado a medida marcada p… |
| `1166-1167` | Procedencia longa: municipio com conjuntos exclusivos | apresentação | Este e o unico ramo que autoriza ler o indicador como medicao do lugar, e a condicao e exatamente nv = 0. A classe proc-ok distingue visualmente o ca… **Risco:** nj = 0 com nv = 0 produziria 'Os 0 conjuntos consumidores que atendem X', frase que afirma cobertura por zero conjuntos; a guarda anterior so exclui … |
| `1168-1169` | Procedencia longa: conjunto unico compartilhado | apresentação | Quando ha um unico conjunto e ele e compartilhado, nao ha media nem ponderacao: o numero municipal e literalmente o do conjunto, identico nos vizinho… **Risco:** A afirmacao de que o numero e identico nos outros municipios vale para o indicador do conjunto, mas nao necessariamente para o valor exibido em cada … |
| `1170` | Procedencia longa: varios conjuntos, media ponderada | apresentação | Ramo residual (nj > 1 e nv > 0). E o unico lugar do trecho que declara a formula de agregacao do indicador de continuidade, a media ponderada por con… **Risco:** Se o pipeline mudar o peso da ponderacao (por exemplo para unidades consumidoras ou para domicilios) esta frase passa a descrever agregacao diferente… |
| `1177-1178` | Procedencia tarifaria: contagem de municipios com a mesma tarifa | agregação | O comentario das linhas 1147-1149 registra a razao: a tarifa e homologada por distribuidora e nao por municipio, entao todo municipio da mesma conces… **Risco:** Varredura O(N) executada a cada chamada, e a funcao e chamada dentro do map de linhas da tabela (linha 1170), a cada renderizacao de ficha; com N na … |
| `1181-1183` | Tamanho dos universos de comparacao no ranking | agregação | Conta o tamanho do conjunto de comparacao a partir do indice pre-construido, e usa vetor vazio quando a chave nao existe, de modo que a ficha nao que… **Risco:** Estas contagens cobrem todos os municipios do escopo, enquanto os denominadores das posicoes exibidos na tabela contam apenas os que tem o dado daque… |
| `1195-1199` | Celula de posicao, denominador e empate | apresentação | Exibir a posicao junto do denominador e do numero de empatados e o que impede ler '1a' como singularidade quando dezenas de municipios tem o mesmo va… **Risco:** O texto do empate so aparece quando e.r.empate e diferente de zero e nao nulo, entao um empate registrado como nulo some da tela. A ordinal feminina … |
| `1202` | Altura do grafico de ranking | apresentação | Reserva 44 pixels por barra horizontal e impoe um piso de 170 pixels para que um cartao com poucas medidas ainda tenha area de desenho utilizavel. Ch… **Risco:** Com muitas medidas a altura cresce sem teto e o cartao passa da tela. Os 44 pixels nao consideram o numero de escopos por medida, que sao tres barras… |
| `1209` | Leitura das faixas de familias do municipio | leitura | Captura em variaveis locais os seis totais que o cartao usa em tabela e grafico, de forma que o mesmo valor alimente os dois e nao haja divergencia e… **Risco:** Nao verifica se ele e igual a pob mais bxr nem se ben mais lac e igual a ele; as identidades sao assumidas do pipeline. Se qualquer um vier nulo, os … |
| `1219-1220` | Participacao de cada faixa no CadUnico | aritmética | Usa o CadUnico inteiro como denominador, e nao o universo elegivel, porque a linha descreve a composicao do cadastro; a linha do universo elegivel ve… **Risco:** Se cad for zero, 100*pob/cad e infinito e atravessa o guarda de pct, que imprime o simbolo de infinito; se pob e cad forem ambos zero o resultado e N… |
| `1223` | Lacuna como parcela do universo elegivel | aritmética | Troca o denominador para o universo elegivel, que e o conjunto de quem tem direito, e por isso o numero e comparavel ao complemento da cobertura exib… **Risco:** ele igual a zero produz infinito ou NaN. Este numero e calculado no navegador a partir de lac e ele, enquanto D.cob vem do pipeline; se as duas orige… |
| `1230-1236` | Reconstrucao da serie mensal a partir de delta | aritmética | O payload guarda a serie em delta: o primeiro valor presente e absoluto e os seguintes sao a diferenca para o mes anterior com valor, conforme a func… **Risco:** Erro em um unico delta propaga para todos os meses seguintes, e nada aqui detecta isso. Se o codificador mudar para zerar a referencia apos um vazio … |
| `1237-1240` | Rotulo de competencia AAAAMM | apresentação | Extrai mes e ano por aritmetica inteira em vez de manipular texto ou construir uma data, o que evita qualquer conversao de fuso horario alterar o mes… **Risco:** Mes fora de 1 a 12 devolve undefined no rotulo, sem erro. O ano e cortado para dois digitos por slice(2), que so funciona para anos de quatro digitos… |
| `1241-1244` | Guarda de disponibilidade da serie municipal | leitura | Omitir o cartao inteiro e a escolha diante de dado ausente, em vez de desenhar um grafico vazio. O municipio sem serie simplesmente nao ganha a secao. **Risco:** A omissao e silenciosa: o leitor nao sabe se o municipio nao tem serie ou se a pagina falhou. Um vetor existente porem inteiro de nulos passa neste g… |
| `1245-1248` | Variacao entre a primeira e a ultima competencia com valor | aritmética | A filtragem de nulos faz a diferenca ser tomada entre competencias que existem, e nao entre as pontas nominais do periodo, que poderiam estar vazias.… **Risco:** Como as pontas usadas sao as observadas e nao as declaradas, o texto que acompanha o numero cita o periodo completo da serie enquanto a diferenca pod… |
| `1258` | Sinal e valor absoluto na frase da serie | apresentação | Separa sinal e magnitude para escrever o sinal com o caractere tipografico de menos em vez do hifen que o Intl produziria, mantendo o alinhamento tab… **Risco:** Variacao zero aparece como '+0', o que sugere ganho. O sinal usado aqui difere do produzido pelo formatador em outros trechos, como o fmt de dcob, en… |
| `1269-1276` | Adiamento da criacao dos graficos e redimensionamento por fonte | apresentação | Chart.js mede o container no instante da criacao. O comentario imediatamente acima registra que, chamado logo apos a escrita do innerHTML e com as fo… **Risco:** Um quadro pode nao bastar se o layout ainda nao assentou, situacao que o proprio arquivo trata de outro modo no mapa, com ResizeObserver. A variavel … |
| `1286-1291` | Barras do ranking em percentil arredondado | estatística | Desenha a posicao relativa e nao o valor bruto, o que e o que torna medidas de unidades diferentes comparaveis no mesmo grafico; a legenda do cartao … **Risco:** O arredondamento e so visual, porem apaga diferenca entre municipios proximos e pode exibir duas barras iguais para posicoes distintas. O rotulo do c… |
| `1292-1297` | Eixo do ranking fixado de 0 a 100 | apresentação | Fixar o eixo em 0 a 100 mantem a mesma referencia visual entre municipios: sem isso o Chart.js ajustaria o maximo ao maior percentil presente e a mes… **Risco:** Um percentil maior que 100, se surgisse, seria cortado no limite do eixo sem indicacao. O piso de largura e um valor absoluto em pixels, entao rotulo… |
| `1298-1302` | Dica do ranking com posicao e denominador | apresentação | A barra mostra percentil e a dica mostra a posicao ordinal com o denominador, de modo que o numero escalado e o numero contado apareçam juntos e nenh… **Risco:** Aqui pos e de sao interpolados sem passar por nf, ao contrario da tabela do mesmo cartao, entao a dica mostra o numero sem separador de milhar e a ta… |
| `1307-1314` | Barras empilhadas de composicao das familias | agregação | As duas barras sao duas particoes do mesmo universo elegivel, uma por faixa de renda e outra por direito exercido. O nulo na posicao da outra barra e… **Risco:** O desenho so comunica a comparacao se pob mais bxr for igual a ben mais lac; nada no codigo verifica essa identidade, e se as duas somas divergirem a… |
| `1317-1322` | Eixo empilhado e dica do grafico de familias | apresentação | Passa as marcas do eixo e os valores da dica pelo mesmo formatador usado nas tabelas, de modo que o separador de milhar seja o mesmo em todo o cartao… **Risco:** nf aplica o padrao do Intl, que arredonda em tres casas; para contagens inteiras isso nao aparece, mas passaria a aparecer se o campo virasse fracion… |
| `1326-1331` | Beneficiarios como dois pontos na serie mensal | serialização | A legenda do cartao registra a razao: a ANEEL publicou apenas duas competencias comparaveis, e o arquivo de marco de 2026 e o unico de 2026 com as 10… **Risco:** As competencias 202412 e 202603 estao escritas no codigo: se a serie deixar de conter alguma delas, indexOf devolve -1, nenhuma posicao casa e o conj… |
| `1332-1339` | Composicao das series do grafico mensal | apresentação | Separa visualmente o que e serie continua do que sao observacoes isoladas: showLine falso e marcador losango impedem que os dois pontos de beneficiar… **Risco:** As quatro series compartilham um unico eixo de valores; se os beneficiarios estiverem em ordem de grandeza muito diferente do universo elegivel, as l… |
| `1340-1348` | Eixos e dica da serie mensal | apresentação | beginAtZero falso e uma escolha declarada de ampliar a variacao do periodo em vez de mostrar a magnitude em relacao ao zero. O modo de interacao por … **Risco:** Com o eixo nao ancorado em zero, uma variacao pequena ocupa toda a altura do grafico e parece grande; nada na tela indica que o eixo esta truncado. O… |
| `2008-2010` | Selecao e corte dos pares de distribuidoras | agregação | O filtro exige duas distribuidoras porque o grafico desenha um par de pontos por municipio. O corte em 14 e limite de espaco vertical do cartao, e o … **Risco:** O slice pega os 14 primeiros na ordem em que o payload chegou; o codigo nao ordena aqui, entao a afirmacao de que sao os de maior divergencia depende… |
| `2015-2020` | Escala horizontal do grafico de pares | cartografia | Escala linear do dominio observado para a faixa de X0 a X0+XW. Incluir -30 e 30 como candidatos ao minimo e ao maximo garante largura minima de domin… **Risco:** Se todos os valores estiverem dentro de mais ou menos 30, o dominio fica fixo em 60 pontos e a comparacao com outra versao do grafico exige conferir … |
| `2021-2027` | Posicao vertical e desempate de rotulos no par | apresentação | O limiar de 104 unidades e a largura aproximada que dois rotulos ocupam lado a lado; abaixo dela um dos rotulos desce 11 unidades para nao escrever p… **Risco:** 104 e valor fixo estimado para o tamanho de fonte 9 e o corte de 14 caracteres: mudar qualquer um dos dois desfaz a protecao, e o codigo nao recalcul… |
| `2028-2039` | Rotulos e marcadores de cada par | apresentação | O nome do municipio ganha coluna propria terminando em X0-16, com corte declarado por reticencia, e os rotulos de valor ficam centrados sob cada pont… **Risco:** O segundo rotulo escreve um '+' fixo antes do numero, entao se o valor da ultima distribuidora for negativo o texto sai com sinal duplo. O primeiro r… |
| `2042-2044` | Linha de referencia do zero no grafico de pares | cartografia | Marca o zero na mesma escala dos pontos, o que e o que permite ler de que lado da linha cada distribuidora ficou, ou seja, quem ganhou e quem perdeu … **Risco:** Se lo e hi ficassem ambos do mesmo lado do zero, px(0) cairia fora da faixa desenhada e a linha sairia do grafico; o piso de -30 e 30 no dominio impe… |
| `2049-2055` | Alturas proporcionais das faixas no fluxo | cartografia | As quatro alturas usam o mesmo denominador, o universo elegivel de dezembro de 2024, e nao o total de cada data. E isso que faz a coluna de 2026 fica… **Risco:** O fator 100 amarra a altura ao viewBox de 168 unidades: se a soma das faixas de 2026 passar de cerca de 1,3 vez o elegivel de 2024, as barras saem da… |
| `2056-2060` | Coluna empilhada do fluxo | apresentação | Empilha as duas faixas a partir de um topo comum, com dois pixels de folga entre elas para separar visualmente os blocos sem legenda intermediaria. A… **Risco:** A folga de 2 unidades entra na altura total mas nao representa familia alguma, entao a soma visual das duas faixas excede levemente a altura proporci… |
| `2065-2066` | Linhas de ligacao entre as duas datas | cartografia | Liga os centros das faixas correspondentes, o que da a leitura de continuidade entre as duas datas e mostra a direcao do deslocamento. A inclinacao d… **Risco:** A linha sugere fluxo de familias de uma faixa para a outra, mas liga apenas a mesma faixa em duas datas: nao ha medicao de transicao individual aqui,… |
| `2069-2072` | Variacao de cada faixa em milhoes | aritmética | As duas diferencas sao escritas em ordem oposta, pob24 menos pob26 e bxr26 menos bxr24, justamente para que ambas saiam positivas e o sinal seja acre… **Risco:** Os sinais estao escritos no codigo, nao derivados do valor: se a pobreza subir, o rotulo mostrara o sinal de menos diante de um numero negativo, e o … |
| `2073-2077` | Totais de cada data no rodape do fluxo | apresentação | Ancora as duas colunas em numeros absolutos, de modo que a comparacao de alturas seja lida junto do total que ela representa. ele24 e o mesmo denomin… **Risco:** Os totais vem de campos proprios do payload e nao da soma das faixas desenhadas; se ele24 nao for igual a pob24 mais bxr24, o rotulo e a altura da co… |
| `2389-2394` | Parametros de zoom e renderizador do mapa | cartografia | O comentario que abre a secao registra a escolha do canvas: com 5.570 poligonos o SVG cria 5.570 nos no DOM e o navegador engasga ao repintar a cada … **Risco:** O padding de 0,35 aumenta a area desenhada e o custo de cada repinte. Os limites 3 e 12 sao absolutos e sao alterados logo em seguida por setMinZoom;… |
| `2420-2424` | Enquadramento inicial e limite de deslocamento | cartografia | Define o zoom minimo em funcao do enquadramento efetivo, e nao por numero fixo, de modo que o piso acompanhe o tamanho real do container. A folga de … **Risco:** setMinZoom e chamado antes do reenquadramento posterior. Se o container ainda nao tiver tamanho quando o fitBounds corre, o zoom medido e o maximo, e… |
| `2437-2446` | Reenquadramento apos o container ganhar tamanho | apresentação | O comentario acima registra o motivo: o container so tem largura e altura depois que o layout assenta, e um fitBounds antes disso faz o Leaflet supor… **Risco:** O caminho de reserva com 120 ms e tempo arbitrario e pode disparar antes do layout em maquina lenta, repetindo exatamente o defeito que o bloco corri… |
| `2455-2462` | Resolucao de cor CSS para literal, com cache | cartografia | O comentario acima registra a razao: a cascata resolvia var() no atributo fill do SVG, mas o canvas recebe fillStyle como cadeia e, se ela nao for co… **Risco:** A deteccao de var() e feita apenas pela primeira letra ser 'v', entao qualquer cadeia iniciada por v entra no caminho de recorte e slice(4,-1) produz… |
| `2464-2477` | Pintura do mapa e montagem da legenda | cartografia | O nulo e testado antes da funcao de cor, entao ausencia de dado nunca passa pelo classificador. A legenda e gerada da mesma rampa que pinta o mapa, e… **Risco:** O emparelhamento por indice supoe que labels e ramp tenham o mesmo comprimento; se labels for maior, as ultimas amostras ficam com fundo indefinido, … |
| `2479-2484` | Contorno do municipio selecionado | cartografia | Limpa e redesenha em uma camada separada, acima das demais, para que o contorno da selecao nao dependa do estilo de preenchimento da metrica. A busca… **Risco:** A busca linear percorre a malha inteira a cada chamada, e paintMap chama markSel a cada troca de metrica; com 5.570 feicoes isso repete a varredura t… |
| `2486-2490` | Enquadramento no municipio selecionado | cartografia | A folga de 70 pixels mantem o entorno visivel em vez de encher a tela com o poligono, e o teto de zoom 10 impede que um municipio pequeno leve o mapa… **Risco:** O try vazio engole qualquer falha de getBounds, inclusive geometria vazia, e o mapa fica onde estava sem nenhuma indicacao. Municipio com territorio … |
| `2500-2507` | Posicionamento da dica dentro da janela | apresentação | Desloca a dica 14 pixels do cursor e a espelha para o outro lado quando ela passaria da borda, com margem de 8 pixels. As reservas de 190 e 70 pixels… **Risco:** O espelhamento nao verifica se a posicao espelhada tambem fica fora da tela: perto do canto superior esquerdo, a dica pode ir para coordenada negativ… |
| `2546-2550` | Tabela equivalente ao mapa, ordenada pela metrica | agregação | Reproduz em texto o conteudo do mapa para a mesma metrica selecionada, filtrando os nulos e contando quantos ficaram de fora, numero que a legenda da… **Risco:** A funcao get e chamada duas vezes por comparacao dentro do sort, ou seja, da ordem de N log N chamadas para 5.570 municipios, recalculando metricas d… |

## Scripts de validação

122 operações em 5 arquivos.

### `reconstrucao/pipeline/valida_decomposicao.py`

| linhas | operação | espécie | o que faz, e o que a tornaria errada |
|---|---|---|---|
| `4-4` | Recorte de municipios com subsidio disponivel | leitura | As medianas de tarifa e de subsidio observado que sustentam a decomposicao sao calculadas sobre esse recorte, para que a comparacao final entre 'econ… **Risco:** u e uma view do DataFrame original (sem .copy(), diferente de valida_desconto.py linha 5); aqui so ha leitura, entao nao ha efeito, mas qualquer atri… |
| `5-5` | Fator de conta a 80 kWh apos desconto escalonado | regra normativa | E a media ponderada das fracoes pagas nas duas primeiras faixas para um consumo de 80 kWh: 30 kWh pagando 35% e os 50 kWh restantes pagando 60%. Repr… **Risco:** A formula esta particularizada para 80 kWh: os numeros 30 e 50 so sao as larguras corretas das faixas nesse consumo. Se alguem reutilizar F80 para ou… |
| `6-7` | Medianas de tarifa residencial e de tarifa Baixa Renda | estatística | Duas medianas independentes descrevem o municipio tipico em cada subclasse tarifaria, e a diferenca relativa mede o desconto de subclasse antes do de… **Risco:** As duas medianas sao calculadas separadamente e podem vir de municipios diferentes: a mediana da razao nao e a razao das medianas, entao 'dif' nao e … |
| `9-13` | Decomposicao da economia da familia a 80 kWh em duas parcelas | aritmética | A soma a+b reconstroi exatamente conta_cheia80 - conta_social80 de 07_tarifa_social.py linhas 14-16, separando a economia em duas causas: a mudanca d… **Risco:** A ordem da decomposicao e uma escolha: aplicando primeiro o desconto escalonado e depois a troca de subclasse, as duas parcelas mudam de valor embora… |
| `15-21` | Confronto entre CDE observada e desconto teorico a 80 e a 97,7 kWh | regra normativa | Usa as aliquotas de desconto 0.65 e 0.40 (as mesmas de valida_desconto.py linhas 9-10) com larguras 30 e 67.7 kWh, que somam 97.7 kWh - o consumo imp… **Risco:** 97.7 kWh esta escrito diretamente na expressao, sem vir de variavel: se o resultado da inversao mudar, este numero nao acompanha. A parcela 0.40*67.7… |

### `reconstrucao/pipeline/valida_desconto.py`

| linhas | operação | espécie | o que faz, e o que a tornaria errada |
|---|---|---|---|
| `4-6` | Filtro de municipios com subsidio utilizavel | leitura | O teste de inversao divide pelo subsidio observado; onde a CDE liquida e nula ou negativa (subs_liquido<=0, que e como a flag foi definida em 06e) o … **Risco:** O filtro exclui apenas subs_liquido<=0. Um municipio com subs_liquido>0 mas linhas_tsee=0 permanece na amostra com subsidio_familia_liq=NaN (06d_conc… |
| `7-12` | Desconto da Tarifa Social em R$, por faixas cumulativas | regra normativa | As tres aliquotas 0.65 / 0.40 / 0.10 sao os complementos das fracoes pagas 0.35 / 0.60 / 0.90 usadas em 07_tarifa_social.py linhas 6-11, cujo comenta… **Risco:** A funcao e constante para k>=220: nenhum consumo acima disso gera desconto adicional, logo o desconto tem teto. Se tar_br for NaN o retorno e NaN sem… |
| `13-22` | Inversao do desconto por bisseccao: consumo implicito | aritmética | desconto_rs e monotona nao decrescente em k, o que torna a bisseccao aplicavel no intervalo onde ela cresce. 60 iteracoes sobre um intervalo de largu… **Risco:** Falha silenciosa com entrada ausente: se sub ou tar_br for NaN, as duas guardas de NaN sao False (comparacao com NaN e sempre False), o teste interno… |
| `23-24` | Aplicacao da inversao linha a linha e descarte dos nao resolvidos | agregação | O zip percorre as duas colunas em paralelo pela ordem das linhas, e a lista resultante e atribuida como coluna nova; o alinhamento depende de o DataF… **Risco:** O dropna remove apenas os NaN efetivamente produzidos; os casos em que a entrada era NaN e a bisseccao devolveu ~1.0 kWh (ver riscos da inversao) sob… |
| `27-27` | Contagem de casos fora do intervalo resolvivel | agregação | A soma de isna() conta as linhas em que a bisseccao devolveu np.nan por uma das duas guardas. O codigo apresenta o numero como diagnostico da cobertu… **Risco:** A contagem subestima os casos realmente nao resolvidos, porque entrada NaN nao gera saida NaN (retorna ~1.0). len(k) + isna().sum() = len(d) por cons… |
| `28-28` | Quantis do consumo implicito | estatística | Os quantis descrevem a distribuicao do consumo que reproduziria o subsidio observado, sem supor forma funcional. O codigo nao registra por que estes … **Risco:** Cada municipio entra com peso 1, independentemente de quantas familias representa: a mediana e a de municipios, nao a de familias. Os valores de bord… |
| `29-29` | Fracao da amostra na faixa 40-150 kWh | limiar | A media de uma serie booleana e a proporcao de verdadeiros. Os limites 40 e 150 kWh sao escritos diretamente na linha; o arquivo nao registra de onde… **Risco:** Os dois limites sao arbitrarios do ponto de vista do codigo: mover qualquer um deles muda a conclusao do teste sem que nada no arquivo justifique o v… |
| `31-33` | Razao subsidio por familia sobre tarifa Baixa Renda | aritmética | R$ dividido por R$/kWh tem unidade de kWh. O proprio codigo declara na linha 32 a hipotese sob teste: se a regra vale, a razao deveria ser aproximada… **Risco:** A razao so seria constante se todo municipio tivesse o mesmo consumo medio e a mesma composicao de faixas; a variabilidade observada mistura variacao… |
| `34-34` | Coeficiente de variacao da razao e seus quartis | estatística | O CV e usado aqui como medida de dispersao relativa para verificar a afirmacao da linha 32 (razao aproximadamente constante). Sendo adimensional, per… **Risco:** O CV supoe media diferente de zero e so e interpretavel para grandeza positiva com escala de razao; se houver r negativo (subsidio liquido negativo j… |
| `35-36` | Coeficiente de variacao do subsidio bruto, para comparacao | estatística | Serve de contrafactual: se dividir pela tarifa reduzisse a dispersao, CV(r) < CV(subsidio) indicaria que parte da variacao do subsidio e explicada pe… **Risco:** A comparacao entre os dois CV so e informativa se as duas series tiverem o mesmo conjunto de linhas nao nulas; NaN em tarifa_baixa_renda reduz a amos… |
| `37-37` | Correlacao de Spearman entre subsidio por familia e tarifa | estatística | Pearson sobre postos e a definicao de Spearman e capta relacao monotona sem supor linearidade nem normalidade, o que e adequado a duas variaveis de e… **Risco:** Cada coluna e ranqueada separadamente sobre toda a serie, e so depois .corr() descarta os pares com NaN. Quando os padroes de ausencia das duas colun… |

### `reconstrucao/pipeline/valida_granularidade.py`

| linhas | operação | espécie | o que faz, e o que a tornaria errada |
|---|---|---|---|
| `5-7` | Quartis da cobertura municipal | estatística | Os cortes sao empiricos e definidos pela propria distribuicao, o que garante grupos de tamanho aproximadamente igual na dimensao cobertura - propried… **Risco:** Cortes derivados dos dados mudam a cada atualizacao da base: a classificacao de um municipio pode mudar sem que a cobertura dele tenha mudado. quanti… |
| `8-13` | Conjunto dos municipios que concentram metade da lacuna estadual | agregação | Reproduz por UF a mesma logica de concentracao de 06d_concentracao.py linhas 18-21 (cumsum sobre o total estadual), para marcar como categoria 0 na d… **Risco:** O municipio que cruza a metade e incluido antes do break, entao o conjunto cobre pelo menos 50% e nunca menos - assimetria deliberada mas nao declara… |
| `14-14` | Faixa de cobertura por quartil | limiar | Discretiza a cobertura nos quartis calculados da propria amostra. A cadeia de condicoes usa < estrito, de modo que o valor exatamente igual a um quar… **Risco:** cobertura NaN faz toda comparacao `<` devolver False e o municipio cai no ramo final, sendo classificado como 3 (melhor quartil) em vez de 'sem dado'… |
| `15-17` | Faixa de escala pela lacuna, com prioridade ao peso estadual | limiar | Combina um criterio relativo (peso dentro do estado, que tem precedencia) com dois cortes absolutos em 1.000 e 100 familias. Os dois cortes estao esc… **Risco:** Os limiares 1000 e 100 sao arbitrarios do ponto de vista do codigo e definem sozinhos o tamanho de duas das quatro categorias. lacuna_pos NaN faz as … |
| `18-22` | Faixa de qualidade com categoria de desigualdade interna | limiar | A categoria 2 captura o caso em que a media ponderada do municipio fica dentro do limite mas ao menos um conjunto ultrapassa (d3_max >= 1) e existe m… **Risco:** Se d3_max for NaN quando violacao existe, a condicao e False e o municipio cai em 3 (dentro do limite). A exigencia n_conj>1 significa que municipio … |
| `23-26` | Faixa de peso da conta sobre a renda, corte em 10% | limiar | 10% da renda domiciliar e o corte usado em todo o projeto para peso da conta (aparece tambem em 06c_faixas_cadunico.py linha 32 e 07_tarifa_social.py… **Risco:** peso_pob80_social usa a tarifa Baixa Renda SEM aplicar o desconto escalonado - 07_tarifa_social.py linha 26 rotula essa mesma coluna como ERRADO e de… |
| `27-28` | Faixa tarifaria por tercis do ranking de tarifa | limiar | 557 e aproximadamente 10% e 2785 aproximadamente 50% de 5.570 municipios: os cortes separam o decil de tarifa mais alta e a metade superior. O codigo… **Risco:** Os cortes sao contagens absolutas presas ao universo de 5.570 municipios: se o painel mudar de tamanho, deixam de corresponder a decil e mediana sem … |
| `29-33` | Codificacao de bandeiras por mascara de bits | limiar | OR bit a bit codifica duas bandeiras independentes num unico inteiro, preservando as quatro combinacoes possiveis numa so dimensao da tupla de classi… **Risco:** Qualquer valor diferente de 1 (inclusive NaN) e tratado como ausencia da bandeira. Como f e um inteiro, a distribuicao impressa no final nao distingu… |
| `34-35` | Tupla de classificacao e contagem de combinacoes distintas | agregação | A tupla e a assinatura de granularidade do municipio: dois municipios com a mesma tupla sao indistinguiveis pelas seis dimensoes que o app usa para c… **Risco:** O espaco maximo de 2304 combinacoes ultrapassa o numero de municipios so em parte, entao a contagem de combinacoes distintas e limitada tanto pela es… |
| `37-41` | Concentracao das combinacoes: maior grupo, oito mais comuns, unicos | estatística | Sao medidas de concentracao da classificacao: se poucas combinacoes cobrem a maior parte dos municipios, a granularidade efetiva e menor do que o num… **Risco:** most_common desempata de forma arbitraria entre combinacoes de mesma contagem, entao 'as 8 mais comuns' nao e um conjunto unicamente definido quando … |
| `43-44` | Distribuicao marginal de cada dimensao | agregação | As marginais mostram se alguma dimensao esta degenerada (quase todos os municipios num unico codigo), o que explicaria concentracao no numero de comb… **Risco:** A leitura posicional x[i] depende de a ordem dos rotulos coincidir exatamente com a ordem das funcoes na tupla da linha 34; nao ha verificacao, e uma… |

### `reconstrucao/pipeline/valida_numeros.py`

| linhas | operação | espécie | o que faz, e o que a tornaria errada |
|---|---|---|---|
| `4` | importacao dos caminhos e das constantes de referencia | leitura | tirar a data de referencia da tarifa e o ano das unidades consumidoras de um modulo compartilhado e o que permite que este validador use exatamente o… **Risco:** INTERIM_ORIG e PROCESSED_ORIG sao importados e nunca usados, o que sugere resto de versao anterior; se _paths mudar o valor das constantes sem que os… |
| `5-9` | leitura do payload e dos artefatos de apoio | leitura | D e o artefato publicado que se quer auditar e P, S, A, F sao artefatos gravados por etapas anteriores do pipeline, logo servem como lado esquerdo de… **Risco:** se qualquer um desses CSV for regravado pela mesma etapa que escreve o payload, a independencia se perde; se os arquivos estiverem desatualizados em … |
| `20` | contador das especies de conferencia | agregação | o comentario imediatamente acima justifica separar as duas especies de conferencia; o contador e o que permite ao resumo dizer quantas comparacoes fo… **Risco:** se alguma comparacao futura nao passar por cmp nem por coer, o resumo subcontara e dara impressao de cobertura menor ou maior que a real |
| `22-23` | atalho posicional cmp_f | apresentação | reordenar os parametros poe a fonte em posicao obrigatoria de leitura na chamada, o que torna visivel, linha a linha, de onde vem o lado recalculado;… **Risco:** a ordem posicional difere da de cmp, entao inverter calc e app ou passar a fonte na posicao errada produz comparacao invertida ou rotulo absurdo sem … |
| `25-33` | comparacao contra fonte anterior ao payload | limiar | o comentario das linhas 11 a 19 registra a razao explicita: o arquivo ja teve cinco comparacoes que nao podiam falhar, porque comparavam uma expressa… **Risco:** a checagem e apenas de fonte nao vazia, nao de fonte verdadeira: uma string qualquer satisfaz o requisito, logo a garantia e documental e nao mecanic… |
| `35-40` | comparacao de coerencia interna do payload | limiar | o comentario das linhas 11 a 19 declara que conferir dois campos do payload entre si e util mas nao e a mesma coisa que validar calculo: nao detecta … **Risco:** passar por coer uma comparacao que poderia ser feita contra fonte anterior enfraquece a auditoria sem alertar ninguem; os dois lados podem estar igua… |
| `46` | elegiveis do CECAD somados no painel | agregação | e soma simples de coluna municipal do painel; o codigo usa esse valor apenas para exibicao na linha 66, onde o rotulo diz que e base preservada no pa… **Risco:** se a coluna tiver nulos, sum os ignora e o total sai subestimado sem aviso; somar uma base de data diferente junto com as de marco de 2026 confundiri… |
| `47` | agregado nacional do SAGI em marco de 2026 | agregação | filtra a competencia e soma a coluna que o proprio pipeline trata como definicao de elegivel; o valor e usado nas linhas 67 a 69 para explicar o exce… **Risco:** se anomes vier como texto e nao inteiro, o filtro retorna vazio e a soma vira zero silenciosamente; mudanca de nome da coluna quebra o acesso por atr… |
| `48` | elegiveis e beneficios em marco de 2026 | agregação | sao os dois lados recalculados das comparacoes das linhas 54 e 55, vindos de painel_municipal.csv, escrito por 09a, contra o payload escrito por 06d … **Risco:** nulos na coluna sao ignorados por sum, o que produziria total menor que o do payload se o payload tratar nulo como zero |
| `49` | elegiveis e beneficios em dezembro de 2024 | agregação | mesmas colunas do painel na competencia anterior, usadas apenas para impressao comparativa nas linhas 61 a 63; o codigo nao as submete a cmp **Risco:** as duas colunas vem de fontes de natureza distinta, elegiveis do CadUnico e beneficiarios da TSEE, e o codigo nao verifica se sao da mesma competencia |
| `50` | familias nao atendidas como soma das lacunas positivas | aritmética | o truncamento em zero e justificado nas linhas 58 e 59, que imprimem o saldo liquido e explicam que a diferenca para a soma das positivas e o excesso… **Risco:** se alguma linha tiver nulo, a subtracao propaga nulo e max compara com None, o que quebra ou distorce; o int trunca a fracao acumulada em vez de arre… |
| `51-53` | somas nacionais reconstruidas do payload | agregação | as listas do payload sao municipais, entao o total nacional publicado tem de ser a soma delas; o padrao x or 0 protege contra nulos, que no payload r… **Risco:** x or 0 tambem converte zero e valores falsos em zero, o que aqui e inofensivo, mas mascararia um payload que usasse False ou string vazia; se a lista… |
| `54` | conferencia dos elegiveis de marco de 2026 | limiar | os dois lados vem de codigos distintos lendo as mesmas fontes, painel escrito por 09a contra payload escrito por 06d e 09, como diz o comentario das … **Risco:** se 09a passar a derivar o painel do proprio payload, a independencia desaparece sem que o codigo perceba, pois a checagem de fonte e textual |
| `55` | conferencia dos beneficios de marco de 2026 | limiar | mesma estrutura da linha anterior, com o painel como caminho anterior ao payload e a fonte declarada **Risco:** tratamento diferente de nulos entre painel e payload deslocaria o total sem indicar erro de calculo |
| `56` | conferencia das familias nao atendidas | limiar | o rotulo diz explicitamente que a grandeza comparada e a soma das positivas, e nao o saldo liquido, evitando a confusao que as linhas 58 e 59 explicam **Risco:** se o payload passar a publicar saldo liquido em lac, a comparacao acusara divergencia que na verdade e mudanca de definicao |
| `57` | cobertura nacional em percentual | aritmética | a razao e calculada dos dois lados a partir de totais obtidos por caminhos distintos, e a tolerancia e reduzida para 0.01 porque a grandeza esta em p… **Risco:** divisao por zero se e26 ou app_ele for zero; erros compensatorios nos dois totais podem manter a razao correta e esconder divergencia nas contagens, … |
| `58-59` | impressao do saldo liquido nacional | apresentação | publicar as duas grandezas lado a lado evita que o leitor confunda saldo liquido com familias nao atendidas; a explicacao impressa e a propria justif… **Risco:** o formato com zero casas arredonda para exibicao e pode sugerir precisao inteira que os dados nao tem; a segunda linha usa prefixo f sem nenhum campo… |
| `61-63` | impressao da data anterior, dezembro de 2024 | aritmética | repete para 2024 exatamente a mesma definicao usada para 2026 nas linhas 50 e 57, o que torna os dois anos comparaveis entre si **Risco:** a repeticao literal da formula permite que as duas versoes divirjam numa edicao futura; esse total de 2024 nao passa por cmp, portanto e impresso sem… |
| `66` | impressao dos elegiveis do CECAD | apresentação | o titulo impresso na linha 65 e a data no rotulo deixam registrado que essa base tem competencia diferente da leitura do presente, evitando que o num… **Risco:** se a data no texto nao acompanhar uma troca de base, o rotulo passa a mentir sobre a competencia |
| `67-69` | excedente do SAGI sobre a soma municipal | aritmética | a explicacao impressa atribui a diferenca a cobertura de 5.571 municipios no SAGI contra a malha do Censo 2022, nomeando o municipio excedente e seu … **Risco:** a diferenca e atribuida inteiramente a um municipio sem que o codigo verifique isso numericamente; se houver outra causa somada, como revisao de comp… |
| `72` | municipios acima do limite de continuidade em 2024 | limiar | o limiar rel maior ou igual a 1 define ultrapassagem do limite regulatorio, ja que rel e a razao entre o indicador apurado e o limite; a contagem e r… **Risco:** empate exato em rel igual a 1 depende de arredondamento na origem e pode mudar a contagem; linhas com rel nulo sao contadas como falso e somem da est… |
| `73` | municipios acima do limite de continuidade em 2025 | limiar | mesma regra de limiar aplicada ao ano seguinte, com a mesma fonte anterior ao payload declarada **Risco:** se as duas competencias tiverem cobertura municipal diferente, as contagens nao sao diretamente comparaveis entre si, ainda que cada uma bata com o p… |
| `74` | reincidentes nos dois anos | agregação | a intersecao logica das duas marcas define reincidencia, e o recalculo parte do CSV de 03c, anterior ao payload **Risco:** se viol nao for estritamente a indicadora de rel maior ou igual a 1, as cinco contagens desta secao deixam de ser mutuamente consistentes; valores nu… |
| `75` | municipios que deixaram de passar do limite | agregação | uma das quatro categorias mutuamente exclusivas cuja soma e conferida na linha 78; recalculada da fonte anterior ao payload **Risco:** municipio sem dado em qualquer dos anos nao entra em nenhuma das quatro categorias, o que so nao produz inconsistencia porque a linha 78 compara a so… |
| `76` | municipios que passaram a ficar acima do limite | agregação | completa o par de transicoes junto com a linha 75, sobre a mesma fonte anterior ao payload **Risco:** o mesmo tratamento de nulos das linhas anteriores; alem disso a categoria limpo, que fecha a soma na linha 78, nao e recalculada aqui e vem apenas do… |
| `77` | soma das quatro categorias de continuidade | agregação | as quatro categorias sao mutuamente exclusivas e exaustivas para quem tem dado nos dois anos, logo devem somar o total com dado; o codigo confere iss… **Risco:** todos os termos saem do payload, entao esta e uma verificacao de coerencia interna e nao detecta erro de calculo comum as quatro categorias |
| `78` | conferencia do fechamento das categorias | limiar | como sao contagens inteiras, a igualdade exata e o criterio correto e dispensa tolerancia **Risco:** por nao usar coer nem cmp, a comparacao nao incrementa nenhum contador, entao uma divergencia aqui e impressa mas nao afeta o codigo de saida do scri… |
| `85` | raiz dos arquivos brutos da ANEEL | leitura | o comentario das linhas 81 a 84 registra que a secao passou a reconstruir a tarifa do arquivo bruto da ANEEL, e nao mais do payload, justamente para … **Risco:** caminho montado por concatenacao de texto, sensivel a mudanca de organizacao dos diretorios brutos |
| `86-87` | conversao de numero em formato brasileiro | aritmética | o arquivo bruto e lido inteiro como texto na linha 89, entao a conversao precisa remover o separador de milhar antes de trocar o decimal; a ordem das… **Risco:** inverter a ordem das substituicoes destruiria o valor; errors coerce transforma sujeira em nulo silenciosamente, o que reduz a base sem aviso |
| `88-89` | leitura bruta das tarifas homologadas | leitura | ler com dtype texto preserva os campos numericos em formato brasileiro para a conversao explicita de _num e evita inferencia de tipo por amostra; low… **Risco:** o caminho fixa a data do snapshot, entao uma atualizacao da base exige editar o codigo; se o arquivo vier em outra codificacao, os rotulos com acento… |
| `90` | acesso limpo a coluna textual | leitura | as comparacoes do filtro sao por igualdade exata de rotulo, entao espacos residuais fariam linhas validas sairem da selecao **Risco:** nao normaliza caixa nem acento, entao variacao de grafia na origem ainda derruba linhas; astype str converte nulo no texto nan, que simplesmente nao … |
| `91-93` | selecao da tarifa residencial B1 convencional | limiar | as seis condicoes juntas isolam uma unica linha tarifaria por distribuidora e vigencia: B1 residencial convencional e a tarifa do consumidor domestic… **Risco:** depende de rotulos textuais com acento e caixa exatos; qualquer mudanca de nomenclatura na ANEEL zera a selecao e a secao inteira quebra ou compara c… |
| `94` | copia da selecao tarifaria | leitura | copiar antes de criar colunas evita escrever em uma fatia da tabela original, que geraria aviso e comportamento indefinido **Risco:** se a selecao for vazia, todas as etapas seguintes operam sobre tabela vazia e as comparacoes finais comparam conjuntos vazios sem erro evidente |
| `95-96` | datas de vigencia da tarifa | aritmética | a tarifa so pode ser atribuida a uma data se o intervalo de vigencia for comparavel, o que exige converter o texto em data **Risco:** errors coerce transforma data invalida em nulo, e nulo falha as comparacoes da linha 100, eliminando a linha sem aviso; o formato e inferido, o que p… |
| `97` | tarifa por quilowatt hora, soma de TUSD e TE | aritmética | a tarifa cheia e a soma da parcela de distribuicao com a de energia, e a divisao por mil converte a unidade publicada, reais por megawatt hora, para … **Risco:** se uma das parcelas nao converter, a soma vira nulo e a linha e descartada adiante; se a unidade da base mudar, a divisao fixa por mil passa a estar … |
| `98` | CNPJ numerico da distribuidora | aritmética | converter para numero nos dois lados e o que permite a juncao da linha 111 casar, ja que a base de tarifas e a comercial podem gravar o CNPJ com form… **Risco:** CNPJ como ponto flutuante perde precisao acima de quinze digitos significativos, o que aqui e tolerado porque o CNPJ tem quatorze; se a base trouxer … |
| `99` | data de referencia da tarifa | leitura | a data nao e escrita aqui: vem da constante compartilhada REF_TARIFA, a mesma que as etapas do pipeline usam, e a linha 133 imprime esse valor dizend… **Risco:** se REF_TARIFA cair fora de toda vigencia da base da ANEEL, o filtro da linha 100 esvazia e as comparacoes seguintes passam a confrontar conjuntos vaz… |
| `100` | tarifas vigentes e positivas na data de referencia | limiar | o intervalo fechado nos dois extremos garante que uma tarifa que inicia ou termina exatamente na data de referencia seja considerada vigente; o corte… **Risco:** se houver sobreposicao de vigencias na base, mais de uma tarifa por distribuidora entra e a mediana da linha 101 e que resolve o empate; nulos em ini… |
| `101` | mediana da tarifa por distribuidora | estatística | o comentario das linhas 81 a 84 declara que a reconstrucao refaz a mediana por CNPJ; a mediana e robusta a registro atipico remanescente quando mais … **Risco:** se o filtro deixar passar linhas de naturezas diferentes para o mesmo CNPJ, a mediana escolhe uma delas sem sinalizar a heterogeneidade; distribuidor… |
| `102-103` | leitura da base comercial por municipio | leitura | restringir as colunas na leitura e o que torna viavel carregar a base, e sao exatamente as quatro necessarias para o par municipio e distribuidora co… **Risco:** se algum desses nomes de coluna mudar no arquivo, a leitura falha por completo; a data do snapshot esta fixa no caminho |
| `104` | data de referencia da base comercial | aritmética | a restricao ao ano exige data tipada, o que a conversao fornece **Risco:** data invalida vira nulo e a linha e descartada no filtro seguinte sem aviso |
| `105` | restricao da base comercial ao ano dos pesos | limiar | o peso de unidades consumidoras precisa ser de um periodo definido e declarado, e o ano vem da constante compartilhada ANO_UC, impressa na linha 133 … **Risco:** ANO_UC e REF_TARIFA sao constantes independentes, entao nada no codigo garante que o ano dos pesos corresponda a data da tarifa; se houver varias com… |
| `106` | CNPJ numerico na base comercial | aritmética | a juncao da linha 111 exige o mesmo tipo nos dois lados, e a linha 98 faz a conversao equivalente na base de tarifas **Risco:** nulo aqui elimina a linha na limpeza da linha 109; formatacao com pontuacao na origem produziria nulo em massa |
| `107` | unidades consumidoras ativas como peso | aritmética | substituir nulo por zero mantem a linha na base mas com peso nulo, o que preserva o par na estrutura sem influenciar a media ponderada da linha 113 **Risco:** se todos os pesos de um municipio forem nulos, a soma e zero e a media ponderada seria invalida, situacao que a linha 113 trata caindo para a media s… |
| `108` | codigo IBGE numerico do municipio | aritmética | o payload identifica municipio pelo codigo IBGE, entao a chave precisa ser do mesmo tipo para o alinhamento da linha 116 funcionar **Risco:** codigo de sete digitos cabe sem perda em ponto flutuante, mas se a base trouxer codigo de seis digitos sem o verificador, o alinhamento com o payload… |
| `109` | limpeza das chaves e tipo inteiro do codigo IBGE | aritmética | linha sem uma das chaves nao pode ser agrupada nem casada, e o inteiro e o tipo que casa com os codigos publicados no payload na linha 115 **Risco:** a conversao para inteiro trunca a parte decimal em vez de arredondar, o que so e seguro porque a limpeza anterior garante ausencia de nulo; o descart… |
| `110-111` | unidades consumidoras por municipio e distribuidora com a tarifa casa… | agregação | somar por par consolida as varias competencias em um unico peso antes da ponderacao; a juncao a esquerda seguida do descarte de tarifa nula mantem ap… **Risco:** municipio cujas distribuidoras todas ficaram sem tarifa desaparece da reconstrucao e some da comparacao final sem contabilizacao; o descarte nao e co… |
| `112-114` | tarifa municipal como media ponderada por unidades consumidoras | estatística | o comentario das linhas 81 a 84 declara que a reconstrucao refaz a media ponderada por unidades consumidoras; ponderar por unidades consumidoras faz … **Risco:** a alternativa de peso zero devolve uma media simples com significado diferente, sem marcar quais municipios cairam nesse caso; se os pesos forem de c… |
| `115` | tarifas publicadas extraidas do payload | leitura | o payload guarda codigo e tarifa em listas paralelas, e o zip as remonta em serie indexada; excluir os nulos evita que municipio sem tarifa publicada… **Risco:** o zip assume que as duas listas tem o mesmo comprimento e a mesma ordem; se divergirem, a associacao entre municipio e tarifa fica errada sem qualque… |
| `116` | alinhamento entre tarifa reconstruida e publicada | agregação | o alinhamento por indice garante que cada linha compara o mesmo municipio nos dois lados, e o descarte de nulos restringe a intersecao, unico dominio… **Risco:** a intersecao pode ser bem menor que os 5.570 municipios sem que isso apareca, ja que so o tamanho da tabela e impresso na linha 132; municipio presen… |
| `117-118` | conferencia dos extremos da tarifa | limiar | o comentario das linhas 81 a 84 registra que esta secao antes comparava o minimo com ele mesmo sobre o proprio payload e por isso nao podia falhar; a… **Risco:** extremos sao sensiveis a uma unica distribuidora atipica, entao a comparacao testa bem as pontas e pouco o miolo da distribuicao, o que e coberto pel… |
| `119-120` | amplitude tarifaria entre o maximo e o minimo | aritmética | a razao e a grandeza divulgada como amplitude e e recalculada dos dois lados a partir dos mesmos extremos ja conferidos nas linhas 117 e 118, com fon… **Risco:** divisao pelo minimo torna a razao muito sensivel a erro no menor valor; se o minimo se aproximar de zero, a amplitude explode e a tolerancia fixa per… |
| `127` | diferenca absoluta por municipio na ultima casa publicada | aritmética | o comentario das linhas 121 a 126 registra que o payload grava a tarifa com quatro casas, entao o lado reconstruido precisa ser arredondado a mesma p… **Risco:** o arredondamento em ponto flutuante decide diferente no meio-passo, que e exatamente a causa das 139 diferencas de uma unidade descritas no comentari… |
| `128` | contagem de coincidencias exatas | agregação | o limiar de um bilionesimo e muito menor que a ultima casa publicada, entao funciona como igualdade exata tolerando apenas residuo de ponto flutuante… **Risco:** o limiar e arbitrario e nao derivado da precisao do formato; se o payload passasse a gravar com mais casas, ele deixaria de separar igualdade de resi… |
| `129-130` | conferencia da reproducao da tarifa em todos os municipios | limiar | o comentario das linhas 121 a 126 declara que a afirmacao verificada e a honesta: reproduz dentro de uma unidade da ultima casa publicada, em todos; … **Risco:** a folga aceita erro real de uma unidade da ultima casa, portanto um vies sistematico dessa magnitude passaria; como so a contagem e comparada, um mun… |
| `131` | impressao da faixa e da amplitude publicadas | apresentação | imprime com quatro casas, que e a precisao com que o payload grava a tarifa segundo o comentario das linhas 121 a 126 **Risco:** a razao exibida com duas casas arredonda e pode diferir da conferida na linha 119 na terceira casa |
| `132` | impressao das coincidencias e da maior diferenca | apresentação | publicar o maior desvio ao lado da contagem permite ao leitor verificar que o pior caso cabe na ultima casa publicada, sustentando a afirmacao do com… **Risco:** seis casas podem sugerir precisao que a origem, com quatro casas, nao possui |
| `133` | impressao da referencia temporal da tarifa e dos pesos | apresentação | imprimir as duas constantes tal como foram usadas nas linhas 99 e 105 deixa a competencia auditavel na propria saida, e o texto afirma que a referenc… **Risco:** a afirmacao de que a referencia e a mesma do CadUnico e da CDE e texto fixo e nao e verificada por nenhuma comparacao do arquivo: se REF_TARIFA deixa… |
| `139-140` | pares de fracao coberta com subsidio positivo nas duas datas | limiar | o comentario das linhas 136 a 138 registra que o app so usa o municipio com subsidio positivo nas duas datas, porque onde a CDE ficou liquida negativ… **Risco:** o zip depende de as duas listas estarem na mesma ordem municipal; o criterio maior que zero exclui o municipio com fracao exatamente zero, decisao qu… |
| `141` | mediana por indice do meio | estatística | para lista de tamanho impar, esse indice e exatamente a mediana; o codigo usa essa definicao como caminho independente da mediana do payload **Risco:** com numero par de municipios, esta funcao devolve o elemento superior e nao a media dos dois centrais, entao pode diferir da mediana do payload por u… |
| `142` | coerencia da mediana da fracao coberta em 2024 | limiar | os dois lados saem do payload, a lista municipal e o campo nacional, por isso o codigo usa coer e nao cmp; conforme o comentario das linhas 11 a 19, … **Risco:** se a lista municipal e o agregado estiverem igualmente errados, a conferencia passa; a tolerancia de 0.06 ponto percentual absorve a diferenca de def… |
| `143` | coerencia da mediana da fracao coberta em 2026 | limiar | mesma estrutura da competencia anterior, sobre o mesmo conjunto de pares filtrado, o que mantem as duas medianas comparaveis entre si **Risco:** os mesmos da conferencia de 2024, por serem dois campos do proprio payload |
| `144` | municipios com ganho na fracao coberta | agregação | a comparacao estrita entre as duas datas do mesmo municipio define ganho, e o universo e o mesmo conjunto filtrado das medianas **Risco:** a comparacao estrita classifica como sem ganho o municipio com variacao nula, e uma variacao infinitesimal por ruido numerico conta como ganho |
| `145` | coerencia do percentual de municipios com ganho | aritmética | o denominador e o mesmo conjunto filtrado usado nas medianas, o que e exigido pelo comentario das linhas 136 a 138; ambos os lados saem do payload, p… **Risco:** divisao por zero se o filtro esvaziar a lista; por ser coerencia interna, nao detecta erro comum a lista e ao agregado |
| `146-147` | impressao do universo e das exclusoes por CDE negativa | aritmética | publicar o tamanho do universo e das exclusoes torna auditavel o recorte descrito no comentario das linhas 136 a 138, em vez de deixar o filtro impli… **Risco:** o texto atribui toda exclusao a CDE liquida negativa, mas o filtro das linhas 139 e 140 tambem remove nulo e valor exatamente zero, causas que a mens… |
| `150` | variacao por distribuidora entre as duas datas | aritmética | a diferenca entre as duas competencias e a grandeza que a decomposicao nacional reparte entre Enel, EDP e demais nas linhas 152 a 154 **Risco:** nulo em qualquer das colunas propaga para a diferenca e a soma do grupo o ignora, o que desloca a parcela sem aviso |
| `151` | listas de agentes dos grupos Enel e EDP | leitura | agrupar as concessionarias por controlador e o que permite falar em variacao do grupo; os rotulos correspondem ao indice de por_agente.csv **Risco:** lista fixa no codigo: se o CSV mudar a grafia de um agente ou se surgir outra distribuidora do grupo, ela cai silenciosamente em demais e as tres par… |
| `152` | conferencia da parcela Enel | limiar | o lado recalculado vem de por_agente.csv, escrito por 10c, anterior ao payload, e a fonte e declarada como cmp exige **Risco:** a tolerancia de 0.51 e apertada para valores grandes em reais, entao diferenca de arredondamento na origem pode acusar divergencia sem haver erro de … |
| `153` | conferencia da parcela EDP | limiar | mesma estrutura da parcela anterior, com a mesma fonte anterior ao payload declarada **Risco:** os mesmos da parcela Enel, alem da dependencia dos rotulos fixos da linha 151 |
| `154` | conferencia da parcela dos demais agentes | limiar | a negacao da uniao dos dois grupos garante particao exaustiva dos agentes, sem sobreposicao nem lacuna, o que sustenta o fechamento conferido na linh… **Risco:** qualquer agente com rotulo grafado diferente do esperado entra aqui sem alarme, e como a particao continua exaustiva o fechamento nao denuncia o erro |
| `155` | soma das tres parcelas publicadas | agregação | como as tres parcelas particionam os agentes, a soma delas deve reproduzir a variacao nacional, o que e conferido na linha seguinte **Risco:** por sair inteiramente do payload, a soma nao detecta erro comum as tres parcelas |
| `156` | coerencia entre a soma das parcelas e a variacao nacional | limiar | os dois lados vem do payload, por isso coer e nao cmp, conforme a distincao das linhas 11 a 19; a tolerancia de 200 e muito maior que a padrao, o que… **Risco:** tolerancia de 200 sem justificativa escrita pode esconder erro real de ate essa magnitude; como e coerencia interna, erro comum ao numerador e ao den… |
| `159` | atalho para os campos de fluxo do CadUnico | leitura | encurta o acesso repetido aos campos de pobreza, baixa renda e elegiveis das duas competencias no laco seguinte **Risco:** se a chave fluxo nao existir no payload, a secao inteira quebra no acesso |
| `160-164` | comparacao dos agregados do CadUnico por faixa e competencia | limiar | o lado esquerdo vem de cadunico_sagi.csv, escrito por 05b, anterior ao payload, e a fonte e declarada, como cmp exige; o laco duplo garante que a mes… **Risco:** o rotulo e derivado do penultimo pedaco do nome da coluna, entao uma renomeacao na origem produz rotulo sem sentido sem quebrar nada; se anomes nao f… |
| `165` | fechamento pobreza mais baixa renda em 2024 | limiar | as duas faixas particionam o universo elegivel, entao a soma deve reproduzir o total; a folga de 2 absorve arredondamento das duas parcelas **Risco:** por nao usar coer nem cmp, uma divergencia aqui e impressa mas nao incrementa o contador de falhas e nao altera o codigo de saida do script; todos os… |
| `166` | fechamento pobreza mais baixa renda em 2026 | limiar | mesma identidade de particao aplicada a competencia seguinte, com a mesma folga de 2 **Risco:** os mesmos da linha anterior: fora da contagem e do codigo de saida |
| `167` | variacao do universo elegivel entre as competencias | aritmética | a razao menos um e a definicao usual de variacao relativa, e o formato com sinal deixa claro se houve expansao ou retracao **Risco:** divisao por zero se o total de 2024 for zero; o valor e apenas impresso e nao passa por nenhuma conferencia |
| `168` | saida da faixa de pobreza entre as competencias | aritmética | e a diferenca entre dois estoques na mesma definicao de faixa, ja conferidos contra o SAGI no laco das linhas 160 a 164 **Risco:** o rotulo fala em familias que sairam da faixa, mas a diferenca de estoques nao e fluxo liquido de saida: entradas e saidas se compensam dentro do per… |
| `175` | leitura do painel por municipio e agente | leitura | o comentario das linhas 171 a 174 registra que esta secao lia os pares do payload e comparava com um campo que 10a escreveu a partir da mesma lista, … **Risco:** se 07b passar a derivar mun_agente.csv do payload, a independencia se perde sem que o codigo perceba |
| `176` | variacao percentual por par municipio e agente | aritmética | trocar zero por nulo antes de dividir evita infinito no denominador nulo e marca o caso como indefinido em vez de gerar valor impossivel, que seria f… **Risco:** variacao relativa sobre base pequena e instavel, o que e mitigado pelo corte de base minima na linha seguinte; base nula no numerador tambem produz n… |
| `177` | filtro de base minima e variacao finita | limiar | o corte em 100 beneficiarios evita que variacao percentual sobre base minuscula domine a analise, e a checagem de finitude remove nulo e infinito; o … **Risco:** o limiar de 100 e arbitrario e nao documentado, e precisa ser identico ao usado por quem escreveu o campo publicado, senao as contagens comparadas na… |
| `178` | quantidade de agentes distintos por municipio | agregação | contar valores distintos, e nao linhas, evita contar duas vezes o mesmo agente que apareca em mais de uma linha para o mesmo municipio **Risco:** a contagem e feita depois do filtro da linha 177, entao municipio cuja segunda distribuidora foi cortada por base pequena deixa de ser contado como t… |
| `179` | municipios com duas ou mais distribuidoras | limiar | o limiar de dois e a propria definicao do fenomeno estudado na secao, municipios com duas concessionarias **Risco:** herda integralmente o recorte da linha 177, entao o conjunto e de municipios com dois agentes acima da base minima, e nao de municipios com dois agen… |
| `180` | subconjunto dos pares em municipios com atendimento multiplo | agregação | a analise de sinais opostos so faz sentido dentro de municipios com mais de um agente, e este recorte garante isso **Risco:** nenhum alem da dependencia dos recortes anteriores |
| `181-185` | contagem de municipios com variacoes de sinais opostos | agregação | ordenar e olhar o primeiro e o ultimo elemento equivale a comparar o minimo com o maximo, e a dupla desigualdade estrita exige que haja ao menos uma … **Risco:** as desigualdades sao estritas, entao variacao exatamente zero nao conta como nenhum dos sinais; a ordenacao por municipio e feita em laco Python, o q… |
| `186-187` | conferencia da contagem de municipios com duas ou mais distribuidoras | limiar | o comentario das linhas 171 a 174 registra que antes os dois lados saiam da mesma linha do mesmo script, e que agora o recalculo parte de mun_agente.… **Risco:** a comparacao so vale se o recorte desta secao, base minima de 100 e variacao finita, for identico ao usado por quem publicou o campo; qualquer difere… |
| `188-189` | conferencia da contagem de municipios com sinais opostos | limiar | mesma reconstrucao a partir de mun_agente.csv, com fonte declarada e tolerancia que exige igualdade exata entre inteiros **Risco:** depende do mesmo recorte da conferencia anterior e ainda do tratamento de variacao exatamente zero, que a comparacao estrita da linha 184 exclui de a… |
| `192-194` | resumo das especies de conferencia | apresentação | o comentario das linhas 11 a 19 diz que o resumo final separa as duas especies, e e o que estas linhas fazem: quem le sabe quantas comparacoes de fat… **Risco:** as conferencias impressas direto nas linhas 78, 165 e 166 nao passam por cmp nem por coer, entao o resumo subconta o que foi realmente verificado |
| `196-200` | nota final sobre o alcance de cada especie de conferencia | apresentação | e a versao impressa da regra que o comentario das linhas 11 a 19 fixa no codigo: so ha deteccao de erro de calculo quando os dois lados vem por camin… **Risco:** e texto fixo: se alguem passar a usar coer onde caberia cmp, a nota continuara afirmando o mesmo rigor sem que nada no codigo detecte a troca |
| `201` | codigo de saida conforme as divergencias | serialização | converter o resultado da auditoria em codigo de saida e o que faz a validacao ter efeito sobre quem a executa, em vez de apenas imprimir texto **Risco:** so conta as divergencias registradas por cmp e coer, entao uma falha nas conferencias impressas diretamente nas linhas 78, 165 e 166 nao altera o cod… |

### `reconstrucao/pipeline/valida_territorio.py`

| linhas | operação | espécie | o que faz, e o que a tornaria errada |
|---|---|---|---|
| `4-9` | Spearman com mascara de pares completos e mascara opcional | estatística | Aqui a mascara de pares completos e aplicada antes de ranquear, o que torna os postos consecutivos e o resultado o Spearman exato dos pares completos… **Risco:** Empates recebem posto medio (padrao do pandas); variaveis com muitos empates - por exemplo d4_corr igual a zero em todo municipio sem favela mapeada … |
| `10-11` | Taxa de lacuna e percentual sem Tarifa Social | aritmética | Normaliza a lacuna pelo universo elegivel para tornar municipios de portes diferentes comparaveis em correlacao de ordem. desc e o complemento da cob… **Risco:** Nao ha replace(0, NaN) no denominador: municipio com familias_elegiveis = 0 gera divisao por zero (inf ou NaN, conforme o numerador), e o inf sobrevi… |
| `12-16` | Correlacoes de favela contra medidas energeticas, todos os municipios | estatística | Seis correlacoes de ordem contra a mesma variavel territorial, para testar se a participacao de favela ordena alguma das medidas energeticas. O codig… **Risco:** Sobre os 5.570 municipios, d4_corr e zero ou ausente na maioria (o proprio arquivo registra 655 com favela mapeada), entao o rho dessa passagem mede … |
| `18-22` | Mesmas correlacoes restritas aos municipios com favela mapeada | estatística | Restringir a amostra aos municipios com favela mapeada remove o contraste mapeado/nao mapeado e deixa apenas a variacao de intensidade, o que separa … **Risco:** A comparacao `d.favela_mapeada==True` falha silenciosamente (devolve tudo False) se a coluna vier como texto 'True'/'False' em vez de booleano apos o… |
| `24-27` | Medianas comparadas entre municipios com e sem favela mapeada | estatística | Contraste de medianas entre dois grupos, robusto a cauda longa, como complemento a correlacao de ordem. O codigo apenas imprime os dois valores: nao … **Risco:** Sem medida de dispersao ou teste, duas medianas proximas ou distantes nao dizem se a diferenca excede a variacao amostral. O operador ~m trata NaN da… |
