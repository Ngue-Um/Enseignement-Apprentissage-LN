/* ALCAM Apprendre — application monopage (vanilla JS).
 * Routes par hash :
 *   #/             -> Accueil
 *   #/catalogue    -> Catalogue des 16 langues
 *   #/vocabulaire  -> Liste des phrases bulu
 *   #/exercices    -> Quatre familles d'exercices
 *   #/a-propos     -> À propos
 */

const state = {
  langues: [],     // catalogue des 16 langues ALCAM
  bulu: [],        // phrases bulu enrichies
  buluWithFr: [],  // phrases bulu qui ont une traduction française non vide
  audioBase: 'audio/bulu/',
  currentAudio: null,
  scores: {        // scores en mémoire seulement (jamais persistés)
    comprehension: { correct: 0, total: 0 },
    reconnaissance: { correct: 0, total: 0 },
    lecture: { correct: 0, total: 0 },
    dictee: { correct: 0, total: 0 },
  }
};

const MODULES = {
  'M2-segmentaux':       { num: 'II',  label: 'Productions segmentales' },
  'M3-suprasegmentaux':  { num: 'III', label: 'Suprasegmentaux' },
  'M4-syntagme-nominal': { num: 'IV',  label: 'Syntagme nominal' },
  'M5-syntagme-verbal':  { num: 'V',   label: 'Syntagme verbal' },
  'M6-phrase':           { num: 'VI',  label: 'La phrase' },
};

const EXO_LABELS = {
  comprehension:  'Audio → Traduction française',
  reconnaissance: 'Texte bulu → Audio',
  lecture:        'Texte bulu → Traduction française',
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
  const [langues, bulu] = await Promise.all([
    fetch('data/languages.json').then(r => r.json()),
    fetch('data/bulu.json').then(r => r.json()),
  ]);
  state.langues = langues;
  state.bulu = bulu;
  state.buluWithFr = bulu.filter(b => b.frenchText && b.langText);
  return { langues, bulu };
}

/* ---------- Routeur ---------- */

const routes = {
  '/':           renderHome,
  '/catalogue':  renderCatalogue,
  '/vocabulaire': renderVocabulaire,
  '/exercices':  renderExercices,
  '/a-propos':   renderAPropos,
};

function getRoute() {
  const h = location.hash.replace(/^#/, '') || '/';
  return routes[h] ? h : '/';
}

function navigate(path) {
  if (location.hash !== '#' + path) location.hash = path;
}

function setActiveNav(path) {
  $$('.nav-link').forEach(a => {
    const target = a.getAttribute('href').replace(/^#/, '');
    a.classList.toggle('active', target === path);
  });
}

function render() {
  stopCurrentAudio();
  const path = getRoute();
  setActiveNav(path);
  routes[path]();
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
  $('#stat-phrases').textContent = state.buluWithFr.length;
  $('#stat-audios').textContent = state.bulu.length;

  // Phrase de démo : prendre un exemple sympa
  const demo = state.buluWithFr.find(d => d.langText.length > 8 && d.langText.length < 25)
            || state.buluWithFr[0];
  if (demo) {
    $('#demo-lang').textContent = demo.langText;
    $('#demo-french').textContent = demo.frenchText;
    const btn = $('#demo-play');
    btn.addEventListener('click', () => playAudio(state.audioBase + demo.audio, btn));
  }
}

function renderCatalogue() {
  mountTemplate('tpl-catalogue');
  const grid = $('#catalogue-grid');
  grid.innerHTML = state.langues.map(l => `
    <article class="bg-white rounded-xl border border-ink-100 p-5 ${l.audio ? '' : 'opacity-90'}">
      <div class="flex items-start justify-between gap-3">
        <div>
          <h3 class="font-serif text-xl text-ink-900 lang-text">${escapeHtml(l.name)}</h3>
          <div class="text-xs text-ink-500 mt-0.5">ISO ${escapeHtml(l.iso)} · ${escapeHtml(l.family)}</div>
        </div>
        ${l.audio
          ? '<span class="text-xs font-semibold bg-emerald-100 text-emerald-800 px-2 py-1 rounded-full">Audio dispo</span>'
          : '<span class="text-xs font-semibold bg-ink-100 text-ink-500 px-2 py-1 rounded-full">À venir</span>'}
      </div>
      <p class="text-sm text-ink-500 mt-3">
        ${l.audio
          ? 'Dataset complet : audios MP3, transcription AGLC, traduction française. Disponible dans Vocabulaire et Exercices.'
          : 'Dataset textuel disponible sur mdc. La couche audio est en cours de constitution par les élèves-professeurs.'}
      </p>
      <div class="mt-4 flex items-center gap-2">
        ${l.audio
          ? `<a href="#/vocabulaire" class="text-sm font-medium text-brand-700 hover:text-brand-800">Explorer →</a>`
          : ''}
        <a href="https://mozilladatacollective.com/organization/cmfv3ichk000amd07piai0zoz" target="_blank" rel="noopener"
           class="text-sm text-ink-500 hover:text-ink-700 underline">mdc</a>
      </div>
    </article>
  `).join('');
}

function renderVocabulaire() {
  mountTemplate('tpl-vocabulaire');
  const list = $('#vocab-list');
  const empty = $('#vocab-empty');
  const filter = $('#vocab-filter');
  const search = $('#vocab-search');

  function update() {
    const mod = filter.value;
    const q = normalizeForCompare(search.value);
    const items = state.buluWithFr.filter(it => {
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
    return `
      <article class="bg-white border border-ink-100 rounded-lg p-4 flex items-center gap-4">
        <button class="play-btn shrink-0" data-audio="${escapeHtml(it.audio)}" aria-label="Écouter">
          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
          <span>Écouter</span>
        </button>
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

/* ---------- Exercices ---------- */

function renderExercices() {
  mountTemplate('tpl-exercices');
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
  // Audio bulu, choisir la bonne traduction française parmi 4
  const target = pick(state.buluWithFr);
  const distractors = pickN(
    state.buluWithFr,
    3,
    new Set([target])
  );
  const choices = shuffle([target, ...distractors]).map(it => ({
    label: it.frenchText,
    correct: it === target,
  }));
  return { target, choices, mode: 'audio-fr' };
}

function buildReconnaissanceRound() {
  // Texte bulu, choisir l'audio correspondant parmi 3
  const target = pick(state.buluWithFr);
  const distractors = pickN(state.buluWithFr, 2, new Set([target]));
  const choices = shuffle([target, ...distractors]).map(it => ({
    label: 'Écouter',
    audio: it.audio,
    correct: it === target,
  }));
  return { target, choices, mode: 'text-audio' };
}

function buildLectureRound() {
  const target = pick(state.buluWithFr);
  const distractors = pickN(state.buluWithFr, 3, new Set([target]));
  const choices = shuffle([target, ...distractors]).map(it => ({
    label: it.frenchText,
    correct: it === target,
  }));
  return { target, choices, mode: 'text-fr' };
}

function buildDicteeRound() {
  const target = pick(state.buluWithFr.filter(it => it.langText.length <= 25));
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
        <p class="text-sm text-ink-500 mb-2">Lis cette phrase en bulu et choisis sa traduction française.</p>
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

  try {
    await loadData();
  } catch (e) {
    $('#app').innerHTML = `
      <div class="bg-amber-50 border border-amber-200 rounded-xl p-6 text-amber-800 max-w-2xl mx-auto">
        <h2 class="font-semibold text-lg">Impossible de charger les données</h2>
        <p class="mt-2 text-sm">Vérifiez que <code>data/bulu.json</code> et <code>data/languages.json</code> sont présents et accessibles.
        Si vous testez en local, servez le dossier avec <code>python -m http.server</code>.</p>
        <pre class="mt-3 text-xs bg-white p-2 rounded">${escapeHtml(String(e))}</pre>
      </div>`;
    return;
  }

  render();
})();
