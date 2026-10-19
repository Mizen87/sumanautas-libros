/* Web de la biblioteca de Sumanautas: idioma ES/EN, filtro por edad y «Escuchar el principio». genera_web.py lo mete
   DENTRO de index.html; se edita aquí y se vuelve a ejecutar el generador. Sin librerías. */
(function () {
  "use strict";
  var raiz = document.documentElement;
  var TXT = {
    es: { oir: "Escuchar el principio", parar: "Parar", fallo: "No se ha podido oír",
          cuentos: function (n) { return n === 1 ? "1 cuento" : n + " cuentos"; } },
    en: { oir: "Listen to the beginning", parar: "Stop", fallo: "Couldn't play it",
          cuentos: function (n) { return n === 1 ? "1 story" : n + " stories"; } }
  };
  var ATRIBUTOS = [["alt", "enAlt", "esAlt"], ["aria-label", "enAria", "esAria"], ["title", "enTitle", "esTitle"], ["content", "enContent", "esContent"]];
  var TRAMOS = ["peques", "exploradores", "aventureros", "maestros"];
  var idioma = "es", tramo = "todos";
  var tarjetas = [].slice.call(document.querySelectorAll(".cuento"));
  var filtros = [].slice.call(document.querySelectorAll(".filtros button"));
  var contador = document.querySelector(".contador");

  function lee(k) { try { return window.localStorage.getItem(k); } catch (e) { return null; } }
  function guarda(k, v) { try { window.localStorage.setItem(k, v); } catch (e) { /* sin almacenamiento: da igual */ } }

  /* ── idioma: cada texto traducible lleva su inglés en data-en (y sus atributos en data-en-alt, data-en-aria…) ── */
  function ponIdioma(l) {
    paraAudio();
    idioma = l === "en" ? "en" : "es";
    raiz.lang = idioma;
    [].forEach.call(document.querySelectorAll("[data-en]"), function (el) {
      if (el.dataset.es === undefined) el.dataset.es = el.textContent;
      el.textContent = idioma === "en" ? el.dataset.en : el.dataset.es;
    });
    ATRIBUTOS.forEach(function (a) {
      [].forEach.call(document.querySelectorAll("[data-en-" + a[0].replace("aria-label", "aria") + "]"), function (el) {
        if (el.dataset[a[2]] === undefined) el.dataset[a[2]] = el.getAttribute(a[0]) || "";
        el.setAttribute(a[0], idioma === "en" ? el.dataset[a[1]] : el.dataset[a[2]]);
      });
    });
    [].forEach.call(document.querySelectorAll(".oir"), function (b) { etiqueta(b, "oir"); });
    [].forEach.call(document.querySelectorAll(".idioma button"), function (b) {
      b.setAttribute("aria-pressed", String(b.dataset.idioma === idioma));
    });
    pintaContador();
  }

  /* ── filtro por edad (se recuerda en la dirección: …/#peques) ── */
  function filtra(t, desdeBoton) {
    tramo = TRAMOS.indexOf(t) >= 0 ? t : "todos";
    tarjetas.forEach(function (c) { c.hidden = !(tramo === "todos" || c.dataset.tramo === tramo); });
    filtros.forEach(function (b) { b.setAttribute("aria-pressed", String(b.dataset.tramo === tramo)); });
    pintaContador();
    if (desdeBoton && window.history && history.replaceState) {
      history.replaceState(null, "", tramo === "todos" ? location.pathname + location.search : "#" + tramo);
    }
  }
  function pintaContador() {
    if (!contador) return;
    var n = tarjetas.filter(function (c) { return !c.hidden; }).length;
    contador.textContent = (idioma === "en" ? "Showing " : "Mostrando ") + TXT[idioma].cuentos(n);
  }
  filtros.forEach(function (b) {
    b.addEventListener("click", function () { paraAudio(); filtra(b.dataset.tramo, true); });
  });

  /* ── «Escuchar el principio»: la página 1 narrada (es_p1.mp3 / en_p1.mp3 de la carpeta del libro) ── */
  var audio = new Audio();
  audio.preload = "none";
  var sonando = null, espera = 0;
  function etiqueta(b, estado) {
    var t = b.querySelector(".txt");
    if (t) t.textContent = TXT[idioma][estado];
    b.classList.toggle("sonando", estado === "parar");
    b.classList.toggle("fallo", estado === "fallo");
    b.setAttribute("aria-pressed", String(estado === "parar"));
  }
  function paraAudio() {
    if (sonando) etiqueta(sonando, "oir");
    sonando = null;
    try { audio.pause(); audio.currentTime = 0; } catch (e) { /* nada */ }
  }
  function falla(b) {
    if (sonando !== b) return;
    sonando = null;
    etiqueta(b, "fallo");
    clearTimeout(espera);
    espera = setTimeout(function () { if (sonando !== b) etiqueta(b, "oir"); }, 2600);
  }
  document.addEventListener("click", function (e) {
    var b = e.target.closest ? e.target.closest(".oir") : null;
    if (!b) return;
    if (sonando === b) { paraAudio(); return; }
    paraAudio();
    sonando = b;
    etiqueta(b, "parar");
    audio.src = idioma === "en" ? b.dataset.audioEn : b.dataset.audioEs;
    var p = audio.play();
    if (p && p.catch) p.catch(function () { falla(b); });
  });
  audio.addEventListener("ended", paraAudio);
  audio.addEventListener("error", function () { if (sonando) falla(sonando); });

  [].forEach.call(document.querySelectorAll(".idioma button"), function (b) {
    b.addEventListener("click", function () { ponIdioma(b.dataset.idioma); guarda("sumanautas-idioma", idioma); });
  });

  /* al cargar: ?lang=en (para compartir la web en inglés) o lo que eligió la otra vez; si no, español */
  var pedido = (location.search.match(/[?&]lang=(es|en)\b/) || [])[1] || lee("sumanautas-idioma");
  if (pedido === "en") ponIdioma("en");
  var alCargar = (location.hash || "").replace("#", "");
  filtra(alCargar, false);
  if (TRAMOS.indexOf(alCargar) >= 0) {
    var bib = document.getElementById("biblioteca");
    var baja = function () { bib.scrollIntoView({ behavior: "instant", block: "start" }); };
    if (bib) { if (document.readyState === "complete") baja(); else window.addEventListener("load", function () { setTimeout(baja, 0); }); }
  }
  window.addEventListener("hashchange", function () {
    var h = (location.hash || "").replace("#", "");
    if (TRAMOS.indexOf(h) >= 0 || h === "") filtra(h, false);
  });
})();
