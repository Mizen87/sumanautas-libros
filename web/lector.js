/* El LECTOR de la web: lector.html?id=<id>[&lang=en][#n]. Lee web/cuentos/<id>.json (lo escribe genera_web.py: solo las
   páginas que se pueden leer en la web) y monta una hoja por pantalla: portada, páginas con su dibujo y su texto, y al final
   «Léelo entero en Sumanautas» (muestra) o «Fin» (entero). Cada hoja se puede escuchar (es_pN.mp3 / en_pN.mp3).
   genera_web.py lo mete dentro de lector.html; se edita aquí y se vuelve a ejecutar el generador. Sin librerías. */
(function () {
  "use strict";
  var raiz = document.documentElement;
  var hojasEl = document.getElementById("hojas");
  var numEl = document.getElementById("num");
  var tituloEl = document.getElementById("ltitulo");
  var oirBtn = document.querySelector(".oirp");
  var antBtn = document.querySelector(".flecha.ant");
  var sigBtn = document.querySelector(".flecha.sig");
  var volver = document.querySelector(".volver");
  var badge = document.getElementById("badge");
  var SITIO = raiz.dataset.sitio || "";
  var TRAMOS = {
    peques: [["Peques", "4-6 años"], ["Little ones", "Ages 4-6"]],
    exploradores: [["Exploradores", "7-10 años"], ["Explorers", "Ages 7-10"]],
    aventureros: [["Aventureros", "11-15 años"], ["Adventurers", "Ages 11-15"]],
    maestros: [["Maestros", "16+ años"], ["Masters", "Ages 16+"]]
  };
  var T = {
    es: {
      bib: "Biblioteca", empezar: "Empezar a leer →", oir: "Escuchar", oirTitulo: "Escuchar el título", parar: "Parar",
      fallo: "No se ha podido oír", portada: "Portada", pagina: function (n, t) { return "Página " + n + " de " + t; },
      fin: "Fin", sigue: "Continúa en el juego", cuento: "Cuento de Sumanautas",
      paginas: function (n) { return n + " páginas"; },
      notaEntero: "¡Puedes leerlo entero aquí, con sus dibujos y su voz!",
      notaMuestra: function (n) { return "Aquí puedes leer las " + n + " primeras páginas."; },
      ganasT: "¿Quieres saber cómo sigue?",
      ganasP: function (r) { return "Te quedan " + r + (r === 1 ? " página" : " páginas") + ". Léelo entero en Sumanautas, narrado en voz alta, con las palabras iluminándose al leer y preguntas al final. ¡Y cada semana llegan cuentos nuevos!"; },
      finT: "¿Te ha gustado?",
      finP: "En Sumanautas hay muchos más cuentos, narrados en voz alta con las palabras iluminándose al leer y preguntas al final. ¡Y cada semana llegan cuentos nuevos!",
      otra: "← Elegir otro cuento", ant: "Página anterior", sig: "Página siguiente", idioma: "Idioma",
      noHay: "No encuentro ese cuento.", irBib: "Ver todos los cuentos",
      sufijo: " · Cuento de Sumanautas", badgeS: "Descárgalo en el", badgeA: "Descárgalo en el App Store"
    },
    en: {
      bib: "Library", empezar: "Start reading →", oir: "Listen", oirTitulo: "Listen to the title", parar: "Stop",
      fallo: "Couldn't play it", portada: "Cover", pagina: function (n, t) { return "Page " + n + " of " + t; },
      fin: "The end", sigue: "Continues in the game", cuento: "A Sumanautas story",
      paginas: function (n) { return n + " pages"; },
      notaEntero: "You can read the whole story here, with its pictures and narration!",
      notaMuestra: function (n) { return "Here you can read the first " + n + " pages."; },
      ganasT: "Want to know what happens next?",
      ganasP: function (r) { return (r === 1 ? "There is 1 more page" : "There are " + r + " more pages") + ". Read it all in Sumanautas, narrated aloud, with the words lighting up as you go and questions at the end. And new stories arrive every week!"; },
      finT: "Did you like it?",
      finP: "Sumanautas has many more stories, narrated aloud with the words lighting up as you go and questions at the end. And new stories arrive every week!",
      otra: "← Choose another story", ant: "Previous page", sig: "Next page", idioma: "Language",
      noHay: "I can't find that story.", irBib: "See all the stories",
      sufijo: " · A Sumanautas story", badgeS: "Download on the", badgeA: "Download on the App Store"
    }
  };
  var q = location.search;
  var id = decodeURIComponent((q.match(/[?&]id=([^&#]+)/) || [])[1] || "");
  var pedido = (q.match(/[?&]lang=(es|en)\b/) || [])[1];
  var idioma = pedido || lee("sumanautas-idioma") || "es";
  if (idioma !== "en") idioma = "es";
  var libro = null, hojas = [], actual = 0, pintores = [], raf = 0;

  function lee(k) { try { return window.localStorage.getItem(k); } catch (e) { return null; } }
  function guarda(k, v) { try { window.localStorage.setItem(k, v); } catch (e) { /* da igual */ } }
  function el(tag, clase, texto) {
    var n = document.createElement(tag);
    if (clase) n.className = clase;
    if (texto !== undefined) n.textContent = texto;
    return n;
  }
  function L() { return T[idioma]; }
  function base() { return "libros/" + encodeURIComponent(libro.id) + "/"; }
  /* un texto que cambia con el idioma: se pinta ahora y cada vez que se cambie */
  function pinta(fn) { pintores.push(fn); fn(); }

  /* ── montar el cuento ── */
  function hojaPortada() {
    var h = el("section", "hoja portada-hoja");
    var fig = el("figure", "dibujo");
    var img = el("img", "lista");
    img.src = "web/portadas/" + encodeURIComponent(libro.id) + ".jpg";
    img.width = 480; img.height = 640; img.alt = "";
    fig.appendChild(img); h.appendChild(fig);
    var cab = el("div", "cab");
    var edad = el("p", "edad"), h1 = el("h1"), nota = el("p", "nota"), nota2 = el("p", "nota");
    var empezar = el("button", "empezar");
    empezar.type = "button";
    empezar.addEventListener("click", function () { ir(1); });
    pinta(function () {
      var t = TRAMOS[libro.tramo] ? TRAMOS[libro.tramo][idioma === "en" ? 1 : 0] : ["", ""];
      edad.textContent = t[0] + " · " + t[1];
      h1.textContent = libro.titulo[idioma === "en" ? 1 : 0];
      nota.textContent = L().cuento + " · " + L().paginas(libro.total);
      nota2.textContent = libro.entero ? L().notaEntero : L().notaMuestra(libro.paginas.length);
      empezar.textContent = L().empezar;
    });
    [edad, h1, nota, nota2, empezar].forEach(function (n) { cab.appendChild(n); });
    h.appendChild(cab);
    h.dataset.audio = libro.titulo_audio ? "titulo" : "";
    return h;
  }
  function hojaPagina(p, n) {
    var h = el("section", "hoja");
    var fig = el("figure", "dibujo");
    var img = el("img");
    if (!p.d) fig.hidden = true;
    img.dataset.src = "web/paginas/" + encodeURIComponent(libro.id) + "/p" + p.d + ".jpg";
    img.width = 600; img.height = 800; img.alt = ""; img.decoding = "async";
    img.addEventListener("load", function () { img.classList.add("lista"); });
    fig.appendChild(img); h.appendChild(fig);
    var texto = el("div", "texto");
    texto.lang = idioma;
    pinta(function () {
      texto.textContent = "";
      texto.lang = idioma;
      (p[idioma] || p.es || "").split(/\n+/).forEach(function (par) { if (par.trim()) texto.appendChild(el("p", "", par.trim())); });
      h.setAttribute("aria-label", L().pagina(n, libro.total));
    });
    h.appendChild(texto);
    h.dataset.audio = p.audio ? "p" + n : "";
    return h;
  }
  function hojaFinal() {
    var h = el("section", "hoja final");
    var c = el("div", "tarjeta-final");
    var ic = el("img", "icono");
    ic.src = "web/icono.jpg"; ic.width = 84; ic.height = 84; ic.alt = "";
    var h2 = el("h2"), p = el("p");
    var b = badge ? badge.content.firstElementChild.cloneNode(true) : el("span");
    var otra = el("a", "otra");
    otra.href = "./" + (idioma === "en" ? "?lang=en" : "") + "#" + encodeURIComponent(libro.id);
    var resto = libro.total - libro.paginas.length;
    pinta(function () {
      h2.textContent = libro.entero ? L().finT : L().ganasT;
      p.textContent = libro.entero ? L().finP : L().ganasP(resto);
      otra.textContent = L().otra;
      otra.href = "./" + (idioma === "en" ? "?lang=en" : "") + "#" + encodeURIComponent(libro.id);
      var s = b.querySelector("small");
      if (s) s.textContent = L().badgeS;
      if (b.setAttribute) b.setAttribute("aria-label", L().badgeA);
    });
    [ic, h2, p, b, el("br"), otra].forEach(function (n) { c.appendChild(n); });
    h.appendChild(c);
    h.dataset.audio = "";
    return h;
  }
  function arma(datos) {
    libro = datos;
    document.body.classList.add("t-" + libro.tramo);
    hojasEl.textContent = "";
    hojas = [hojaPortada()];
    libro.paginas.forEach(function (p, i) { hojas.push(hojaPagina(p, i + 1)); });
    hojas.push(hojaFinal());
    hojas.forEach(function (h) { hojasEl.appendChild(h); });
    pinta(function () {
      var t = libro.titulo[idioma === "en" ? 1 : 0];
      tituloEl.textContent = t;
      document.title = t + L().sufijo;
      var d = document.querySelector('meta[name="description"]');
      var p1 = (libro.paginas[0] && (libro.paginas[0][idioma] || libro.paginas[0].es)) || "";
      if (d) d.setAttribute("content", t + ". " + p1.replace(/\s+/g, " ").slice(0, 140) + "…");
    });
    var can = document.createElement("link");
    can.rel = "canonical";
    can.href = SITIO + "lector.html?id=" + encodeURIComponent(libro.id);
    document.head.appendChild(can);
    var inicio = parseInt((location.hash || "").replace("#", ""), 10);
    actual = isNaN(inicio) ? 0 : Math.max(0, Math.min(hojas.length - 1, inicio));
    requestAnimationFrame(function () { hojasEl.scrollLeft = actual * hojasEl.clientWidth; cambia(true); });
    document.querySelector(".lpie").hidden = false;
  }
  function fallo() {
    hojasEl.textContent = "";
    var a = el("div", "aviso");
    var p = el("p", "", L().noHay), ir = el("a", "", L().irBib);
    ir.href = "./";
    a.appendChild(p); a.appendChild(ir);
    hojasEl.appendChild(a);
    document.querySelector(".lpie").hidden = true;
  }

  /* ── pasar de hoja ── */
  function carga(i) {
    for (var j = i - 1; j <= i + 2; j++) {
      var img = hojas[j] && hojas[j].querySelector("img[data-src]");
      if (img && !img.getAttribute("src")) img.src = img.dataset.src;
    }
  }
  function ir(i) {
    i = Math.max(0, Math.min(hojas.length - 1, i));
    var suave = !(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
    hojasEl.scrollTo({ left: i * hojasEl.clientWidth, behavior: suave ? "smooth" : "auto" });
  }
  function cambia(primera) {
    paraAudio();
    carga(actual);
    antBtn.disabled = actual === 0;
    sigBtn.disabled = actual === hojas.length - 1;
    pintaNum();
    hojas.forEach(function (h, k) { h.setAttribute("aria-hidden", String(k !== actual)); h.inert = k !== actual; });
    if (!primera && window.history && history.replaceState) history.replaceState(null, "", location.pathname + location.search + (actual ? "#" + actual : ""));
  }
  function pintaNum() {
    if (!libro) return;
    var ult = hojas.length - 1;
    numEl.textContent = actual === 0 ? L().portada : actual === ult ? (libro.entero ? L().fin : L().sigue) : L().pagina(actual, libro.total);
    var a = hojas[actual] && hojas[actual].dataset.audio;
    oirBtn.hidden = !a;
    if (!sonando) etiqueta(actual === 0 ? "oirTitulo" : "oir");
  }
  hojasEl.addEventListener("scroll", function () {
    if (raf) return;
    raf = requestAnimationFrame(function () {
      raf = 0;
      var i = Math.round(hojasEl.scrollLeft / Math.max(1, hojasEl.clientWidth));
      if (i !== actual && hojas[i]) { actual = i; cambia(false); }
    });
  }, { passive: true });
  window.addEventListener("resize", function () { if (hojas.length) hojasEl.scrollLeft = actual * hojasEl.clientWidth; });
  antBtn.addEventListener("click", function () { ir(actual - 1); });
  sigBtn.addEventListener("click", function () { ir(actual + 1); });
  document.addEventListener("keydown", function (e) {
    if (e.altKey || e.ctrlKey || e.metaKey) return;
    if (e.key === "ArrowRight") { ir(actual + 1); e.preventDefault(); }
    else if (e.key === "ArrowLeft") { ir(actual - 1); e.preventDefault(); }
  });

  /* ── escuchar la hoja (la portada: el título) ── */
  var audio = new Audio();
  audio.preload = "none";
  var sonando = false, espera = 0;
  function etiqueta(estado) {
    oirBtn.querySelector(".txt").textContent = L()[estado];
    oirBtn.classList.toggle("sonando", estado === "parar");
    oirBtn.classList.toggle("fallo", estado === "fallo");
    oirBtn.setAttribute("aria-pressed", String(estado === "parar"));
  }
  function paraAudio() {
    sonando = false;
    try { audio.pause(); audio.currentTime = 0; } catch (e) { /* nada */ }
    if (libro) etiqueta(actual === 0 ? "oirTitulo" : "oir");
  }
  function falla() {
    if (!sonando) return;
    sonando = false;
    etiqueta("fallo");
    clearTimeout(espera);
    espera = setTimeout(function () { if (!sonando) etiqueta(actual === 0 ? "oirTitulo" : "oir"); }, 2600);
  }
  oirBtn.addEventListener("click", function () {
    if (sonando) { paraAudio(); return; }
    var a = hojas[actual] && hojas[actual].dataset.audio;
    if (!a) return;
    sonando = true;
    etiqueta("parar");
    audio.src = base() + idioma + "_" + a + ".mp3";
    var p = audio.play();
    if (p && p.catch) p.catch(falla);
  });
  audio.addEventListener("ended", paraAudio);
  audio.addEventListener("error", falla);

  /* ── idioma ── */
  function ponIdioma(l) {
    idioma = l === "en" ? "en" : "es";
    raiz.lang = idioma;
    paraAudio();
    pintores.forEach(function (fn) { fn(); });
    var s = volver.querySelector(".t");
    if (s) s.textContent = L().bib;
    volver.href = "./" + (idioma === "en" ? "?lang=en" : "") + (libro ? "#" + encodeURIComponent(libro.id) : "");
    antBtn.setAttribute("aria-label", L().ant);
    sigBtn.setAttribute("aria-label", L().sig);
    document.querySelector(".idioma").setAttribute("aria-label", L().idioma);
    [].forEach.call(document.querySelectorAll(".idioma button"), function (b) { b.setAttribute("aria-pressed", String(b.dataset.idioma === idioma)); });
    pintaNum();
    if (libro && window.history && history.replaceState) {
      history.replaceState(null, "", location.pathname + "?id=" + encodeURIComponent(libro.id) + (idioma === "en" ? "&lang=en" : "") + (actual ? "#" + actual : ""));
    }
  }
  [].forEach.call(document.querySelectorAll(".idioma button"), function (b) {
    b.addEventListener("click", function () { ponIdioma(b.dataset.idioma); guarda("sumanautas-idioma", idioma); });
  });

  ponIdioma(idioma);
  if (!/^[a-z0-9-]{1,120}$/.test(id)) { fallo(); return; }
  fetch("web/cuentos/" + encodeURIComponent(id) + ".json")
    .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(function (d) { arma(d); ponIdioma(idioma); })
    .catch(fallo);
})();
