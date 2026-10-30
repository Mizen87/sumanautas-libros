/* La CANCIÓN de la web: cancion.html?id=<id>[&lang=en]. Lee web/canciones.json (lo escribe genera_web.py). [30-oct, él]
   «según el idioma que tengamos establecido en la web saldrán en el idioma contrario»: con la web en español suena en inglés
   (y «Ver en español» traduce la letra línea a línea); con la web en inglés, en español. La línea que suena se ilumina palabra
   a palabra y la letra la sigue sola; tocar una línea salta a ella. Las 20 primeras, enteras; las demás, solo el 10 % del
   principio y «Escúchala entera en Sumanautas». Sin librerías. */
(function () {
  "use strict";
  var q = location.search;
  var id = decodeURIComponent((q.match(/[?&]id=([^&]+)/) || [])[1] || "");
  function lee(k) { try { return window.localStorage.getItem(k); } catch (e) { return null; } }
  function guarda(k, v) { try { window.localStorage.setItem(k, v); } catch (e) { /* da igual */ } }
  var idioma = (q.match(/[?&]lang=(es|en)\b/) || [])[1] || lee("sumanautas-idioma") || "es";
  var TXT = {
    es: { volver: "Canciones", sig: "Siguiente canción ▶", simul: "Simultáneo: las dos letras a la vez", seguido: "▶▶ Seguidas: al acabar, pasa a la siguiente", cuenta: "La siguiente empieza en {n}…", atras: "Volver a las canciones", menos: "Letra más pequeña", mas: "Letra más grande", cargando: "Cargando la canción…", nohay: "No encontramos esta canción.", ver: "Ver en español", verMeta: "Ver en inglés",
          play: "Reproducir", pausa: "Pausa", reinicia: "Desde el principio", finT: "¡Muy bien!",
          fin: "En el juego Sumanautas, al acabar cada canción hay 3 preguntas para repasar lo aprendido, y cada semana llegan canciones nuevas.",
          muestraT: "¿Quieres oírla entera?", muestra: "Esta es solo una muestra. Escúchala entera, con su letra y sus preguntas, en Sumanautas." },
    en: { volver: "Songs", sig: "Next song ▶", simul: "Both at once: the two lyrics together", seguido: "▶▶ Autoplay: next song when it ends", cuenta: "Next song in {n}…", atras: "Back to the songs", menos: "Smaller text", mas: "Bigger text", cargando: "Loading the song…", nohay: "We couldn't find this song.", ver: "See in English", verMeta: "See in Spanish",
          play: "Play", pausa: "Pause", reinicia: "From the start", finT: "Well done!",
          fin: "In the Sumanautas game, every song ends with 3 questions to review what you learned, and new songs arrive every week.",
          muestraT: "Want to hear it all?", muestra: "This is just a preview. Listen to the whole song, with its lyrics and questions, in Sumanautas." }
  };
  var PLAY = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M7 4.5v15l12-7.5z"/></svg>';
  var PAUSA = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M6 4h4.5v16H6zM13.5 4H18v16h-4.5z"/></svg>';
  var main = document.getElementById("cmain"), tit = document.getElementById("ctitulo");
  var datos = null, c = null, audio = null, lineas = [], actual = -1, traduce = false, raf = 0, metaDe = "";
  /* [30-oct, él] «Simultáneo»: debajo de cada línea, su traducción (se recuerda en este navegador) */
  var simul = lee("sumanautas-simultaneo") === "1";
  /* [30-oct, él: «un botón para continuar con la siguiente canción automáticamente al acabar»] «Seguidas» (se recuerda en este navegador) */
  var seguido = lee("sumanautas-seguido") === "1", tSig = 0;

  function T() { return TXT[idioma]; }
  /* [30-oct, él: «en el texto de CarPlay, ponerlo en negrita, más gordo»] CarPlay no deja elegir la letra, pero hay letras que YA son
     negritas (las «sans-serif bold» de Unicode): se cambian a-z, A-Z y 0-9; las tildes y la ñ van como acento encima (á = a + ´) */
  function negrita(t) {
    var out = "";
    String(t).normalize("NFD").split("").forEach(function (ch) {
      var n = ch.charCodeAt(0);
      if (n >= 65 && n <= 90) out += String.fromCodePoint(0x1D5D4 + n - 65);
      else if (n >= 97 && n <= 122) out += String.fromCodePoint(0x1D5EE + n - 97);
      else if (n >= 48 && n <= 57) out += String.fromCodePoint(0x1D7EC + n - 48);
      else out += ch;
    });
    return out;
  }
  /* el tamaño de la letra (px): 16-56 ([30-oct, él] «que pueda aumentarla más»); sin guardar, el de la pantalla */
  function letraPx(v) {
    if (v === undefined) { var g = parseInt(lee("sumanautas-letra-cancion"), 10); return g >= 16 && g <= 56 ? g : (window.innerWidth < 760 ? 20 : 22); }
    v = Math.max(16, Math.min(56, v)); guarda("sumanautas-letra-cancion", String(v));
    document.documentElement.style.setProperty("--letra", v + "px");
    if (actual >= 0 && lineas[actual]) lineas[actual].scrollIntoView({ block: "center" });
    return v;
  }
  document.documentElement.style.setProperty("--letra", letraPx() + "px");
  function canta() { return idioma === "en" ? "es" : "en"; }     // el idioma CONTRARIO al de la web
  function mm(s) { s = Math.max(0, Math.floor(s || 0)); return Math.floor(s / 60) + ":" + ("0" + (s % 60)).slice(-2); }
  function el(tag, cls, txt) { var x = document.createElement(tag); if (cls) x.className = cls; if (txt != null) x.textContent = txt; return x; }

  function pinta() {
    document.documentElement.lang = idioma;
    [].forEach.call(document.querySelectorAll(".idioma button"), function (b) { b.setAttribute("aria-pressed", String(b.dataset.idioma === idioma)); });
    document.querySelector(".volver .t").textContent = T().volver;
    if (audio) { audio.pause(); cancelAnimationFrame(raf); }
    clearInterval(tSig);
    main.innerHTML = "";
    if (!datos) { main.appendChild(el("p", "aviso", T().cargando)); return; }
    c = null;
    datos.canciones.forEach(function (x) { if (x.id === id) c = x; });
    if (!c) { main.appendChild(el("p", "aviso", T().nohay)); return; }
    var m = canta(), titulo = c.t[m === "en" ? 1 : 0], trad = c.t[m === "en" ? 0 : 1];
    tit.textContent = titulo;
    document.title = titulo + " · Sumanautas";
    var lado = el("div", "lado");
    var img = el("img", "portada"); img.src = "canciones/" + encodeURIComponent(c.id) + "/portada.jpg"; img.alt = ""; img.width = 768; img.height = 768;
    lado.appendChild(img);
    lado.appendChild(el("h1", "ctit", titulo));
    lado.appendChild(el("p", "csub", trad));
    var mandos = el("div", "mandos");
    var bp = el("button", "play"); bp.type = "button"; bp.innerHTML = PLAY; bp.setAttribute("aria-label", T().play);
    var br = el("button", "reinicia", "↺"); br.type = "button"; br.setAttribute("aria-label", T().reinicia);
    var bt = el("button", "traduce"); bt.type = "button";
    mandos.appendChild(bp); mandos.appendChild(br); mandos.appendChild(bt);
    lado.appendChild(mandos);
    var bs = el("button", "simul"); bs.type = "button"; bs.textContent = T().simul;
    lado.appendChild(bs);
    // [30-oct, él: «otro botón que ponga siguiente y pase a la siguiente canción; así no tenemos que salir atrás para poner otra»]
    var i = datos.canciones.indexOf(c), n = datos.canciones.length, sig = datos.canciones[(i + 1) % n], ant = datos.canciones[(i - 1 + n) % n];
    function enlace(x) { return "?id=" + encodeURIComponent(x.id) + (idioma === "en" ? "&lang=en" : ""); }
    function salta(x) {
      id = x.id; traduce = false; if (history.replaceState) history.replaceState(null, "", enlace(x)); pinta();
      if (!document.hidden) window.scrollTo(0, 0);
      if (audio) { var p = audio.play(); if (p && p.catch) p.catch(function () { /* sin permiso para sonar solo: queda en ▶ */ }); }
    }
    var bn = el("a", "siguiente", T().sig);
    bn.href = enlace(sig);
    bn.addEventListener("click", function (ev) { ev.preventDefault(); salta(sig); });
    lado.appendChild(bn);
    var bq = el("button", "simul seguido", T().seguido); bq.type = "button"; bq.setAttribute("aria-pressed", String(seguido));
    bq.addEventListener("click", function () { seguido = !seguido; guarda("sumanautas-seguido", seguido ? "1" : "0"); bq.setAttribute("aria-pressed", String(seguido)); if (!seguido) { clearInterval(tSig); cuenta.hidden = true; } });
    lado.appendChild(bq);
    var barra = el("div", "barra"), relleno = el("i"); barra.appendChild(relleno); lado.appendChild(barra);
    var tiempo = el("p", "tiempo", "0:00 / " + mm(c[m].d)); lado.appendChild(tiempo);
    // [30-oct, él: «pon un botón para volver atrás, que hay mucho espacio para ponerlo»] grande, bajo los mandos
    var atras = el("a", "atras", "← " + T().atras); atras.href = "./" + (idioma === "en" ? "?lang=en" : "") + "#canciones";
    lado.appendChild(atras);
    // [30-oct, él: «y que podamos ajustar el tamaño de la letra»] A− / A+ (se recuerda en este navegador)
    var tam = el("div", "tamano");
    [["−", -2, T().menos], ["+", 2, T().mas]].forEach(function (x) {
      var b = el("button", null); b.type = "button"; b.setAttribute("aria-label", x[2]);
      b.innerHTML = '<span class="a">A</span>' + x[0];
      b.addEventListener("click", function () { letraPx(letraPx() + x[1] * 2); });
      tam.appendChild(b);
    });
    lado.appendChild(tam);
    main.appendChild(lado);
    var ul = el("ul", "letra"); ul.setAttribute("lang", m);
    var letra = c[m].l, otra = c[m === "en" ? "es" : "en"].l;
    lineas = [];
    letra.forEach(function (ln, k) {
      var li = el("li");
      li.dataset.k = k;
      ul.appendChild(li); lineas.push(li);
      li.addEventListener("click", function () { audio.currentTime = Math.max(0, ln[1] - 0.15); audio.play(); });
    });
    var columna = el("div"); columna.appendChild(ul);
    var fin = el("div", "fin"); fin.hidden = true;
    fin.appendChild(el("h3", null, c.entera ? T().finT : T().muestraT));
    fin.appendChild(el("p", null, c.entera ? T().fin : T().muestra));
    var cuenta = el("p", "cuenta"); cuenta.hidden = true; fin.appendChild(cuenta);
    var bn2 = el("a", "siguiente", T().sig); bn2.href = bn.href;
    bn2.addEventListener("click", function (ev) { ev.preventDefault(); bn.click(); });
    fin.appendChild(bn2);
    fin.insertAdjacentHTML("beforeend", document.getElementById("badge").innerHTML);
    columna.appendChild(fin);
    main.appendChild(columna);
    function textos() {
      bt.innerHTML = "";
      var f = el("img"); f.src = "web/bandera_" + ((traduce ? m : idioma) === "en" ? "gb" : "es") + ".png"; f.alt = "";
      bt.appendChild(f); bt.appendChild(el("span", null, traduce ? T().verMeta : T().ver));
      bs.setAttribute("aria-pressed", String(simul));
      letra.forEach(function (ln, k) {
        var li = lineas[k];
        li.innerHTML = "";
        li.className = k > 0 && ln[1] - letra[k - 1][1] > 6 ? "parte" : "";
        if (traduce) { li.textContent = (ln[3] || (otra[k] || ln)[0]); li.lang = idioma; }
        else {
          li.lang = m; ln[0].split(" ").forEach(function (w, i) { if (i) li.appendChild(document.createTextNode(" ")); li.appendChild(el("span", "w", w)); });
          if (simul) { var tr = el("span", "tr", (ln[3] || (otra[k] || ln)[0])); tr.lang = idioma; li.appendChild(tr); }
        }
      });
      actual = -1;
    }
    bt.addEventListener("click", function () { if (simul) { simul = false; guarda("sumanautas-simultaneo", "0"); traduce = true; } else traduce = !traduce; textos(); paso(); });
    bs.addEventListener("click", function () { simul = !simul; guarda("sumanautas-simultaneo", simul ? "1" : "0"); if (simul) traduce = false; textos(); paso(); });
    textos();
    if (!audio) audio = new Audio();      // (uno solo para todas: en el iPhone, el que ya sonó con un toque puede pasar a la siguiente solo)
    audio.src = "canciones/" + encodeURIComponent(c.id) + "/" + m + (c.entera ? "" : "_muestra") + ".mp3";
    audio.preload = "auto";
    bp.addEventListener("click", function () { if (audio.paused) audio.play(); else audio.pause(); });
    br.addEventListener("click", function () { audio.currentTime = 0; audio.play(); });
    barra.addEventListener("click", function (ev) { var r = barra.getBoundingClientRect(); audio.currentTime = Math.max(0, Math.min(1, (ev.clientX - r.left) / r.width)) * (audio.duration || c[m].d); });
    audio.onplay = function () { clearInterval(tSig); cuenta.hidden = true; bp.innerHTML = PAUSA; bp.setAttribute("aria-label", T().pausa); fin.hidden = true; raf = requestAnimationFrame(bucle); };
    // [30-oct, él: «cuando me sale CarPlay, poder darle a siguiente canción y que pasara»] los botones de CarPlay, de la pantalla
    // bloqueada y de los auriculares (Media Session): título y portada, ▶/❚❚, ⏭ la siguiente, ⏮ al principio o la anterior
    if ("mediaSession" in navigator) {
      try {
        meta(-1);
        var ms = navigator.mediaSession, accion = function (a, f) { try { ms.setActionHandler(a, f); } catch (e) { /* ese botón no existe aquí */ } };
        accion("play", function () { audio.play(); });
        accion("pause", function () { audio.pause(); });
        accion("nexttrack", function () { salta(sig); });
        accion("previoustrack", function () { if (audio.currentTime > 3) audio.currentTime = 0; else salta(ant); });
        accion("seekto", function (d) { if (d && d.seekTime != null) audio.currentTime = d.seekTime; });
      } catch (e) { /* navegador sin Media Session */ }
    }
    // [30-oct, él: «que saliera en el CarPlay la frase que está cantando en inglés y debajo la traducción en español, así los niños
    // podrían leerlo y aprender»] en CarPlay y en la pantalla bloqueada: arriba (título) la frase que suena, debajo (artista) su
    // traducción; antes de la primera frase, el título de la canción y su traducción
    // ([30-oct, él: «parpadea la imagen, quiero que se vea la imagen como antes»] la portada siempre; solo cambia el texto, frase a frase)
    // ([30-oct, él: «que no parpadee»] la portada se manda UNA vez por canción; en cada frase solo se cambia el texto)
    function meta(k) {
      if (!("mediaSession" in navigator) || typeof MediaMetadata === "undefined") return;
      var ln = k >= 0 ? letra[k] : null, ti = negrita(ln ? ln[0] : titulo), ar = negrita(ln ? (ln[3] || (otra[k] || ln)[0]) : trad), md = navigator.mediaSession.metadata;
      try {
        if (md && metaDe === c.id + idioma) { md.title = ti; md.artist = ar; if (md.title === ti) return; }
        navigator.mediaSession.metadata = new MediaMetadata({ title: ti, artist: ar,
          album: "Sumanautas · " + (idioma === "en" ? "Songs to learn Spanish" : "Canciones para aprender inglés"),
          artwork: [{ src: new URL("canciones/" + encodeURIComponent(c.id) + "/portada.jpg", location.href).href, sizes: "768x768", type: "image/jpeg" }] });
        metaDe = c.id + idioma;
      } catch (e) { /* navegador sin Media Session */ }
    }
    audio.ontimeupdate = function () { if (document.hidden) paso(); };     // (con la pantalla bloqueada no hay animación: así la frase de CarPlay sigue cambiando)
    audio.onpause = function () { bp.innerHTML = PLAY; bp.setAttribute("aria-label", T().play); };
    audio.onended = function () {
      fin.hidden = false; fin.scrollIntoView({ behavior: "smooth", block: "center" });
      if (!seguido) return;
      if (document.hidden) { salta(sig); return; }      // (con la pantalla bloqueada o en el coche, sin cuenta atrás)
      var quedan = 4;
      function cuentaAtras() { quedan--; if (quedan <= 0) { clearInterval(tSig); salta(sig); } else { cuenta.hidden = false; cuenta.textContent = T().cuenta.replace("{n}", quedan); } }
      cuentaAtras(); tSig = setInterval(cuentaAtras, 1000);
    };
    function paso() {
      var t = audio.currentTime, d = audio.duration || c[m].d;
      relleno.style.width = (100 * Math.min(1, t / d)) + "%";
      tiempo.textContent = mm(t) + " / " + mm(d);
      var k = -1;
      for (var i = 0; i < letra.length; i++) { if (t >= letra[i][1] - 0.2) k = i; else break; }
      if (k !== actual) {
        if (actual >= 0 && lineas[actual]) lineas[actual].classList.remove("suena", "trad");
        if (k >= 0) { lineas[k].classList.add("suena"); if (traduce) lineas[k].classList.add("trad"); lineas[k].scrollIntoView({ behavior: "smooth", block: "center" }); }
        actual = k;
        meta(k);
      }
      if (k >= 0 && !traduce) {
        var ws = lineas[k].querySelectorAll(".w"), ini = letra[k][2];
        for (var j = 0; j < ws.length; j++) ws[j].classList.toggle("ya", t >= (ini[j] || 1e9));
      }
    }
    function bucle() { paso(); if (!audio.paused) raf = requestAnimationFrame(bucle); }
  }

  [].forEach.call(document.querySelectorAll(".idioma button"), function (b) {
    b.addEventListener("click", function () {
      idioma = b.dataset.idioma === "en" ? "en" : "es"; guarda("sumanautas-idioma", idioma); traduce = false;
      if (history.replaceState) history.replaceState(null, "", "?id=" + encodeURIComponent(id) + (idioma === "en" ? "&lang=en" : ""));
      pinta();
    });
  });
  pinta();
  fetch("web/canciones.json", { cache: "no-cache" }).then(function (r) { return r.json(); }).then(function (d) { datos = d; pinta(); })
    .catch(function () { main.innerHTML = ""; main.appendChild(el("p", "aviso", T().nohay)); });
})();
