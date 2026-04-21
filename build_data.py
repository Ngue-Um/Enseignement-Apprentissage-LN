#!/usr/bin/env python3
"""
build_data.py — Prépare les fichiers JSON consommés par l'app web.

Pour la langue principale (Bulu) :
  - lit `mapping.tsv` du dataset TTS (audio_filename -> sentence)
  - lit `ALCAM_dataset_bulu.tsv` (LangEx -> FrenchEx, Word -> French, POS, Class…)
  - tente une jointure approximative entre les deux sources via la sentence langue
  - produit `data/bulu.json` avec un tableau de phrases :
      { id, audio, langText, frenchText, word, frenchWord, pos, classNoun, module }

Pour les autres langues du catalogue : produit `data/languages.json`
listant l'ensemble des 16 langues ALCAM publiées sur mdc, avec leur statut.
"""

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent  # le dossier du cours qui contient les TSV bruts
OUT_DIR = ROOT / "data"
OUT_DIR.mkdir(exist_ok=True)


def normalize(text: str) -> str:
    """Normalise une chaîne pour comparaison : NFC, lowercase, espaces compactés."""
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


TONAL_DIACRITICS = set("\u0301\u0300\u0302\u030C\u030B\u030F\u0304\u0306")


def count_tonal_marks(text: str) -> int:
    """Compte les diacritiques tonals dans une chaîne déjà NFD-isable."""
    if not text:
        return 0
    decomposed = unicodedata.normalize("NFD", text)
    return sum(1 for ch in decomposed if ch in TONAL_DIACRITICS)


def guess_module(pos: str, class_noun: str, lang_text: str = "", word_only: bool = False) -> str:
    """Affecte la phrase à un module MINESEC (heuristique enrichie).

    - Mot seul, court  → Module II (segmentaux) si peu de tons,
                          Module III (suprasegmentaux) si tons denses
    - Plusieurs mots, pos=v → Module V (syntagme verbal)
    - Plusieurs mots, pos=n → Module IV (syntagme nominal)
    - Sinon, plusieurs mots → Module VI (la phrase)
    """
    pos = (pos or "").lower().strip()
    text = (lang_text or "").strip()
    n_tokens = len([t for t in text.split() if t])
    n_tones = count_tonal_marks(text)

    # Cas du mot isolé / vocabulaire
    if word_only or n_tokens <= 1:
        # Si la densité tonale est forte (≥ 2 tons sur le mot), on l'attribue à III
        if n_tones >= 2:
            return "M3-suprasegmentaux"
        return "M2-segmentaux"

    # Phrases / syntagmes
    if pos == "n":
        return "M4-syntagme-nominal"
    if pos in ("v", "verb"):
        return "M5-syntagme-verbal"
    # Densité tonale très forte sur une phrase courte → III
    if n_tokens <= 3 and n_tones >= 4:
        return "M3-suprasegmentaux"
    return "M6-phrase"


def load_alcam(path: Path):
    """Charge ALCAM_dataset_bulu.tsv. Retourne deux index :
       by_word : Word normalisé -> ligne
       by_langex : LangEx normalisé -> ligne
    """
    rows = []
    with path.open("r", encoding="utf-8") as f:
        header = next(f).rstrip("\n").split("\t")
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < len(header):
                parts += [""] * (len(header) - len(parts))
            row = dict(zip(header, parts))
            rows.append(row)
    by_word = {}
    by_langex = {}
    for r in rows:
        w = normalize(r.get("Word", "")).strip(" _")
        if w and w != "_":
            by_word.setdefault(w, []).append(r)
        lex = normalize(r.get("LangEx", "")).strip(" _")
        if lex and lex != "_":
            by_langex.setdefault(lex, []).append(r)
    return rows, by_word, by_langex


def load_mapping(path: Path):
    """Charge mapping.tsv : audio_filename, key, sentence, attempts"""
    rows = []
    with path.open("r", encoding="utf-8") as f:
        header = next(f).rstrip("\n").split("\t")
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < len(header):
                parts += [""] * (len(header) - len(parts))
            row = dict(zip(header, parts))
            rows.append(row)
    return rows


def split_sentence(sentence: str):
    """Une sentence du mapping est typiquement 'mot ; phrase d'exemple'.
       Retourne (mot, phrase) où l'un peut être vide.
    """
    if ";" in sentence:
        parts = [p.strip() for p in sentence.split(";", 1)]
        return parts[0], parts[1]
    return sentence.strip(), ""


def build_bulu(audio_dir: Path, mapping_path: Path, alcam_path: Path):
    mapping = load_mapping(mapping_path)
    rows, by_word, by_langex = load_alcam(alcam_path)

    matched_word = 0
    matched_lex = 0
    unmatched = 0

    items = []
    for m in mapping:
        audio = m.get("audio_filename", "").strip()
        sentence = m.get("sentence", "").strip()
        if not audio or not sentence:
            continue

        # Vérifier que l'audio existe
        if not (audio_dir / audio).exists():
            continue

        word_part, ex_part = split_sentence(sentence)
        word_n = normalize(word_part)
        ex_n = normalize(ex_part) if ex_part else ""

        item = {
            "id": m.get("key", "")[:12],
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

        # 1) tenter la jointure par LangEx (phrase)
        match = None
        if ex_n and ex_n in by_langex:
            match = by_langex[ex_n][0]
            item["matchedBy"] = "langex"
            matched_lex += 1
        # 2) sinon, par Word
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
            # Si le mapping ne fournit pas d'ex_part mais qu'on est tombé sur un Word
            # match, on est sur du vocabulaire isolé.
            if item["matchedBy"] == "word" and not item["frenchText"]:
                item["frenchText"] = item["frenchWord"]
            item["module"] = guess_module(
                item["pos"], item["classNoun"],
                lang_text=item["langText"], word_only=word_only,
            )
        else:
            item["module"] = guess_module("", "", lang_text=item["langText"], word_only=word_only)

        items.append(item)

    print(
        f"Bulu: total={len(items)}, langex_match={matched_lex}, "
        f"word_match={matched_word}, unmatched={unmatched}"
    )
    return items


# ----------- 16 langues ALCAM (catalogue) -----------
LANGUES = [
    {"slug": "basaa",          "name": "Bàsàa",            "iso": "bas", "family": "Bantoue A.43", "audio": False},
    {"slug": "ewondo",         "name": "Èwòndó",           "iso": "ewo", "family": "Bantoue A.72", "audio": False},
    {"slug": "bulu",           "name": "Bulu",             "iso": "bum", "family": "Bantoue A.74", "audio": True},
    {"slug": "gbaya",          "name": "Gbáyá",            "iso": "gya", "family": "Oubanguienne", "audio": False},
    {"slug": "tikar",          "name": "Tikar",            "iso": "tik", "family": "Bantoïde",     "audio": False},
    {"slug": "fong",           "name": "Fòŋ",              "iso": "—",   "family": "Bantoue A.50", "audio": False},
    {"slug": "mvele",          "name": "Mvélé",            "iso": "—",   "family": "Bantoue A.50", "audio": False},
    {"slug": "bakossi",        "name": "Bakossi",          "iso": "bss", "family": "Bantoue A.15", "audio": False},
    {"slug": "tuki-tumbele",   "name": "Tuki-Tumbele",     "iso": "—",   "family": "Bantoue A.60", "audio": False},
    {"slug": "tuki-tukombe",   "name": "Tuki-Tukombe",     "iso": "—",   "family": "Bantoue A.60", "audio": False},
    {"slug": "balom",          "name": "Balom",            "iso": "—",   "family": "Bantoue A.60", "audio": False},
    {"slug": "badjia",         "name": "Bàdjíà",           "iso": "—",   "family": "Bantoue",      "audio": False},
    {"slug": "banoo",          "name": "Banɔɔ",            "iso": "—",   "family": "Bantoue A.40", "audio": False},
    {"slug": "mipa",           "name": "Mìpá",             "iso": "—",   "family": "Bantoue",      "audio": False},
    {"slug": "yezoum",         "name": "Yezoum",           "iso": "—",   "family": "Bantoue A.70", "audio": False},
    {"slug": "diboum",         "name": "Diboum",           "iso": "—",   "family": "Bantoue",      "audio": False},
]


def main():
    bulu_audio = WORKSPACE / "Bulu" / "Bulu_tts_dataset_384clips_2379s_20260406-1522_part2of2"
    bulu_mapping = bulu_audio / "mapping.tsv"
    bulu_alcam = WORKSPACE / "ALCAM_dataset_bulu.tsv"

    bulu_items = build_bulu(bulu_audio, bulu_mapping, bulu_alcam)

    (OUT_DIR / "bulu.json").write_text(
        json.dumps(bulu_items, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    (OUT_DIR / "languages.json").write_text(
        json.dumps(LANGUES, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Wrote {OUT_DIR / 'bulu.json'} ({len(bulu_items)} items)")
    print(f"Wrote {OUT_DIR / 'languages.json'} ({len(LANGUES)} langues)")


if __name__ == "__main__":
    main()
