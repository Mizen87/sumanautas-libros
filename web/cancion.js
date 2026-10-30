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
    es: { volver: "Canciones", sig: "Siguiente canción ▶", simul: "Simultáneo: las dos letras a la vez", atras: "Volver a las canciones", menos: "Letra más pequeña", mas: "Letra más grande", cargando: "Cargando la canción…", nohay: "No encontramos esta canción.", ver: "Ver en español", verMeta: "Ver en inglés",
          play: "Reproducir", pausa: "Pausa", reinicia: "Desde el principio", finT: "¡Muy bien!",
          fin: "En el juego Sumanautas, al acabar cada canción hay 3 preguntas para repasar lo aprendido, y cada semana llegan canciones nuevas.",
          muestraT: "¿Quieres oírla entera?", muestra: "Esta es solo una muestra. Escúchala entera, con su letra y sus preguntas, en Sumanautas." },
    en: { volver: "Songs", sig: "Next song ▶", simul: "Both at once: the two lyrics together", atras: "Back to the songs", menos: "Smaller text", mas: "Bigger text", cargando: "Loading the song…", nohay: "We couldn't find this song.", ver: "See in English", verMeta: "See in Spanish",
          play: "Play", pausa: "Pause", reinicia: "From the start", finT: "Well done!",
          fin: "In the Sumanautas game, every song ends with 3 questions to review what you learned, and new songs arrive every week.",
          muestraT: "Want to hear it all?", muestra: "This is just a preview. Listen to the whole song, with its lyrics and questions, in Sumanautas." }
  };
  var PLAY = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M7 4.5v15l12-7.5z"/></svg>';
  var PAUSA = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M6 4h4.5v16H6zM13.5 4H18v16h-4.5z"/></svg>';
  var main = document.getElementById("cmain"), tit = document.getElementById("ctitulo");
  var datos = null, c = null, audio = null, lineas = [], actual = -1, traduce = false, raf = 0;
  /* [30-oct, él] «Simultáneo»: debajo de cada línea, su traducción (se recuerda en este navegador) */
  var simul = lee("sumanautas-simultaneo") === "1";

  function T() { return TXT[idioma]; }
  /* el tamaño de la letra (px): 16-40; sin guardar, el de la pantalla */
  function letraPx(v) {
    if (v === undefined) { var g = parseInt(lee("sumanautas-letra-cancion"), 10); return g >= 16 && g <= 40 ? g : (window.innerWidth < 760 ? 20 : 22); }
    v = Math.max(16, Math.min(40, v)); guarda("sumanautas-letra-cancion", String(v));
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
    var i = datos.canciones.indexOf(c), sig = datos.canciones[(i + 1) % datos.canciones.length];
    var bn = el("a", "siguiente", T().sig);
    bn.href = "?id=" + encodeURIComponent(sig.id) + (idioma === "en" ? "&lang=en" : "");
    bn.addEventListener("click", function (ev) { ev.preventDefault(); id = sig.id; traduce = false; if (history.replaceState) history.replaceState(null, "", bn.getAttribute("href")); pinta(); window.scrollTo(0, 0); if (audio) audio.play(); });
    lado.appendChild(bn);
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
      b.addEventListener("click", function () { letraPx(letraPx() + x[1]); });
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
        if (traduce) { li.textContent = (otra[k] || ln)[0]; li.lang = idioma; }
        else {
          li.lang = m; ln[0].split(" ").forEach(function (w, i) { if (i) li.appendChild(document.createTextNode(" ")); li.appendChild(el("span", "w", w)); });
          if (simul) { var tr = el("span", "tr", (otra[k] || ln)[0]); tr.lang = idioma; li.appendChild(tr); }
        }
      });
      actual = -1;
    }
    bt.addEventListener("click", function () { if (simul) { simul = false; guarda("sumanautas-simultaneo", "0"); traduce = true; } else traduce = !traduce; textos(); paso(); });
    bs.addEventListener("click", function () { simul = !simul; guarda("sumanautas-simultaneo", simul ? "1" : "0"); if (simul) traduce = false; textos(); paso(); });
    textos();
    audio = new Audio("canciones/" + encodeURIComponent(c.id) + "/" + m + (c.entera ? "" : "_muestra") + ".mp3");
    audio.preload = "auto";
    bp.addEventListener("click", function () { if (audio.paused) audio.play(); else audio.pause(); });
    br.addEventListener("click", function () { audio.currentTime = 0; audio.play(); });
    barra.addEventListener("click", function (ev) { var r = barra.getBoundingClientRect(); audio.currentTime = Math.max(0, Math.min(1, (ev.clientX - r.left) / r.width)) * (audio.duration || c[m].d); });
    audio.addEventListener("play", function () { bp.innerHTML = PAUSA; bp.setAttribute("aria-label", T().pausa); fin.hidden = true; raf = requestAnimationFrame(bucle); });
    audio.addEventListener("pause", function () { bp.innerHTML = PLAY; bp.setAttribute("aria-label", T().play); });
    audio.addEventListener("ended", function () { fin.hidden = false; fin.scrollIntoView({ behavior: "smooth", block: "center" }); });
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
