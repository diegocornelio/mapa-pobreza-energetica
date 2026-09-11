"""Confere que cada trecho transcrito em docs/FORMULAS.md ainda bate com o codigo.

Documentacao de calculo envelhece em silencio: alguem corrige uma linha, o numero
publicado muda, e o documento continua descrevendo a versao antiga com a mesma
confianca de antes. Este script existe para que isso falhe alto.

Cada bloco de codigo em docs/FORMULAS.md e precedido por um marcador

    <!-- fonte: caminho/do/arquivo.py 12-21 -->

e o que vem no bloco tem de ser, caractere a caractere, o que esta naquelas linhas.

Uso:  python valida_formulas.py
Saida: codigo 0 se tudo confere; 1 e o relatorio das divergencias se nao.
"""
import re, sys, difflib
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DOC = RAIZ / "docs" / "FORMULAS.md"

MARCADOR = re.compile(
    r"<!--\s*fonte:\s*(?P<arq>[^\s]+)\s+(?P<ini>\d+)-(?P<fim>\d+)\s*-->\s*\n"
    r"```[a-z]*\n(?P<codigo>.*?)```",
    re.S)

def main():
    if not DOC.exists():
        print(f"nao encontrei {DOC}")
        return 1
    texto = DOC.read_text(encoding="utf-8")
    blocos = list(MARCADOR.finditer(texto))
    if not blocos:
        print("nenhum bloco com marcador de fonte em docs/FORMULAS.md")
        return 1

    falhas = []
    for m in blocos:
        arq, ini, fim = m["arq"], int(m["ini"]), int(m["fim"])
        doc = m["codigo"].rstrip("\n").splitlines()
        caminho = RAIZ / arq
        if not caminho.exists():
            falhas.append((arq, f"{ini}-{fim}", ["arquivo nao existe"]))
            continue
        linhas = caminho.read_text(encoding="utf-8").splitlines()
        if fim > len(linhas):
            falhas.append((arq, f"{ini}-{fim}",
                           [f"o arquivo tem {len(linhas)} linhas; o marcador pede ate {fim}"]))
            continue
        real = linhas[ini - 1:fim]
        if doc != real:
            d = list(difflib.unified_diff(real, doc, "no arquivo", "no documento", lineterm="", n=0))
            falhas.append((arq, f"{ini}-{fim}", d[2:]))

    print(f"blocos conferidos: {len(blocos)}")
    if not falhas:
        arquivos = sorted({m["arq"] for m in blocos})
        print(f"arquivos cobertos : {len(arquivos)}")
        for a in arquivos:
            n = sum(1 for m in blocos if m["arq"] == a)
            print(f"  ok  {a}  ({n} {'bloco' if n == 1 else 'blocos'})")
        print("\ntodas as transcricoes conferem com o codigo")
        return 0

    print(f"DIVERGENCIAS: {len(falhas)}\n")
    for arq, faixa, diff in falhas:
        print(f"--- {arq} linhas {faixa}")
        for l in diff[:14]:
            print(f"    {l}")
        print()
    print("docs/FORMULAS.md descreve codigo que nao existe mais. Corrija o documento")
    print("ou o marcador de linhas antes de publicar qualquer numero.")
    return 1

if __name__ == "__main__":
    sys.exit(main())
