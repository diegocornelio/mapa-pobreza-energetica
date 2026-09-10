# Decisões

Registro datado das escolhas de leitura e de método. Cada uma diz o que foi decidido, por
quê, e o que a falsificaria.

---

## Leitura das bases

**2026-09-10 · Ponte distribuidora→município pelo CNPJ.** Usar `NumCNPJ` do INDGER contra
`NumCNPJDistribuidora` do arquivo de tarifas, e não `SigAgente`. O nome do agente casa
apenas 560 municípios; o CNPJ casa os 5.570. *Falsificaria:* encontrar CNPJ divergente
entre os dois arquivos para a mesma concessão.

**2026-09-10 · DEC e FEC anuais pela soma dos doze meses.** `NumPeriodoIndice` assume
apenas 1 a 12, e todas as 6.264 séries de 2024 têm 12 períodos; não existe registro
anual. O limite, em `AnoLimiteQualidade`, é anual. *Falsificaria:* achar no arquivo um
período 0 ou 13 representando o ano fechado.

**2026-09-10 · Agregação de continuidade ponderada por consumidores.** Usar
`SigIndicador = NumCon` como peso na ponte conjunto→município, em vez de média simples ou
pior caso. Municípios grandes são atendidos por dezenas de conjuntos muito desiguais: o
Rio tem 78, com o pior a 6,19× o limite e a média ponderada em 0,93×. O pior conjunto
permanece publicado como coluna auxiliar. *Falsificaria:* demonstrar que `NumCon` não
representa consumidores do conjunto.

**2026-09-10 · Denominador territorial na tabela 4712.** A variável 1009909 do SIDRA 9887
é percentual **dentro** do universo das favelas, não do município. O denominador correto é
a variável 381 da 4712, na mesma espécie de domicílio. *Falsificaria:* o IBGE publicar
que 1009909 se refere ao total municipal.

**2026-09-10 · Renda domiciliar, não per capita.** A conta é paga pelo domicílio. O
tamanho médio vem de moradores ÷ domicílios e varia 2,56× entre municípios.
*Falsificaria:* mostrar que a tarifa residencial é cobrada por morador.

**2026-09-10 · Desconto escalonado aplicado sobre a tarifa Baixa Renda.** A tarifa
publicada da subclasse é a base, não a conta: as linhas "Tarifa Social faixa 01/02" são
idênticas à "Baixa Renda". O desconto da Lei 12.212/2010 incide sobre ela.
*Falsificaria:* a inversão contra a CDE produzir consumo implícito fora de faixa
plausível — testado, dá 97,7 kWh na mediana.

**2026-09-05 · Contagem TSEE por linhas de benefício.** `NumCPFCNPJCliente` vem mascarado
no arquivo aberto e subconta quando usado como chave única. *Consequência declarada:*
unidade consumidora não é família, e 80 municípios apresentam sobrecobertura.

**2026-09-05 · Espinha de 5.570 municípios.** Filtrar `Lagoa Mirim` (4300001) e `Lagoa
dos Patos` (4300002) da malha `geobr` de 2022, que retorna 5.572 polígonos incluindo dois
registros especiais do RS. Filtrar `Boa Esperança do Norte` (5101837) do CECAD, município
criado após a malha de 2022. Preserva comparabilidade com o IBGE.

---

## Tratamento de ausência

**2026-09-10 · Ausência nunca vira zero.** Onde uma fonte não cobre um município, o campo
fica vazio e o aplicativo escreve "indisponível". Vale para os 14 municípios sem apuração
de DEC/FEC e para os 32 com CDE líquida negativa. *Motivo:* zero e "não medido" produzem
leituras opostas, e a versão anterior os confundia em três lugares distintos.

**2026-09-10 · Subsídio da CDE sem clip.** Bruto, estornos e líquido em colunas separadas.
O clip anterior inflava o total nacional em R$ 25,8 milhões e zerava 32 municípios, entre
eles 11 da Baixada Fluminense e o Rio de Janeiro.

**2026-09-10 · Sobrecobertura exposta, não zerada.** Os 80 municípios com mais benefícios
que famílias elegíveis recebem sinalização própria.

**2026-09-10 · Zero territorial é medição.** Nos 4.915 municípios sem favela identificada,
o zero vale, porque o Censo 2022 percorreu todo o território. Isso só passou a ser
verdade depois de corrigir o denominador.

---

## Método

**2026-09-10 · Sem índice composto.** Retirando duas das quatro dimensões, apenas 7 dos
100 primeiros permaneciam no topo. Além disso, não atendidas e qualidade do fornecimento
são independentes (Spearman −0,098), o que significa problemas distintos sob
responsabilidades distintas. *Falsificaria:* demonstrar estabilidade do ranking sob
esquemas alternativos de peso.

**2026-09-10 · Sem normalização min-max.** Sem composição a fazer, cada medida é publicada
na sua unidade. Faixas fixas e declaradas nos mapas, não quantis, para que a mesma cor
signifique o mesmo valor entre execuções.

**2026-09-10 · Escala divergente na razão DEC/FEC, com neutro em 1,00.** É polaridade, não
magnitude: abaixo de 1 é cumprimento, acima é violação. As demais medidas usam escala
sequencial de um matiz.

**2026-09-10 · 80 kWh como consumo de referência.** É o limiar da Lei 15.235/2025, a única
hipótese com ancoragem externa. Os cenários de 30 e 100 kWh são publicados ao lado, porque
o resultado depende inteiramente da escolha.

**2026-09-10 · Território como contexto operacional, não como vulnerabilidade.** A
participação de favela não tem associação detectável com nenhuma medida energética
(|rho| < 0,09). Renomear a variável para "comunidade vulnerável à pobreza energética" foi
avaliado e **recusado**: afirmaria relação que o dado contradiz e quebraria a
rastreabilidade até a nomenclatura do IBGE. *Falsificaria:* microdado domiciliar que
mostrasse a associação — que a agregação municipal não consegue ver.

**2026-09-10 · "Famílias não atendidas", não "lacuna".** Jargão descreve o buraco na
estatística; o rótulo adotado descreve pessoas.

**2026-09-10 · Encaminhamentos por bandas, não por exceção.** Um desenho baseado apenas em
limiares de cauda deixava 1.322 municípios sem nenhum item. O desenho por bandas produz 4
a 7 por município e 191 assinaturas distintas. *Motivo:* caixa vazia em um quarto dos
municípios não é rigor, é feature inútil.

**2026-09-10 · Três graus de encaminhamento.** Aritmética, processo e verificação. Nenhum
texto afirma efeito causal de ação sobre indicador; os de grau aritmética afirmam apenas o
que decorre da definição do indicador ou de tarifa publicada.

---

## Decisões revistas

**Descartada — agregar continuidade pelo pior conjunto.** Recomendada num plano anterior.
O teste mostrou que distorce cidades grandes: o Rio apareceria entre os piores do país por
causa de um conjunto entre 78. Substituída pela ponderação por consumidores.

**Descartado — validar o desconto por convergência com a CDE.** O argumento comparava a
economia total da família (R$ 33,20) com o subsídio da CDE (R$ 30,03), que são grandezas
diferentes: a CDE reembolsa o desconto escalonado (R$ 25,68), não a mudança de subclasse
(R$ 7,51). Ficaram próximos porque dois erros se cancelaram parcialmente. Substituído pelo
teste de inversão.

**Retirada — a compensação DEC/FEC como evidência de prestação de contas.** Chegou-se a
tratar a existência de compensação em municípios sem violação coletiva como contradição.
Não é: os indicadores com prefixo `PG` remetem a indicadores individuais (DIC, FIC, DMIC),
que podem ser violados sem que o coletivo do conjunto ultrapasse o limite.

---

## Decisões anteriores, agora superadas

Registradas porque explicam o que havia antes. Todas descritas em `docs/CORRECOES.md`.

| data | decisão | superada por |
|---|---|---|
| 2026-09-05 | tarifa por mediana nacional B1, com `tarifa_flag_estimativa = true` em todos os municípios | C2 |
| 2026-09-05 | DEC/FEC agregados sem atentar para a periodicidade | C1 |
| 2026-09-05 | renda por classes usada diretamente como denominador per capita | C5 |
| 2026-09-05 | piso zero em `subsidio_tsee_reais` | C4 |
| 2026-09-05 | ajuste do teste de rótulo curto de 12 para 13 caracteres | rótulos curtos deixaram de existir com o fim do índice composto |
