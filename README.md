# Mapa da Pobreza Energética

Quatro medidas de pobreza energética nos 5.570 municípios brasileiros, a partir de
oito bases abertas da ANEEL, do MDS e do IBGE.

**Aplicativo:** (aplicativo)

Página única autocontida, sem servidor e sem dependência externa. Escolha um município
e ele responde para ele em todas as páginas.

---

## O que responde

| pergunta | medida |
|---|---|
| Quantas famílias elegíveis não recebem a Tarifa Social? | **9.968.144** no país, cobertura de 64,3% |
| A distribuidora cumpre o limite de continuidade? | **2.082 municípios** acima do limite da ANEEL em 2024 |
| Quanto pesa a conta para quem é pobre aqui? | mediana de 9,75% da renda a 80 kWh, sem o benefício |
| O território explica pobreza energética? | não, na escala municipal — e o resultado nulo está publicado |

## O que não responde

Quem é pobre em energia dentro de cada casa. Se a ausência do benefício é privação real
ou defasagem de cadastro. Quanto uma família paga de fato — a tarifa homologada não
inclui ICMS nem PIS/COFINS. Qualquer relação de causa e efeito. Qualquer inferência
sobre furto de energia.

`docs/LIMITES.md` traz a lista completa, e ela é parte do resultado, não ressalva de
rodapé.

## Não há índice composto

Um índice das quatro dimensões foi construído e testado. Retirando duas delas, apenas
**7 dos 100 primeiros** permaneciam no topo, com deslocamento mediano acima de mil
posições. Há ainda razão substantiva: famílias não atendidas e qualidade do fornecimento
são estatisticamente independentes (Spearman −0,098). Somá-las apaga a informação de que
são problemas distintos, em municípios distintos, sob responsabilidades distintas.

Por isso o produto é um **mapa de medidas separadas**, e não um ranking.

---

## Estrutura do repositório

```
reconstrucao/          o que produz o resultado publicado
  app/                 fonte do aplicativo e HTML gerado
  dados/               dataset municipal, payloads e agregado da CDE
  pipeline/            19 scripts numerados na ordem de execução
docs/                  método, correções, limites, dicionário, fontes
data/sources/          registro das fontes com URL e data de referência
data/processed/        saída da versão anterior, mantida para comparação
src/, app/, tests/     código da versão anterior — ver aviso abaixo
```

**Aviso sobre `src/`, `app/app.py` e `tests/`.** São a versão anterior deste trabalho,
que continha os seis defeitos descritos em `docs/CORRECOES.md`. Estão preservados para
que a comparação entre as duas versões seja auditável, e **não** produzem o resultado
publicado.

## Como reproduzir

Ver `docs/REPRODUCAO.md`. Em resumo: ajustar `reconstrucao/pipeline/_paths.py`, executar
os 14 scripts na ordem e conferir contra os números de referência de `docs/VALIDACAO.md`.

Os dados brutos são cerca de 3 GB e não acompanham o repositório. As URLs de origem
estão em `data/sources/fontes.csv`.

## Documentação

| arquivo | conteúdo |
|---|---|
| `docs/METODO.md` | as quatro medidas, com fórmula e razão de cada escolha |
| `docs/CORRECOES.md` | os seis defeitos encontrados, a prova de cada um e o efeito da correção |
| `docs/LIMITES.md` | o que os dados não dizem |
| `docs/DICIONARIO.md` | as 35 colunas do dataset municipal |
| `docs/FONTES.md` | as oito bases, com estado de leitura |
| `docs/REPRODUCAO.md` | como executar o pipeline |
| `docs/VALIDACAO.md` | testes aplicados e números de referência |
| `docs/DECISOES.md` | registro datado das decisões de leitura |

## Licenças

Código: MIT. Dados derivados: CC-BY 4.0.

## Autor

Diego H. C. de Rezende, fundador da Struktur Energia. Engenheiro de Computação e mestre
em Engenharia de Software, com experiência em desenvolvimento de software, ciência de
dados, gestão de projetos e operação de sistemas em ambientes de alta complexidade e
missão crítica. Cursa o MBA em Gestão de Riscos na Comercialização de Energia (USP/CCEE)
e o MBA em Data Science, Inteligência Artificial e Analytics (USP/ESALQ).
