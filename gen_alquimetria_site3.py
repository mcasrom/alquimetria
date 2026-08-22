import json, re, unicodedata, os, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(os.path.join(BASE, "data", "serpavi.json")):
    DATA = os.path.join(BASE, "data", "serpavi.json")
    OUT = BASE
else:
    DATA = "/tmp/serpavi.json"
    OUT = BASE
SITE = "https://alquimetria.viajeinteligencia.com"

d = json.load(open(DATA, encoding="utf-8"))
datos = d["datos"]

def slug(s):
    s = unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

def fmt(n):
    return "—" if n is None else ("%s" % format(int(round(n)), ",").replace(",", "."))

def series(cod):
    s = datos[cod]["serie"]
    return [{"a": int(a), "v": s[a]["alquiler_mensual"]} for a in sorted(s)]

def area_svg(cod, w=700, h=150):
    s = series(cod)
    if len(s) < 2: return ""
    vs = [x["v"] for x in s]; mn, mx = min(vs), max(vs)
    pad = 8
    X = lambda i: pad + i * (w - 2 * pad) / (len(s) - 1)
    Y = lambda v: h - pad - (v - mn) * (h - 2 * pad) / (mx - mn or 1)
    pts = " ".join(f"{X(i):.1f},{Y(x['v']):.1f}" for i, x in enumerate(s))
    grad = f'<defs><linearGradient id="g{cod}" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#f87171" stop-opacity="0.5"/><stop offset="100%" stop-color="#f87171" stop-opacity="0.03"/></linearGradient></defs>'
    base_y = h - pad
    area = f"{X(0):.1f},{base_y} {pts} {X(len(s)-1):.1f},{base_y}"
    return (f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto" role="img" aria-label="Evolución del alquiler 2011-2024">{grad}'
            f'<polygon points="{area}" fill="url(#g{cod})"/><polyline points="{pts}" fill="none" stroke="#f87171" stroke-width="2"/>'
            f'<circle cx="{X(0):.1f}" cy="{Y(vs[0]):.1f}" r="3" fill="#f87171"/>'
            f'<circle cx="{X(len(s)-1):.1f}" cy="{Y(vs[-1]):.1f}" r="3" fill="#fbbf24"/></svg>')

def var_pct(cod):
    s = series(cod)
    if len(s) < 2: return None
    a, b = s[0]["v"], s[-1]["v"]
    return round((b - a) / a * 100, 1) if a else None

def tabla_serie(cod):
    s = series(cod)
    rows = ""
    for i in range(0, len(s), 2):
        a1, v1 = s[i]["a"], s[i]["v"]
        a2 = s[i+1]["a"] if i+1 < len(s) else None
        v2 = s[i+1]["v"] if i+1 < len(s) else None
        c1 = "#34d399" if v1 >= (s[i-1]["v"] if i else v1) else "#f87171"
        rows += f"<tr><td>{a1}</td><td class='r'><b>{fmt(v1)} €</b></td>"
        if a2: rows += f"<td>{a2}</td><td class='r'><b>{fmt(v2)} €</b></td>"
        rows += "</tr>"
    return rows

# ============ CSS comun ============
CSS = """
:root{--bg:#0f172a;--card:#1e293b;--fg:#e2e8f0;--mut:#94a3b8;--acc:#38bdf8;--rojo:#f87171;--verde:#34d399;--ambar:#fbbf24}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--fg);line-height:1.6}
.wrap{max-width:960px;margin:0 auto;padding:22px}
h1{font-size:26px}h2{font-size:18px;color:var(--acc);margin:24px 0 10px;border-bottom:1px solid #334155;padding-bottom:6px}
.mut{color:var(--mut);font-size:13px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px;margin:14px 0}
.kpi{background:var(--card);border-radius:10px;padding:14px}
.kpi b{display:block;font-size:21px}
.kpi span{font-size:11px;color:var(--mut)}
.pos{color:var(--verde)}.neg{color:var(--rojo)}
table{width:100%;border-collapse:collapse;font-size:13px;background:var(--card);border-radius:8px;overflow:hidden}
th{background:#0f172a;color:var(--mut);text-align:left;padding:8px 10px;font-size:11px;text-transform:uppercase}
td{padding:7px 10px;border-top:1px solid #1e293b}
td.r{text-align:right}
a{color:var(--acc)}
.aviso{background:#7f1d1d;border:1px solid #b91c1c;border-radius:10px;padding:14px 16px;margin:16px 0;font-size:0.92em}
.aviso b{color:#fca5a5}
.cta{display:inline-block;margin:6px 4px 6px 0;padding:10px 16px;border:1px solid #334155;border-radius:8px;background:#1e293b;color:var(--fg);text-decoration:none;font-size:13px}
.cta:hover{border-color:var(--acc);background:#334155}
.nav{display:flex;gap:12px;font-size:13px;margin-bottom:14px;flex-wrap:wrap}
details{border:1px solid #334155;border-radius:10px;padding:12px 16px;margin:8px 0;background:#0e1322}
summary{cursor:pointer;font-weight:600}
.src{font-size:11px;color:var(--mut);margin-top:26px;line-height:1.7;border-top:1px solid #1e293b;padding-top:12px}
.bar{height:10px;border-radius:4px;background:#0f172a;overflow:hidden;margin-top:4px}
.bar>div{height:100%;border-radius:4px}
@media (max-width:700px){.wrap{padding:14px}h1{font-size:22px}}
"""

# ============ INDEX ============
filas_rank = []
for cod, v in datos.items():
    var = var_pct(cod)
    a11 = series(cod)[0]["v"]; a24 = series(cod)[-1]["v"]
    filas_rank.append({"cod": cod, "n": v["nombre"], "a11": a11, "a24": a24, "var": var})
medios = [r["a11"] for r in filas_rank]; medios24 = [r["a24"] for r in filas_rank]
media11 = sum(medios)/len(medios); media24 = sum(medios24)/len(medios24)
media_var = (media24-media11)/media11*100
max_var = max((r["var"] for r in filas_rank if r["var"] is not None))
max_var_r = max((r for r in filas_rank if r["var"] is not None), key=lambda r: r["var"])
max24 = max(filas_rank, key=lambda r: r["a24"]); min24 = min(filas_rank, key=lambda r: r["a24"])

def bar_html(pct, color):
    if pct is None: return '<div class="bar"><div style="width:3%;background:#334155"></div></div>'
    p = max(3, int(abs(pct)/max_var*100)) if max_var else 3
    return f'<div class="bar"><div style="width:{p}%;background:{color}"></div></div>'

rank_cards = ""
for r in sorted(filas_rank, key=lambda x: -(x["var"] if x["var"] is not None else -999)):
    col = "#f87171" if r["var"] and r["var"] > 0 else "#34d399"
    var_t = f'<b style="color:{col}">{"+" if r["var"] and r["var"]>0 else ""}{r["var"]:.1f}%</b>' if r["var"] is not None else "n/d"
    rank_cards += f"""<details>
<summary style="display:flex;flex-wrap:wrap;align-items:center;gap:12px;">
  <span style="min-width:200px;"><a href="ccaa/{slug(r['n'])}.html">{r['n']}</a></span>
  <span style="color:#8993a8;font-size:0.9em;">{fmt(r['a11'])} € → <b>{fmt(r['a24'])} €</b></span>
  <span>{var_t}</span>
  <span style="flex:1;min-width:70px;">{bar_html(r['var'], col)}</span>
  <span style="font-size:0.8em;color:#38bdf8">ver ficha →</span>
</summary>
<div style="margin-top:10px">{area_svg(r['cod'], 700, 90)}</div>
</details>"""

FAQS = [
    ("¿Qué es el SERPAVI?", "El Sistema Estatal de Referencia del Precio del Alquiler de Vivienda (SERPAVI), del Ministerio de Vivienda, da la mediana de la cuantía mensual de los contratos de alquiler por zona, a partir de las fianzas del Catastro/AEAT. Es un precio orientativo para nuevos contratos."),
    ("¿Qué es el IRAV?", "El Índice de Referencia de Arrendamientos de Vivienda (IRAV), publicado por el INE desde enero de 2026, es el índice legal para actualizar la renta de los contratos existentes en zonas de mercado tensionado."),
    ("¿Cuál es la diferencia entre SERPAVI e IRAV?", "El SERPAVI orienta (precio para contratos nuevos) y el IRAV actualiza (índice legal para revisar rentas existentes). Se confunden mucho: uno referencia, el otro actualiza."),
    ("¿Qué cambió en el SERPAVI en 2026?", "La Resolución de 16 de abril de 2026 (BOE-A-2026-8691) actualizó el SERPAVI con nueva metodología y, por primera vez, cubre todas las provincias, incluidas Álava, Bizkaia y Gipuzkoa."),
    ("¿Por qué el precio de Alquimetría parece más bajo que el de los portales?", "Mostramos la mediana de TODOS los contratos (incluidos antiguos con rentas congeladas), no el precio de un inquilino nuevo. Los portales muestran nuevas contrataciones, que son más altas."),
]
faq_html = "".join(f"<details><summary>{q}</summary><div style='margin-top:8px;color:#b6c0d4;font-size:0.9em'>{a}</div></details>" for q, a in FAQS)

faq_json = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
    {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQS]}

index = f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Alquimetría · La subida del alquiler por comunidad autónoma (2011-2024) · SERPAVI</title>
<meta name="description" content="Cuánto ha subido el alquiler en cada comunidad autónoma: ranking, gráficos y evolución 2011-2024. Datos oficiales SERPAVI del Ministerio de Vivienda. Qué es SERPAVI vs IRAV.">
<link rel="canonical" href="{SITE}/">
<link rel="icon" type="image/png" href="icon-192.png">
<meta property="og:type" content="website"><meta property="og:title" content="Alquimetría · La subida del alquiler por comunidad autónoma">
<meta property="og:description" content="Cuánto ha subido el alquiler en tu región (2011-2024). Datos oficiales SERPAVI.">
<meta property="og:image" content="{SITE}/og.png">
<script type="application/ld+json">{json.dumps(faq_json, ensure_ascii=False)}</script>
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"Dataset","name":"Precio del alquiler por CCAA (SERPAVI 2011-2024)","description":"Mediana mensual del alquiler por comunidad autónoma, serie definitiva 2011-2024, SERPAVI (Ministerio de Vivienda).","url":"{SITE}/","temporalCoverage":"2011/2024","inLanguage":"es","creator":{{"@type":"Organization","name":"Alquimetría","url":"{SITE}"}}}}</script>
<style>{CSS}</style></head><body><div class="wrap">
<div class="nav"><b>Alquimetría</b> · <a href="serpavi-vs-irav.html">SERPAVI vs IRAV (qué cambia en 2026)</a> · <a href="https://municipal.viajeinteligencia.com">Población de los municipios de España</a> · <a href="https://www.viajeinteligencia.com">Ecosistema</a></div>
<h1>🏠 Alquimetría · La subida del alquiler por comunidad autónoma</h1>
<p class="mut">Serie oficial 2011-2024 · datos del Ministerio de Vivienda (SERPAVI) · mediana mensual, vivienda colectiva</p>
<div class="aviso"><b>⚠️ Esto es evolución histórica (2011-2024), no el precio de mercado de hoy.</b> El último dato definitivo es <b>2024</b>. Desde entonces los alquileres han seguido subiendo. Para el <b>precio actual</b> de tu zona, usa la app oficial del Ministerio o los portales de mercado.</div>
<div class="grid">
  <div class="kpi"><b>{media_var:+.1f}%</b><span>subida media España (CCAA), 2011→2024 ({fmt(media11)} € → {fmt(media24)} €)</span></div>
  <div class="kpi"><b>{max_var:+.1f}%</b><span>mayor subida: {max_var_r['n']}</span></div>
  <div class="kpi"><b>{fmt(max24['a24'])} €</b><span>alquiler más alto 2024: {max24['n']}</span></div>
  <div class="kpi"><b>{fmt(min24['a24'])} €</b><span>alquiler más bajo 2024: {min24['n']}</span></div>
</div>
<h2>Ranking por subida del alquiler (2011 → 2024)</h2>
{rank_cards}
<h2>¿Qué es SERPAVI y qué es el IRAV?</h2>
{faq_html}
<div style="margin-top:16px"><a class="cta" href="serpavi-vs-irav.html">Leer: SERPAVI vs IRAV, qué cambia en 2026 →</a><a class="cta" href="https://municipal.viajeinteligencia.com">Ver la población de los municipios de España →</a></div>
<div class="src">Fuente: SERPAVI (Ministerio de Vivienda y Agenda Urbana), mediana mensual vivienda colectiva (ALQTBID12_M_VC), 2011-2024 · © 2026 M. Castillo · <a href="mailto:nearme@viajeinteligencia.com">contacto</a> · datos abiertos, sin cookies.</div>
</div></body></html>"""
open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(index)
print("index.html OK", len(index)//1024, "KB")

# ============ PAGINAS POR CCAA ============
os.makedirs(os.path.join(OUT, "ccaa"), exist_ok=True)
sitemap = [f"{SITE}/", f"{SITE}/serpavi-vs-irav.html"]
for cod, v in datos.items():
    s = series(cod); var = var_pct(cod)
    a11, a24 = s[0]["v"], s[-1]["v"]
    maxa = max(s, key=lambda x: x["v"]); mina = min(s, key=lambda x: x["v"])
    var_fmt = f"{var:+.1f}%" if var is not None else "n/d"
    n = v["nombre"]; sl = slug(n)
    up = a24 >= a11
    var_txt = f"{abs(var):.1f}%" if var is not None else "n/d"
    ctx = f"El alquiler en {n} {'subió' if up else 'bajó'} un {var_txt} entre 2011 y {a24} ({fmt(a11)} € → {fmt(a24)} € mensuales). Máximo en {maxa['a']} ({fmt(maxa['v'])} €); mínimo en {mina['a']} ({fmt(mina['v'])} €)."
    page = f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Evolución del alquiler en {n} (2011-2024) · Alquimetría</title>
<meta name="description" content="Cuánto ha subido el alquiler en {n}: evolución {s[0]['a']}-{s[-1]['a']}, {fmt(a11)} € → {fmt(a24)} € mensuales ({var_fmt}). Datos oficiales SERPAVI (Ministerio de Vivienda).">
<link rel="canonical" href="{SITE}/ccaa/{sl}.html">
<link rel="icon" type="image/png" href="../icon-192.png">
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"Dataset","name":"Evolución del alquiler en {n}","description":"Serie 2011-2024, mediana mensual, SERPAVI.","url":"{SITE}/ccaa/{sl}.html","temporalCoverage":"2011/2024","inLanguage":"es"}}</script>
<style>{CSS}</style></head><body><div class="wrap">
<div class="nav"><a href="../">← Alquimetría (ranking)</a> · <a href="../serpavi-vs-irav.html">SERPAVI vs IRAV</a> · <a href="https://municipal.viajeinteligencia.com">Municipios</a></div>
<h1>🏠 Evolución del alquiler en {n}</h1>
<p class="mut">Serie oficial 2011-2024 · SERPAVI (Ministerio de Vivienda) · mediana mensual</p>
<div class="grid">
  <div class="kpi"><b>{fmt(a11)} €</b><span>2011</span></div>
  <div class="kpi"><b>{fmt(a24)} €</b><span>{s[-1]['a']}</span></div>
  <div class="kpi"><b class="{'pos' if up else 'neg'}">{"+" if var and var>0 else ""}{var_txt}</b><span>variación total</span></div>
  <div class="kpi"><b>{fmt(maxa['v'])} €</b><span>máximo ({maxa['a']})</span></div>
</div>
{area_svg(cod)}
<p style="margin:10px 0">{ctx}</p>
<h2>Serie completa</h2>
<table><tr><th>Año</th><th class="r">€/mes</th><th>Año</th><th class="r">€/mes</th></tr>{tabla_serie(cod)}</table>
<div style="margin-top:16px"><a class="cta" href="../">Ver el ranking de todas las comunidades →</a><a class="cta" href="https://municipal.viajeinteligencia.com">¿Y cuánta población tiene tu municipio? →</a></div>
<div class="src">Fuente: SERPAVI (Ministerio de Vivienda y Agenda Urbana), mediana mensual vivienda colectiva, {s[0]['a']}-{s[-1]['a']} · datos oficiales, sin cookies · © 2026 M. Castillo.</div>
</div></body></html>"""
    open(os.path.join(OUT, "ccaa", sl + ".html"), "w", encoding="utf-8").write(page)
    sitemap.append(f"{SITE}/ccaa/{sl}.html")
    print("ccaa/" + sl + ".html OK")

# ============ SERPAVI VS IRAV ============
ed = f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>SERPAVI vs IRAV: qué cambia en 2026 y cuál usar · Alquimetría</title>
<meta name="description" content="SERPAVI e IRAV son cosas distintas: el SERPAVI orienta (precio para contratos nuevos) y el IRAV actualiza (índice legal). Qué cambió con la Resolución de abril 2026.">
<link rel="canonical" href="{SITE}/serpavi-vs-irav.html">
<link rel="icon" type="image/png" href="icon-192.png">
<script type="application/ld+json">{json.dumps(faq_json, ensure_ascii=False)}</script>
<style>{CSS}</style></head><body><div class="wrap">
<div class="nav"><a href="../">← Alquimetría</a> · <a href="https://municipal.viajeinteligencia.com">Municipios</a> · <a href="https://www.viajeinteligencia.com">Ecosistema</a></div>
<h1>📊 SERPAVI vs IRAV: cuál es cuál y qué cambió en 2026</h1>
<p class="mut">La confusión entre SERPAVI e IRAV es real y reciente. Esto es lo que debes saber, sin humo.</p>
<div class="grid">
  <div class="kpi"><b>SERPAVI</b><span>Ministerio de Vivienda · precio orientativo para CONTRATOS NUEVOS</span></div>
  <div class="kpi"><b>IRAV</b><span>INE (desde enero 2026) · índice LEGAL para ACTUALIZAR contratos existentes</span></div>
</div>
<h2>La diferencia en 30 segundos</h2>
<ul style="margin:10px 0 10px 22px">
<li><b>SERPAVI</b>: te dice cuánto se cobra de media en una zona (orienta el precio de un alquiler nuevo).</li>
<li><b>IRAV</b>: es el índice oficial que limita cuánto puede subir la renta de un contrato que ya existe (zonas tensionadas).</li>
<li>Uno <b>referencia</b>, el otro <b>actualiza</b>. No son intercambiables.</li>
</ul>
<h2>Qué cambió en 2026</h2>
<ul style="margin:10px 0 10px 22px">
<li><b>Resolución de 16 de abril de 2026 (BOE-A-2026-8691)</b>: el SERPAVI actualiza su metodología y, por primera vez, cubre todas las provincias, incluidas Álava, Bizkaia y Gipuzkoa.</li>
<li><b>IRAV en vigor desde enero de 2026</b>: el INE publica el índice mensual que se aplica a la actualización de rentas en zonas tensionadas.</li>
<li>Hay mucha confusión pública documentada — esta página es la diferencia, clara.</li>
</ul>
<h2>Preguntas frecuentes</h2>
{faq_html}
<div style="margin-top:16px"><a class="cta" href="../">Ver la evolución del alquiler por comunidad →</a><a class="cta" href="https://municipal.viajeinteligencia.com">Ver la población de los municipios de España →</a></div>
<div class="src">© 2026 M. Castillo · Alquimetría usa el SERPAVI histórico (2011-2024), no el IRAV. Para el precio actual, consulta las fuentes oficiales. Sin asesoramiento legal.</div>
</div></body></html>"""
open(os.path.join(OUT, "serpavi-vs-irav.html"), "w", encoding="utf-8").write(ed)
sitemap.append(f"{SITE}/serpavi-vs-irav.html")

# ============ SITEMAP ============
sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for u in sorted(set(sitemap)):
    sm.append(f"  <url><loc>{u}</loc><lastmod>{datetime.date.today().isoformat()}</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>")
sm.append("</urlset>")
open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8").write("\n".join(sm))
print("sitemap:", len(sitemap), "URLs")
print("TOTAL: alquimetria v3 generado")
