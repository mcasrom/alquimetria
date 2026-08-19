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

medios = [r[2] for r in rows if r[2]]
medios24 = [r[3] for r in rows if r[3]]
media11 = sum(medios) / len(medios)
media24 = sum(medios24) / len(medios24)
media_var = (media24 - media11) / media11 * 100
max_var = max(r[4] for r in rows if r[4] is not None)
max_var_row = max((r for r in rows if r[4] is not None), key=lambda r: r[4])
max24 = max((r for r in rows if r[3]), key=lambda r: r[3])
min24 = min((r for r in rows if r[3]), key=lambda r: r[3])

def sparkline(serie, w=180, h=40):
    vals = [v["alquiler_mensual"] for a, v in serie.items()]
    if len(vals) < 2:
        return ""
    lo, hi = min(vals), max(vals)
    rng = (hi - lo) or 1
    pts = []
    for i, v in enumerate(vals):
        x = i / (len(vals) - 1) * w
        y = h - 4 - (v - lo) / rng * (h - 8)
        pts.append(f"{x:.1f},{y:.1f}")
    color = "#f87171" if vals[-1] >= vals[0] else "#34d399"
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" style="vertical-align:middle;">'
            f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" stroke-width="2"/>'
            f'<circle cx="{w:.1f}" cy="{pts[-1].split(",")[1]}" r="3" fill="{color}"/></svg>')

def bar(pct, maxp):
    w = max(2, int(pct / maxp * 100)) if maxp else 2
    return f'<div style="height:8px;background:#f87171;border-radius:4px;width:{w}%;max-width:100%;"></div>'

cards = []
for cod, nombre, a11, a24, var, serie in sorted(rows, key=lambda r: -(r[4] if r[4] is not None else -999)):
    var_txt = f"<b style=\"color:{'#f87171' if var and var > 0 else '#34d399'}\">{var:+.1f}%</b>" if var is not None else "n/d"
    a11_txt = f"{a11:,.0f} €" if a11 else "n/d"
    a24_txt = f"{a24:,.0f} €" if a24 else "n/d"
    bar_html = bar(var, max_var) if var is not None else ""
    cards.append(f"""<details id="c{cod}" style="border:1px solid #232b3d;border-radius:10px;padding:12px 16px;margin:8px 0;background:#0e1322;">
<summary style="cursor:pointer;display:flex;flex-wrap:wrap;align-items:center;gap:12px;font-weight:600;">
  <span style="min-width:190px;">{nombre}</span>
  <span style="color:#8993a8;font-size:0.9em;">{a11_txt} → <b>{a24_txt}</b></span>
  <span>{var_txt}</span>
  <span style="flex:1;min-width:60px;">{bar_html}</span>
</summary>
<div style="margin-top:10px;display:flex;align-items:center;gap:16px;flex-wrap:wrap;">
  {sparkline(serie)}
  <div style="font-size:0.8em;color:#8993a8;">{serie and " · ".join(f"{a}: {v['alquiler_mensual']:,.0f}€" for a, v in serie.items()) or ""}</div>
</div>
</details>""")

cards_html = "\n".join(cards)

ld = {"@context": "https://schema.org", "@graph": [
    {"@type": "WebSite", "name": "Alquimetría", "url": SITE, "inLanguage": "es",
     "description": "Evolución del precio del alquiler por comunidad autónoma en España (2011-2024), datos oficiales SERPAVI del Ministerio de Vivienda."},
    {"@type": "Dataset", "name": "Precio del alquiler por CCAA (SERPAVI 2011-2024)",
     "description": "Cuantía mensual del alquiler (mediana) por comunidad autónoma. Serie definitiva 2011-2024, fuente oficial SERPAVI (Ministerio de Vivienda y Agenda Urbana).",
     "url": SITE, "inLanguage": "es", "temporalCoverage": "2011/2024",
     "creator": {"@type": "Organization", "name": "Alquimetría", "url": SITE}},
]}

html = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Alquimetría · Evolución del alquiler por comunidad autónoma 2011-2024 | Viaje Inteligencia</title>
<meta name="description" content="Cuánto ha subido el alquiler en cada comunidad autónoma: ranking, gráficos y evolución 2011-2024. Datos oficiales SERPAVI del Ministerio de Vivienda, con metodología y fuentes.">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{SITE}/">
<meta property="og:type" content="website">
<meta property="og:title" content="Alquimetría · La subida del alquiler por comunidad autónoma">
<meta property="og:description" content="Cuánto ha subido el alquiler en tu región (2011-2024). Datos oficiales SERPAVI.">
<meta property="og:locale" content="es_ES">
<meta property="og:image" content="{SITE}/og.png">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">
{json.dumps(ld, ensure_ascii=False, indent=1)}
</script>
<style>
body {{ font-family: -apple-system, 'Inter', sans-serif; background: #0b0f17; color: #e7ebf3; max-width: 900px; margin: 0 auto; padding: 24px; line-height: 1.6; }}
h1 {{ font-size: 1.6em; margin-bottom: 4px; }} .sub {{ color: #8993a8; }}
a {{ color: #67e8f9; }}
.kpis {{ display: grid; grid-template-columns: repeat(auto-fit,minmax(190px,1fr)); gap: 10px; margin: 18px 0; }}
.kpi {{ background: #0e1322; border: 1px solid #232b3d; border-radius: 10px; padding: 14px; }}
.kpi .n {{ font-size: 1.5em; font-weight: 700; color: #ffb454; }} .kpi .l {{ font-size: 0.75em; color: #8993a8; }}
.note {{ font-size: 0.8em; color: #8993a8; background:#0e1322; border:1px solid #232b3d; border-radius:8px; padding:10px 14px; margin:14px 0; }}
.fuente {{ font-size: 0.75em; color: #576076; margin-top: 24px; border-top: 1px solid #232b3d; padding-top: 12px; }}
</style>
</head>
<body>
<h1>🏠 Alquimetría · La subida del alquiler por comunidad autónoma</h1>
<p class="sub">Serie oficial 2011-2024 · datos del Ministerio de Vivienda (SERPAVI) · mediana de la cuantía mensual, vivienda colectiva</p>

<div class="kpis">
  <div class="kpi"><div class="n">{media_var:+.1f}%</div><div class="l">subida media España (CCAA), 2011→2024 ({media11:,.0f} € → {media24:,.0f} €)</div></div>
  <div class="kpi"><div class="n">{max_var:+.1f}%</div><div class="l">mayor subida: {max_var_row[1]}</div></div>
  <div class="kpi"><div class="n">{max24[3]:,.0f} €</div><div class="l">alquiler más alto 2024: {max24[1]}</div></div>
  <div class="kpi"><div class="n">{min24[3]:,.0f} €</div><div class="l">alquiler más bajo 2024: {min24[1]}</div></div>
</div>

<div class="note">⚠️ <b>Último dato definitivo: 2024.</b> La estadística oficial SERPAVI se publica con desfase anual (el definitivo de 2025 aún no está publicado por el Ministerio). Esta página se actualiza cuando el organismo lo publica. Los precios de mercado han seguido subiendo desde 2024; aquí solo se muestran cifras oficiales verificables.</div>

<p style="font-size:0.85em;color:#8993a8;">Ranking por subida (2011 → 2024):</p>
{cards_html}

<div class="fuente">
<b>Metodología y fuentes:</b> datos oficiales del <a href="https://www.mivau.gob.es/arquitectura-vivienda-y-suelo/vivienda-en-alquiler" rel="noopener">Ministerio de Vivienda y Agenda Urbana — SERPAVI</a> (Sistema Estatal de Precios de Referencia del Alquiler). Se usa la <b>mediana de la cuantía mensual del alquiler (€/mes)</b> de <b>vivienda colectiva</b> (ALQTBID12_M_VC), por comunidad autónoma, años 2011-2024. La mediana evita distorsiones de pisos extremos. La media nacional es la media simple de las 19 comunidades y ciudades autónomas. Cifras en euros corrientes.
<br><br>© <a href="https://www.viajeinteligencia.com/">Viaje Inteligencia</a> · contacto: <a href="mailto:nearme@viajeinteligencia.com">nearme@viajeinteligencia.com</a>
</div>
</body>
</html>
"""
OUT.write_text(html, encoding="utf-8")
print(f"OK: {OUT} · media España {media_var:+.1f}% · max {max_var_row[1]} {max_var:+.1f}%")
