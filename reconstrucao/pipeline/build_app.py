"""Injeta os payloads no template e grava o HTML publicável.

Uso:  python build_app.py
Saída: site/index.html  (~1,9 MB, autocontido)
"""
import io, os
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
tpl = io.open(BASE / "app" / "mapa.template.html", encoding="utf-8").read()
dados = io.open(BASE / "dados" / "dados.json", encoding="utf-8").read()
geo = io.open(BASE / "dados" / "geo.json", encoding="utf-8").read()

for nome, payload in (("dados.json", dados), ("geo.json", geo)):
    if "</script" in payload.lower():
        raise SystemExit(f"{nome} contém '</script' e quebraria o HTML")

# Chart.js vai embutido, e nao carregado de CDN: a pagina e um arquivo unico que
# abre do disco e funciona sem internet. A procedencia e o hash do arquivo estao
# em reconstrucao/app/vendor/PROVENIENCIA.txt.
chart = io.open(BASE / "app" / "vendor" / "chart.umd.min.js", encoding="utf-8").read()
leafjs = io.open(BASE / "app" / "vendor" / "leaflet.js", encoding="utf-8").read()
leafcss = io.open(BASE / "app" / "vendor" / "leaflet.css", encoding="utf-8").read()
for nome, txt in (("chart.umd.min.js", chart), ("leaflet.js", leafjs)):
    if "</script" in txt.lower():
        raise SystemExit(f"{nome} contém '</script' e quebraria o HTML")
if "</style" in leafcss.lower():
    raise SystemExit("leaflet.css contém '</style' e quebraria o HTML")

# O 09_payload.py reescreve dados.json do zero e as etapas 10a a 10e acrescentam a
# ele. Rodar o 09 isolado, para publicar uma constante nova, descarta em silencio a
# comparacao entre datas, a serie mensal e os conjuntos, e o app e montado sobre um
# payload mutilado sem que nada acuse. Aconteceu duas vezes. A guarda abaixo exige
# as chaves que so existem depois da cadeia completa.
_EXIGIDAS = ("nac", "cont", "frac26", "serie", "ncj", "agvar", "nar")
_faltam = [k for k in _EXIGIDAS if k not in json.loads(dados)]
if _faltam:
    raise SystemExit(
        "build_app: payload incompleto, faltam as chaves " + ", ".join(_faltam)
        + ". O 09_payload.py foi rodado isolado? Ele reescreve dados.json do zero."
        + " Rode 10a a 10e antes de montar a pagina.")

html = (tpl.replace("__DATA__", dados)
           .replace("__GEO__", geo)
           .replace("__CHARTJS__", chart)
           .replace("__LEAFLETJS__", leafjs)
           .replace("__LEAFLETCSS__", leafcss))
for ph in ("__DATA__", "__GEO__", "__CHARTJS__", "__LEAFLETJS__", "__LEAFLETCSS__"):
    if ph in html:
        raise SystemExit(f"placeholder {ph} não substituído")

destino = BASE.parent / "site" / "index.html"
destino.parent.mkdir(parents=True, exist_ok=True)
io.open(destino, "w", encoding="utf-8", newline="\n").write(html)
print(f"{destino}: {os.path.getsize(destino)/1e6:.2f} MB")
