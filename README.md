# ALCAM Apprendre — Prototype d'outil interactif pour l'enseignement des langues camerounaises

Prototype web statique, déployable sur **GitHub Pages** sans aucune étape de compilation.
Réalisé dans le cadre du cours **LACC2342 — Outils pour la production du matériel didactique
numérique et multimédia en langues camerounaises**, dispensé à l'École Normale Supérieure
de Yaoundé par le **Prof. Emmanuel Ngue Um**.

Aperçu : un site responsive qui propose **dix-neuf leçons clé-en-main** pour
le bulu (fiche enseignant + fiche élève) ainsi qu'une banque de **184 phrases**
audio (transcription AGLC + traduction française) et **quatre familles d'exercices
interactifs**, le tout aligné sur les programmes officiels MINESEC. L'outil est
conçu pour soulager le travail des enseignants — y compris ceux qui ne sont pas
locuteurs natifs fluides — et pour rendre les apprentissages immédiatement
accessibles aux élèves.

## Démonstration en local

```bash
git clone https://github.com/<votre-org>/alcam-apprendre.git
cd alcam-apprendre
python3 -m http.server 8080
```

Puis ouvrir <http://localhost:8080> dans un navigateur.

> Servir via un vrai serveur (et non en `file://`) est nécessaire car l'application
> charge ses données par `fetch()`.

## Déploiement sur GitHub Pages

1. Créer un dépôt public, par exemple `alcam-apprendre`.
2. Pousser tout le contenu de ce dossier à la racine de la branche `main`.
3. Sur GitHub : **Settings → Pages**.
   - **Source** : *Deploy from a branch*.
   - **Branch** : `main` / `/ (root)`.
4. Quelques secondes plus tard, le site est accessible sur
   `https://<votre-org>.github.io/alcam-apprendre/`.

Le fichier `.nojekyll` à la racine désactive le filtrage Jekyll, ce qui évite que
GitHub Pages ignore certains fichiers (notamment ceux commençant par `_`).

## Structure du dépôt

```
prototype-langues-camerounaises/
├── index.html               # point d'entrée SPA
├── app.js                   # logique : routage, leçons, exercices, lecteur audio
├── styles.css               # styles complémentaires à Tailwind (CDN)
├── build_data.py            # script Python : fusionne mapping.tsv + ALCAM_*.tsv
├── build_lessons.py         # script Python : génère lessons_bulu.json (19 fiches)
├── data/
│   ├── languages.json       # catalogue des 16 langues ALCAM
│   ├── bulu.json            # 184 phrases bulu (177 avec traduction française)
│   └── lessons_bulu.json    # 19 leçons clé-en-main (fiche prof + fiche élève)
├── audio/
│   └── bulu/                # 184 fichiers MP3 (≈ 11 Mo)
├── assets/
│   └── favicon.svg
├── .nojekyll
├── .gitignore
└── README.md
```

## Modèle de données (`data/<langue>.json`)

Chaque langue est un tableau d'objets dont les champs sont :

| champ         | type   | description                                                            |
|---------------|--------|------------------------------------------------------------------------|
| `id`          | string | identifiant court (12 caractères du hash audio)                        |
| `audio`       | string | nom du fichier MP3, relatif à `audio/<langue>/`                        |
| `langText`    | string | phrase en langue, transcription AGLC                                   |
| `langWord`    | string | mot-clé en langue (souvent identique à `langText` pour le vocabulaire) |
| `frenchText`  | string | traduction française de la phrase (peut être vide)                     |
| `frenchWord`  | string | traduction française du mot-clé (peut être vide)                       |
| `pos`         | string | partie du discours (`n`, `v`…)                                         |
| `classNoun`   | string | classe nominale bantoue (1, 2, 3…)                                     |
| `module`      | string | code module MINESEC : `M2-segmentaux`, `M3-suprasegmentaux`, `M4-syntagme-nominal`, `M5-syntagme-verbal`, `M6-phrase` |
| `matchedBy`   | string | `langex` ou `word` selon la stratégie de jointure (informatif)         |

## Ajouter une nouvelle langue ALCAM

Pour étendre le prototype à l'une des 15 autres langues du catalogue :

1. **Préparer les données**.
   - Récupérer le `mapping.tsv` du dataset SABRE/TTS (colonnes `audio_filename`, `key`, `sentence`).
   - Récupérer le TSV ALCAM correspondant (colonnes `Word`, `French`, `LangEx`, `FrenchEx`, `POS`, `Class`…).
   - Lancer `python3 build_data.py` après avoir adapté les chemins en haut du script.
2. **Déposer** le JSON produit dans `data/<langue>.json`.
3. **Copier** les MP3 dans `audio/<langue>/`.
4. **Activer la langue** dans `data/languages.json` en passant `"audio": true` pour la langue concernée.
5. (optionnel) Ajouter la prise en charge multi-langue dans `app.js` (variable `state.audioBase`).

## Modules MINESEC pris en charge

Les phrases bulu sont automatiquement réparties dans les modules suivants à partir de
la partie du discours (`pos`) et de la classe nominale (`classNoun`) :

- **Module II — Productions segmentales** (par défaut)
- **Module III — Suprasegmentaux** (à enrichir manuellement avec un champ `tonal`)
- **Module IV — Syntagme nominal** (`pos = n`)
- **Module V — Syntagme verbal** (`pos = v`)
- **Module VI — La phrase**

## Leçons clé-en-main

Le fichier `data/lessons_bulu.json` (généré par `build_lessons.py`) découpe ces cinq
modules en dix-neuf leçons d'environ 60 minutes. Chaque leçon est pensée pour être
utilisable telle quelle, y compris par un enseignant qui ne serait pas locuteur natif
fluide du bulu : le plan en cinq étapes laisse une réelle liberté pédagogique, et la
fiche élève propose des activités concrètes alignées sur les objectifs MINESEC.

| Code   | Module | Titre |
|--------|--------|-------|
| II.1   | II     | Mes premiers mots en bulu |
| II.2   | II     | Voyelles ouvertes et voyelles fermées |
| III.1  | III    | Tons hauts et tons bas |
| III.2  | III    | Le ton qui monte, le ton qui descend |
| III.3  | III    | Paires aux tons opposés |
| III.4  | III    | Rythme et longueur des syllabes |
| IV.1   | IV     | Désigner les objets de la maison |
| IV.2   | IV     | Compter en bulu |
| IV.3   | IV     | Décrire avec des adjectifs |
| V.1    | V      | Verbes d'action du quotidien |
| V.2    | V      | La famille et les personnes |
| V.3    | V      | Les animaux du village et de la forêt |
| V.4    | V      | Manger, boire, cultiver |
| VI.1   | VI     | Phrases existentielles : « il y a » |
| VI.2   | VI     | Décrire un objet par sa qualité |
| VI.3   | VI     | Localiser : ici, là, là-bas |
| VI.4   | VI     | Comparer et opposer |
| VI.5   | VI     | Petits récits : raconter une scène |
| VI.6   | VI     | Demander, répondre, dialoguer |

### Schéma d'une leçon (`data/lessons_bulu.json`)

```jsonc
{
  "id": "II-1",
  "code": "II.1",
  "module": "M2-segmentaux",
  "title": "Mes premiers mots en bulu",
  "duration": "60 min",
  "level": "6e",
  "objectives": ["...", "..."],
  "vocabulary": [ /* items ALCAM (audio + langText + frenchText + …) */ ],
  "teacher": {
    "intro":   "Cette leçon dure environ 60 min…",
    "steps":   [ {"title": "Mise en route (5 min)", "instruction": "..."} , … ],
    "freedom": "Si les élèves accrochent, prolongez par…",
    "tips":    "Si vous n'êtes pas locuteur natif…"
  },
  "student": {
    "intro":      "Aujourd'hui nous découvrons…",
    "activities": [ {"title": "Activité 1 — Écouter et répéter", "instruction": "..."} , … ],
    "memo":       "Le bulu utilise des sons absents du français (ə, ɔ, ɛ)…"
  }
}
```

### Visualisation dans l'app

- **`/lecons`** — index de toutes les leçons, filtrable par module.
- **`/lecon/<id>`** — détail d'une leçon avec deux panneaux :
  - sur **grand écran (≥ 1024px)**, fiche enseignant et fiche élève s'affichent
    **côte à côte**, ce qui permet à l'enseignant de préparer son cours avec la
    fiche élève déjà sous les yeux ;
  - sur **mobile/tablette**, un sélecteur permet de basculer d'un panneau à l'autre.

### Régénérer les leçons

```bash
python3 build_lessons.py
```

Le script lit `data/bulu.json` et reconstitue intégralement `data/lessons_bulu.json`
à partir du plan inscrit en haut de `build_lessons.py`. Les filtres thématiques
(par regex sur la traduction française et la transcription) garantissent que
chaque leçon ne mobilise **que des données ALCAM existantes** ; aucune phrase
n'est inventée.

## Quatre familles d'exercices

| Code              | Modalité                      | Niveau MINESEC ciblé        |
|-------------------|-------------------------------|------------------------------|
| `comprehension`   | Audio → Traduction française  | Compréhension orale, II → VI |
| `reconnaissance`  | Texte bulu → Audio            | Identification phonique, II  |
| `lecture`         | Texte bulu → Traduction       | Lecture silencieuse, IV → VI |
| `dictee`          | Audio → Transcription AGLC    | Production écrite, II-III    |

Le score de la dictée est calculé par similarité de Levenshtein normalisée
(`>= 80%` est considéré comme une réussite). Aucun score n'est persisté : tout
est en mémoire le temps de la session.

## Crédits

- **Données ALCAM** : Institut des Humanités numériques africaines, publiées
  sur [Mozilla Data Collective](https://mozilladatacollective.com/organization/cmfv3ichk000amd07piai0zoz).
- **Audios bulu** : générés via SABRE et publiés sur mdc.
- **Conception pédagogique & encadrement** : Prof. Emmanuel Ngue Um (ENS Yaoundé).
- **Code** : licence MIT.
- **Données et audios** : licence CC-BY (attribution aux locuteurs et au dépositaire).

## Liens utiles

- Programme officiel MINESEC — Langues Nationales 6e/5e (août 2014) et 4e/3e (décembre 2014).
- Mozilla Data Collective : <https://mozilladatacollective.com>
- SABRE — Speech Annotation and Basic Recording Environment : <https://mdc-dataset-toolbox-ifuhj.ondigitalocean.app/sabre>
- Syllabus du cours LACC2342 : <https://github.com/Ngue-Um/syllabi>
- Syllabus prérequis (LCC2 — Technologies vocales) : <https://github.com/Ngue-Um/syllabi/blob/main/Technologies%20vocales%20pour%20les%20langues%20africaines%20peu%20dot%C3%A9es.md>

---

> Ce prototype n'est pas un produit fini : c'est un **gabarit pédagogique** que les
> élèves-professeurs doivent pouvoir cloner, étendre à leur langue de référence,
> et déployer eux-mêmes sur leur propre dépôt GitHub Pages dans le cadre du projet du
> semestre.
