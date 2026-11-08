// Küchenhelfer: Zutaten und Schritte abhaken, Bildschirm wach halten.
(function () {
  function abhaken(liste, mitAktuell) {
    var punkte = Array.prototype.slice.call(liste);
    punkte.forEach(function (li) {
      li.setAttribute('role', 'checkbox');
      li.setAttribute('aria-checked', 'false');
      li.tabIndex = 0;
      function umschalten() {
        var an = li.classList.toggle('erledigt');
        li.setAttribute('aria-checked', an ? 'true' : 'false');
        if (mitAktuell) {
          punkte.forEach(function (p) { p.classList.remove('aktuell'); });
          var naechster = punkte.find(function (p) { return !p.classList.contains('erledigt'); });
          if (naechster && punkte.some(function (p) { return p.classList.contains('erledigt'); })) naechster.classList.add('aktuell');
        }
      }
      li.addEventListener('click', function (e) { if (e.target.closest('a')) return; umschalten(); });
      li.addEventListener('keydown', function (e) { if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); umschalten(); } });
    });
  }

  function wachSchalter(nach) {
    if (!('wakeLock' in navigator)) return;
    var lock = null, an = false;
    var btn = document.createElement('button');
    btn.className = 'wach-schalter'; btn.type = 'button';
    function zeichnen() {
      btn.setAttribute('aria-pressed', an ? 'true' : 'false');
      btn.textContent = an ? '☀️ Bildschirm bleibt an' : '🌙 Bildschirm wach halten';
    }
    async function holen() {
      try { lock = await navigator.wakeLock.request('screen'); lock.addEventListener('release', function () { lock = null; }); }
      catch (e) { an = false; zeichnen(); }
    }
    btn.addEventListener('click', function () {
      an = !an; zeichnen();
      if (an) holen(); else if (lock) { lock.release(); lock = null; }
    });
    document.addEventListener('visibilitychange', function () {
      if (an && !lock && document.visibilityState === 'visible') holen();
    });
    nach.insertAdjacentElement('afterend', btn); zeichnen();
  }

  function einrichten() {
    var zutaten = document.querySelector('.md-content .zutaten');
    if (!zutaten) return; // keine Rezeptseite
    abhaken(zutaten.querySelectorAll('ul > li'), false);
    var h2 = zutaten.querySelector('h2');
    if (h2) {
      var hinweis = document.createElement('p');
      hinweis.className = 'zutaten-hinweis';
      hinweis.textContent = 'Antippen zum Abhaken';
      h2.insertAdjacentElement('afterend', hinweis);
    }
    var schritte = document.querySelector('.md-content .schritte');
    if (schritte) abhaken(schritte.querySelectorAll('ol > li'), true);
    var info = document.querySelector('.md-content .rezept-info') || document.querySelector('.md-content article h1');
    if (info) wachSchalter(info);
  }

  // Material lädt Seiten teils ohne Neuladen; daher auf jeden Seitenwechsel reagieren
  if (window.document$ && window.document$.subscribe) window.document$.subscribe(einrichten);
  else if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', einrichten);
  else einrichten();
})();
