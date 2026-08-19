import json
import datetime
from pathlib import Path

BASE = Path("/home/deploy/alquimetria")
DATA = BASE / "data" / "serpavi.json"
OUT = BASE / "index.html"
SITE = "https://alquimetria.viajeinteligencia.com"

d = json.load(open(DATA, encoding="utf-8"))
datos = d["datos"]
hoy = datetime.date.today().isoformat()

rows = []
for cod, v in datos.items():
    serie = v["serie"]
    a11 = serie.get("2011", {}).get("alquiler_mensual")
    a24 = serie.get("2024", {}).get("alquiler_mensual")
    if a11 and a24:
        var = (a24 - a11) / a11 * 100
        rows.append((cod, v["nombre"], a11, a24, var, serie))
    else:
        rows.append((cod, v["nombre"], None, a24, None, serie))
rows.sort(key=lambda r: -(r[4] if r[4] is not None else -999))

trs = []
itemlist = []
for i, (cod, nombre, a11, a24, var, serie) in enumerate(rows, start=1):
    var_txt = f"<span style=\"color:{'#f87171' if var and var > 0 else '#34d399'}\">{var:+.1f}%</span>" if var is not None else "n/d"
    a11_txt = f"{a11:,.0f} €" if a11 else "n/d"
    a24_txt = f"{a24:,.0f} €" if a24 else "n/d"
    serie_ld = ""
    if serie:
        serie_ld = "<div style=\"font-size:0.8em;color:#8993a8;margin-top:4px;\">" + " · ".join(
            f"{a}: {s['alquiler_mensual']:,.0f}€" for a, s in serie.items()) + "</div>"
    trs.append(f"""<details style="border:1px solid #232b3d;border-radius:8px;padding:10px 14px;margin:6px 0;background:#0e1322;">
<summary style="cursor:pointer;font-weight:600;">{nombre} <span style="color:#ffb454;margin-left:8px;">{a11_txt} → {a24_txt}</span> <span style="margin-left:8px;">{var_txt}</span></summary>{serie_ld}
</details>""")
    itemlist.append({"@type": "ListItem", "position": i, "name": nombre,
                     "url": f"{SITE}/#c{cod}"})

rows_html = "\n".join(trs)

ld = {"@context": "https://schema.org", "@graph": [
    {"@type": "WebSite", "name": "Alquimetría", "url": SITE, "inLanguage": "es",
     "description": "Evolución del precio del alquiler por comunidad autónoma en España (2011-2024), datos oficiales SERPAVI."},
    {"@type": "Dataset", "name": "Precio del alquiler por CCAA (SERPAVI 2011-2024)",
     "description": "Cuantía mensual del alquiler por comunidad autónoma, mediana, datos oficiales del Ministerio de Vivienda.",
     "url": SITE, "inLanguage": "es",
     "creator": {"@type": "Organization", "name": "Alquimetría", "url": SITE}},
    {"@type": "ItemList", "itemListElement": itemlist},
]}

html = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Alquimetría · Precio del alquiler por comunidad autónoma (2011-2024) | Viaje Inteligencia</title>
<meta name="description" content="Evolución del precio del alquiler en España por comunidad autónoma: cuánto subió cada región entre 2011 y 2024. Datos oficiales del Ministerio de Vivienda (SERPAVI), sin registro.">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{SITE}/">
<meta property="og:type" content="website">
<meta property="og:title" content="Alquimetría · El precio del alquiler por comunidad autónoma">
<meta property="og:description" content="Cuánto ha subido el alquiler en tu comunidad (2011-2024). Datos oficiales SERPAVI.">
<meta property="og:locale" content="es_ES">
<meta property="og:image" content="{SITE}/og.png">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">
{json.dumps(ld, ensure_ascii=False, indent=1)}
</script>
<style>
body {{ font-family: -apple-system, 'Inter', sans-serif; background: #0b0f17; color: #e7ebf3; max-width: 860px; margin: 0 auto; padding: 24px; line-height: 1.6; }}
h1 {{ font-size: 1.6em; margin-bottom: 4px; }} .sub {{ color: #8993a8; font-size: 0.95em; }}
a {{ color: #67e8f9; }} .fuente {{ font-size: 0.75em; color: #576076; margin-top: 24px; border-top: 1px solid #232b3d; padding-top: 12px; }}
</style>
</head>
<body>
<h1>🏠 Alquimetría · El precio del alquiler por comunidad autónoma</h1>
<p class="sub">Cuánto ha subido el alquiler en cada región de España, 2011 → 2024. Datos oficiales del Ministerio de Vivienda (SERPAVI).</p>
<p style="font-size:0.8em;color:#8993a8;">Ordenado por subida: las comunidades donde más ha subido el alquiler primero.</p>
{rows_html}
<p class="fuente">Fuente: Ministerio de Vivienda y Agenda Urbana — SERPAVI (sistema estatal de precios de alquiler). Mediana de la cuantía mensual del alquiler. Dato de 2026-03. · <a href="https://www.viajeinteligencia.com/">Viaje Inteligencia</a></p>
</body>
</html>
"""
OUT.write_text(html, encoding="utf-8")
print(f"OK: {OUT} ({len(rows)} CCAA)")
