"""Injeta os payloads no template e grava o HTML publicável.

Uso:  python build_app.py
Saída: reconstrucao/app/mapa.html  (~1,9 MB, autocontido)
"""
import io, os
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
tpl = io.open(BASE / "app" / "mapa.template.html", encoding="utf-8").read()
dados = io.open(BASE / "dados" / "dados.json", encoding="utf-8").read()
geo = io.open(BASE / "dados" / "geo.json", encoding="utf-8").read()

for nome, payload in (("dados.json", dados), ("geo.json", geo)):
    if "</script" in payload.lower():
        raise SystemExit(f"{nome} contém '</script' e quebraria o HTML")

html = tpl.replace("__DATA__", dados).replace("__GEO__", geo)
if "__DATA__" in html or "__GEO__" in html:
    raise SystemExit("placeholder não substituído")

destino = BASE / "app" / "mapa.html"
io.open(destino, "w", encoding="utf-8", newline="\n").write(html)
print(f"{destino}: {os.path.getsize(destino)/1e6:.2f} MB")
