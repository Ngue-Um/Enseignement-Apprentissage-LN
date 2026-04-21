# ALCAM Apprendre — Prototype d'outil interactif pour l'enseignement des langues camerounaises

Prototype web statique, déployable sur **GitHub Pages** sans aucune étape de compilation.
Réalisé dans le cadre du cours **LACC2342 — Outils pour la production du matériel didactique
numérique et multimédia en langues camerounaises**, dispensé à l'École Normale Supérieure
de Yaoundé par le **Prof. Emmanuel Ngue Um**.

Aperçu : un site responsive qui permet de consulter le vocabulaire bulu (audio MP3 +
transcription AGLC + traduction française) et de réaliser quatre familles d'exercices
interactifs alignés sur les programmes officiels MINESEC.

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
├── app.js                   # logique : routage, exercices, lecteur audio
├── styles.css               # styles complémentaires à Tailwind (CDN)
├── build_data.py            # script Python : fusionne mapping.tsv + ALCAM_*.tsv
├── data/
│   ├── languages.json       # catalogue des 16 langues ALCAM
│   └── bulu.json            # 184 phrases bulu (152 avec traduction française)
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
