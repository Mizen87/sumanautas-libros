#!/usr/bin/env python3
"""LA WEB DE LA BIBLIOTECA de Sumanautas → https://mizen87.github.io/sumanautas-libros/ (publicidad del juego).

[19-oct-2026, el dueño: «una página web con todos los cuentos que hay en el juego; así sería publicidad, con mis enlaces al
juego y a mi página web»]. Lee catalogo.json y cada libros/<id>/libro.json y escribe:
  · index.html               la portada del sitio (ES por defecto, botón ES/EN): el juego, capturas y TODOS los cuentos con
                             su portada, edad, «Incluido»/«¡Nuevo!», el principio de la página 1 (una o dos frases),
                             «Escuchar» (libros/<id>/es_p1.mp3 o en_p1.mp3), «Leer» (→ el lector) y el App Store.
                             El CSS (web/estilo.css) y el JS (web/app.js) van DENTRO: se editan allí y se vuelve a ejecutar.
  · web/portadas/<id>.jpg    miniaturas 480×640 (≈40 KB); solo se rehacen si la portada es más nueva (dibujos rehechos).
  · web/og.jpg               1200×630 para compartir (WhatsApp, X, Facebook…): mosaico de portadas + icono + «N cuentos».
  · web/icono.jpg, icono-180.png, favicon.png y web/capturas/*.jpg   solo si faltan (del repo del juego).
  · lector.html              [19-oct, él: «no se ven las imágenes del cuento: solo se puede escuchar, tampoco leer»] EL LECTOR:
                             lector.html?id=<id>[&lang=en][#n] (URL para compartir). Portada, una hoja por página con su dibujo,
                             su texto y «Escuchar» (es_pN.mp3 / en_pN.mp3), deslizar o flechas, ES/EN y una hoja final. Estático:
                             web/lector.css y web/lector.js van dentro; los datos, en web/cuentos/<id>.json.
  · web/cuentos/<id>.json    lo que el lector puede enseñar: título, edad, nº de páginas y SOLO las páginas legibles en la web
                             (texto es/en y su dibujo, como Libro.Dibujo del juego). Sin las preguntas del final.
  · web/paginas/<id>/pN.jpg  los dibujos de esas páginas, 600×800 (≈60 KB).
ENTEROS O MUESTRA: [19-oct, él: «que se lean enteros en la web los que hay ahora, pero los que vayan saliendo a partir de
ahora, esos no»] web/enteros.json es una lista FIJA (los 40 del 19-oct-2026; este script NUNCA la amplía): los que están, enteros;
los demás, las MUESTRA primeras páginas y después «¿Quieres saber cómo sigue? Léelo entero en Sumanautas» (App Store).
«Incluido» = como el juego (TiendaCuentos.DePago): los de regalo y los de antes del 8-oct-2026. «¡Nuevo!» = la última tanda.
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
MUESTRA = 3                   # páginas que se pueden leer en la web de los cuentos que NO están en web/enteros.json
ENTEROS = os.path.join(WEB, "enteros.json")
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


def dibujo(lj, i):
    """Como Libro.Dibujo(i) del juego (Libros.cs): la página i (desde 0) enseña el último de «dibujos» que no pasa de ella
    (los dibujos se estrenan en esas páginas y las demás repiten el último); sin «dibujos», uno por página."""
    p, dib = i + 1, lj.get("dibujos") or []
    if not dib: return p
    mejor = dib[0]
    for d in dib:
        if mejor < d <= p: mejor = d
    return mejor


def enteros():
    """Los ids que la web deja leer enteros (lista FIJA del 19-oct-2026: aquí solo se lee, nunca se amplía)."""
    try: return set(json.load(open(ENTEROS, encoding="utf-8"))["ids"])
    except Exception as ex: aviso("sin web/enteros.json (todos irán con muestra):", ex); return set()


def datos_lector(b, lj, entero):
    """web/cuentos/<id>.json: SOLO lo que se puede leer en la web (enteros: todo; los demás, MUESTRA páginas). Sin preguntas."""
    pags = lj.get("paginas") or []
    arch = set(b.get("archivos", []))
    legibles = []
    for i, p in enumerate(pags if entero else pags[:MUESTRA]):
        d = dibujo(lj, i)
        legibles.append({"es": p.get("es", ""), "en": p.get("en", "") or p.get("es", ""),
                         "d": d if f"p{d}.jpg" in arch or os.path.exists(os.path.join(BIB, "libros", b["id"], f"p{d}.jpg")) else 0,
                         "audio": f"es_p{i + 1}.mp3" in arch and f"en_p{i + 1}.mp3" in arch})
    tit = b["titulo"]
    return {"id": b["id"], "titulo": [tit[0], tit[1] if len(tit) > 1 else tit[0]], "tramo": b["tramo"], "entero": entero,
            "total": len(pags), "titulo_audio": "es_titulo.mp3" in arch and "en_titulo.mp3" in arch, "paginas": legibles}


def escribe_si_cambia(ruta, texto):
    try:
        if open(ruta, encoding="utf-8").read() == texto: return False
    except FileNotFoundError: pass
    tmp = ruta + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f: f.write(texto)
    os.replace(tmp, ruta)
    return True


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


def dibujo_web(src, dst):
    if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src): return False
    im = ImageOps.fit(Image.open(src).convert("RGB"), (600, 800), Image.LANCZOS)
    guarda_jpg(im, dst, 65_000, calidades=(76, 72, 68, 64, 60, 56))
    return True


def redondea(im, radio):
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, im.width - 1, im.height - 1], radio, fill=255)
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.paste(im.convert("RGB"), (0, 0), m)
    return out


def version(n):
    """Las 8 primeras letras del md5 de web/<n> (para «?v=…»: si el archivo cambia, la dirección también)."""
    f = os.path.join(WEB, n)
    return hashlib.md5(open(f, "rb").read()).hexdigest()[:8] if os.path.exists(f) else "0"


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
    idq = urllib.parse.quote(b["id"])
    url = f"lector.html?id={idq}"
    entero = b["_entero"]
    leer_es, leer_en = ("Leer", "Read") if entero else ("Leer el principio", "Read the beginning")
    tienda_es, tienda_en = (("Más cuentos en Sumanautas", "More stories in Sumanautas") if entero
                            else ("Léelo entero en Sumanautas", "Read it all in Sumanautas"))
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
               f'<span class="txt">Escuchar</span></button>')
    return f"""
    <li class="cuento t-{b['tramo']}" data-tramo="{b['tramo']}" id="{e(b['id'])}">
      <a class="tapa" href="{url}" data-lector="{e(b['id'])}">
        <img src="web/portadas/{idq}.jpg" width="480" height="640" loading="lazy" decoding="async" alt="Leer «{e(tes)}»" data-en-alt="Read “{e(ten)}”">
        {'<span class="sellos-tapa">' + ''.join(sellos) + '</span>' if sellos else ''}
      </a>
      <div class="info">
        <p class="edad" data-en="{e(t[1])} · {e(t[3])}">{e(t[0])} · {e(t[2])}</p>
        <h3 id="t{n}"><a href="{url}" data-lector="{e(b['id'])}" data-en="{e(ten)}">{e(tes)}</a></h3>
        <p class="trozo" data-en="{e(b['_trozo_en'])}">{e(b['_trozo_es'])}</p>
      </div>
      <div class="botones">
        <div class="fila">
          {oir}
          <a class="leer-l" href="{url}" data-lector="{e(b['id'])}" aria-describedby="t{n}"><span class="libro" aria-hidden="true"></span><span data-en="{leer_en}">{leer_es}</span></a>
        </div>
        <a class="leer" href="{APP_STORE}" rel="noopener" aria-describedby="t{n}"><span data-en="{tienda_en}">{tienda_es}</span> <span aria-hidden="true">→</span></a>
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
    v_ic = version("icono.jpg"); v_180 = version("icono-180.png"); v_fav = version("favicon.png")      # ([21-oct, él: «aún no me sale el nuevo icono»] con su versión: al cambiar, el navegador lo vuelve a bajar)
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
<link rel="icon" type="image/png" sizes="64x64" href="web/favicon.png?v={v_fav}">
<link rel="apple-touch-icon" href="web/icono-180.png?v={v_180}">
<style>
{css}
</style>
</head>
<body>
<a class="salta" href="#biblioteca" data-en="Skip to the stories">Saltar a los cuentos</a>
<header class="cielo">
  <div class="envoltorio">
    <nav class="barra" aria-label="Sumanautas">
      <a class="marca" href="./"><img src="web/icono.jpg?v={v_ic}" width="38" height="38" alt="">Sumanautas</a>
      <a class="web" href="{JUCABIME}">jucabime.com</a>
      <div class="idioma" role="group" aria-label="Idioma" data-en-aria="Language">
        <button type="button" data-idioma="es" aria-pressed="true" lang="es" title="Español"><img class="bandera" src="web/bandera_es.png" alt="" width="20" height="14">ES</button>
        <button type="button" data-idioma="en" aria-pressed="false" lang="en" title="English"><img class="bandera" src="web/bandera_gb.png" alt="" width="20" height="14">EN</button>
      </div>
    </nav>
    <div class="heroe">
      <div>
        <img class="icono-grande" src="web/icono.jpg?v={v_ic}" width="96" height="96" alt="Icono de Sumanautas" data-en-alt="Sumanautas app icon">
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
  <p class="entradilla" data-en="{total} original stories full of values and humour, illustrated and read aloud in Spanish and English. Open one to read it with its pictures and listen to it, page by page.">{total} cuentos originales con valores y humor, ilustrados y narrados en voz alta en español y en inglés. Abre uno para leerlo con sus dibujos y escucharlo página a página.</p>
  <div class="semanal"><span data-en="📬 New stories arrive every week · Updated {f_en}">📬 Cada semana llegan cuentos nuevos · Actualizado el {f_es}</span></div>
  <div class="filtros" role="group" aria-label="Filtrar por edad" data-en-aria="Filter by age">
    {''.join(filtros)}
  </div>
  <p class="contador" aria-live="polite">Mostrando {total} cuentos</p>
  <ul class="cuentos">{tarjetas}
  </ul>

  <section class="ganas" aria-labelledby="h-ganas">
    <h2 id="h-ganas" data-en="And in the game, even more!">¡Y en el juego, mucho más!</h2>
    <p data-en="In Sumanautas every story is narrated aloud with the words lighting up as you go and questions at the end, inside a 3D adventure full of things to learn. And new stories arrive every week!">En Sumanautas cada cuento se lee narrado en voz alta, con las palabras iluminándose al leer y preguntas al final, dentro de una aventura en 3D llena de cosas que aprender. ¡Y cada semana llegan cuentos nuevos!</p>
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


def lector_html():
    """lector.html: estático (lo mismo cada semana); los datos de cada cuento, en web/cuentos/<id>.json."""
    css = open(os.path.join(WEB, "lector.css"), encoding="utf-8").read()
    js = open(os.path.join(WEB, "lector.js"), encoding="utf-8").read()
    js = js.replace('"web/icono.jpg"', '"web/icono.jpg?v=' + version("icono.jpg") + '"')      # ([21-oct] la hoja final, también con su versión)
    v_og = hashlib.md5(open(os.path.join(WEB, "og.jpg"), "rb").read()).hexdigest()[:8]
    v_ic = version("icono.jpg"); v_180 = version("icono-180.png"); v_fav = version("favicon.png")      # ([21-oct, él: «aún no me sale el nuevo icono»] con su versión: al cambiar, el navegador lo vuelve a bajar)
    desc = "Lee y escucha los cuentos de Sumanautas con sus dibujos, en español y en inglés."
    return f"""<!doctype html>
<html lang="es" data-sitio="{SITIO}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Cuentos de Sumanautas</title>
<meta name="description" content="{e(desc)}">
<meta name="theme-color" content="#3fa9f5">
<meta name="apple-itunes-app" content="app-id={APP_ID}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Sumanautas">
<meta property="og:title" content="Cuentos de Sumanautas">
<meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="{SITIO}web/og.jpg?v={v_og}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="es_ES">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{SITIO}web/og.jpg?v={v_og}">
<link rel="icon" type="image/png" sizes="64x64" href="web/favicon.png?v={v_fav}">
<link rel="apple-touch-icon" href="web/icono-180.png?v={v_180}">
<style>
{css}
</style>
</head>
<body>
<header class="lbarra">
  <a class="volver" href="./"><span aria-hidden="true">←</span><img src="web/icono.jpg?v={v_ic}" width="26" height="26" alt=""><span class="t">Biblioteca</span></a>
  <p class="ltitulo" id="ltitulo">Sumanautas</p>
  <div class="idioma" role="group" aria-label="Idioma">
    <button type="button" data-idioma="es" aria-pressed="true" lang="es" title="Español"><img class="bandera" src="web/bandera_es.png" alt="" width="20" height="14">ES</button>
    <button type="button" data-idioma="en" aria-pressed="false" lang="en" title="English"><img class="bandera" src="web/bandera_gb.png" alt="" width="20" height="14">EN</button>
  </div>
</header>
<main class="hojas" id="hojas"><div class="aviso"><p>Cargando el cuento…</p></div></main>
<nav class="lpie" hidden>
  <button type="button" class="flecha ant" aria-label="Página anterior">‹</button>
  <div class="centro">
    <button type="button" class="oirp" aria-pressed="false"><span class="ico" aria-hidden="true"></span><span class="txt">Escuchar</span></button>
    <span class="num" id="num" aria-live="polite"></span>
  </div>
  <button type="button" class="flecha sig" aria-label="Página siguiente">›</button>
</nav>
<template id="badge">{badge_app()}</template>
<noscript><p class="aviso">Para leer los cuentos hace falta JavaScript. <a href="./">Volver a la biblioteca</a></p></noscript>
<script>
{js}
</script>
</body>
</html>
"""


def main():
    cat = json.load(open(os.path.join(BIB, "catalogo.json"), encoding="utf-8"))
    os.makedirs(os.path.join(WEB, "portadas"), exist_ok=True)
    libros, nuevas, dibujos_nuevos, dibujos_usados = [], 0, 0, {}
    lista_enteros = enteros()
    for d in ("cuentos", "paginas"): os.makedirs(os.path.join(WEB, d), exist_ok=True)
    for b in cat["libros"]:
        d = os.path.join(BIB, "libros", b["id"])
        if b.get("tramo") not in TRAMOS: aviso("tramo desconocido, no sale:", b["id"]); continue
        try: lj = json.load(open(os.path.join(d, "libro.json"), encoding="utf-8"))
        except Exception as ex: aviso("sin libro.json, no sale:", b["id"], ex); continue
        if not os.path.exists(os.path.join(d, "portada.jpg")): aviso("sin portada, no sale:", b["id"]); continue
        p1 = (lj.get("paginas") or [{}])[0]
        b = dict(b, _trozo_es=trozo(p1.get("es", "")), _trozo_en=trozo(p1.get("en", "") or p1.get("es", "")))
        nuevas += miniatura(os.path.join(d, "portada.jpg"), os.path.join(WEB, "portadas", b["id"] + ".jpg"))
        b["_entero"] = b["id"] in lista_enteros
        datos = datos_lector(b, lj, b["_entero"])
        escribe_si_cambia(os.path.join(WEB, "cuentos", b["id"] + ".json"), json.dumps(datos, ensure_ascii=False, separators=(",", ":")) + "\n")
        dp = os.path.join(WEB, "paginas", b["id"])
        os.makedirs(dp, exist_ok=True)
        usados = {f"p{p['d']}.jpg" for p in datos["paginas"] if p["d"]}
        for f in sorted(usados): dibujos_nuevos += dibujo_web(os.path.join(d, f), os.path.join(dp, f))
        dibujos_usados[b["id"]] = usados
        libros.append(b)
    if not libros: sys.exit("no hay libros en el catálogo")
    ids = {b["id"] for b in libros}
    for f in glob.glob(os.path.join(WEB, "portadas", "*.jpg")) + glob.glob(os.path.join(WEB, "cuentos", "*.json")):   # de libros que ya no están
        if os.path.splitext(os.path.basename(f))[0] not in ids: os.remove(f); print("  fuera:", os.path.relpath(f, WEB))
    for dp in glob.glob(os.path.join(WEB, "paginas", "*")):
        for f in glob.glob(os.path.join(dp, "*")):                  # dibujos que ya no se enseñan (libro fuera, o dibujos cambiados)
            if os.path.basename(f) not in dibujos_usados.get(os.path.basename(dp), set()): os.remove(f)
        if not os.listdir(dp): os.rmdir(dp)
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
    escribe_si_cambia(os.path.join(BIB, "lector.html"), lector_html())
    kb = lambda ps: sum(os.path.getsize(p) for p in ps) / 1024
    port = glob.glob(os.path.join(WEB, "portadas", "*.jpg"))
    caps = glob.glob(os.path.join(WEB, "capturas", "*.jpg"))
    pags = glob.glob(os.path.join(WEB, "paginas", "*", "*.jpg"))
    jsons = glob.glob(os.path.join(WEB, "cuentos", "*.json"))
    n_ent = sum(1 for b in libros if b["_entero"])
    print(f"web: {len(libros)} cuentos ({gratis} incluidos en el juego) · lector: {n_ent} enteros y {len(libros) - n_ent} con muestra de {MUESTRA} páginas"
          f" · miniaturas nuevas: {nuevas} · dibujos nuevos: {dibujos_nuevos}" + (f" · creados: {', '.join(hechos)}" if hechos else ""))
    print(f"  lector.html {kb([os.path.join(BIB, 'lector.html')]):.0f} KB · dibujos {kb(pags) / 1024:.1f} MB ({len(pags)}) · "
          f"datos {kb(jsons):.0f} KB ({len(jsons)})")
    print(f"  index.html {kb([os.path.join(BIB, 'index.html')]):.0f} KB · portadas {kb(port):.0f} KB ({len(port)}) · "
          f"capturas {kb(caps):.0f} KB · icono {kb([os.path.join(WEB, 'icono.jpg')]):.0f} KB · og.jpg {kb([os.path.join(WEB, 'og.jpg')]):.0f} KB")


if __name__ == "__main__":
    main()
