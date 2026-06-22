/* Likalo — Enseignement/Apprentissage des Langues et Cultures Camerounaises
 * Application monopage (vanilla JS).
 * Routes par hash :
 *   #/             -> Accueil
 *   #/catalogue    -> Catalogue des 16 langues
 *   #/lecons       -> Index des leçons (langue active)
 *   #/lecon/:id    -> Fiche enseignant + élève d'une leçon
 *   #/vocabulaire  -> Liste du vocabulaire (langue active)
 *   #/exercices    -> Quatre familles d'exercices
 *   #/a-propos     -> À propos
 *
 * Langue active : state.currentLang (défaut : 'bulu')
 * Changement via switchLanguage(slug) qui recharge vocab + leçons.
 * Modules langues  : M1–M8  (MINESEC Langues Nationales)
 * Modules cultures : MC1–MC5 (MINESEC Cultures Nationales)
 */

const state = {
  langues: [],        // catalogue des 16 langues ALCAM
  currentLang: 'bulu',  // langue active
  currentLangName: 'Bulu',
  vocab: [],          // phrases de la langue active
  vocabWithFr: [],    // vocab filtré (traduction non vide)
  lessons: [],        // leçons de la langue active
  audioBase: 'audio/bulu/',
  emacBase: 'audio/emac/',
  currentAudio: null,
  preferredPane: 'teacher',  // mémoire de session pour la bascule mobile
  scores: {           // scores en mémoire seulement (jamais persistés)
    comprehension: { correct: 0, total: 0 },
    reconnaissance: { correct: 0, total: 0 },
    lecture: { correct: 0, total: 0 },
    dictee: { correct: 0, total: 0 },
  }
};

const MODULES = {
  /* ── Langues Nationales (MINESEC) ── */
  'M1-diversite':        { num: 'I',    label: 'Diversité linguistique camerounaise', type: 'langue' },
  'M2-segmentaux':       { num: 'II',   label: 'Productions segmentales',             type: 'langue' },
  'M3-suprasegmentaux':  { num: 'III',  label: 'Suprasegmentaux',                     type: 'langue' },
  'M4-syntagme-nominal': { num: 'IV',   label: 'Syntagme nominal',                    type: 'langue' },
  'M5-syntagme-verbal':  { num: 'V',    label: 'Syntagme verbal',                     type: 'langue' },
  'M6-phrase':           { num: 'VI',   label: 'La phrase',                           type: 'langue' },
  'M7-quotidien-1':      { num: 'VII',  label: 'Gestion du quotidien — Niveau 1',     type: 'langue' },
  'M8-quotidien-2':      { num: 'VIII', label: 'Gestion du quotidien — Niveau 2',     type: 'langue' },
  /* ── Cultures Nationales (MINESEC) ── */
  'MC1-diversite-culturelle':  { num: 'C-I',   label: 'Diversité culturelle camerounaise',             type: 'culture' },
  'MC2-modes-de-vie':          { num: 'C-II',  label: 'Pratiques culturelles — Modes de vie',          type: 'culture' },
  'MC3-evenements':            { num: 'C-III', label: 'Pratiques culturelles — Événements de la vie',  type: 'culture' },
  'MC4-communaute-1':          { num: 'C-IV',  label: 'Pratiques culturelles en communauté — Niv. I',  type: 'culture' },
  'MC5-communaute-2':          { num: 'C-V',   label: 'Pratiques culturelles en communauté — Niv. II', type: 'culture' },
};

const EXO_LABELS = {
  comprehension:  'Audio → Traduction française',
  reconnaissance: 'Texte lang. → Audio',
  lecture:        'Texte lang. → Traduction française',
  dictee:         'Audio → Transcription AGLC',
};

/* ---------- Utilitaires ---------- */

function $(sel, root = document) { return root.querySelector(sel); }
function $$(sel, root = document) { return Array.from(root.querySelectorAll(sel)); }

function escapeHtml(str) {
  return String(str ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function shuffle(arr) {
  const a = arr.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function pick(arr) { return arr[Math.floor(Math.random() * arr.length)]; }

function pickN(arr, n, exclude = new Set()) {
  const pool = arr.filter(x => !exclude.has(x));
  return shuffle(pool).slice(0, n);
}

function stopCurrentAudio() {
  if (state.currentAudio) {
    state.currentAudio.pause();
    state.currentAudio.currentTime = 0;
    state.currentAudio = null;
  }
  $$('.play-btn.is-playing').forEach(b => b.classList.remove('is-playing'));
}

function playAudio(url, btn = null) {
  stopCurrentAudio();
  const a = new Audio(url);
  state.currentAudio = a;
  if (btn) btn.classList.add('is-playing');
  a.addEventListener('ended', () => { if (btn) btn.classList.remove('is-playing'); state.currentAudio = null; });
  a.addEventListener('pause', () => { if (btn) btn.classList.remove('is-playing'); });
  a.addEventListener('error', () => { if (btn) btn.classList.remove('is-playing'); state.currentAudio = null; });
  a.play().catch(() => { if (btn) btn.classList.remove('is-playing'); });
}

function normalizeForCompare(s) {
  if (!s) return '';
  return s.toString()
    .normalize('NFC')
    .toLowerCase()
    .replace(/\s+/g, ' ')
    .replace(/[.,;:!?()\[\]"'«»]/g, '')
    .trim();
}

function similarity(a, b) {
  // Levenshtein normalisé en pourcentage
  a = normalizeForCompare(a);
  b = normalizeForCompare(b);
  if (!a && !b) return 100;
  if (!a || !b) return 0;
  const m = a.length, n = b.length;
  const dp = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));
  for (let i = 0; i <= m; i++) dp[i][0] = i;
  for (let j = 0; j <= n; j++) dp[0][j] = j;
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      dp[i][j] = a[i - 1] === b[j - 1]
        ? dp[i - 1][j - 1]
        : 1 + Math.min(dp[i - 1][j - 1], dp[i - 1][j], dp[i][j - 1]);
    }
  }
  const dist = dp[m][n];
  return Math.round((1 - dist / Math.max(m, n)) * 100);
}

/* ---------- Chargement des données ---------- */

async function loadData() {
  const [langues, vocab, lessons] = await Promise.all([
    fetch('data/languages.json').then(r => r.json()),
    fetch(`data/${state.currentLang}.json`).then(r => r.json()).catch(() => []),
    fetch(`data/lessons_${state.currentLang}.json`).then(r => r.json()).catch(() => ({ lessons: [] })),
  ]);
  state.langues = langues;
  state.vocab = vocab;
  state.vocabWithFr = vocab.filter(b => b.frenchText && b.langText);
  state.lessons = lessons.lessons || [];
  const langInfo = langues.find(l => l.slug === state.currentLang);
  state.currentLangName = langInfo ? langInfo.name : state.currentLang;
  state.audioBase = `audio/${state.currentLang}/`;
  // Populate all language selectors (nav + mobile)
  ['nav-lang-selector', 'mobile-lang-selector'].forEach(id => {
    const sel = document.getElementById(id);
    if (sel && !sel.options.length) {
      langues.forEach(l => {
        const opt = new Option(l.name, l.slug);
        sel.add(opt);
      });
    }
    if (sel) sel.value = state.currentLang;
  });
  return { langues, vocab, lessons };
}

async function switchLanguage(slug) {
  if (state.currentLang === slug) return;
  state.currentLang = slug;
  stopCurrentAudio();
  const [vocab, lessons] = await Promise.all([
    fetch(`data/${slug}.json`).then(r => r.json()).catch(() => []),
    fetch(`data/lessons_${slug}.json`).then(r => r.json()).catch(() => ({ lessons: [] })),
  ]);
  state.vocab = vocab;
  state.vocabWithFr = vocab.filter(b => b.frenchText && b.langText);
  state.lessons = lessons.lessons || [];
  const langInfo = state.langues.find(l => l.slug === slug);
  state.currentLangName = langInfo ? langInfo.name : slug;
  state.audioBase = `audio/${slug}/`;
  render();
  updateLangSelector();
}

function updateLangSelector() {
  const navSel = document.getElementById('nav-lang-selector');
  if (navSel) navSel.value = state.currentLang;
  $$('.lang-selector').forEach(sel => { sel.value = state.currentLang; });
}

/* ---------- Routeur ---------- */

// Routes statiques + routes paramétriques.
// Chaque entrée paramétrique a la forme [regex, renderer].
const STATIC_ROUTES = {
  '/':            renderHome,
  '/catalogue':   renderCatalogue,
  '/lecons':      renderLecons,
  '/vocabulaire': renderVocabulaire,
  '/exercices':   renderExercices,
  '/a-propos':    renderAPropos,
};

const PARAM_ROUTES = [
  [/^\/lecon\/([A-Za-z0-9-]+)$/, (id) => renderLecon(id)],
];

function resolveRoute() {
  const path = location.hash.replace(/^#/, '') || '/';
  if (STATIC_ROUTES[path]) {
    return { path, run: STATIC_ROUTES[path] };
  }
  for (const [re, fn] of PARAM_ROUTES) {
    const m = path.match(re);
    if (m) return { path, run: () => fn(...m.slice(1)) };
  }
  return { path: '/', run: STATIC_ROUTES['/'] };
}

function navigate(path) {
  if (location.hash !== '#' + path) location.hash = path;
}

function setActiveNav(path) {
  // Surligne le lien dont le préfixe correspond.
  $$('.nav-link').forEach(a => {
    const target = a.getAttribute('href').replace(/^#/, '');
    const active = path === target
      || (target !== '/' && path.startsWith(target));
    a.classList.toggle('active', active);
  });
}

function render() {
  stopCurrentAudio();
  const { path, run } = resolveRoute();
  setActiveNav(path);
  run();
  $('#mobile-menu')?.classList.add('hidden');
  window.scrollTo(0, 0);
}

window.addEventListener('hashchange', render);

/* ---------- Vues ---------- */

function mountTemplate(id) {
  const tpl = document.getElementById(id);
  const node = tpl.content.cloneNode(true);
  const app = $('#app');
  app.innerHTML = '';
  app.appendChild(node);
}

function renderHome() {
  mountTemplate('tpl-home');
  $('#stat-langues').textContent = state.langues.length;
  $('#stat-phrases').textContent = state.vocabWithFr.length;
  $('#stat-audios').textContent = state.vocab.filter(v => v.audio).length;
  const phrasesLangEl = $('#stat-phrases-lang');
  if (phrasesLangEl) phrasesLangEl.textContent = state.currentLangName;
  const demoLangName = $('#demo-lang-name');
  if (demoLangName) demoLangName.textContent = state.currentLangName;
  const demoBadgeLang = $('#demo-badge-lang');
  if (demoBadgeLang) demoBadgeLang.textContent = state.currentLangName;

  // Phrase de démo : prendre un exemple sympa
  const demo = state.vocabWithFr.find(d => d.langText.length > 8 && d.langText.length < 25)
            || state.vocabWithFr[0];
  if (demo) {
    $('#demo-lang').textContent = demo.langText;
    $('#demo-french').textContent = demo.frenchText;
    const btn = $('#demo-play');
    if (demo.audio) {
      btn.addEventListener('click', () => playAudio(state.audioBase + demo.audio, btn));
    } else {
      btn.style.display = 'none';
    }
  }

  // Injecter le sélecteur de langue dans la home si présent
  const langSel = $('#home-lang-selector');
  if (langSel) {
    langSel.innerHTML = state.langues.map(l =>
      `<option value="${escapeHtml(l.slug)}" ${l.slug===state.currentLang?'selected':''}>${escapeHtml(l.name)}</option>`
    ).join('');
    langSel.value = state.currentLang;
    langSel.classList.add('lang-selector');
    langSel.addEventListener('change', () => switchLanguage(langSel.value));
  }
}

function renderCatalogue() {
  mountTemplate('tpl-catalogue');
  const grid = $('#catalogue-grid');
  grid.innerHTML = state.langues.map(l => {
    const isActive = l.slug === state.currentLang;
    const emacBadge = l.emacCount > 0
      ? `<span class="text-xs font-semibold bg-amber-100 text-amber-800 px-2 py-1 rounded-full">${l.emacCount} audio EMAC</span>`
      : '';
    const audioBadge = l.audio
      ? '<span class="text-xs font-semibold bg-emerald-100 text-emerald-800 px-2 py-1 rounded-full">Synthèse vocale</span>'
      : '';
    return `
    <article class="bg-white rounded-xl border ${isActive ? 'border-brand-400 ring-2 ring-brand-200' : 'border-ink-100'} p-5">
      <div class="flex items-start justify-between gap-3">
        <div>
          <h3 class="font-serif text-xl text-ink-900 lang-text">${escapeHtml(l.name)}</h3>
          <div class="text-xs text-ink-500 mt-0.5">ISO ${escapeHtml(l.iso)} · ${escapeHtml(l.family)}</div>
          ${l.region ? `<div class="text-xs text-ink-400 mt-0.5">Région : ${escapeHtml(l.region)}</div>` : ''}
        </div>
        <div class="flex flex-col gap-1 items-end">${audioBadge}${emacBadge}</div>
      </div>
      <p class="text-sm text-ink-500 mt-3">
        ${l.audio
          ? 'Dataset complet : audios MP3, transcription AGLC, traduction française.'
          : 'Dataset textuel ALCAM disponible.'}
        ${l.emacCount > 0 ? ` Ressources musicales EMAC intégrées dans les leçons.` : ''}
      </p>
      <div class="mt-4 flex items-center gap-3">
        <button class="text-sm font-medium text-brand-700 hover:text-brand-800 switch-lang-btn" data-slug="${escapeHtml(l.slug)}">
          ${isActive ? '✓ Langue active' : 'Activer →'}
        </button>
        <a href="https://mozilladatacollective.com/organization/cmfv3ichk000amd07piai0zoz" target="_blank" rel="noopener"
           class="text-sm text-ink-500 hover:text-ink-700 underline">mdc</a>
      </div>
    </article>`;
  }).join('');

  $$('.switch-lang-btn').forEach(btn => {
    btn.addEventListener('click', () => switchLanguage(btn.dataset.slug));
  });
}

function renderVocabulaire() {
  mountTemplate('tpl-vocabulaire');
  const list = $('#vocab-list');
  const empty = $('#vocab-empty');
  const filter = $('#vocab-filter');
  const search = $('#vocab-search');

  // Titre de langue si présent
  const title = $('#vocab-lang-title');
  if (title) title.textContent = state.currentLangName;

  function update() {
    const mod = filter.value;
    const q = normalizeForCompare(search.value);
    const items = state.vocabWithFr.filter(it => {
      if (mod && it.module !== mod) return false;
      if (!q) return true;
      return normalizeForCompare(it.langText).includes(q)
        || normalizeForCompare(it.frenchText).includes(q);
    });
    if (!items.length) {
      list.innerHTML = '';
      empty.classList.remove('hidden');
      return;
    }
    empty.classList.add('hidden');
    list.innerHTML = items.slice(0, 100).map(it => renderVocabRow(it)).join('');
    list.querySelectorAll('[data-audio]').forEach(btn => {
      btn.addEventListener('click', () => playAudio(state.audioBase + btn.dataset.audio, btn));
    });
  }

  function renderVocabRow(it) {
    const mod = MODULES[it.module] || { num: '—', label: '' };
    const hasAudio = !!it.audio;
    return `
      <article class="bg-white border border-ink-100 rounded-lg p-4 flex items-center gap-4">
        ${hasAudio ? `
        <button class="play-btn shrink-0" data-audio="${escapeHtml(it.audio)}" aria-label="Écouter">
          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
          <span>Écouter</span>
        </button>` : `<span class="w-8 shrink-0"></span>`}
        <div class="flex-1 min-w-0">
          <p class="lang-text text-lg text-ink-900 truncate" title="${escapeHtml(it.langText)}">${escapeHtml(it.langText)}</p>
          <p class="text-sm text-ink-500 truncate" title="${escapeHtml(it.frenchText)}">${escapeHtml(it.frenchText)}</p>
        </div>
        <div class="text-xs text-ink-400 hidden sm:block whitespace-nowrap">
          Module ${mod.num}
        </div>
      </article>
    `;
  }

  filter.addEventListener('change', update);
  search.addEventListener('input', update);
  update();
}

function renderAPropos() {
  mountTemplate('tpl-apropos');
}

/* ---------- Leçons ---------- */

const MODULE_ORDER = [
  /* Langues Nationales */
  'M1-diversite',
  'M2-segmentaux',
  'M3-suprasegmentaux',
  'M4-syntagme-nominal',
  'M5-syntagme-verbal',
  'M6-phrase',
  'M7-quotidien-1',
  'M8-quotidien-2',
  /* Cultures Nationales */
  'MC1-diversite-culturelle',
  'MC2-modes-de-vie',
  'MC3-evenements',
  'MC4-communaute-1',
  'MC5-communaute-2',
];

function renderLecons() {
  mountTemplate('tpl-lecons');
  // Update title with current language name
  const leconsTitleEl = $('#lecons-title');
  if (leconsTitleEl) leconsTitleEl.textContent = `Leçons — ${state.currentLangName}`;
  const root = $('#lecons-modules');
  const filter = $('#lecons-filter');

  function update() {
    const sel = filter.value;
    const lessons = state.lessons.filter(L => !sel || L.module === sel);

    // Regrouper par module en respectant l'ordre MINESEC
    const byMod = {};
    for (const L of lessons) {
      (byMod[L.module] ||= []).push(L);
    }

    if (!lessons.length) {
      root.innerHTML = `<div class="text-center text-ink-400 py-12">Aucune leçon dans ce module.</div>`;
      return;
    }

    // Split modules into langue vs culture domains
    const langMods    = MODULE_ORDER.filter(m => byMod[m] && (MODULES[m]?.type !== 'culture'));
    const cultureMods = MODULE_ORDER.filter(m => byMod[m] && (MODULES[m]?.type === 'culture'));

    function renderDomain(mods, domainTitle, domainColor) {
      if (!mods.length) return '';
      return `
        <div class="mb-2">
          <h2 class="font-serif text-xl font-semibold ${domainColor} mb-4 pb-1 border-b border-ink-100">${domainTitle}</h2>
          <div class="space-y-8">
            ${mods.map(m => {
              const list = byMod[m];
              const meta = MODULES[m] || { num: '?', label: '' };
              return `
                <div>
                  <h3 class="font-serif text-lg text-ink-900 mb-1">Module ${meta.num} — ${escapeHtml(meta.label)}</h3>
                  <p class="text-sm text-ink-500 mb-3">${list.length} leçon${list.length > 1 ? 's' : ''}</p>
                  <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    ${list.map(renderLeconCard).join('')}
                  </div>
                </div>
              `;
            }).join('')}
          </div>
        </div>`;
    }

    root.innerHTML =
      renderDomain(langMods,    '🗣 Langues Nationales',  'text-ink-900') +
      renderDomain(cultureMods, '🏺 Cultures Nationales', 'text-emerald-800');
  }

  filter.addEventListener('change', update);
  update();
}

function renderLeconCard(L) {
  const objectives = L.objectives.slice(0, 2).map(o => escapeHtml(o)).join(' · ');
  const isCulture  = (MODULES[L.module]?.type === 'culture');
  const borderCls  = isCulture ? 'hover:border-emerald-400' : 'hover:border-brand-300';
  const codeCls    = isCulture ? 'text-emerald-700' : 'text-brand-600';
  const badge      = isCulture
    ? `<span class="text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded-full">Culture</span>`
    : '';
  return `
    <a href="#/lecon/${escapeHtml(L.id)}" class="group block bg-white border border-ink-100 rounded-xl p-5 ${borderCls} hover:shadow transition">
      <div class="flex items-center justify-between gap-3 mb-2">
        <span class="font-serif text-2xl ${codeCls}">${escapeHtml(L.code)}</span>
        <div class="flex items-center gap-2">
          ${badge}
          <span class="text-xs text-ink-400 uppercase tracking-wide">${escapeHtml(L.level)}</span>
        </div>
      </div>
      <h3 class="font-semibold text-lg text-ink-900 group-hover:text-brand-700">${escapeHtml(L.title)}</h3>
      <p class="text-sm text-ink-500 mt-2 line-clamp-2">${objectives}</p>
      <div class="mt-3 flex items-center gap-3 text-xs text-ink-400">
        ${L.vocabulary.length ? `<span>${L.vocabulary.length} item${L.vocabulary.length > 1 ? 's' : ''} vocab</span><span>·</span>` : ''}
        <span class="${isCulture ? 'text-emerald-700' : 'text-brand-700'} font-medium">Ouvrir →</span>
      </div>
    </a>
  `;
}

function renderLecon(id) {
  const L = state.lessons.find(x => x.id === id);
  if (!L) {
    $('#app').innerHTML = `
      <div class="bg-amber-50 border border-amber-200 rounded-xl p-6 text-amber-800 max-w-2xl mx-auto">
        <h2 class="font-semibold text-lg">Leçon introuvable</h2>
        <p class="mt-2 text-sm">L'identifiant <code>${escapeHtml(id)}</code> ne correspond à aucune leçon.</p>
        <p class="mt-3"><a class="text-amber-900 underline" href="#/lecons">Retour aux leçons</a></p>
      </div>`;
    return;
  }

  mountTemplate('tpl-lecon');
  const meta = MODULES[L.module] || { num: '?', label: '' };

  $('#lecon-module-tag').textContent = `Module ${meta.num} — ${meta.label}`;
  $('#lecon-title').textContent = L.title;
  $('#lecon-code').textContent = L.code;
  $('#lecon-meta').textContent = `Durée indicative : ${L.duration} · Niveau : ${L.level}`;

  $('#lecon-objectives').innerHTML = L.objectives
    .map(o => `<li>${escapeHtml(o)}</li>`).join('');

  // Panneau enseignant
  $('#lecon-teacher-intro').textContent = L.teacher.intro;
  $('#lecon-teacher-steps').innerHTML = L.teacher.steps.map((s, i) => `
    <li class="relative pl-12">
      <span class="absolute left-0 top-0 w-9 h-9 grid place-items-center rounded-full bg-brand-100 text-brand-700 font-serif font-semibold">${i + 1}</span>
      <div class="font-semibold text-ink-900">${escapeHtml(s.title)}</div>
      <p class="text-sm text-ink-700 mt-1">${escapeHtml(s.instruction)}</p>
    </li>
  `).join('');
  $('#lecon-teacher-freedom').textContent = L.teacher.freedom;
  $('#lecon-teacher-tips').textContent = L.teacher.tips;

  // Panneau élève
  $('#lecon-student-intro').textContent = L.student.intro;
  $('#lecon-student-activities').innerHTML = L.student.activities.map((a, i) => `
    <li class="relative pl-12">
      <span class="absolute left-0 top-0 w-9 h-9 grid place-items-center rounded-full bg-emerald-100 text-emerald-700 font-serif font-semibold">${i + 1}</span>
      <div class="font-semibold text-ink-900">${escapeHtml(a.title)}</div>
      <p class="text-sm text-ink-700 mt-1">${escapeHtml(a.instruction)}</p>
    </li>
  `).join('');
  $('#lecon-student-memo').textContent = L.student.memo;

  // Vocabulaire ALCAM
  $('#lecon-voc-count').textContent = `${L.vocabulary.length} entrée${L.vocabulary.length > 1 ? 's' : ''}`;
  $('#lecon-voc-list').innerHTML = L.vocabulary.map(it => {
    const hasAudio = !!it.audio;
    return `
    <article class="bg-white border border-ink-100 rounded-lg p-3 flex items-center gap-3">
      ${hasAudio ? `
      <button class="play-btn shrink-0" data-audio="${escapeHtml(it.audio)}" aria-label="Écouter">
        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
      </button>` : `<span class="w-8 shrink-0 text-center text-ink-300 text-xs">—</span>`}
      <div class="flex-1 min-w-0">
        <p class="lang-text text-base text-ink-900 truncate" title="${escapeHtml(it.langText)}">${escapeHtml(it.langText)}</p>
        <p class="text-xs text-ink-500 truncate" title="${escapeHtml(it.frenchText)}">${escapeHtml(it.frenchText)}</p>
      </div>
    </article>`;
  }).join('');
  $$('#lecon-voc-list [data-audio]').forEach(btn => {
    btn.addEventListener('click', () => playAudio(state.audioBase + btn.dataset.audio, btn));
  });

  // Ressources musicales EMAC
  const emacSection = $('#lecon-emac-section');
  if (emacSection) {
    const resources = L.emacResources || [];
    if (resources.length > 0) {
      emacSection.classList.remove('hidden');
      $('#lecon-emac-list').innerHTML = resources.map(e => `
        <article class="bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-center gap-3">
          <button class="play-btn shrink-0 text-amber-700" data-emac="${escapeHtml(e.file)}" aria-label="Écouter ${escapeHtml(e.title)}">
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
          </button>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-ink-900 truncate">${escapeHtml(e.title)}</p>
            <p class="text-xs text-ink-500">${escapeHtml(e.genre)} · ${escapeHtml(e.ethnic)}</p>
          </div>
        </article>
      `).join('');
      $$('#lecon-emac-list [data-emac]').forEach(btn => {
        btn.addEventListener('click', () => playAudio(state.emacBase + btn.dataset.emac, btn));
      });
    } else {
      emacSection.classList.add('hidden');
    }
  }

  // Bascule mobile teacher / student
  applyPaneVisibility();
  $$('.lecon-toggle-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      state.preferredPane = btn.dataset.pane;
      $$('.lecon-toggle-btn').forEach(b => b.classList.toggle('is-active', b === btn));
      applyPaneVisibility();
    });
  });

  // Navigation prev / next
  const idx = state.lessons.findIndex(x => x.id === id);
  const prev = state.lessons[idx - 1];
  const next = state.lessons[idx + 1];
  $('#lecon-nav').innerHTML = `
    ${prev
      ? `<a href="#/lecon/${escapeHtml(prev.id)}" class="inline-flex items-center gap-2 text-sm text-ink-700 hover:text-brand-700">
           <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
           ${escapeHtml(prev.code)} · ${escapeHtml(prev.title)}
         </a>`
      : '<span></span>'}
    ${next
      ? `<a href="#/lecon/${escapeHtml(next.id)}" class="inline-flex items-center gap-2 text-sm text-ink-700 hover:text-brand-700">
           ${escapeHtml(next.code)} · ${escapeHtml(next.title)}
           <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
         </a>`
      : '<span></span>'}
  `;
}

function applyPaneVisibility() {
  const teacher = $('#lecon-teacher-pane');
  const student = $('#lecon-student-pane');
  // Sur lg+, les deux panneaux s'affichent côte-à-côte (toggle masqué).
  // Sur < lg, le toggle pilote la visibilité.
  if (!teacher || !student) return;
  // On utilise une classe spécifique pour ne masquer qu'en mode mobile
  teacher.classList.toggle('is-hidden-mobile', state.preferredPane !== 'teacher');
  student.classList.toggle('is-hidden-mobile', state.preferredPane !== 'student');
  $$('.lecon-toggle-btn').forEach(b => {
    b.classList.toggle('is-active', b.dataset.pane === state.preferredPane);
  });
}

/* ---------- Exercices ---------- */

function renderExercices() {
  mountTemplate('tpl-exercices');
  // Update title and exercise labels with current language name
  const exoTitleEl = $('#exo-title');
  if (exoTitleEl) exoTitleEl.textContent = `Exercices interactifs — ${state.currentLangName}`;
  const lang = state.currentLangName;
  const reconLabel = $('#exo-label-reconnaissance');
  if (reconLabel) reconLabel.textContent = `Texte ${lang} → Audio correspondant`;
  const lectureLabel = $('#exo-label-lecture');
  if (lectureLabel) lectureLabel.textContent = `Texte ${lang} → Traduction française`;
  const compDesc = $('#exo-desc-comprehension');
  if (compDesc) compDesc.textContent = `Écoute la phrase en ${lang} et choisis la bonne traduction française parmi quatre.`;
  const reconDesc = $('#exo-desc-reconnaissance');
  if (reconDesc) reconDesc.textContent = `Lis la phrase en ${lang} et choisis, parmi trois enregistrements, celui qui lui correspond.`;
  const lectureDesc = $('#exo-desc-lecture');
  if (lectureDesc) lectureDesc.textContent = `Sans audio, traduis depuis le ${lang} écrit. Idéal pour réviser la phonologie de l'AGLC.`;
  $$('.exo-card').forEach(card => {
    card.addEventListener('click', () => startExercise(card.dataset.exo));
  });
}

function startExercise(kind) {
  const stage = $('#exo-stage');
  $('#exo-menu').classList.add('hidden');
  stage.classList.remove('hidden');
  state.scores[kind] = { correct: 0, total: 0 };

  function newRound() {
    const round =
      kind === 'comprehension'  ? buildComprehensionRound() :
      kind === 'reconnaissance' ? buildReconnaissanceRound() :
      kind === 'lecture'        ? buildLectureRound() :
      kind === 'dictee'         ? buildDicteeRound() : null;

    stage.innerHTML = renderRound(kind, round);
    bindRound(kind, round, stage, newRound);
  }

  $('#exo-stage').innerHTML = '';
  newRound();
}

function backToMenu() {
  $('#exo-menu').classList.remove('hidden');
  $('#exo-stage').classList.add('hidden');
  $('#exo-stage').innerHTML = '';
  stopCurrentAudio();
}

function buildComprehensionRound() {
  // Audio → traduction française (seulement pour les langues avec audio)
  const pool = state.vocabWithFr.filter(it => it.audio);
  if (!pool.length) return buildLectureRound(); // fallback si pas d'audio
  const target = pick(pool);
  const choices = shuffle([target, ...pickN(pool, 3, new Set([target]))]).map(it => ({
    label: it.frenchText, correct: it === target,
  }));
  return { target, choices, mode: 'audio-fr' };
}

function buildReconnaissanceRound() {
  // Texte langue → audio
  const pool = state.vocabWithFr.filter(it => it.audio);
  if (!pool.length) return buildLectureRound();
  const target = pick(pool);
  const choices = shuffle([target, ...pickN(pool, 2, new Set([target]))]).map(it => ({
    label: 'Écouter', audio: it.audio, correct: it === target,
  }));
  return { target, choices, mode: 'text-audio' };
}

function buildLectureRound() {
  const target = pick(state.vocabWithFr);
  const choices = shuffle([target, ...pickN(state.vocabWithFr, 3, new Set([target]))]).map(it => ({
    label: it.frenchText, correct: it === target,
  }));
  return { target, choices, mode: 'text-fr' };
}

function buildDicteeRound() {
  const pool = state.vocabWithFr.filter(it => it.audio && it.langText.length <= 25);
  if (!pool.length) return buildLectureRound();
  const target = pick(pool);
  return { target, mode: 'dictee' };
}

function renderRound(kind, round) {
  const score = state.scores[kind];
  const pct = score.total === 0 ? 0 : Math.round(100 * score.correct / score.total);
  const header = `
    <div class="bg-white border border-ink-100 rounded-xl p-5 mb-5">
      <div class="flex items-center justify-between gap-3">
        <button id="exo-back" class="text-sm text-ink-500 hover:text-ink-700 inline-flex items-center gap-1">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
          Retour
        </button>
        <div class="text-sm text-ink-500">
          <span class="font-medium text-ink-700">${EXO_LABELS[kind]}</span>
          · score ${score.correct}/${score.total} (${pct}%)
        </div>
      </div>
      <div class="progress-track mt-3">
        <div class="progress-fill" style="width: ${pct}%"></div>
      </div>
    </div>
  `;

  if (round.mode === 'dictee') {
    return header + `
      <div class="bg-white border border-ink-100 rounded-xl p-6">
        <p class="text-sm text-ink-500 mb-2">Écoute la phrase et écris-la dans l'orthographe AGLC.</p>
        <button class="play-btn" id="exo-play" data-audio="${escapeHtml(round.target.audio)}">
          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
          <span>Écouter</span>
        </button>
        <textarea id="exo-input" rows="3" class="lang-text mt-4 w-full border border-ink-200 rounded-md p-3 text-lg focus:outline-none focus:ring-2 focus:ring-brand-300" placeholder="Écris ce que tu entends…"></textarea>
        <div class="mt-3 flex flex-wrap gap-2">
          <button id="exo-validate" class="px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg text-sm font-medium">Valider</button>
          <button id="exo-skip" class="px-4 py-2 bg-white border border-ink-200 hover:border-ink-300 text-ink-700 rounded-lg text-sm">Passer</button>
        </div>
        <div id="exo-feedback" class="mt-4 hidden"></div>
      </div>
    `;
  }

  if (round.mode === 'audio-fr') {
    return header + `
      <div class="bg-white border border-ink-100 rounded-xl p-6">
        <p class="text-sm text-ink-500 mb-2">Écoute la phrase et choisis la bonne traduction.</p>
        <button class="play-btn" id="exo-play" data-audio="${escapeHtml(round.target.audio)}">
          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
          <span>Écouter</span>
        </button>
        <div class="grid sm:grid-cols-2 gap-3 mt-5">
          ${round.choices.map((c, i) => `
            <button class="choice" data-i="${i}" data-correct="${c.correct ? '1' : '0'}">${escapeHtml(c.label)}</button>
          `).join('')}
        </div>
        <div id="exo-feedback" class="mt-4 hidden"></div>
      </div>
    `;
  }

  if (round.mode === 'text-audio') {
    return header + `
      <div class="bg-white border border-ink-100 rounded-xl p-6">
        <p class="text-sm text-ink-500 mb-2">Lis cette phrase et choisis l'audio qui lui correspond.</p>
        <p class="lang-text text-2xl text-ink-900 my-4">${escapeHtml(round.target.langText)}</p>
        <div class="grid sm:grid-cols-3 gap-3 mt-5">
          ${round.choices.map((c, i) => `
            <button class="choice flex items-center justify-between" data-i="${i}" data-correct="${c.correct ? '1' : '0'}" data-audio="${escapeHtml(c.audio)}">
              <span class="inline-flex items-center gap-2">
                <span class="w-8 h-8 grid place-items-center bg-ink-900 text-white rounded-md">
                  <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                </span>
                Audio ${i + 1}
              </span>
              <span class="text-xs text-ink-400">à choisir</span>
            </button>
          `).join('')}
        </div>
        <div id="exo-feedback" class="mt-4 hidden"></div>
      </div>
    `;
  }

  if (round.mode === 'text-fr') {
    return header + `
      <div class="bg-white border border-ink-100 rounded-xl p-6">
        <p class="text-sm text-ink-500 mb-2">Lis cette phrase en ${escapeHtml(state.currentLangName)} et choisis sa traduction française.</p>
        <p class="lang-text text-2xl text-ink-900 my-4">${escapeHtml(round.target.langText)}</p>
        <div class="grid sm:grid-cols-2 gap-3 mt-5">
          ${round.choices.map((c, i) => `
            <button class="choice" data-i="${i}" data-correct="${c.correct ? '1' : '0'}">${escapeHtml(c.label)}</button>
          `).join('')}
        </div>
        <div id="exo-feedback" class="mt-4 hidden"></div>
      </div>
    `;
  }
}

function bindRound(kind, round, root, nextRound) {
  $('#exo-back')?.addEventListener('click', backToMenu);

  if (round.mode === 'dictee') {
    const playBtn = $('#exo-play');
    const input = $('#exo-input');
    const fb = $('#exo-feedback');
    playBtn.addEventListener('click', () => playAudio(state.audioBase + round.target.audio, playBtn));

    function evaluate() {
      const user = input.value.trim();
      const expected = round.target.langText;
      const sim = similarity(user, expected);
      const ok = sim >= 80;
      state.scores[kind].total += 1;
      if (ok) state.scores[kind].correct += 1;

      fb.classList.remove('hidden');
      fb.innerHTML = `
        <div class="rounded-lg p-4 ${ok ? 'bg-emerald-50 border border-emerald-200' : 'bg-amber-50 border border-amber-200'}">
          <p class="text-sm font-semibold ${ok ? 'text-emerald-800' : 'text-amber-800'}">
            ${ok ? '✓ Bien' : '≈ À améliorer'} — similarité ${sim}%
          </p>
          <div class="mt-2 text-sm">
            <p><span class="text-ink-500">Réponse attendue :</span> <span class="lang-text">${escapeHtml(expected)}</span></p>
            <p><span class="text-ink-500">Traduction :</span> <em class="text-ink-600">${escapeHtml(round.target.frenchText)}</em></p>
          </div>
          <button id="exo-next" class="mt-3 px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg text-sm">Suivant</button>
        </div>
      `;
      $('#exo-next').addEventListener('click', nextRound);
      $('#exo-validate').setAttribute('disabled', 'true');
      $('#exo-skip').setAttribute('disabled', 'true');
      input.setAttribute('readonly', 'true');
    }

    $('#exo-validate').addEventListener('click', evaluate);
    $('#exo-skip').addEventListener('click', () => {
      state.scores[kind].total += 1;
      fb.classList.remove('hidden');
      fb.innerHTML = `
        <div class="rounded-lg p-4 bg-ink-100 border border-ink-200">
          <p class="text-sm font-semibold text-ink-700">Phrase passée</p>
          <p class="mt-2 text-sm"><span class="text-ink-500">Réponse :</span> <span class="lang-text">${escapeHtml(round.target.langText)}</span></p>
          <p class="text-sm"><em class="text-ink-600">${escapeHtml(round.target.frenchText)}</em></p>
          <button id="exo-next" class="mt-3 px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg text-sm">Suivant</button>
        </div>
      `;
      $('#exo-next').addEventListener('click', nextRound);
      $('#exo-validate').setAttribute('disabled', 'true');
      $('#exo-skip').setAttribute('disabled', 'true');
    });

    setTimeout(() => input.focus(), 50);
    return;
  }

  // Tous les autres modes : QCM
  const playBtn = $('#exo-play');
  if (playBtn) {
    playBtn.addEventListener('click', () => playAudio(state.audioBase + round.target.audio, playBtn));
    // jouer automatiquement après un court délai
    setTimeout(() => playBtn.click(), 200);
  }

  const choices = $$('#exo-stage .choice');
  choices.forEach(btn => {
    btn.addEventListener('click', () => {
      // text-audio : jouer l'audio cliqué (premier clic), valider au second clic ?
      // Simplification : jouer ET valider en même temps.
      if (round.mode === 'text-audio' && btn.dataset.audio) {
        playAudio(state.audioBase + btn.dataset.audio, btn);
      }
      if (btn.dataset.evaluated) return;
      // Marquer toutes les choix comme évalués
      choices.forEach(b => { b.dataset.evaluated = '1'; b.setAttribute('disabled', 'true'); });
      const ok = btn.dataset.correct === '1';
      state.scores[kind].total += 1;
      if (ok) state.scores[kind].correct += 1;
      // Retour visuel
      choices.forEach(b => {
        if (b.dataset.correct === '1') b.classList.add('is-correct');
        if (b === btn && !ok) b.classList.add('is-wrong');
      });
      const fb = $('#exo-feedback');
      fb.classList.remove('hidden');
      fb.innerHTML = `
        <div class="rounded-lg p-4 ${ok ? 'bg-emerald-50 border border-emerald-200' : 'bg-amber-50 border border-amber-200'}">
          <p class="text-sm font-semibold ${ok ? 'text-emerald-800' : 'text-amber-800'}">
            ${ok ? '✓ Bonne réponse' : '✗ Réponse incorrecte'}
          </p>
          <div class="mt-2 text-sm">
            <p><span class="text-ink-500">Phrase :</span> <span class="lang-text">${escapeHtml(round.target.langText)}</span></p>
            <p><span class="text-ink-500">Traduction :</span> <em class="text-ink-600">${escapeHtml(round.target.frenchText)}</em></p>
          </div>
          <button id="exo-next" class="mt-3 px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg text-sm">Question suivante</button>
        </div>
      `;
      $('#exo-next').addEventListener('click', nextRound);
    });
  });
}

/* ---------- Démarrage ---------- */

(async function init() {
  // Menu mobile
  $('#mobile-toggle').addEventListener('click', () => {
    $('#mobile-menu').classList.toggle('hidden');
  });

  // Récupérer la langue depuis le hash si spécifiée (#/langue/basaa)
  const langMatch = location.hash.match(/#\/langue\/([a-z-]+)/);
  if (langMatch) state.currentLang = langMatch[1];

  try {
    await loadData();
  } catch (e) {
    $('#app').innerHTML = `
      <div class="bg-amber-50 border border-amber-200 rounded-xl p-6 text-amber-800 max-w-2xl mx-auto">
        <h2 class="font-semibold text-lg">Impossible de charger les données</h2>
        <p class="mt-2 text-sm">Vérifiez que <code>data/languages.json</code> et les fichiers JSON de langue sont présents et accessibles.
        Si vous testez en local, servez le dossier avec <code>python -m http.server</code>.</p>
        <pre class="mt-3 text-xs bg-white p-2 rounded">${escapeHtml(String(e))}</pre>
      </div>`;
    return;
  }

  render();
})();
