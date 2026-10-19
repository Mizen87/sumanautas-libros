#!/usr/bin/env python3
"""LA WEB DE LA BIBLIOTECA de Sumanautas → https://mizen87.github.io/sumanautas-libros/ (publicidad del juego).

[19-oct-2026, el dueño: «una página web con todos los cuentos que hay en el juego; así sería publicidad, con mis enlaces al
juego y a mi página web»]. Lee catalogo.json y cada libros/<id>/libro.json y escribe:
  · index.html               la portada del sitio (ES por defecto, botón ES/EN): el juego, capturas y TODOS los cuentos con
                             su portada, edad, «Gratis»/«¡Nuevo!», el principio de la página 1 (una o dos frases, NO el
                             cuento), «Escuchar el principio» (libros/<id>/es_p1.mp3 o en_p1.mp3) y «Léelo entero» → App Store.
                             El CSS (web/estilo.css) y el JS (web/app.js) van DENTRO: se editan allí y se vuelve a ejecutar.
  · web/portadas/<id>.jpg    miniaturas 480×640 (≈40 KB); solo se rehacen si la portada es más nueva (dibujos rehechos).
  · web/og.jpg               1200×630 para compartir (WhatsApp, X, Facebook…): mosaico de portadas + icono + «N cuentos».
  · web/icono.jpg, icono-180.png, favicon.png y web/capturas/*.jpg   solo si faltan (del repo del juego).
«Gratis» = como el juego (TiendaCuentos.DePago): los de regalo y los de antes del 8-oct-2026. «¡Nuevo!» = los de la última tanda.
NUNCA nombra Android ni Google Play. No toca privacidad.html ni soporte.html (los enlaza el App Store), ni hace git.

Uso:  python3 web/genera_web.py        (cada lunes, después de genera_libro.py: ver «publica» en genera_libro.py)"""
import datetime, glob, hashlib, html, io, json, os, re, sys, urllib.parse
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

WEB = os.path.dirname(os.path.abspath(__file__))
BIB = os.path.dirname(WEB)
JUEGO = os.path.expanduser("~/Desktop/Sumanautas/Sumanautas-Unity")
ICONO = os.path.join(JUEGO, "herramientas", "icono", "icono_1024.png")
CAPTURAS_DE = os.path.join(JUEGO, "herramientas", "tienda_appstore", "tienda_final", "es-ES", "mac")
FUENTE = "/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf"

SITIO = "https://mizen87.github.io/sumanautas-libros/"
APP_ID = "6820056090"
APP_STORE = f"https://apps.apple.com/app/id{APP_ID}"
JUCABIME = "https://jucabime.com"
CORTE = "2026-10-08"          # TiendaCuentos.Corte: desde ese día, los cuentos nuevos van a la tienda del castillo (puntos)

TRAMOS = {   # id: (es, en, edades es, edades en, emoji) — como en el juego (Textos.cs: tramo_*)
    "peques":       ("Peques", "Little ones", "4-6 años", "Ages 4-6", "🐣"),
    "exploradores": ("Exploradores", "Explorers", "7-10 años", "Ages 7-10", "🧭"),
    "aventureros":  ("Aventureros", "Adventurers", "11-15 años", "Ages 11-15", "🚀"),
    "maestros":     ("Maestros", "Masters", "16+ años", "Ages 16+", "🎓"),
}
ORDEN_TRAMO = list(TRAMOS)
CHIPS = [("🔢", "Mates", "Math"), ("📚", "Cuentos nuevos cada semana", "New stories every week"),
         ("🤖", "Robótica", "Robotics"), ("🎵", "Música", "Music"), ("💬", "Inglés", "English"),
         ("🧑‍🚀", "Carné de astronauta", "Astronaut card"), ("🌙", "La Luna y Marte", "The Moon and Mars")]
# (archivo de tienda_final/es-ES/mac, nombre en web/capturas, pie es, pie en): las de Mac SIN su título (se recorta el juego)
CAPTURAS = [("01_01_pueblo.png", "pueblo", "Explora Puerto Suma", "Explore Puerto Suma"),
            ("02_05_ejercicio.png", "escuela", "Aprende paso a paso en la escuela", "Learn step by step at school"),
            ("04_06_marte_colonia.png", "marte", "Construye tu colonia en Marte", "Build your colony on Mars"),
            ("05_08_galaxia.png", "galaxia", "Viaja por el sistema solar", "Travel across the solar system")]
RECORTE_CAPTURA = (170, 308, 2710, 1735)   # el juego dentro de la captura de 2880×1800 (compone_tienda.py: banda 17 %, 16:9)
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


def e(s):
    return html.escape(str(s), quote=True)


def aviso(*a):
    print("  ⚠", *a, file=sys.stderr)


# ── lo mismo que el juego (TiendaCuentos.cs) ──
def es_fecha(s):
    return isinstance(s, str) and len(s) >= 10 and s[4] == "-" and s[7] == "-" and (s[:4] + s[5:7] + s[8:10]).isdigit()


def fecha_de(b):
    return b["fecha"][:10] if es_fecha(b.get("fecha")) else b["id"][:10] if es_fecha(b["id"]) else ""


def de_pago(b):
    f = fecha_de(b)
    return not b.get("gratis") and bool(f) and f >= CORTE


def orden(b):
    return fecha_de(b) or (b["publicado"][:10] if es_fecha(b.get("publicado")) else "")


# ── el principio de la página 1: la primera frase o dos (hasta ~90 letras; nunca el cuento) ──
FIN = re.compile(r'[.!?…]+[»”"’)]*\s+')
EMPIEZA = re.compile(r'—?\s?[¡¿«“"\'A-ZÁÉÍÓÚÑÜ0-9]')


def frases(t):
    t = re.sub(r"\s+", " ", t).strip()
    out, ini = [], 0
    for m in FIN.finditer(t):
        if EMPIEZA.match(t, m.end()):          # «—dijo», «cry the ducklings»: la frase sigue
            out.append(t[ini:m.end()].strip()); ini = m.end()
    if ini < len(t): out.append(t[ini:].strip())
    return [f for f in out if f]


def trozo(t, minimo=90, maximo=230):
    r, n = "", 0
    for f in frases(t):
        if r and (len(r) >= minimo or (n >= 2 and len(r) >= 50) or n >= 4 or len(r) + 1 + len(f) > maximo): break
        r = (r + " " + f).strip(); n += 1
    if len(r) > maximo:                          # una frase larguísima: se corta en una coma (o, si no, por palabras)
        corte = max(r.rfind(s, 0, maximo) for s in (", ", ": ", "; "))
        r = r[:corte] if corte > 100 else r[:maximo].rsplit(" ", 1)[0].rstrip(",;:—-")
    if r.endswith("…") or (r.endswith(".") and not r.endswith("..")): r = r[:-1]   # la web pone «…» detrás (CSS)
    return r


def fecha_bonita(f):
    d = datetime.date.fromisoformat(f[:10])
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}", f"{MONTHS[d.month - 1]} {d.day}, {d.year}"


# ── imágenes ──
def guarda_jpg(im, dst, objetivo, calidades=(84, 80, 76, 72, 68, 64, 60, 56, 52)):
    for q in calidades:
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=q, optimize=True, progressive=True)
        if buf.tell() <= objetivo: break
    tmp = dst + ".tmp"
    with open(tmp, "wb") as f: f.write(buf.getvalue())
    os.replace(tmp, dst)


def miniatura(src, dst):
    if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src): return False
    im = ImageOps.fit(Image.open(src).convert("RGB"), (480, 640), Image.LANCZOS)
    guarda_jpg(im, dst, 40_000)
    return True


def redondea(im, radio):
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, im.width - 1, im.height - 1], radio, fill=255)
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.paste(im.convert("RGB"), (0, 0), m)
    return out


def iconos():
    hechos = []
    faltan = [n for n in ("icono.jpg", "icono-180.png", "favicon.png") if not os.path.exists(os.path.join(WEB, n))]
    if not faltan: return hechos
    if not os.path.exists(ICONO): aviso("no encuentro el icono del juego:", ICONO); return hechos
    im = Image.open(ICONO).convert("RGB")
    for n in faltan:
        d = os.path.join(WEB, n)
        if n == "icono.jpg": guarda_jpg(im.resize((256, 256), Image.LANCZOS), d, 28_000)
        else: im.resize((180, 180) if "180" in n else (64, 64), Image.LANCZOS).save(d, "PNG", optimize=True)
        hechos.append(n)
    return hechos


def capturas():
    os.makedirs(os.path.join(WEB, "capturas"), exist_ok=True)
    hechos = []
    for src, nombre, _, _ in CAPTURAS:
        d = os.path.join(WEB, "capturas", nombre + ".jpg")
        if os.path.exists(d): continue
        s = os.path.join(CAPTURAS_DE, src)
        if not os.path.exists(s): aviso("falta la captura", s); continue
        im = Image.open(s).convert("RGB")
        if im.size != (2880, 1800): aviso("la captura no es de 2880×1800, se usa entera:", s); rec = im
        else: rec = im.crop(RECORTE_CAPTURA)
        guarda_jpg(ImageOps.fit(rec, (800, 450), Image.LANCZOS), d, 75_000)
        hechos.append(nombre)
    return hechos


def degradado(w, h, a, b):
    im = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(im)
    for y in range(h):
        t = y / (h - 1)
        d.line([(0, y), (w, y)], fill=tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3)))
    return im


def fuente(tam):
    try: return ImageFont.truetype(FUENTE, tam)
    except Exception: return ImageFont.load_default(size=tam)


def og(libros, total):
    """1200×630: a la derecha, un mosaico inclinado de portadas; a la izquierda, el icono, el nombre y «N cuentos»."""
    W, H = 1200, 630
    base = degradado(W, H, (63, 169, 245), (24, 92, 196)).convert("RGBA")
    cw, ch, hueco, cols, filas = 170, 227, 18, 5, 4
    capa = Image.new("RGBA", (cols * (cw + hueco) + hueco, filas * (ch + hueco) + ch), (0, 0, 0, 0))
    sombra = Image.new("RGBA", capa.size, (0, 0, 0, 0))
    ds = ImageDraw.Draw(sombra)
    tapas = [Image.open(os.path.join(WEB, "portadas", b["id"] + ".jpg")) for b in libros]
    k = 0
    for c in range(cols):
        baja = (c % 2) * (ch // 2) - ch // 3
        for f in range(filas):
            x, y = hueco + c * (cw + hueco), hueco + f * (ch + hueco) + baja
            t = ImageOps.fit(tapas[k % len(tapas)].convert("RGB"), (cw - 8, ch - 8), Image.LANCZOS); k += 1
            marco = Image.new("RGB", (cw, ch), (255, 255, 255)); marco.paste(t, (4, 4))
            ds.rounded_rectangle([x + 4, y + 10, x + cw + 4, y + ch + 10], 16, fill=(8, 30, 80, 110))
            capa.alpha_composite(redondea(marco, 16), (x, y))
    sombra = sombra.filter(ImageFilter.GaussianBlur(8))
    sombra.alpha_composite(capa)
    capa = sombra.rotate(9, expand=True, resample=Image.BICUBIC)
    base.alpha_composite(capa, (430, (H - capa.height) // 2))
    velo = Image.new("L", (W, H), 0)
    dv = ImageDraw.Draw(velo)
    for x in range(W):
        a = 236 if x < 470 else max(0, int(236 * (1 - (x - 470) / 190)))
        dv.line([(x, 0), (x, H)], fill=a)
    base.paste(Image.new("RGBA", (W, H), (28, 104, 206, 255)), (0, 0), velo)
    d = ImageDraw.Draw(base)
    if os.path.exists(os.path.join(WEB, "icono.jpg")):
        ic = Image.open(os.path.join(WEB, "icono.jpg")).convert("RGB").resize((132, 132), Image.LANCZOS)
        d.rounded_rectangle([60, 56, 60 + 140, 56 + 140], 34, fill=(255, 255, 255))
        base.alpha_composite(redondea(ic, 30), (64, 60))
    def texto(xy, s, tam, color, sombra=True):
        f = fuente(tam)
        if sombra: d.text((xy[0] + 3, xy[1] + 4), s, font=f, fill=(10, 40, 100))
        d.text(xy, s, font=f, fill=color)
    texto((60, 222), "Sumanautas", 78, (255, 255, 255))
    texto((62, 322), f"{total} cuentos con valores", 38, (255, 255, 255))
    texto((62, 368), "y mucho humor", 38, (255, 255, 255))
    texto((62, 428), "¡Nuevos cada semana!", 38, (255, 214, 64))
    lema = "Juego educativo 3D, sin anuncios"     # (Arial Rounded no tiene «·»)
    ancho = d.textlength(lema, font=fuente(25))
    d.rounded_rectangle([60, 506, 60 + ancho + 48, 562], 28, fill=(255, 255, 255))
    texto((84, 519), lema, 25, (24, 92, 196), sombra=False)
    guarda_jpg(base.convert("RGB"), os.path.join(WEB, "og.jpg"), 190_000, calidades=(84, 80, 76, 72))


# ── la página ──
def badge_app(clase=""):
    manzana = ('<svg viewBox="0 0 384 512" aria-hidden="true" focusable="false"><path fill="currentColor" d="M318.7 268.7c-.2-36.7 '
               '16.4-64.4 50-84.8-18.8-26.9-47.2-41.7-84.7-44.6-35.5-2.8-74.3 20.7-88.5 20.7-15 0-49.4-19.7-76.4-19.7C63.3 141.2 4 '
               '184.8 4 273.5q0 39.3 14.4 81.2c12.8 36.7 59 126.7 107.2 125.2 25.2-.6 43-17.9 75.8-17.9 31.8 0 48.3 17.9 76.4 17.9 '
               '48.6-.7 90.4-82.5 102.6-119.3-65.2-30.7-61.7-90-61.7-91.9zm-56.6-164.2c27.3-32.4 24.8-61.9 24-72.5-24.1 1.4-52 16.4-67.9 '
               '34.9-17.5 19.8-27.8 44.3-25.6 71.9 26.1 2 49.9-11.4 69.5-34.3z"/></svg>')   # glifo de Font Awesome Free (CC BY 4.0)
    return (f'<a class="appstore {clase}" href="{APP_STORE}" rel="noopener" aria-label="Descárgalo en el App Store" '
            f'data-en-aria="Download on the App Store">{manzana}<span><small data-en="Download on the">Descárgalo en el</small>'
            f'<b>App Store</b></span></a>')


def tarjeta(b, n, ultima):
    t = TRAMOS[b["tramo"]]
    sellos = []
    if orden(b) == ultima: sellos.append('<span class="sello nuevo" data-en="New!">¡Nuevo!</span>')
    if not de_pago(b):
        # ([19-oct] «Incluido», no «Gratis»: en el juego la Librería va con el desbloqueo del juego completo; así no confunde)
        sellos.append('<span class="sello gratis" title="Incluido en la Librería de Puerto Suma" '
                      'data-en-title="Included in the Puerto Suma Bookshop" data-en="Included">Incluido</span>')
    ruta = "libros/" + urllib.parse.quote(b["id"]) + "/"
    tes, ten = b["titulo"][0], b["titulo"][1] if len(b["titulo"]) > 1 else b["titulo"][0]
    oir = ""
    if "es_p1.mp3" in b.get("archivos", []) and "en_p1.mp3" in b.get("archivos", []):
        oir = (f'<button type="button" class="oir" aria-pressed="false" aria-describedby="t{n}" data-audio-es="{ruta}es_p1.mp3" '
               f'data-audio-en="{ruta}en_p1.mp3"><span class="ico" aria-hidden="true"></span>'
               f'<span class="txt">Escuchar el principio</span></button>')
    return f"""
    <li class="cuento t-{b['tramo']}" data-tramo="{b['tramo']}" id="{e(b['id'])}">
      <div class="tapa">
        <img src="web/portadas/{urllib.parse.quote(b['id'])}.jpg" width="480" height="640" loading="lazy" decoding="async" alt="Portada de «{e(tes)}»" data-en-alt="Cover of “{e(ten)}”">
        {'<div class="sellos-tapa">' + ''.join(sellos) + '</div>' if sellos else ''}
      </div>
      <div class="info">
        <p class="edad" data-en="{e(t[1])} · {e(t[3])}">{e(t[0])} · {e(t[2])}</p>
        <h3 id="t{n}" data-en="{e(ten)}">{e(tes)}</h3>
        <p class="trozo" data-en="{e(b['_trozo_en'])}">{e(b['_trozo_es'])}</p>
      </div>
      <div class="botones">
        {oir}
        <a class="leer" href="{APP_STORE}" rel="noopener" aria-describedby="t{n}"><span data-en="Read it all in Sumanautas">Léelo entero en Sumanautas</span> <span aria-hidden="true">→</span></a>
      </div>
    </li>"""


def pagina(libros, actualizado):
    total = len(libros)
    ultima = max(orden(b) for b in libros)
    cuenta = {k: sum(1 for b in libros if b["tramo"] == k) for k in TRAMOS}
    gratis = sum(1 for b in libros if not de_pago(b))
    f_es, f_en = fecha_bonita(actualizado or ultima)
    css = open(os.path.join(WEB, "estilo.css"), encoding="utf-8").read()
    js = open(os.path.join(WEB, "app.js"), encoding="utf-8").read()
    v_og = hashlib.md5(open(os.path.join(WEB, "og.jpg"), "rb").read()).hexdigest()[:8]
    abanico, vistos = [], set()             # 3 portadas de la última tanda, de edades distintas (la del medio, delante)
    for b in libros:
        if b["tramo"] not in vistos and len(abanico) < 3: abanico.append(b); vistos.add(b["tramo"])
    abanico = [abanico[1], abanico[0], abanico[2]] if len(abanico) == 3 else abanico
    titulo_es = "Sumanautas · Cuentos para niños y una aventura educativa en 3D"
    titulo_en = "Sumanautas · Stories for kids and a 3D learning adventure"
    desc_es = (f"{total} cuentos con valores y humor, narrados en español e inglés, y una aventura en 3D donde aprendes mates, "
               "robótica, música e inglés sin darte cuenta. Sin anuncios.")
    desc_en = (f"{total} stories full of values and humour, narrated in Spanish and English, and a 3D adventure where you learn "
               "math, robotics, music and English without noticing. No ads.")
    og_titulo = f"Sumanautas · {total} cuentos y una aventura en 3D para aprender"
    filtros = [f'<button type="button" data-tramo="todos" aria-pressed="true"><b data-en="All">Todos</b>'
               f'<small data-en="{total} stories">{total} cuentos</small></button>']
    for k, t in TRAMOS.items():
        filtros.append(f'<button type="button" class="t-{k}" data-tramo="{k}" aria-pressed="false"><b><span aria-hidden="true">{t[4]} </span>'
                       f'<span data-en="{e(t[1])}">{e(t[0])}</span></b><small data-en="{e(t[3])} · {cuenta[k]}">{e(t[2])} · {cuenta[k]}</small></button>')
    chips = "".join(f'<li><span aria-hidden="true">{i}</span><span data-en="{e(en)}">{e(es)}</span></li>' for i, es, en in CHIPS)
    fotos = "".join(
        f'<li><img src="web/capturas/{n}.jpg" width="800" height="450" loading="lazy" decoding="async" alt="Captura del juego: {e(es)}" '
        f'data-en-alt="Game screenshot: {e(en)}"><p data-en="{e(en)}">{e(es)}</p></li>'
        for _, n, es, en in CAPTURAS if os.path.exists(os.path.join(WEB, "capturas", n + ".jpg")))
    tapas_abanico = "".join(f'<img src="web/portadas/{urllib.parse.quote(b["id"])}.jpg" width="480" height="640" alt="" decoding="async">' for b in abanico)
    tarjetas = "".join(tarjeta(b, n, ultima) for n, b in enumerate(libros, 1))
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title data-en="{e(titulo_en)}">{e(titulo_es)}</title>
<meta name="description" content="{e(desc_es)}" data-en-content="{e(desc_en)}">
<link rel="canonical" href="{SITIO}">
<meta name="theme-color" content="#3fa9f5">
<meta name="apple-itunes-app" content="app-id={APP_ID}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Sumanautas">
<meta property="og:url" content="{SITIO}">
<meta property="og:title" content="{e(og_titulo)}">
<meta property="og:description" content="{e(desc_es)}">
<meta property="og:image" content="{SITIO}web/og.jpg?v={v_og}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Portadas de los cuentos de Sumanautas">
<meta property="og:locale" content="es_ES">
<meta property="og:locale:alternate" content="en_US">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(og_titulo)}">
<meta name="twitter:description" content="{e(desc_es)}">
<meta name="twitter:image" content="{SITIO}web/og.jpg?v={v_og}">
<link rel="icon" type="image/png" sizes="64x64" href="web/favicon.png">
<link rel="apple-touch-icon" href="web/icono-180.png">
<style>
{css}
</style>
</head>
<body>
<a class="salta" href="#biblioteca" data-en="Skip to the stories">Saltar a los cuentos</a>
<header class="cielo">
  <div class="envoltorio">
    <nav class="barra" aria-label="Sumanautas">
      <a class="marca" href="./"><img src="web/icono.jpg" width="38" height="38" alt="">Sumanautas</a>
      <a class="web" href="{JUCABIME}">jucabime.com</a>
      <div class="idioma" role="group" aria-label="Idioma" data-en-aria="Language">
        <button type="button" data-idioma="es" aria-pressed="true" lang="es" title="Español">ES</button>
        <button type="button" data-idioma="en" aria-pressed="false" lang="en" title="English">EN</button>
      </div>
    </nav>
    <div class="heroe">
      <div>
        <img class="icono-grande" src="web/icono.jpg" width="96" height="96" alt="Icono de Sumanautas" data-en-alt="Sumanautas app icon">
        <h1>Sumanautas</h1>
        <p class="gancho" data-en="The 3D adventure where you learn without even noticing">La aventura en 3D donde aprendes sin darte cuenta</p>
        <ul class="chips" aria-label="Lo que hay en el juego" data-en-aria="What's in the game">{chips}</ul>
        <ul class="lemas"><li data-en="No ads">Sin anuncios</li><li data-en="From age 4 to grandparents">De 4 años a los abuelos</li></ul>
        <div class="acciones">
          {badge_app()}
          <a class="boton-claro" href="#biblioteca" data-en="See the {total} stories ↓">Ver los {total} cuentos ↓</a>
        </div>
        <p class="autor"><span data-en="A game by">Un juego de</span> <a href="{JUCABIME}">jucabime.com</a></p>
      </div>
      <div class="abanico" aria-hidden="true">{tapas_abanico}</div>
    </div>
  </div>
  <svg class="ola" viewBox="0 0 1440 56" preserveAspectRatio="none" aria-hidden="true" focusable="false"><path fill="#fff8ec" d="M0 30C240 66 480 2 720 22s480 30 720 2V56H0Z"/></svg>
</header>

<section class="juego envoltorio" aria-labelledby="h-juego">
  <h2 class="titulo-seccion" id="h-juego" data-en="Take a look inside">Así es el juego</h2>
  <ul class="carrusel">{fotos}</ul>
</section>

<main id="biblioteca" class="biblioteca envoltorio" aria-labelledby="h-bib">
  <h2 class="titulo-seccion" id="h-bib" data-en="The story library">La biblioteca de cuentos</h2>
  <p class="entradilla" data-en="{total} original stories full of values and humour, illustrated and read aloud in Spanish and English. Here is how each one begins: the rest is waiting in the game.">{total} cuentos originales con valores y humor, ilustrados y narrados en voz alta en español y en inglés. Aquí tienes el principio de cada uno: el resto te espera en el juego.</p>
  <div class="semanal"><span data-en="📬 New stories arrive every week · Updated {f_en}">📬 Cada semana llegan cuentos nuevos · Actualizado el {f_es}</span></div>
  <div class="filtros" role="group" aria-label="Filtrar por edad" data-en-aria="Filter by age">
    {''.join(filtros)}
  </div>
  <p class="contador" aria-live="polite">Mostrando {total} cuentos</p>
  <ul class="cuentos">{tarjetas}
  </ul>

  <section class="ganas" aria-labelledby="h-ganas">
    <h2 id="h-ganas" data-en="Want to know what happens next?">¿Quieres saber cómo sigue?</h2>
    <p data-en="In Sumanautas you read every story to the end, narrated aloud with the words lighting up as you go and questions at the end. And new stories arrive every week!">En Sumanautas cada cuento se lee entero, narrado en voz alta con las palabras iluminándose al leer y con preguntas al final. ¡Y cada semana llegan cuentos nuevos!</p>
    {badge_app()}
  </section>
</main>

<footer class="pie">
  <div class="envoltorio">
    <nav aria-label="Enlaces" data-en-aria="Links">
      <a href="{JUCABIME}">jucabime.com</a>
      <a href="{APP_STORE}" rel="noopener" data-en="Sumanautas on the App Store">Sumanautas en el App Store</a>
      <a href="privacidad.html" data-en="Privacy">Privacidad</a>
      <a href="soporte.html" data-en="Support">Soporte</a>
    </nav>
    <p>© {datetime.date.today().year} jucabime</p>
    <p class="marcas" data-en="Apple, the Apple logo and App Store are trademarks of Apple Inc., registered in the U.S. and other countries.">Apple, el logotipo de Apple y App Store son marcas comerciales de Apple Inc., registradas en EE. UU. y en otros países.</p>
  </div>
</footer>
<script>
{js}
</script>
</body>
</html>
""", gratis


def main():
    cat = json.load(open(os.path.join(BIB, "catalogo.json"), encoding="utf-8"))
    os.makedirs(os.path.join(WEB, "portadas"), exist_ok=True)
    libros, nuevas = [], 0
    for b in cat["libros"]:
        d = os.path.join(BIB, "libros", b["id"])
        if b.get("tramo") not in TRAMOS: aviso("tramo desconocido, no sale:", b["id"]); continue
        try: lj = json.load(open(os.path.join(d, "libro.json"), encoding="utf-8"))
        except Exception as ex: aviso("sin libro.json, no sale:", b["id"], ex); continue
        if not os.path.exists(os.path.join(d, "portada.jpg")): aviso("sin portada, no sale:", b["id"]); continue
        p1 = (lj.get("paginas") or [{}])[0]
        b = dict(b, _trozo_es=trozo(p1.get("es", "")), _trozo_en=trozo(p1.get("en", "") or p1.get("es", "")))
        nuevas += miniatura(os.path.join(d, "portada.jpg"), os.path.join(WEB, "portadas", b["id"] + ".jpg"))
        libros.append(b)
    if not libros: sys.exit("no hay libros en el catálogo")
    ids = {b["id"] for b in libros}
    for f in glob.glob(os.path.join(WEB, "portadas", "*.jpg")):     # las de libros que ya no están
        if os.path.basename(f)[:-4] not in ids: os.remove(f); print("  fuera:", os.path.basename(f))
    # los más nuevos primero (como la Librería del juego); en cada tanda, de peques a maestros
    libros.sort(key=lambda b: (b["titulo"][0].lower()))
    libros.sort(key=lambda b: ORDEN_TRAMO.index(b["tramo"]))
    libros.sort(key=orden, reverse=True)
    hechos = iconos() + capturas()
    og(libros, len(libros))
    texto, gratis = pagina(libros, cat.get("actualizado", ""))
    tmp = os.path.join(BIB, "index.html.tmp")
    with open(tmp, "w", encoding="utf-8") as f: f.write(texto)
    os.replace(tmp, os.path.join(BIB, "index.html"))
    kb = lambda ps: sum(os.path.getsize(p) for p in ps) / 1024
    port = glob.glob(os.path.join(WEB, "portadas", "*.jpg"))
    caps = glob.glob(os.path.join(WEB, "capturas", "*.jpg"))
    print(f"web: {len(libros)} cuentos ({gratis} gratis) · miniaturas nuevas: {nuevas}" + (f" · creados: {', '.join(hechos)}" if hechos else ""))
    print(f"  index.html {kb([os.path.join(BIB, 'index.html')]):.0f} KB · portadas {kb(port):.0f} KB ({len(port)}) · "
          f"capturas {kb(caps):.0f} KB · icono {kb([os.path.join(WEB, 'icono.jpg')]):.0f} KB · og.jpg {kb([os.path.join(WEB, 'og.jpg')]):.0f} KB")


if __name__ == "__main__":
    main()
