"""
publicador.py — Genera artículos con Claude y los sube a GitHub/Netlify
Uso: python publicador.py
     python publicador.py --web hogar
     python publicador.py --web hogar --lang es
"""

import re
import json
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

import requests
from config import ANTHROPIC_API_KEY, WEBS, ARTICULOS_POR_WEB, MODELO

def ok(msg):    print(f"  ✅ {msg}")
def info(msg):  print(f"  ℹ️  {msg}")
def err(msg):   print(f"  ❌ {msg}")
def titulo(msg): print(f"\n{'='*55}\n  {msg}\n{'='*55}")

# ── Claude API ────────────────────────────────────────────────
def llamar_claude(prompt: str) -> str:
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": MODELO,
            "max_tokens": 8000,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["content"][0]["text"]

# ── Generar artículo ──────────────────────────────────────────
def generar_articulo(nicho: str, idioma: str, articulos_existentes: list) -> dict:
    lang_name = "español" if idioma == "es" else "English"
    evitar = ", ".join(articulos_existentes[-20:]) if articulos_existentes else "ninguno"

    prompt = f"""Eres un experto con más de 10 años de experiencia práctica en {nicho}. Escribes contenido profundo, honesto y útil basado en experiencia real.

Genera un artículo completo en {lang_name} siguiendo estas instrucciones al pie de la letra:

KEYWORD Y TEMA:
- Elige una keyword de cola larga muy específica con intención de búsqueda clara (informacional o transaccional)
- Que tenga buen CPC (mínimo 0.5€) y baja-media competencia
- NO repitas estos temas ya publicados: {evitar}

ESTRUCTURA OBLIGATORIA DEL ARTÍCULO (1500-2000 palabras):
1. Introducción con el problema que resuelve (2-3 párrafos, incluye keyword en el primero)
2. Al menos 4 secciones H2 con contenido detallado
3. Subsecciones H3 donde sea relevante
4. Una sección H2 llamada "Errores comunes que debes evitar" con lista de errores reales
5. Una sección H2 de preguntas frecuentes (FAQ) con 4-5 preguntas y respuestas concretas
6. Conclusión con llamada a la acción

REQUISITOS DE CALIDAD:
- Datos concretos, cifras y ejemplos reales donde sea posible
- Lenguaje natural, como si lo escribiera una persona experta
- Incluir consejos que solo alguien con experiencia real sabría
- Listas con al menos 3-5 puntos donde uses ul/li
- Negritas en los conceptos más importantes con <strong>

Responde ÚNICAMENTE con un JSON válido (sin markdown, sin explicaciones), con esta estructura exacta:
{{
  "titulo": "Título del artículo optimizado para SEO (con keyword principal)",
  "slug": "titulo-en-minusculas-con-guiones-sin-acentos",
  "descripcion": "Meta description de 150 caracteres máximo que incite al clic",
  "keyword": "keyword principal de cola larga",
  "categoria": "categoría del artículo",
  "autor": "nombre ficticio realista de experto en el tema",
  "extracto": "Resumen del artículo en 2 frases que expliquen el valor para el lector",
  "contenido_html": "<article>...contenido completo en HTML con h2, h3, p, ul, li, strong...</article>"
}}"""

    respuesta = llamar_claude(prompt)
    respuesta = re.sub(r"^```json\s*", "", respuesta.strip())
    respuesta = re.sub(r"\s*```$", "", respuesta.strip())
    return json.loads(respuesta)

# ── HTML del artículo ─────────────────────────────────────────
def construir_html_articulo(articulo: dict, web: dict, idioma: str) -> str:
    nombre_web = web["nombre_es"] if idioma == "es" else web["nombre_en"]
    otro_idioma = "en" if idioma == "es" else "es"
    fecha = datetime.now().strftime("%d/%m/%Y" if idioma == "es" else "%B %d, %Y")
    volver = "← Inicio" if idioma == "es" else "← Home"

    return f"""<!DOCTYPE html>
<html lang="{idioma}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{articulo['titulo']} — {nombre_web}</title>
<meta name="description" content="{articulo['descripcion']}">
<meta name="keywords" content="{articulo['keyword']}">
<meta property="og:title" content="{articulo['titulo']}">
<meta property="og:description" content="{articulo['descripcion']}">
<meta property="og:type" content="article">
<link rel="alternate" hreflang="{otro_idioma}" href="../{otro_idioma}/{articulo['slug']}.html">
<link rel="canonical" href="{articulo['slug']}.html">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<!-- <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXX" crossorigin="anonymous"></script> -->
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{--serif:'Playfair Display',Georgia,serif;--sans:'DM Sans',system-ui,sans-serif;--ink:#1a1815;--ink-2:#5a5650;--ink-3:#9a9590;--accent:#c8622a;--border:#e8e4de;--bg:#fdfcfa}}
body{{font-family:var(--sans);background:var(--bg);color:var(--ink);font-size:17px;line-height:1.75;font-weight:300}}
nav{{background:white;border-bottom:1px solid var(--border);padding:0 clamp(1rem,5vw,4rem);display:flex;align-items:center;justify-content:space-between;height:60px;position:sticky;top:0;z-index:100}}
.nav-logo{{font-family:var(--serif);font-size:1.1rem;font-weight:600;color:var(--ink);text-decoration:none}}
.nav-logo span{{color:var(--accent)}}
.back{{font-size:.85rem;color:var(--accent);text-decoration:none;font-weight:500}}
.back:hover{{text-decoration:underline}}
.ad-banner{{background:#f9f6f1;border:1px dashed var(--border);height:90px;display:flex;align-items:center;justify-content:center;color:var(--ink-3);font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;margin:0 clamp(1rem,5vw,4rem) 1.5rem}}
main{{max-width:760px;margin:0 auto;padding:2.5rem clamp(1rem,5vw,2rem) 4rem}}
.art-meta{{font-size:.78rem;color:var(--ink-3);margin-bottom:1.5rem;display:flex;gap:1rem;align-items:center;flex-wrap:wrap}}
.art-cat{{background:#f0e0d4;color:var(--accent);padding:.2rem .6rem;border-radius:2rem;font-weight:500;font-size:.72rem;letter-spacing:.06em;text-transform:uppercase}}
h1{{font-family:var(--serif);font-size:clamp(1.8rem,4vw,2.6rem);font-weight:600;line-height:1.18;letter-spacing:-.01em;margin-bottom:1.25rem}}
article h2{{font-family:var(--serif);font-size:1.45rem;font-weight:600;margin:2.25rem 0 .85rem;line-height:1.25}}
article h3{{font-family:var(--serif);font-size:1.15rem;font-weight:600;margin:1.75rem 0 .65rem}}
article p{{margin-bottom:1.25rem;color:var(--ink-2)}}
article ul,article ol{{margin:0 0 1.25rem 1.5rem}}
article li{{margin-bottom:.4rem;color:var(--ink-2)}}
article strong{{color:var(--ink);font-weight:500}}
.ad-mid{{background:#f9f6f1;border:1px dashed var(--border);height:250px;display:flex;align-items:center;justify-content:center;color:var(--ink-3);font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;margin:2.5rem 0;border-radius:2px}}
footer{{background:#1a1815;color:rgba(255,255,255,.45);padding:2rem clamp(1rem,5vw,4rem);text-align:center;font-size:.8rem}}
footer a{{color:rgba(255,255,255,.4);text-decoration:none;margin:0 .75rem}}
footer a:hover{{color:white}}
@media(max-width:600px){{main{{padding:1.5rem 1rem 3rem}}}}
</style>
</head>
<body>
<nav>
  <a href="../{idioma}/index.html" class="nav-logo">{nombre_web}</a>
  <a href="../{idioma}/index.html" class="back">{volver}</a>
</nav>
<div class="ad-banner">
  <!-- <ins class="adsbygoogle" style="display:block" data-ad-client="ca-pub-XXXXXXXX" data-ad-slot="XXXXXXXX" data-ad-format="auto"></ins><script>(adsbygoogle=window.adsbygoogle||[]).push({{}})</script> -->
  <span>Publicidad</span>
</div>
<main>
  <div class="art-meta">
    <span class="art-cat">{articulo['categoria']}</span>
    <span>{fecha}</span>
    <span>·</span>
    <span>Por <strong>{articulo.get('autor', 'Equipo editorial')}</strong></span>
  </div>
  <h1>{articulo['titulo']}</h1>
  <p class="art-intro">{articulo.get('extracto', '')}</p>
  <div class="ad-mid">
    <!-- <ins class="adsbygoogle" style="display:block;width:300px;height:250px" data-ad-client="ca-pub-XXXXXXXX" data-ad-slot="XXXXXXXX"></ins><script>(adsbygoogle=window.adsbygoogle||[]).push({{}})</script> -->
    <span>Publicidad</span>
  </div>
  {articulo['contenido_html']}
</main>
<footer>
  <p>© 2025 {nombre_web} · <a href="../{idioma}/index.html">Inicio</a> · <a href="#">Privacidad</a> · <a href="#">Aviso legal</a></p>
</footer>
</body>
</html>"""

# ── Inyectar artículos en el index original ───────────────────
def inyectar_articulos(ruta_web: str, web: dict, idioma: str, historial: list):
    index_path = Path(ruta_web) / idioma / "index.html"
    if not index_path.exists():
        err(f"No existe index.html en {ruta_web}/{idioma}/")
        return

    content = index_path.read_text(encoding="utf-8")

    START = "<!-- ARTICULOS_START -->"
    END   = "<!-- ARTICULOS_END -->"

    if START not in content:
        err(f"No se encontraron marcadores en {idioma}/index.html — asegúrate de usar los index actualizados")
        return

    ver_mas = "Leer artículo →" if idioma == "es" else "Read article →"

    # Construir tarjetas con el estilo original de cada web
    articulos_recientes = list(reversed(historial))[:20]
    cards_html = ""
    for art in articulos_recientes:
        extracto = art.get("extracto", "")
        categoria = art.get("categoria", "")
        fecha = art.get("fecha", "")[:10]
        cards_html += f"""
      <a href="{art['slug']}.html" class="article-card">
        <div class="article-thumb">📄</div>
        <div>
          <p class="article-tag">{categoria}</p>
          <h3 class="article-title">{art['titulo']}</h3>
          <p class="article-excerpt">{extracto}</p>
          <p class="article-meta">{fecha} · {ver_mas}</p>
        </div>
      </a>"""

    nuevo = f"\n      {START}\n{cards_html}\n      {END}"
    new_content = re.sub(
        rf"{re.escape(START)}.*?{re.escape(END)}",
        nuevo,
        content,
        flags=re.DOTALL,
    )

    index_path.write_text(new_content, encoding="utf-8")
    ok(f"index.html actualizado con {len(articulos_recientes)} artículo(s)")

# ── Historial ─────────────────────────────────────────────────
def cargar_historial(ruta_web: str, idioma: str) -> list:
    path = Path(ruta_web) / f"historial_{idioma}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return []

def guardar_historial(ruta_web: str, idioma: str, historial: list):
    path = Path(ruta_web) / f"historial_{idioma}.json"
    path.write_text(json.dumps(historial, ensure_ascii=False, indent=2), encoding="utf-8")

# ── Git push ──────────────────────────────────────────────────
def git_push(ruta_web: str, mensaje: str):
    try:
        subprocess.run(["git", "add", "."], cwd=ruta_web, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", mensaje], cwd=ruta_web, check=True, capture_output=True)
        subprocess.run(["git", "push"], cwd=ruta_web, check=True, capture_output=True)
        ok("Git push OK → Netlify desplegará en ~30 segundos")
    except subprocess.CalledProcessError as e:
        err(f"Error en git: {e.stderr.decode()}")

# ── Procesar web + idioma ─────────────────────────────────────
def procesar(nombre_web: str, web: dict, idioma: str):
    ruta = web["ruta"]
    carpeta_idioma = Path(ruta) / idioma

    if not carpeta_idioma.exists():
        err(f"No existe la carpeta {carpeta_idioma}")
        return

    historial = cargar_historial(ruta, idioma)
    slugs_existentes = [a["slug"] for a in historial]

    for i in range(ARTICULOS_POR_WEB):
        info(f"Generando artículo {i+1}/{ARTICULOS_POR_WEB} ({idioma.upper()})...")
        try:
            articulo = generar_articulo(web["nicho"], idioma, slugs_existentes)
            html = construir_html_articulo(articulo, web, idioma)

            slug = articulo["slug"]
            archivo = carpeta_idioma / f"{slug}.html"
            archivo.write_text(html, encoding="utf-8")
            ok(f"Artículo creado: {idioma}/{slug}.html")
            ok(f"Título: {articulo['titulo']}")

            historial.append({
                "slug": slug,
                "titulo": articulo["titulo"],
                "extracto": articulo.get("extracto", ""),
                "categoria": articulo.get("categoria", ""),
                "fecha": datetime.now().isoformat(),
                "idioma": idioma,
            })
            slugs_existentes.append(slug)

        except json.JSONDecodeError as e:
            err(f"Claude no devolvió JSON válido: {e}")
        except Exception as e:
            err(f"Error generando artículo: {e}")

    guardar_historial(ruta, idioma, historial)

    # Inyectar artículos en el index original manteniendo el diseño
    inyectar_articulos(ruta, web, idioma, historial)

    fecha_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    git_push(ruta, f"Auto: {ARTICULOS_POR_WEB} artículo(s) {idioma.upper()} [{fecha_str}]")

# ── Main ──────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--web", choices=list(WEBS.keys()))
    parser.add_argument("--lang", choices=["es", "en"])
    args = parser.parse_args()

    webs_a_procesar = {args.web: WEBS[args.web]} if args.web else WEBS
    idiomas = [args.lang] if args.lang else ["es", "en"]

    titulo("PUBLICADOR AUTOMÁTICO — Inicio")
    print(f"  Webs: {list(webs_a_procesar.keys())}")
    print(f"  Idiomas: {idiomas}")
    print(f"  Artículos por web/idioma: {ARTICULOS_POR_WEB}")

    for nombre, web in webs_a_procesar.items():
        titulo(f"Web: {nombre.upper()}")
        for idioma in idiomas:
            info(f"Procesando idioma: {idioma.upper()}")
            procesar(nombre, web, idioma)

    titulo("PROCESO COMPLETADO")
    print("  Netlify desplegará los cambios en ~1 minuto.\n")

if __name__ == "__main__":
    main()
