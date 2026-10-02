/* Likalo — interface bilingue français / anglais.
 * - La langue d'interface est mémorisée dans le navigateur (localStorage « likalo-ui »).
 * - En anglais, les textes de l'interface sont traduits à partir du dictionnaire data/en/ui.json,
 *   et les contenus (leçons, fiches, glossaires) sont lus dans data/en/.
 * - Ajouter / corriger une traduction : modifier data/en/ui.json (voir le guide).
 */
(function () {
  var KEY = 'likalo-ui';
  var lang = null;
  try { lang = localStorage.getItem(KEY); } catch (e) {}
  var q = location.search.match(/[?&]lang=(en|fr)\b/);
  if (q) { lang = q[1]; try { localStorage.setItem(KEY, lang); } catch (e) {} }
  if (lang !== 'en' && lang !== 'fr') lang = /^en\b/i.test(navigator.language || '') ? 'en' : 'fr';
  window.LIKALO_UI = lang;
  document.documentElement.lang = lang;

  var css = document.createElement('style');
  css.textContent =
    'html.i18n-wait body{visibility:hidden}' +
    '.ui-toggle{display:inline-flex;border:1px solid #d6d3d1;border-radius:9999px;overflow:hidden;background:#fff;font:600 12px/1 system-ui,sans-serif}' +
    '.ui-toggle button{padding:6px 9px;color:#57534e;background:transparent;border:0;cursor:pointer;min-width:34px}' +
    '.ui-toggle button.on{background:#1c1917;color:#fff}' +
    '[data-ui-toggle=float]{position:fixed;right:12px;bottom:12px;z-index:60;box-shadow:0 2px 8px rgba(0,0,0,.15)}';
  document.head.appendChild(css);

  window.setUiLang = function (l) {
    try { localStorage.setItem(KEY, l); } catch (e) {}
    location.reload();
  };

  /* Bouton FR | EN : tout élément [data-ui-toggle] reçoit le sélecteur ; sinon un petit bouton flottant. */
  function mountToggles() {
    var html = '<button type="button" data-l="fr" aria-label="Français">FR</button>' +
               '<button type="button" data-l="en" aria-label="English">EN</button>';
    var slots = document.querySelectorAll('[data-ui-toggle]');
    if (!slots.length) {
      var f = document.createElement('div');
      f.setAttribute('data-ui-toggle', 'float');
      document.body.appendChild(f);
      slots = [f];
    }
    Array.prototype.forEach.call(slots, function (el) {
      el.classList.add('ui-toggle');
      el.innerHTML = html;
      el.setAttribute('role', 'group');
      el.setAttribute('aria-label', lang === 'en' ? 'Interface language' : "Langue de l'interface");
      Array.prototype.forEach.call(el.querySelectorAll('button'), function (b) {
        b.classList.toggle('on', b.dataset.l === lang);
        b.addEventListener('click', function () { if (b.dataset.l !== lang) window.setUiLang(b.dataset.l); });
      });
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mountToggles);
  else mountToggles();

  if (lang !== 'en') return;

  /* ---------- Traduction de l'interface (anglais) ---------- */
  var root = document.documentElement;
  root.classList.add('i18n-wait');
  var reveal = function () { root.classList.remove('i18n-wait'); };
  setTimeout(reveal, 2500); // sécurité : ne jamais laisser la page invisible

  var TEXT = {}, PATS = [], ready = false;
  var ATTRS = ['placeholder', 'title', 'aria-label', 'alt'];
  var SKIP = { SCRIPT: 1, STYLE: 1, NOSCRIPT: 1, TEXTAREA: 1, CODE: 1 };

  function tr(s) {
    var core = s.replace(/\s+/g, ' ').trim();
    if (!core || !/[A-Za-zÀ-ÿ]/.test(core)) return null;
    var e = TEXT[core];
    if (e === undefined) {
      for (var i = 0; i < PATS.length; i++) {
        if (PATS[i][0].test(core)) { e = core.replace(PATS[i][0], PATS[i][1]); break; }
      }
    }
    if (e === undefined || e === core) return null;
    var lead = s.match(/^\s*/)[0], trail = s.match(/\s*$/)[0];
    return lead + e + trail;
  }

  function walk(node) {
    if (!node) return;
    if (node.nodeType === 3) {
      var p = node.parentNode;
      if (p && (SKIP[p.nodeName] || (p.closest && p.closest('[data-no-i18n]')))) return;
      var t = tr(node.data);
      if (t !== null) node.data = t;
      return;
    }
    if (node.nodeType !== 1 && node.nodeType !== 9 && node.nodeType !== 11) return;
    if (node.nodeType === 1) {
      if (node.hasAttribute('data-no-i18n')) return;
      for (var a = 0; a < ATTRS.length; a++) {
        var v = node.getAttribute(ATTRS[a]);
        if (v) { var tv = tr(v); if (tv !== null) node.setAttribute(ATTRS[a], tv); }
      }
      if (SKIP[node.nodeName]) return;
      if (node.nodeName === 'TEMPLATE') { walk(node.content); return; }
    }
    for (var c = node.firstChild; c; c = c.nextSibling) walk(c);
  }
  window.likaloTranslate = function (n) { if (ready) walk(n || document); };

  var obs = new MutationObserver(function (muts) {
    if (!ready) return;
    for (var i = 0; i < muts.length; i++) {
      var m = muts[i];
      if (m.type === 'characterData') walk(m.target);
      else if (m.type === 'attributes') walk(m.target);
      else for (var j = 0; j < m.addedNodes.length; j++) walk(m.addedNodes[j]);
    }
  });

  fetch('data/en/ui.json').then(function (r) { return r.json(); }).then(function (d) {
    TEXT = d.text || {};
    PATS = (d.patterns || []).map(function (p) { return [new RegExp(p[0]), p[1]]; });
    ready = true;
    walk(document);
    obs.observe(document, { subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: ATTRS });
    reveal();
  }).catch(reveal);
})();
