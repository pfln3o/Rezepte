// Hält den Bildschirm beim Kochen an (Screen Wake Lock), wo der Browser das kann.
(function () {
  if (!('wakeLock' in navigator)) return;
  var lock = null, an = false, btn = null;
  function zeichnen() {
    if (!btn) return;
    btn.setAttribute('aria-pressed', an ? 'true' : 'false');
    btn.textContent = an ? '☀️ Bildschirm bleibt an' : '🌙 Bildschirm wach halten';
  }
  async function holen() {
    try { lock = await navigator.wakeLock.request('screen'); lock.addEventListener('release', function () { lock = null; }); }
    catch (e) { an = false; zeichnen(); }
  }
  document.addEventListener('visibilitychange', function () {
    if (an && !lock && document.visibilityState === 'visible') holen();
  });
  function einbauen() {
    var h1 = document.querySelector('.md-content article h1');
    if (!h1 || !document.querySelector('.md-content article h2#zubereitung')) return; // nur auf Rezeptseiten
    btn = document.createElement('button');
    btn.className = 'wach-schalter'; btn.type = 'button';
    btn.addEventListener('click', function () {
      an = !an; zeichnen();
      if (an) holen(); else if (lock) { lock.release(); lock = null; }
    });
    h1.insertAdjacentElement('afterend', btn); zeichnen();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', einbauen); else einbauen();
})();
