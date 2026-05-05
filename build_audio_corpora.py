#!/usr/bin/env python3
"""
build_audio_corpora.py — Pour chaque langue ALCAM disposant d'audio
(Basaa, Bakossi, Fong, Mvele, Yezoum, en plus du Bulu déjà géré),
joint le mapping audio + le TSV ALCAM en items prêts à l'emploi.

Sortie :
  - prototype-langues-camerounaises/data/<slug>.json  (items, comme bulu.json)
  - prototype-langues-camerounaises/audio/<slug>/*.mp3 (copie des MP3)

Note : ce script ne génère PAS les leçons — c'est build_other_languages.py
qui les construit à partir des items créés ici.
"""

import json
import re
import shutil
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent
DATA_DIR = ROOT / "data"
AUDIO_DIR_ROOT = ROOT / "audio"
DATA_DIR.mkdir(exist_ok=True)
AUDIO_DIR_ROOT.mkdir(exist_ok=True)

# Réutilise les helpers
import sys
sys.path.insert(0, str(ROOT))
from build_data import normalize, count_tonal_marks, guess_module, load_alcam, split_sentence


# Pour chaque slug (utilisé dans languages.json), on déclare :
#   - le chemin du dataset ALCAM (TSV)
#   - le chemin du dossier audio
#   - le chemin du mapping audio (TSV avec ou sans en-tête)
#   - bool : le mapping a-t-il un en-tête ?
LANGS_WITH_AUDIO = {
    "basaa":   {
        "alcam":  WORKSPACE / "Basaa"   / "ALCAM_Basaa.tsv",
        "audio":  WORKSPACE / "Basaa"   / "audio_files_MP3",
        "map":    WORKSPACE / "Basaa"   / "audio_files_MP3" / "audio_mapping_MP3.tsv",
        "header": False,
    },
    "bakossi": {
        "alcam":  WORKSPACE / "Bakosi"  / "ALCAM _dataset_bakosi_bbs.tsv",
        "audio":  WORKSPACE / "Bakosi"  / "audio_files_MP3",
        "map":    WORKSPACE / "Bakosi"  / "audio_files_MP3" / "audio_mapping_MP3.tsv",
        "header": False,
    },
    "fong":    {
        "alcam":  WORKSPACE / "Fong"    / "ALCAM_datasheet_Fong.tsv",
        "audio":  WORKSPACE / "Fong"    / "audio_files_MP3",
        "map":    WORKSPACE / "Fong"    / "audio_files_MP3" / "audio_mapping_MP3.tsv",
        "header": True,
    },
    "mvele":   {
        "alcam":  WORKSPACE / "Mvele"   / "ALCAM_mvele_datasheet .tsv",
        "audio":  WORKSPACE / "Mvele"   / "audio_files",
        "map":    WORKSPACE / "Mvele"   / "audio_files" / "audio_mapping.tsv",
        "header": False,
    },
    "yezoum":  {
        "alcam":  WORKSPACE / "Yezoum"  / "ALCAM_dataset_Yezoum.tsv",
        "audio":  WORKSPACE / "Yezoum"  / "audio_files_MP3",
        "map":    WORKSPACE / "Yezoum"  / "audio_files_MP3" / "audio_mapping_MP3.tsv",
        "header": False,
    },
}


def load_mapping(path: Path, has_header: bool):
    """Renvoie une liste de tuples (audio_filename, sentence_raw).

    Le mapping a typiquement la forme :
       audio.mp3<TAB>mot; phrase
    Parfois (Fong, Yezoum) :
       audio.mp3<TAB>mot;<TAB>phrase
    On gère les deux cas en concaténant les colonnes au-delà de la première.
    """
    rows = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8", errors="replace") as f:
        if has_header:
            next(f, None)
        for line in f:
            parts = line.rstrip("\r\n").split("\t")
            if not parts or not parts[0].strip():
                continue
            audio = parts[0].strip()
            # Colonne 2 et plus = sentence (joint par espace ou tab selon la source)
            rest = "\t".join(parts[1:]).strip()
            rows.append((audio, rest))
    return rows


def build_for_language(slug, cfg):
    print(f"\n=== {slug} ===")
    if not cfg["alcam"].exists():
        print(f"  ! ALCAM introuvable: {cfg['alcam']}")
        return None
    if not cfg["audio"].exists():
        print(f"  ! audio dir introuvable: {cfg['audio']}")
        return None

    # 1. Charger le mapping et l'ALCAM
    mapping = load_mapping(cfg["map"], cfg["header"])
    rows, by_word, by_langex = load_alcam(cfg["alcam"])
    print(f"  mapping rows: {len(mapping)}, ALCAM rows: {len(rows)}")

    # 2. Copier les MP3 dans audio/<slug>/
    target_dir = AUDIO_DIR_ROOT / slug
    target_dir.mkdir(exist_ok=True)
    copied = 0
    for fname in cfg["audio"].iterdir():
        if not fname.is_file():
            continue
        if fname.suffix.lower() not in (".mp3", ".wav", ".m4a", ".ogg"):
            continue
        dst = target_dir / fname.name
        if not dst.exists():
            shutil.copy2(fname, dst)
        copied += 1
    print(f"  audio files in target: {copied}")

    # 3. Construire les items en joignant mapping x ALCAM
    items = []
    matched_word = matched_lex = unmatched = 0

    for audio, sentence in mapping:
        if not audio or not sentence:
            continue
        if not (target_dir / audio).exists():
            continue

        word_part, ex_part = split_sentence(sentence)
        word_n = normalize(word_part)
        ex_n = normalize(ex_part) if ex_part else ""

        item = {
            "id": Path(audio).stem[:12],
            "audio": audio,
            "langText": ex_part if ex_part else word_part,
            "langWord": word_part,
            "frenchText": "",
            "frenchWord": "",
            "pos": "",
            "classNoun": "",
            "module": "M2-segmentaux",
            "matchedBy": None,
        }

        match = None
        if ex_n and ex_n in by_langex:
            match = by_langex[ex_n][0]
            item["matchedBy"] = "langex"
            matched_lex += 1
        elif word_n and word_n in by_word:
            match = by_word[word_n][0]
            item["matchedBy"] = "word"
            matched_word += 1
        else:
            unmatched += 1

        word_only = not bool(ex_part)
        if match:
            item["frenchText"] = match.get("FrenchEx", "").strip(" _")
            item["frenchWord"] = match.get("French", "").strip(" _")
            item["pos"] = match.get("POS", "").strip(" _")
            item["classNoun"] = match.get("Class", "").strip(" _")
            if item["matchedBy"] == "word" and not item["frenchText"]:
                item["frenchText"] = item["frenchWord"]
            item["module"] = guess_module(item["pos"], item["classNoun"],
                                          lang_text=item["langText"], word_only=word_only)
        else:
            item["module"] = guess_module("", "", lang_text=item["langText"], word_only=word_only)

        items.append(item)

    print(f"  items={len(items)} (langex_match={matched_lex}, word_match={matched_word}, unmatched={unmatched})")

    # 4. Écrire <slug>.json à côté de bulu.json
    out_path = DATA_DIR / f"{slug}.json"
    out_path.write_text(json.dumps(items, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    print(f"  -> {out_path}")
    return items


def main():
    for slug, cfg in LANGS_WITH_AUDIO.items():
        build_for_language(slug, cfg)
    print("\nDone.")


if __name__ == "__main__":
    main()
