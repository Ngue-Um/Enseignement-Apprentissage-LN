#!/usr/bin/env python3
"""
build_other_languages.py — Génère lessons_<slug>.json pour les langues
ALCAM autres que le bulu, à partir des datasets TSV bruts.

Chaque langue obtient le MÊME plan pédagogique de 45 leçons que le bulu,
mais sans audio (les exemples textuels sont tirés de son propre TSV).
L'application affichera ces langues comme des « bibliothèques » :
les fiches enseignant et élève fonctionnent, mais la lecture audio
est désactivée tant que les enregistrements ne sont pas réalisés.
"""

import json
import re
import unicodedata
import sys
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent  # /.../Cours-sur-outils-numériques_S2
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)


# Réutilise les fonctions du module principal
sys.path.insert(0, str(ROOT))
from build_lessons import (
    LESSONS_PLAN, build_lesson, matches, select, trim,
)
from build_data import LANGUES, normalize, count_tonal_marks, guess_module


def load_tsv(path: Path):
    """Charge un TSV ALCAM générique. Retourne une liste de dicts (rows)."""
    rows = []
    with path.open("r", encoding="utf-8", errors="replace") as f:
        header = next(f).rstrip("\n").rstrip("\r").split("\t")
        for line in f:
            parts = line.rstrip("\n").rstrip("\r").split("\t")
            if len(parts) < len(header):
                parts += [""] * (len(header) - len(parts))
            elif len(parts) > len(header):
                parts = parts[:len(header)]
            row = dict(zip(header, parts))
            rows.append(row)
    return rows


def tsv_rows_to_items(rows, slug):
    """Convertit des lignes TSV ALCAM en items compatibles avec build_lesson."""
    items = []
    seen_ids = Counter()

    for r in rows:
        word = (r.get("Word") or "").strip(" _")
        french_word = (r.get("French") or r.get("FrenchRef") or "").strip(" _")
        lang_ex = (r.get("LangEx") or "").strip(" _")
        # Some TSVs have LangExEdit ; if non-vide, prefer it
        lang_ex_edit = (r.get("LangExEdit") or "").strip(" _")
        if lang_ex_edit:
            lang_ex = lang_ex_edit
        french_ex = (r.get("FrenchEx") or "").strip(" _")
        pos = (r.get("POS") or "").strip(" _")
        class_noun = (r.get("Class") or "").strip(" _")

        # Item « mot isolé »
        if word and word != "_":
            wn = normalize(word)
            seen_ids[wn] += 1
            items.append({
                "id": f"{slug}-w-{wn[:24]}-{seen_ids[wn]}",
                "audio": "",
                "langText": word,
                "frenchText": french_word or "",
                "langWord": word,
                "frenchWord": french_word or "",
                "pos": pos,
                "classNoun": class_noun,
                "module": guess_module(pos, class_noun, lang_text=word, word_only=True),
                "matchedBy": "word_only",
            })

        # Item « phrase d'exemple »
        if lang_ex and lang_ex != "_":
            ln = normalize(lang_ex)
            seen_ids[ln] += 1
            items.append({
                "id": f"{slug}-ex-{ln[:24]}-{seen_ids[ln]}",
                "audio": "",
                "langText": lang_ex,
                "frenchText": french_ex or "",
                "langWord": word,
                "frenchWord": french_word or "",
                "pos": pos,
                "classNoun": class_noun,
                "module": guess_module(pos, class_noun, lang_text=lang_ex, word_only=False),
                "matchedBy": "langex",
            })

    # Dédoublonner par langText
    seen = set()
    deduped = []
    for it in items:
        key = (it["langText"], it.get("frenchText", ""))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(it)

    return deduped


# Mapping slug -> chemin du TSV correspondant (depuis WORKSPACE)
TSV_BY_SLUG = {
    "basaa":        WORKSPACE / "ALCAM_Basaa.tsv",
    "ewondo":       WORKSPACE / "ALCAM_Ewondo.tsv",
    "yezoum":       WORKSPACE / "ALCAM_dataset_Yezoum.tsv",
    "diboum":       WORKSPACE / "ALCAM_dataset_Diboum - Feuille 1.tsv",
    "balom":        WORKSPACE / "ALCAM_dataset_balom - Feuille 1.tsv",
    "gbaya":        WORKSPACE / "ALCAM_dataset_gbaya 1 - Feuille 1.tsv",
    "mipa":         WORKSPACE / "ALCAM_dataset_mìpá - Feuille 1.tsv",
    "tuki-tukombe": WORKSPACE / "ALCAM_dataset_tukombe_tungoro_bag - Feuille 1.tsv",
    "tuki-tumbele": WORKSPACE / "ALCAM _dataset_Tuki_Tumbele_bag - bas.tsv",
    "fong":         WORKSPACE / "ALCAM_datasheet_Fong.tsv",
    "mvele":        WORKSPACE / "ALCAM_mvele_datasheet .tsv",
    "bakossi":      WORKSPACE / "ALCAM _dataset_bakosi_bbs.tsv",
    "badjia":       WORKSPACE / "AlCAM_dataset_badjia - badjia.tsv",
    "banoo":        WORKSPACE / "AlCAM_dataset_batanga_banɔɔ - Feuille 1.tsv",
    "tikar":        WORKSPACE / "AlCAM_dataset_tikar - Feuille 1.tsv",
}


def build_for_language(slug, name, tsv_path):
    # 1) Si un dataset audio-rich a déjà été construit (par build_audio_corpora.py),
    #    on l'utilise — ça donne des leçons avec audio.
    audio_json = DATA_DIR / f"{slug}.json"
    has_audio = False
    if audio_json.exists():
        try:
            items = json.loads(audio_json.read_text(encoding="utf-8"))
            has_audio = any(it.get("audio") for it in items)
            print(f"  using audio-rich {audio_json.name} ({len(items)} items, audio={has_audio})")
        except Exception as e:
            print(f"  ! lecture {audio_json}: {e} — fallback TSV", file=sys.stderr)
            items = None
    else:
        items = None

    # 2) Sinon, fallback : on extrait des items à partir du TSV brut (sans audio)
    if items is None:
        if not tsv_path.exists():
            print(f"  ! {slug}: fichier TSV introuvable: {tsv_path}", file=sys.stderr)
            return None
        rows = load_tsv(tsv_path)
        items = tsv_rows_to_items(rows, slug)

    if not items:
        print(f"  ! {slug}: aucun item disponible", file=sys.stderr)
        return None

    lessons = [build_lesson(plan, items) for plan in LESSONS_PLAN]
    counts = Counter(l["module"] for l in lessons)
    voc_total = sum(len(l["vocabulary"]) for l in lessons)

    out = {
        "language": slug,
        "languageName": name,
        "audio": has_audio,
        "lessons": lessons,
        "stats": {
            "total_lessons": len(lessons),
            "by_module": dict(counts),
            "vocabulary_items": voc_total,
            "corpus_items": len(items),
        },
    }

    out_path = DATA_DIR / f"lessons_{slug}.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    audio_tag = "AUDIO" if has_audio else "texte"
    print(f"  - {slug:14} ({name}) [{audio_tag}]: {len(lessons)} leçons, "
          f"{voc_total} items voc, corpus={len(items)}")
    return out


def main():
    print("Génération des fichiers lessons_<slug>.json pour les autres langues ALCAM...")
    print()

    languages_with_lessons = ["bulu"]  # déjà construit par build_lessons.py
    for lang in LANGUES:
        slug = lang["slug"]
        if slug == "bulu":
            continue
        tsv_path = TSV_BY_SLUG.get(slug)
        if not tsv_path:
            print(f"  ! {slug}: pas de TSV mappé, ignoré")
            continue
        result = build_for_language(slug, lang["name"], tsv_path)
        if result:
            languages_with_lessons.append(slug)

    # Met à jour languages.json avec un flag has_lessons
    enriched = []
    for lang in LANGUES:
        copy = dict(lang)
        copy["has_lessons"] = lang["slug"] in languages_with_lessons
        enriched.append(copy)
    (DATA_DIR / "languages.json").write_text(
        json.dumps(enriched, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nLanguages with lessons: {len(languages_with_lessons)}")
    print(f"Updated {DATA_DIR / 'languages.json'}")


if __name__ == "__main__":
    main()
