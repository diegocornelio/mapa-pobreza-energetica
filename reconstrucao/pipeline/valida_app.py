# -*- coding: utf-8 -*-
"""Impede que numero calculado seja escrito a mao na prosa do aplicativo.

O aplicativo nao calcula regra: ele le o payload. Enquanto essa disciplina for
respeitada, nenhuma pagina pode mostrar dado velho, porque nao existe dado na
tela que nao venha do arquivo gerado pelo pipeline. O risco nao esta no calculo,
esta na prosa: uma frase que diz "em 80 municipios ha mais beneficios que
familias elegiveis" envelhece em silencio quando a base muda, e nenhum validador
de numeros percebe, porque para eles aquilo e texto.

Foi o que aconteceu. A mudanca para a base casada por data levou a sobrecobertura
de 80 para 35 municipios e o saldo liquido de 9.938.086 para 10.426.463, e a
pagina do metodo seguiu afirmando os valores antigos por semanas.

Este validador extrai todo literal numerico da prosa do template e exige que cada
um esteja declarado abaixo, com a sua origem. Literal de norma pode ficar: muda
por ato publicado, e a atualizacao e deliberada. Literal de calculo nao pode:
tem de ser derivado do payload em tempo de execucao.

Roda depois de build_app.py e devolve codigo diferente de zero se encontrar
literal nao declarado.
"""
import re, sys, pathlib

BASE = pathlib.Path(__file__).resolve().parents[1]
TEMPLATE = BASE / "app" / "mapa.template.html"

# Literais que podem permanecer escritos a mao, com a razao de cada um.
# NORMA     valor fixado em lei, decreto ou resolucao; muda por ato publicado
# ESTRUTURA constante do desenho do dado, nao resultado de calculo
# FAIXA     rotulo de banda de mapa, que acompanha o vetor breaks ao lado
# HISTORICO numero de uma correcao ja ocorrida, que descreve o passado e nao o presente
DECLARADOS = {
    # --- NORMA ---
    "80":        "NORMA · limiar de consumo da Lei 15.235/2025 e da REN 1.147/2025",
    "120":       "NORMA · limiar do Desconto Social, REN 1.147/2025 art. 179 §4º",
    "100":       "NORMA · percentual de reducao, REN 1.147/2025 art. 179 §1º I",
    "218":       "NORMA · linha de pobreza do CadUnico, Decreto 11.566/2023",
    "12.212":    "NORMA · numero da lei do desconto escalonado, revogado em 2025",
    "15.235":    "NORMA · numero da lei da gratuidade",
    "1.147":     "NORMA · numero da resolucao da ANEEL",
    "1.300":     "NORMA · numero da medida provisoria",
    "1.000":     "NORMA · numero da resolucao normativa alterada",
    "10.438":    "NORMA · numero da lei da Tarifa Social",
    "11.566":    "NORMA · numero do decreto da linha de pobreza",
    "0,35":      "NORMA · fator de pagamento da regra revogada, contexto historico",
    "0,60":      "NORMA · fator de pagamento da regra revogada, contexto historico",
    "0,50625":   "NORMA · fator a 80 kWh da regra revogada, contexto historico",
    "25":        "NORMA · numero da portaria interministerial da CVA",
    # --- ESTRUTURA ---
    "5.570":     "ESTRUTURA · municipios da malha do Censo 2022",
    "5.571":     "ESTRUTURA · municipios cobertos pelo SAGI",
    # --- HISTORICO, das correcoes ja registradas ---
    "89,8%":     "HISTORICO · C3, participacao de favela em Sao Paulo antes da correcao",
    "2,56":      "HISTORICO · C5, variacao do tamanho do domicilio citada na correcao",
    "3.383":     "HISTORICO · C4, municipios com estorno na CDE",
    "479.764":   "HISTORICO · divergencia por agente x por municipio, ja explicada",
    "479.911":   "HISTORICO · a outra ponta da mesma divergencia",
    "97,7":      "HISTORICO · consumo implicito sob a regra revogada, em dez/2024",
    "142,7":     "HISTORICO · o mesmo calculo aplicado a marco de 2026, que revelou o erro",
}

# Padroes de literal que envelhecem. Numero puro sem formatacao nao entra: e
# indice, largura de css ou argumento de funcao, e nao valor publicado.
PADROES = [
    ("moeda",      r"R\$\s?\d[\d.]*,\d{2}"),
    ("percentual", r"\b\d+,\d+%"),
    ("milhar",     r"\b\d{1,3}(?:\.\d{3})+\b"),
]

# A prosa e o que esta fora de <script> puro? Nao: o template e todo script com
# template literals dentro. O criterio util e outro: literal dentro de uma string
# de texto, e nao em expressao. Aproximamos excluindo as linhas que sao
# claramente de configuracao (breaks, labels de faixa, css).
IGNORA_LINHA = re.compile(r"breaks:\s*\[|labels:\s*\[|^\s*[.#@]|px\)|grid-template|@media")


def sem_comentarios(texto):
    """Remove comentarios de bloco e de linha, preservando a numeracao das linhas.

    Comentario nao vai para a tela. Um comentario que explica um defeito passado
    cita numeros daquele defeito de proposito, e obriga-lo a entrar na lista de
    declarados poluiria a lista com historico que nao e publicado.
    """
    fora = []
    dentro_bloco = False
    for linha in texto.splitlines():
        if dentro_bloco:
            if "*/" in linha:
                linha = linha.split("*/", 1)[1]
                dentro_bloco = False
            else:
                fora.append(""); continue
        while "/*" in linha:
            antes, resto = linha.split("/*", 1)
            if "*/" in resto:
                linha = antes + resto.split("*/", 1)[1]
            else:
                linha = antes; dentro_bloco = True; break
        linha = re.sub(r"(?<!:)//.*$", "", linha)     # // mas nao http://
        linha = re.sub(r"<!--.*?-->", "", linha)
        fora.append(linha)
    return fora


def prosa(texto):
    """Devolve (numero_da_linha, linha) das linhas candidatas a conter prosa."""
    for i, linha in enumerate(sem_comentarios(texto), 1):
        if IGNORA_LINHA.search(linha):
            continue
        yield i, linha


def main():
    t = TEMPLATE.read_text(encoding="utf-8")
    achados = {}
    for n, linha in prosa(t):
        for rot, pat in PADROES:
            for m in re.finditer(pat, linha):
                lit = m.group(0)
                chave = lit.replace("R$", "").strip()
                if chave in DECLARADOS or lit in DECLARADOS:
                    continue
                achados.setdefault(lit, []).append((n, rot))

    if not achados:
        print(f"valida_app: nenhum literal numerico nao declarado em {TEMPLATE.name}")
        print(f"  {len(DECLARADOS)} literais declarados, todos com origem registrada")
        return 0

    print(f"valida_app: {len(achados)} literal(is) nao declarado(s) na prosa do template")
    print()
    print("  Cada um precisa de uma de duas coisas: ser derivado do payload em tempo")
    print("  de execucao, se for resultado de calculo; ou entrar em DECLARADOS com a")
    print("  sua origem, se vier de norma, de estrutura ou de historico ja corrigido.")
    print()
    for lit, ocs in sorted(achados.items()):
        linhas = ", ".join(str(n) for n, _ in ocs[:6])
        print(f"  {lit:<18} {ocs[0][1]:<11} linha(s) {linhas}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
