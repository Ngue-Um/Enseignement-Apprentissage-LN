#!/usr/bin/env python3
"""
build_lessons.py — Génère `data/lessons_bulu.json`, un découpage des modules
MINESEC en ~20 leçons clé-en-main pour le bulu.

Chaque leçon contient :
  - une fiche professeur (étapes 1 à 5 avec liberté pédagogique)
  - une fiche élève (préparation, activités, mémo « à retenir »)
  - le vocabulaire ALCAM mobilisé (uniquement des données existantes,
    aucun ajout extérieur)

L'objectif n'est pas de produire un cours figé mais un *gabarit* utilisable
en l'état — y compris pour des enseignants qui ne sont pas locuteurs natifs
fluides — et adaptable à la réalité de la classe.
"""

import json
import re
import unicodedata
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
BULU_JSON = DATA_DIR / "bulu.json"


def load_bulu():
    return json.loads(BULU_JSON.read_text(encoding="utf-8"))


def matches(item, *, fr_pattern=None, lang_pattern=None,
            module=None, pos=None, max_tokens=None, min_tokens=None,
            min_tones=None, has_french_only=True):
    fr = (item.get("frenchText") or "").lower()
    lg = (item.get("langText") or "").lower()
    if has_french_only and not fr:
        return False
    if fr_pattern and not re.search(fr_pattern, fr, re.IGNORECASE):
        return False
    if lang_pattern and not re.search(lang_pattern, lg, re.IGNORECASE):
        return False
    if module and item.get("module") != module:
        return False
    if pos and item.get("pos") not in pos:
        return False
    if max_tokens is not None and len(item.get("langText", "").split()) > max_tokens:
        return False
    if min_tokens is not None and len(item.get("langText", "").split()) < min_tokens:
        return False
    if min_tones is not None:
        n = sum(1 for ch in unicodedata.normalize("NFD", item.get("langText", ""))
                if ch in "\u0301\u0300\u0302\u030C")
        if n < min_tones:
            return False
    return True


def select(items, *, max_n=8, **filters):
    out = []
    seen = set()
    for it in items:
        if it["id"] in seen:
            continue
        if matches(it, **filters):
            seen.add(it["id"])
            out.append(it)
        if len(out) >= max_n:
            break
    return out


# Champs minimaux pour l'affichage en classe : audio, transcription, traduction
def trim(it):
    return {
        "id": it.get("id"),
        "audio": it.get("audio"),
        "langText": it.get("langText"),
        "frenchText": it.get("frenchText"),
        "langWord": it.get("langWord"),
        "frenchWord": it.get("frenchWord"),
        "pos": it.get("pos"),
    }


# ----------------------------------------------------------------------
#   GÉNÉRATEUR DE LEÇONS
#
#  Chaque leçon est une fonction qui prend la liste complète bulu et
#  renvoie un dict structuré. On centralise la construction pour
#  garantir un format identique partout.
# ----------------------------------------------------------------------

LESSONS_PLAN = [
    # === Module I — Diversité linguistique camerounaise (6e, 15h) =========
    {
        "id": "I-1",
        "code": "I.1",
        "module": "M1-diversite",
        "moduleTitle": "Module I — Diversité linguistique camerounaise",
        "title": "Le Cameroun, mosaïque de 239 langues",
        "duration": "60 min",
        "level": "6e",
        "objectives": [
            "Prendre conscience de la diversité linguistique du Cameroun",
            "Situer quelques grandes familles de langues sur la carte",
            "Adopter une attitude de respect envers toutes les langues du pays",
        ],
        "filter": dict(max_tokens=2, has_french_only=True),
        "teacher_steps": [
            ("Mise en route (5 min)",
             "Demandez aux élèves combien de langues ils pensent qu'on parle "
             "au Cameroun. Recueillez les estimations au tableau. Annoncez "
             "le chiffre officiel : environ 239 langues vivantes (ALCAM)."),
            ("Carte au tableau (15 min)",
             "Tracez (ou affichez) une carte simplifiée des grandes zones "
             "linguistiques : Bantu (Sud, Centre, Est, Littoral), Soudaniques "
             "(Nord), Adamawa-Oubanguiennes, Tchadiques. Montrez qu'aucune "
             "région n'est mono-langue."),
            ("Témoignages (15 min)",
             "Faites circuler la parole : chaque élève dit la (ou les) "
             "langue(s) parlée(s) à la maison. Notez la liste collective "
             "au tableau. Valorisez la diversité présente dans la classe."),
            ("Réflexion guidée (15 min)",
             "Question : pourquoi enseigne-t-on les langues nationales à "
             "l'école aujourd'hui ? Faites émerger : transmission, "
             "patrimoine, citoyenneté, identité."),
            ("Clôture (10 min)",
             "Bilan collectif : « ce que je retiens, c'est… ». Annoncez la "
             "prochaine leçon : la place du bulu."),
        ],
        "freedom": (
            "Si la classe est multiethnique (souvent le cas), invitez des "
            "élèves à dire bonjour dans leur langue. Variante : faites "
            "préparer une mini-affiche par binôme à exposer en salle."
        ),
        "student_intro": (
            "Le Cameroun parle environ 239 langues. C'est une richesse. "
            "Aujourd'hui, tu découvres cette mosaïque et la place de ta "
            "propre langue dans ce paysage."
        ),
        "student_activities": [
            ("Activité 1 — Estimer puis vérifier",
             "Avant la leçon, écris ton estimation du nombre de langues du "
             "Cameroun. À la fin, compare avec le chiffre réel."),
            ("Activité 2 — Ma langue, mes langues",
             "Liste les langues parlées chez toi. Souligne celle que tu "
             "utilises le plus souvent."),
            ("Activité 3 — Carte mentale",
             "Dessine une carte mentale : « langues du Cameroun » au centre, "
             "et autour les grandes familles vues en classe."),
        ],
        "memo": (
            "Le Cameroun est l'un des pays les plus plurilingues d'Afrique : "
            "239 langues environ, regroupées en 4 grandes familles. Aucune "
            "langue n'est plus légitime qu'une autre."
        ),
    },
    {
        "id": "I-2",
        "code": "I.2",
        "module": "M1-diversite",
        "moduleTitle": "Module I — Diversité linguistique camerounaise",
        "title": "Identifier la place du bulu",
        "duration": "60 min",
        "level": "6e",
        "objectives": [
            "Situer le bulu dans la famille bantu (zone A.70)",
            "Reconnaître quelques langues apparentées (ewondo, fang, eton)",
            "Localiser l'aire bulu sur la carte du Cameroun",
        ],
        "filter": dict(max_tokens=2, has_french_only=True),
        "teacher_steps": [
            ("Rappel (5 min)",
             "Reprenez avec la classe les 4 grandes familles vues en I.1. "
             "Demandez : « à laquelle pensez-vous que le bulu appartient ? »."),
            ("Présentation (15 min)",
             "Le bulu est une langue bantu (zone A.70 selon la classification "
             "Guthrie). Au tableau, dessinez un arbre : Bantu → A → A.70 → "
             "bulu, ewondo, fang, eton. Faites observer la proximité."),
            ("Carte régionale (15 min)",
             "Affichez une carte du Sud-Cameroun. Délimitez l'aire bulu "
             "(régions du Sud et du Centre, autour de Sangmélima, Ebolowa). "
             "Faites placer 3 villes par les élèves au tableau."),
            ("Comparaison guidée (15 min)",
             "Comparez 5 mots dans les 4 langues sœurs (eau, maison, enfant, "
             "manger, soleil). Faites observer les ressemblances."),
            ("Clôture (10 min)",
             "Bilan : « le bulu n'est pas isolé, il est entouré de langues "
             "cousines ». Annoncez la prochaine leçon."),
        ],
        "freedom": (
            "Si vous avez en classe des élèves locuteurs d'ewondo, fang ou "
            "eton, sollicitez-les pour les comparaisons. C'est plus vivant "
            "qu'un cours magistral."
        ),
        "student_intro": (
            "Le bulu fait partie de la famille bantu, au sud du Cameroun. "
            "Il a des langues sœurs très proches : ewondo, fang, eton. "
            "Aujourd'hui, tu apprends à le situer."
        ),
        "student_activities": [
            ("Activité 1 — Famille",
             "Complète l'arbre : Bantu → A → A.70 → … (cite 4 langues)."),
            ("Activité 2 — Carte",
             "Sur la carte du Cameroun, colorie l'aire bulu en orange clair."),
            ("Activité 3 — Comparer",
             "Pour les 5 mots du jour, entoure ce qui se ressemble entre "
             "le bulu et l'ewondo (ou fang)."),
        ],
        "memo": (
            "Le bulu appartient à la zone bantu A.70 (classification Guthrie). "
            "Ses langues sœurs sont l'ewondo, le fang et l'eton."
        ),
    },
    {
        "id": "I-3",
        "code": "I.3",
        "module": "M1-diversite",
        "moduleTitle": "Module I — Diversité linguistique camerounaise",
        "title": "Langue, dialecte, langue officielle",
        "duration": "60 min",
        "level": "6e",
        "objectives": [
            "Distinguer langue, dialecte et variété régionale",
            "Identifier les deux langues officielles du Cameroun",
            "Comprendre le statut des langues nationales à l'école",
        ],
        "filter": dict(max_tokens=2, has_french_only=True),
        "teacher_steps": [
            ("Accroche (5 min)",
             "Posez la question piège : « le bulu est-il une langue ou un "
             "dialecte ? ». Recueillez les réponses, sans trancher tout de "
             "suite."),
            ("Définitions (15 min)",
             "Au tableau : LANGUE = système autonome, intercompréhension "
             "limitée avec ses voisines. DIALECTE = variété régionale d'une "
             "même langue. LANGUE OFFICIELLE = langue de l'administration. "
             "Tranchez : le bulu est une LANGUE à part entière."),
            ("Statuts au Cameroun (15 min)",
             "Expliquez : 2 langues officielles (français, anglais), "
             "239 langues nationales protégées par la Constitution (art. 1 "
             "al. 3, révision 1996). Affichez les deux concepts au tableau."),
            ("Étude de cas (15 min)",
             "Faites lire (en groupe) un court extrait de loi ou de circulaire "
             "MINESEC mentionnant l'enseignement des langues nationales. "
             "Faites repérer le mot « national »."),
            ("Clôture (10 min)",
             "Synthèse : un mot pour chacun. « À retenir : … »."),
        ],
        "freedom": (
            "Si le débat « langue ou dialecte » prend, ne le coupez pas : "
            "c'est un excellent point d'entrée vers la sociolinguistique. "
            "Vous pouvez faire émerger la dimension politique du choix."
        ),
        "student_intro": (
            "Tout le monde parle une langue. Mais qu'est-ce qui fait qu'on "
            "appelle quelque chose une langue, un dialecte, ou une langue "
            "officielle ? Aujourd'hui, on clarifie."
        ),
        "student_activities": [
            ("Activité 1 — Définir",
             "Recopie les trois définitions vues au tableau."),
            ("Activité 2 — Classer",
             "Pour chaque exemple donné par le professeur, dis si c'est une "
             "LANGUE, un DIALECTE, ou une LANGUE OFFICIELLE."),
            ("Activité 3 — Réfléchir",
             "En 3 lignes, explique pourquoi il est important d'enseigner "
             "les langues nationales à l'école."),
        ],
        "memo": (
            "Au Cameroun, 2 langues officielles (français, anglais) "
            "coexistent avec ~239 langues nationales reconnues. "
            "Le bulu est une langue nationale à part entière, pas un dialecte."
        ),
    },

    # === Module II — Productions segmentales ============================
    {
        "id": "II-1",
        "code": "II.1",
        "module": "M2-segmentaux",
        "moduleTitle": "Module II — Productions segmentales",
        "title": "Mes premiers mots en bulu",
        "duration": "60 min",
        "level": "6e",
        "objectives": [
            "Identifier 6 mots usuels du bulu à l'oreille",
            "Reproduire les sons du bulu absents du français",
            "Associer un mot bulu à sa traduction française",
        ],
        "filter": dict(max_tokens=2, has_french_only=True),
        "teacher_steps": [
            ("Mise en route (5 min)",
             "Saluez la classe en bulu (mbolo). Demandez aux élèves quels mots de "
             "leur langue maternelle ils connaissent déjà. Annoncez l'objectif : "
             "« aujourd'hui, nous allons reconnaître nos premiers mots en bulu »."),
            ("Écoute guidée (15 min)",
             "Faites écouter chaque mot deux fois. Demandez aux élèves de répéter "
             "à voix haute, sans regarder la transcription. Insistez sur les sons "
             "qui n'existent pas en français (ə, ɔ, ɛ, voyelles longues)."),
            ("Découverte de la transcription AGLC (15 min)",
             "Affichez la transcription au tableau. Faites observer les caractères "
             "spéciaux. Lisez chaque mot en pointant les lettres ; demandez aux "
             "élèves de venir au tableau pointer le mot que vous prononcez."),
            ("Pratique (15 min)",
             "Activité d'appariement audio ↔ traduction (cf. fiche élève). "
             "Donnez 3 minutes par mot. Circulez et corrigez la prononciation."),
            ("Clôture (10 min)",
             "Demandez à chaque élève de prononcer un mot de son choix. "
             "Notez collectivement la liste au tableau. Annoncez la leçon suivante."),
        ],
        "freedom": (
            "Si les élèves accrochent, prolongez par une mini-saynette : "
            "deux élèves se saluent en bulu, l'un demande « comment ça va ? » "
            "(à introduire si vous le connaissez), l'autre répond. "
            "Sinon, contentez-vous des 6 mots ci-contre."
        ),
        "student_intro": (
            "Aujourd'hui nous découvrons nos six premiers mots en bulu. "
            "Tu vas les écouter, les répéter, et apprendre à les écrire en AGLC."
        ),
        "student_activities": [
            ("Activité 1 — Écouter et répéter",
             "Clique sur ▶ chaque mot. Répète-le à voix haute trois fois. "
             "Coche la case quand tu sais le prononcer."),
            ("Activité 2 — Apparier",
             "Relie chaque mot bulu à sa traduction française."),
            ("Activité 3 — Écrire",
             "Écris en AGLC, sans regarder, les trois mots que tu connais le mieux."),
        ],
        "memo": (
            "Le bulu utilise des sons absents du français (ə, ɔ, ɛ). "
            "Ces sons s'écrivent grâce à l'alphabet général AGLC."
        ),
    },
    {
        "id": "II-2",
        "code": "II.2",
        "module": "M2-segmentaux",
        "moduleTitle": "Module II — Productions segmentales",
        "title": "Voyelles ouvertes et voyelles fermées",
        "duration": "60 min",
        "level": "6e",
        "objectives": [
            "Distinguer à l'oreille les voyelles ouvertes (ɛ, ɔ) et fermées (e, o)",
            "Reproduire correctement la voyelle centrale ə",
            "Lire correctement des mots contenant ces voyelles",
        ],
        "filter": dict(max_tokens=3, lang_pattern=r"[ɛɔə]"),
        "teacher_steps": [
            ("Mise en route (5 min)",
             "Rappel rapide de la leçon II.1. Demandez à 3 élèves de prononcer "
             "un mot vu la fois précédente. Corrigez bienveillamment."),
            ("Présentation des voyelles AGLC (15 min)",
             "Au tableau, dressez le tableau des sept voyelles du bulu : "
             "i, e, ɛ, a, ɔ, o, u + ə. Pour chaque voyelle, prononcez-la "
             "en exagérant l'ouverture de la bouche. Faites répéter en chœur."),
            ("Écoute discriminative (20 min)",
             "Faites écouter les mots du jour. À chaque écoute, demandez : "
             "« quelle voyelle entendez-vous ? » Notez les réponses. "
             "L'enjeu n'est pas de tout réussir mais d'aiguiser l'oreille."),
            ("Lecture à voix haute (15 min)",
             "Distribuez la fiche élève. En binôme, les élèves lisent les mots "
             "à tour de rôle. Le binôme valide ou corrige."),
            ("Clôture (5 min)",
             "Recensez collectivement les voyelles « difficiles ». "
             "Annoncez le passage aux tons (Module III)."),
        ],
        "freedom": (
            "Si la classe est nombreuse, organisez l'écoute discriminative en "
            "demi-groupes. Vous pouvez aussi remplacer la lecture à voix haute "
            "par un dictée chuchotée si les élèves sont à l'aise."
        ),
        "student_intro": (
            "Le bulu a sept voyelles. Quatre d'entre elles n'existent pas en "
            "français écrit : ɛ, ɔ, ə, et la longue. Aujourd'hui tu apprends "
            "à les distinguer."
        ),
        "student_activities": [
            ("Activité 1 — Reconnaître la voyelle",
             "Pour chaque mot, écoute et écris la première voyelle que tu entends. "
             "Choisis parmi : i, e, ɛ, a, ɔ, o, u, ə."),
            ("Activité 2 — Lire en binôme",
             "Avec ton voisin, lisez chaque mot à tour de rôle. Celui qui écoute "
             "valide ou corrige. Changez de rôle après chaque mot."),
            ("Activité 3 — Recopier",
             "Recopie soigneusement les trois mots les plus difficiles dans ton cahier."),
        ],
        "memo": (
            "Les voyelles ɛ et ɔ se prononcent bouche plus ouverte que e et o. "
            "La voyelle ə (« e muet ») est centrale, ni avant ni arrière."
        ),
    },

    # === Module III — Suprasegmentaux ====================================
    {
        "id": "III-1",
        "code": "III.1",
        "module": "M3-suprasegmentaux",
        "moduleTitle": "Module III — Suprasegmentaux",
        "title": "Tons hauts et tons bas",
        "duration": "60 min",
        "level": "6e",
        "objectives": [
            "Comprendre que le bulu est une langue à tons",
            "Distinguer un ton haut (´) d'un ton bas (`) à l'oreille",
            "Lire correctement des mots porteurs de tons",
        ],
        "filter": dict(module="M3-suprasegmentaux", max_tokens=3, min_tones=2),
        "teacher_steps": [
            ("Accroche (5 min)",
             "Comparez deux mots quasi-identiques au tableau (par exemple "
             "mə̀nɛ́n « gros » vs un autre mot que vous connaissez). Demandez à la "
             "classe : « qu'est-ce qui change ? ». Faites émerger l'idée de hauteur."),
            ("Présentation des tons (15 min)",
             "Expliquez la convention AGLC : accent aigu = ton haut, "
             "accent grave = ton bas, circonflexe = descendant, antiflexe = montant. "
             "Mimez chaque ton avec la main (haut, bas, descendant, montant)."),
            ("Écoute et geste (15 min)",
             "Faites écouter chaque mot du jour. À chaque ton, les élèves lèvent "
             "ou baissent la main. Cette gestuelle est essentielle pour ancrer la "
             "perception tonale."),
            ("Marquage tonal (15 min)",
             "Distribuez la fiche élève. Sur la transcription dépouillée des tons, "
             "les élèves placent les accents au bon endroit après écoute. "
             "Corrigez collectivement."),
            ("Clôture (10 min)",
             "Faites prononcer un mot par chaque rangée. Comparez les rangées : "
             "qui prononce le plus juste ? Cette émulation aide la mémorisation."),
        ],
        "freedom": (
            "Si vos élèves ont du mal, restez plus longtemps sur deux tons "
            "(haut/bas) avant d'aborder les contours (montant/descendant). "
            "Vous pouvez aussi chanter les tons sur deux notes (sol-do)."
        ),
        "student_intro": (
            "Le bulu est une langue à tons : la même suite de lettres peut "
            "vouloir dire des choses différentes selon que la voix monte ou "
            "descend. Aujourd'hui tu apprends à entendre les tons."
        ),
        "student_activities": [
            ("Activité 1 — Lever-baisser la main",
             "Écoute chaque mot. Lève la main si la voix monte, baisse-la si "
             "la voix descend. Vérifie en regardant la transcription."),
            ("Activité 2 — Placer les accents",
             "Sur le mot écrit sans tons, dessine au-dessus de chaque syllabe "
             "une flèche : ↑ pour haut, ↓ pour bas."),
            ("Activité 3 — Imiter",
             "Choisis 3 mots et enregistre-toi (ou prononce-les à voix haute "
             "trois fois). Compare avec l'audio."),
        ],
        "memo": (
            "En AGLC : á = ton haut, à = ton bas, â = ton descendant, ǎ = ton "
            "montant. Un mauvais ton = un autre mot, ou un mot incompréhensible."
        ),
    },
    {
        "id": "III-2",
        "code": "III.2",
        "module": "M3-suprasegmentaux",
        "moduleTitle": "Module III — Suprasegmentaux",
        "title": "Le ton qui monte, le ton qui descend",
        "duration": "60 min",
        "level": "6e",
        "objectives": [
            "Identifier un ton montant et un ton descendant",
            "Reproduire ces mouvements tonals en isolation et dans un mot",
            "Marquer correctement les tons en AGLC",
        ],
        "filter": dict(module="M3-suprasegmentaux", min_tones=3, max_tokens=4),
        "teacher_steps": [
            ("Rappel (5 min)",
             "Faites rappeler par un élève les conventions tonales vues en III.1. "
             "Affichez les quatre symboles au tableau."),
            ("Démonstration (10 min)",
             "Prononcez successivement : á (haut), à (bas), â (haut→bas), "
             "ǎ (bas→haut). Faites bien sentir la durée plus longue des contours."),
            ("Écoute discriminative (20 min)",
             "Pour chaque mot du jour, demandez aux élèves d'identifier le ton "
             "de la dernière syllabe. Notez collectivement. Vérifiez avec la "
             "transcription officielle."),
            ("Production (15 min)",
             "En binôme, un élève prononce un mot en cachant la transcription, "
             "l'autre dessine la courbe tonale sur son cahier. Échangez."),
            ("Clôture (10 min)",
             "Mini-quiz oral : 5 mots à identifier ton par ton. Corrigez "
             "immédiatement et félicitez les progrès."),
        ],
        "freedom": (
            "Si vous disposez d'un piano ou d'un téléphone avec une appli de "
            "réglage de hauteur, faites-le entendre : cela aide énormément. "
            "Sinon, le geste de la main suffit largement."
        ),
        "student_intro": (
            "Au-delà du ton haut et du ton bas, le bulu connaît deux contours : "
            "le ton qui monte (â pas — non, ǎ : bas→haut) et celui qui descend "
            "(â : haut→bas). C'est subtil mais on s'y habitue."
        ),
        "student_activities": [
            ("Activité 1 — Tracer la courbe",
             "Pour chaque mot, dessine sur ton cahier une ligne qui suit la voix : "
             "horizontale pour un ton plat, oblique pour un contour."),
            ("Activité 2 — Dictée tonale",
             "Le professeur prononce un mot. Sur ta fiche, ajoute uniquement les "
             "accents au-dessus de la transcription nue."),
            ("Activité 3 — S'enregistrer",
             "Choisis le mot le plus long et enregistre-toi sur ton téléphone. "
             "Réécoute : tes contours sont-ils nets ?"),
        ],
        "memo": (
            "Les contours (â, ǎ) sont plus longs que les tons plats (á, à). "
            "Bien marquer la durée aide à les rendre audibles."
        ),
    },
    {
        "id": "III-3",
        "code": "III.3",
        "module": "M3-suprasegmentaux",
        "moduleTitle": "Module III — Suprasegmentaux",
        "title": "Paires aux tons opposés",
        "duration": "60 min",
        "level": "6e",
        "objectives": [
            "Repérer que deux mots de même squelette consonantique peuvent "
            "différer uniquement par les tons",
            "Mémoriser quelques couples utiles",
            "Lire à voix haute en respectant les tons",
        ],
        "filter": dict(module="M3-suprasegmentaux", min_tones=2, max_tokens=2),
        "teacher_steps": [
            ("Mise en route (5 min)",
             "Demandez aux élèves : « avez-vous déjà confondu deux mots à cause "
             "des tons ? ». Recueillez les anecdotes."),
            ("Découverte (15 min)",
             "Présentez les mots du jour groupés deux par deux quand c'est "
             "possible. Faites lire et entendre les contrastes."),
            ("Mémorisation (15 min)",
             "Jeu du « pong tonal » : vous prononcez un mot, les élèves doivent "
             "produire le mot opposé tonalement (s'il existe dans la liste)."),
            ("Application en phrase courte (15 min)",
             "Faites construire à l'oral une phrase simple « moi je dis X » en "
             "français pour ancrer le sens. Le but est moins la phrase que la "
             "consolidation lexicale."),
            ("Clôture (10 min)",
             "Demandez à chaque élève de prononcer son mot préféré et d'expliquer "
             "pourquoi en français."),
        ],
        "freedom": (
            "Si les élèves ne saisissent pas le contraste, isolez la voyelle "
            "tonique et faites-la chanter sur deux notes. Si tout va bien, "
            "passez à la lecture des phrases du module IV."
        ),
        "student_intro": (
            "On dit parfois que le bulu est une langue « musicale ». Ce n'est "
            "pas un cliché : un même mot peut changer de sens selon la mélodie. "
            "Apprends quelques paires utiles."
        ),
        "student_activities": [
            ("Activité 1 — Trier",
             "Classe les mots par hauteur globale : plutôt aigu, plutôt grave, "
             "ou les deux."),
            ("Activité 2 — Répéter en boucle",
             "Choisis un mot et répète-le 10 fois en exagérant les tons. "
             "Au début c'est étrange ; au bout de 10 fois, ça vient."),
            ("Activité 3 — Réutiliser",
             "Note dans ton cahier 3 mots que tu veux retenir absolument. "
             "Reviens-y demain."),
        ],
        "memo": (
            "Deux mots peuvent ne différer que par les tons. La transcription "
            "AGLC les distingue grâce aux accents."
        ),
    },
    {
        "id": "III-4",
        "code": "III.4",
        "module": "M3-suprasegmentaux",
        "moduleTitle": "Module III — Suprasegmentaux",
        "title": "Rythme et longueur des syllabes",
        "duration": "60 min",
        "level": "6e",
        "objectives": [
            "Repérer les voyelles longues (notées par redoublement ou « : »)",
            "Identifier les syllabes accentuées dans une phrase courte",
            "Lire un énoncé bulu avec un rythme correct",
        ],
        "filter": dict(min_tokens=3, max_tokens=6, min_tones=3),
        "teacher_steps": [
            ("Mise en route (5 min)",
             "Tapez dans les mains au rythme d'une phrase française. Demandez : "
             "« combien de battements ? ». Annoncez : « aujourd'hui on tape le "
             "rythme du bulu »."),
            ("Présentation (10 min)",
             "Au tableau, écrivez une phrase du jour. Soulignez les syllabes "
             "longues. Expliquez la convention AGLC : voyelle redoublée ou « : »."),
            ("Tape-rythme (20 min)",
             "Faites réécouter chaque phrase. Les élèves tapent en rythme : "
             "1 tape par syllabe, 2 tapes pour une syllabe longue. C'est très "
             "ludique et efficace."),
            ("Lecture rythmée (15 min)",
             "En groupes de 4, les élèves lisent une phrase en respectant les "
             "longueurs. Vérifiez l'aisance, pas la perfection."),
            ("Clôture (10 min)",
             "Une phrase au choix, tous ensemble, à voix haute, avec rythme. "
             "Cela donne le sentiment de « parler bulu »."),
        ],
        "freedom": (
            "Vous pouvez utiliser un tambour, un crayon sur la table, n'importe "
            "quel objet pour marquer la pulsation. Pas besoin d'instrument."
        ),
        "student_intro": (
            "Une phrase bulu a son propre rythme : certaines syllabes sont "
            "courtes, d'autres longues. Bien marquer le rythme rend la phrase "
            "compréhensible."
        ),
        "student_activities": [
            ("Activité 1 — Compter les syllabes",
             "Pour chaque phrase, compte les syllabes. Vérifie en tapant des mains."),
            ("Activité 2 — Repérer les longues",
             "Souligne dans la transcription les voyelles écrites « aa » ou « a: »."),
            ("Activité 3 — Lire en rythme",
             "À voix haute, en tapant le rythme. Pas de précipitation : la "
             "régularité prime sur la vitesse."),
        ],
        "memo": (
            "Une voyelle longue se note « aa » ou « a: » en AGLC. "
            "Le rythme du bulu n'est pas celui du français."
        ),
    },

    # === Module IV — Syntagme nominal ====================================
    {
        "id": "IV-1",
        "code": "IV.1",
        "module": "M4-syntagme-nominal",
        "moduleTitle": "Module IV — Syntagme nominal",
        "title": "Désigner les objets de la maison",
        "duration": "60 min",
        "level": "5e",
        "objectives": [
            "Nommer 6 objets du quotidien en bulu",
            "Construire un syntagme nominal simple « le X »",
            "Reconnaître l'accord de classe",
        ],
        "filter": dict(fr_pattern=r"\b(maison|porte|fen[êe]tre|toit|mur|chaise|table|lit|natte|cuisine|marmite|assiette|plat|cuvette|panier|pot|couteau|corde|bois|feu|case|pierre|calebasse|cuillère|pirogue|hache)\b", max_n=8),
        "teacher_steps": [
            ("Mise en route (5 min)",
             "Demandez aux élèves de nommer en français trois objets qui les "
             "entourent en classe. Listez-les au tableau."),
            ("Découverte du vocabulaire (15 min)",
             "Pour chaque objet du jour : faites écouter le mot bulu, montrez ou "
             "mimez l'objet, faites répéter. Insistez sur la prononciation."),
            ("Mémorisation (15 min)",
             "Jeu de l'aveugle : un élève ferme les yeux, vous nommez un objet en "
             "bulu, l'élève désigne un objet de la classe correspondant. Sinon, "
             "support image distribué."),
            ("Construction de groupes nominaux (15 min)",
             "Présentez 2-3 phrases simples du jour avec un objet (« il y a une "
             "X dans la calebasse »). Faites repérer le nom dans la phrase."),
            ("Clôture (10 min)",
             "Tour de table : chaque élève nomme un objet en bulu et le pointe. "
             "Validez avec bienveillance."),
        ],
        "freedom": (
            "Apportez si possible quelques vrais objets en classe (calebasse, "
            "marmite). C'est imparable. Sinon, des images suffisent."
        ),
        "student_intro": (
            "Quand on apprend une langue, le plus utile est de pouvoir désigner "
            "ce qu'on a sous les yeux. Apprends à nommer les objets de la maison."
        ),
        "student_activities": [
            ("Activité 1 — Écouter et désigner",
             "Pour chaque mot, désigne dans ta tête ou sur une image l'objet "
             "correspondant."),
            ("Activité 2 — Recopier",
             "Recopie chaque mot en AGLC, soigneusement, avec ses tons."),
            ("Activité 3 — Réutiliser",
             "Choisis 3 objets autour de toi et essaie de les nommer en bulu "
             "(ceux que tu as appris)."),
        ],
        "memo": (
            "Les noms bulu portent une « classe » (1, 2, 3…). C'est un peu comme "
            "le genre en français mais il y a beaucoup plus de classes."
        ),
    },
    {
        "id": "IV-2",
        "code": "IV.2",
        "module": "M4-syntagme-nominal",
        "moduleTitle": "Module IV — Syntagme nominal",
        "title": "Compter en bulu",
        "duration": "60 min",
        "level": "5e",
        "objectives": [
            "Énoncer les nombres de 1 à 10 en bulu",
            "Construire un syntagme nominal avec déterminant numéral",
            "Lire et écrire les nombres en AGLC",
        ],
        "filter": dict(pos=("num",)),
        "teacher_steps": [
            ("Mise en route (5 min)",
             "Comptez ensemble jusqu'à 10 en français. Annoncez : « et maintenant, "
             "en bulu »."),
            ("Présentation des nombres (15 min)",
             "Faites écouter chaque nombre du jour. Faites répéter en chœur "
             "puis individuellement. Affichez les chiffres au tableau."),
            ("Mémorisation (15 min)",
             "Jeu de la chaîne : élève 1 dit « 1 », élève 2 dit « 1, 2 », "
             "élève 3 dit « 1, 2, 3 »… Tout le monde participe."),
            ("Application (15 min)",
             "Phrases du type « 3 enfants et 2 chiens » : faites repérer "
             "le nombre puis le nom qu'il modifie."),
            ("Clôture (10 min)",
             "Petit calcul : « 2 + 3 = ? » à dire en bulu. Validez ensemble."),
        ],
        "freedom": (
            "Si la classe est dynamique, ajoutez la dimension corporelle : "
            "les élèves se mettent debout en formant des groupes de N selon le "
            "nombre prononcé. C'est très efficace pour ancrer."
        ),
        "student_intro": (
            "Compter, c'est l'une des choses les plus utiles dans la vie "
            "quotidienne. Apprends les nombres en bulu pour faire le marché, "
            "compter tes camarades, dire ton âge."
        ),
        "student_activities": [
            ("Activité 1 — Compter à voix haute",
             "Compte de 1 à 10 en bulu sans regarder ton cahier. "
             "Recommence trois fois."),
            ("Activité 2 — Écrire",
             "Écris en AGLC les nombres de 1 à 5."),
            ("Activité 3 — Phrases-éclairs",
             "Forme oralement : « 2 chèvres », « 3 enfants », « 5 maisons » "
             "(les noms que tu as déjà vus)."),
        ],
        "memo": (
            "En bulu, le nombre se place souvent après le nom : "
            "« enfants trois » plutôt que « trois enfants ». Observe bien l'ordre."
        ),
    },
    {
        "id": "IV-3",
        "code": "IV.3",
        "module": "M4-syntagme-nominal",
        "moduleTitle": "Module IV — Syntagme nominal",
        "title": "Décrire avec des adjectifs",
        "duration": "60 min",
        "level": "5e",
        "objectives": [
            "Utiliser les adjectifs courants (grand, petit, beau, gros)",
            "Faire l'accord de l'adjectif avec le nom",
            "Construire des descriptions courtes",
        ],
        "filter": dict(pos=("adj",), max_tokens=3),
        "teacher_steps": [
            ("Mise en route (5 min)",
             "Au tableau : « j'ai vu un X grand-petit-beau ». Demandez aux "
             "élèves de dire en français comment ils décrivent une personne, un "
             "animal, un objet."),
            ("Présentation des adjectifs (15 min)",
             "Pour chaque adjectif du jour : prononciation, exemple en phrase, "
             "geste illustrant le sens (mains écartées pour « grand », etc.)."),
            ("Repérage de l'accord (15 min)",
             "Comparez le singulier et le pluriel d'un même adjectif. Faites "
             "remarquer le changement de préfixe (l'élève n'a pas besoin de "
             "tout maîtriser, juste de remarquer)."),
            ("Production (15 min)",
             "Chaque élève choisit un objet de la classe et tente une description "
             "à 2 mots : nom + adjectif. Validez à l'oral."),
            ("Clôture (10 min)",
             "Faites lire 3 phrases descriptives complètes du jour. "
             "Insistez sur le rythme et les tons."),
        ],
        "freedom": (
            "Si vous repérez que les élèves confondent adjectif et nom, "
            "passez plus de temps sur le repérage. Si tout va bien, lancez "
            "le concours du « plus beau syntagme »."
        ),
        "student_intro": (
            "Les adjectifs sont les mots qui décrivent. En bulu, ils s'accordent "
            "avec le nom (au singulier comme au pluriel). Apprends-en quelques-uns."
        ),
        "student_activities": [
            ("Activité 1 — Sens",
             "Pour chaque adjectif, mime le sens (grand : tu écartes les bras ; "
             "petit : tu rapetisses ; etc.)."),
            ("Activité 2 — Singulier/pluriel",
             "Repère, dans les exemples du jour, les adjectifs au singulier puis "
             "au pluriel. Le préfixe change."),
            ("Activité 3 — Décris",
             "Décris en bulu un objet de ta chambre avec deux mots : un nom + "
             "un adjectif. Note dans ton cahier."),
        ],
        "memo": (
            "L'adjectif s'accorde avec le nom. Singulier et pluriel ont des "
            "préfixes différents. Le détail n'a pas à être maîtrisé tout de suite."
        ),
    },

    # === Module V — Syntagme verbal ======================================
    {
        "id": "V-1",
        "code": "V.1",
        "module": "M5-syntagme-verbal",
        "moduleTitle": "Module V — Syntagme verbal",
        "title": "Verbes d'action du quotidien",
        "duration": "60 min",
        "level": "5e",
        "objectives": [
            "Identifier 6 verbes d'action courants en bulu",
            "Construire une phrase « je + verbe »",
            "Comprendre une phrase action courte",
        ],
        "filter": dict(pos=("v",), fr_pattern=r"\b(aller|venir|courir|marcher|prendre|donner|voir|regarder|entendre|[ée]couter|parler|dire|faire|mettre|rester|partir|arriver|monter|descendre|tomber|porter|frapper|jouer|travailler|planter|chercher|trouver|connaitre|conna[ît]tre|aimer|dormir|manger|boire|chanter|danser|crier|rire|pleurer|tuer)\b", max_n=8),
        "teacher_steps": [
            ("Mise en route (5 min)",
             "Demandez à 5 élèves de mimer une action quelconque. La classe "
             "devine en français. Annoncez : « on va apprendre à le dire en bulu »."),
            ("Présentation des verbes (15 min)",
             "Chaque verbe : audio + mime + traduction. Faites répéter en chœur."),
            ("Compréhension orale (15 min)",
             "Faites écouter les phrases d'exemple. Pour chacune, demandez : "
             "« qui fait quoi ? »."),
            ("Production guidée (15 min)",
             "Chaque élève forme une phrase « je + verbe » en bulu, à l'oral, "
             "puis l'écrit dans son cahier."),
            ("Clôture (10 min)",
             "Mini-saynète : un élève mime, un autre dit la phrase en bulu. "
             "Permutez les rôles."),
        ],
        "freedom": (
            "Si la classe a peu de temps, sélectionnez 4 verbes seulement "
            "mais faites-les vraiment maîtriser plutôt que d'en survoler 8."
        ),
        "student_intro": (
            "Avec quelques verbes d'action, on peut déjà raconter beaucoup. "
            "Apprends-en six et tu pourras décrire ce que tu fais chaque jour."
        ),
        "student_activities": [
            ("Activité 1 — Mime",
             "Pour chaque verbe, mime l'action. Demande à un camarade de deviner."),
            ("Activité 2 — Phrases « je »",
             "Forme oralement : « je vais », « je viens », « je mange »… "
             "Note dans ton cahier."),
            ("Activité 3 — Compréhension",
             "Écoute une phrase et dis (en français) qui fait quoi."),
        ],
        "memo": (
            "En bulu, le verbe peut porter un préfixe sujet. Le pronom personnel "
            "peut être collé ou séparé. À ce stade, contente-toi de reconnaître "
            "le verbe."
        ),
    },
    {
        "id": "V-2",
        "code": "V.2",
        "module": "M5-syntagme-verbal",
        "moduleTitle": "Module V — Syntagme verbal",
        "title": "La famille et les personnes",
        "duration": "60 min",
        "level": "5e",
        "objectives": [
            "Nommer les membres de la famille proche",
            "Comprendre une phrase parlant de quelqu'un",
            "Présenter brièvement un proche",
        ],
        "filter": dict(fr_pattern=r"\b(p[èe]re|m[èe]re|fr[èe]re|s[œo]ur|enfant|fils|fille|mari|femme|oncle|tante|cousin|ami|grand-p|grand-m|parent|b[ée]b[ée]|gar[çc]on|homme|femme|jeune|vieux|vieille|gens|personne)\b", max_n=8),
        "teacher_steps": [
            ("Mise en route (5 min)",
             "Demandez aux élèves : « avec qui habitez-vous ? ». Recueillez "
             "les réponses en français au tableau."),
            ("Présentation du vocabulaire (15 min)",
             "Audio + traduction pour chaque mot. Insistez sur le tutoiement "
             "respectueux que la culture bulu valorise pour les aînés."),
            ("Mémorisation (15 min)",
             "Arbre généalogique au tableau. Chaque élève vient placer un mot "
             "à la bonne case. Variante en binôme sur fiche."),
            ("Compréhension (15 min)",
             "Phrases d'exemple sur la famille (« sa mère », « ses enfants »…). "
             "Identifiez collectivement de qui on parle."),
            ("Clôture (10 min)",
             "Chaque élève dit oralement, en bulu, le mot pour « ma mère » "
             "ou « mon père ». Validez."),
        ],
        "freedom": (
            "La famille est un sujet sensible (deuils, séparations). Restez "
            "souple sur les présentations personnelles ; restreignez si besoin "
            "à des personnages fictifs (« Pierre, Marie »)."
        ),
        "student_intro": (
            "La famille est au cœur de la culture bulu. Les mots pour « père », "
            "« mère », « enfant » sont parmi les premiers à apprendre."
        ),
        "student_activities": [
            ("Activité 1 — Arbre",
             "Sur ton cahier, dessine ton arbre généalogique à 3 niveaux. "
             "Note en bulu les mots que tu connais."),
            ("Activité 2 — Présenter",
             "À l'oral : « ma mère + adjectif que tu connais »."),
            ("Activité 3 — Compréhension",
             "Écoute une phrase et dis de quel proche on parle."),
        ],
        "memo": (
            "Les mots de famille en bulu portent souvent un préfixe possessif. "
            "Au début, contente-toi de reconnaître la racine."
        ),
    },
    {
        "id": "V-3",
        "code": "V.3",
        "module": "M5-syntagme-verbal",
        "moduleTitle": "Module V — Syntagme verbal",
        "title": "Les animaux du village et de la forêt",
        "duration": "60 min",
        "level": "5e",
        "objectives": [
            "Nommer 6 animaux courants",
            "Distinguer animaux domestiques et sauvages",
            "Décrire ce qu'un animal fait",
        ],
        "filter": dict(fr_pattern=r"\b(chien|chat|poule|coq|ch[èe]vre|mouton|vache|boeuf|oiseau|poisson|serpent|rat|souris|antilope|panth[èe]re|l[ée]opard|crocodile|tortue|singe|[ée]l[ée]phant|escargot|fourmi)\b", max_n=8),
        "teacher_steps": [
            ("Mise en route (5 min)",
             "Demandez : « quels animaux trouve-t-on autour du village ? ». "
             "Listez en français au tableau."),
            ("Présentation (15 min)",
             "Pour chaque animal : audio + image (ou cri imité) + traduction. "
             "Distinguez deux colonnes : domestiques / sauvages."),
            ("Mémorisation (15 min)",
             "Jeu : vous prononcez le nom de l'animal, les élèves miment "
             "l'animal (ailes pour l'oiseau, ramper pour le serpent…)."),
            ("Phrases d'action (15 min)",
             "Phrases « l'animal X fait Y » du jour. Faites repérer le verbe."),
            ("Clôture (10 min)",
             "Concours du plus beau « cri d'animal » avec son nom en bulu."),
        ],
        "freedom": (
            "Adaptez aux animaux locaux : si vous êtes en zone forestière, "
            "insistez sur les sauvages ; en zone villageoise, sur les domestiques. "
            "Restez sur le vocabulaire bulu attesté dans la fiche."
        ),
        "student_intro": (
            "Les animaux peuplent les contes et les chansons en bulu. "
            "En connaître les noms permet de comprendre beaucoup d'histoires."
        ),
        "student_activities": [
            ("Activité 1 — Trier",
             "Classe les animaux en deux colonnes : domestiques / sauvages."),
            ("Activité 2 — Mimer",
             "Mime trois animaux et fais deviner à un camarade leur nom en bulu."),
            ("Activité 3 — Phrase courte",
             "Choisis un animal et un verbe (« courir », « manger »…) et "
             "fabrique oralement une phrase de 2 mots."),
        ],
        "memo": (
            "Les noms d'animaux ont leurs préfixes propres. Les contes bulu "
            "donnent une grande place aux animaux."
        ),
    },
    {
        "id": "V-4",
        "code": "V.4",
        "module": "M5-syntagme-verbal",
        "moduleTitle": "Module V — Syntagme verbal",
        "title": "Manger, boire, cultiver",
        "duration": "60 min",
        "level": "5e",
        "objectives": [
            "Connaître les verbes liés à l'alimentation",
            "Comprendre une phrase autour du repas et du champ",
            "Construire une phrase « je mange + nourriture »",
        ],
        "filter": dict(fr_pattern=r"\b(manger|boire|eau|vin|riz|mais|ma[ïi]s|banane|igname|manioc|viande|poisson|sel|huile|sucre|fruit|pain|lait|repas|cuit|cuire|champ|planter|r[ée]colter|march[ée]|nourriture|cuisiner)\b", max_n=8),
        "teacher_steps": [
            ("Mise en route (5 min)",
             "Demandez : « qu'avez-vous mangé ce matin ? ». Listez les aliments "
             "en français au tableau."),
            ("Présentation du vocabulaire (15 min)",
             "Audio + traduction pour chaque mot. Distinguez actions (manger, "
             "boire, cuire) et aliments (eau, manioc, poisson…)."),
            ("Construction de phrases (15 min)",
             "Modèle : « je + verbe + aliment ». Chaque élève en construit une "
             "à l'oral."),
            ("Compréhension (15 min)",
             "Phrases d'exemple. Identifiez la nourriture mentionnée."),
            ("Clôture (10 min)",
             "Tour de classe : « moi je mange X ». Chaque élève répond."),
        ],
        "freedom": (
            "Sujet riche culturellement (tabous alimentaires, plats régionaux). "
            "Restez factuel et bienveillant ; n'imposez aucune préférence."
        ),
        "student_intro": (
            "Tout le monde mange, tout le monde boit. Apprends à le dire en bulu : "
            "ce sont des phrases que tu utiliseras tous les jours."
        ),
        "student_activities": [
            ("Activité 1 — Catégoriser",
             "Sépare verbes et aliments dans deux listes."),
            ("Activité 2 — Construire",
             "Forme 3 phrases « je verbe aliment »."),
            ("Activité 3 — Audio",
             "Écoute une phrase et dis ce qu'on mange ou boit."),
        ],
        "memo": (
            "Les noms d'aliments portent souvent une classe nominale spécifique. "
            "Reste sur la racine au début."
        ),
    },

    # === Module VI — La phrase ===========================================
    {
        "id": "VI-1",
        "code": "VI.1",
        "module": "M6-phrase",
        "moduleTitle": "Module VI — La phrase",
        "title": "Phrases existentielles : « il y a »",
        "duration": "60 min",
        "level": "5e",
        "objectives": [
            "Reconnaître la structure « il y a » en bulu",
            "Identifier le sujet et le complément de lieu",
            "Produire une phrase « il y a X dans Y »",
        ],
        "filter": dict(fr_pattern=r"\b(il y a|y a|il existe)\b", max_n=8),
        "teacher_steps": [
            ("Mise en route (5 min)",
             "Demandez : « qu'y a-t-il dans la salle de classe ? ». Recueillez "
             "des réponses en français : « il y a un tableau, des chaises… »."),
            ("Présentation de la structure (15 min)",
             "Phrases du jour. Repérez collectivement le marqueur d'existence "
             "et le complément de lieu."),
            ("Repérage (15 min)",
             "Pour chaque phrase : entourez le sujet, soulignez le lieu. "
             "Variante en binôme avec correction."),
            ("Production (15 min)",
             "Chaque élève forme une phrase à partir d'un objet vu en IV.1 "
             "et d'un lieu. Modèle : « il y a une calebasse dans la maison »."),
            ("Clôture (10 min)",
             "Lecture des plus belles productions. Faites valoriser l'effort."),
        ],
        "freedom": (
            "Si la classe a déjà bien acquis la structure, lancez un concours : "
            "qui produit la phrase la plus longue tout en restant correcte ? "
            "Sinon, restez sur le modèle simple."
        ),
        "student_intro": (
            "La structure « il y a » est très utile : elle permet de décrire ce "
            "qui se trouve dans un endroit. Apprends à la reconnaître."
        ),
        "student_activities": [
            ("Activité 1 — Repérer",
             "Pour chaque phrase, entoure le mot qui désigne le lieu."),
            ("Activité 2 — Compléter",
             "Sur un trou « il y a ___ dans la maison », place un mot vu en IV.1."),
            ("Activité 3 — Inventer",
             "Décris ce qu'il y a sur ton bureau, en bulu, en deux phrases."),
        ],
        "memo": (
            "« il y a » se construit en bulu autour d'un verbe d'existence. "
            "Le complément de lieu suit souvent."
        ),
    },
    {
        "id": "VI-2",
        "code": "VI.2",
        "module": "M6-phrase",
        "moduleTitle": "Module VI — La phrase",
        "title": "Décrire un objet par sa qualité",
        "duration": "60 min",
        "level": "5e",
        "objectives": [
            "Construire une phrase « X est Y » (Y = adjectif)",
            "Faire l'accord adjectif/nom",
            "Lire une phrase descriptive avec aisance",
        ],
        "filter": dict(fr_pattern=r"\b(est)\b", pos=("adj",), max_n=8),
        "teacher_steps": [
            ("Mise en route (5 min)",
             "Au tableau : « ce stylo est ___ ». Demandez aux élèves de "
             "compléter en français avec un adjectif."),
            ("Présentation (15 min)",
             "Phrases du jour. Identifiez nom-sujet, copule, adjectif."),
            ("Repérage de l'accord (15 min)",
             "Comparez les phrases : la marque de classe sur l'adjectif change "
             "selon le nom. Faites observer sans trop insister."),
            ("Production (15 min)",
             "« mon livre est petit », « ma maison est grande »… "
             "Chaque élève en produit deux à l'oral, puis à l'écrit."),
            ("Clôture (10 min)",
             "Trois élèves au choix lisent leurs phrases à voix haute."),
        ],
        "freedom": (
            "Sujet idéal pour intégrer les adjectifs vus en IV.3. "
            "Si vos élèves bloquent sur l'accord, ne le corrigez pas trop "
            "frontalement à ce stade : laissez-les s'imprégner."
        ),
        "student_intro": (
            "Décrire, c'est dire ce qu'une chose est. Avec un nom et un "
            "adjectif, tu peux déjà beaucoup."
        ),
        "student_activities": [
            ("Activité 1 — Repérer",
             "Souligne l'adjectif dans chaque phrase."),
            ("Activité 2 — Transformer",
             "Sur le modèle d'une phrase du jour, change le nom : "
             "« le X est grand » → « la Y est grande »."),
            ("Activité 3 — Inventer",
             "Décris 3 objets de ta classe en bulu."),
        ],
        "memo": (
            "L'adjectif s'accorde avec le nom. La copule (« être ») prend "
            "souvent une forme courte (« nə̀ »)."
        ),
    },
    {
        "id": "VI-3",
        "code": "VI.3",
        "module": "M6-phrase",
        "moduleTitle": "Module VI — La phrase",
        "title": "Localiser : ici, là, là-bas",
        "duration": "60 min",
        "level": "5e",
        "objectives": [
            "Comprendre le système des démonstratifs spatiaux",
            "Distinguer « ici », « là », « là-bas »",
            "Localiser un objet ou une personne",
        ],
        "filter": dict(fr_pattern=r"\b(ici|l[àa]|l[àa]-bas|en haut|en bas|dehors|dedans|loin|pr[èe]s)\b", max_n=8),
        "teacher_steps": [
            ("Mise en route (5 min)",
             "Au tableau : pointez votre bureau (ici), un élève (là), la fenêtre "
             "(là-bas). Verbalisez en français."),
            ("Présentation (15 min)",
             "Phrases du jour comportant les marqueurs de lieu. Pour chacune, "
             "désignez physiquement le point dont on parle."),
            ("Geste et mémoire (15 min)",
             "Vous prononcez « ici / là / là-bas » : les élèves pointent dans la "
             "salle. Ce mouvement aide énormément."),
            ("Production (15 min)",
             "Chaque élève dit une phrase « il y a X ici/là/là-bas » en désignant."),
            ("Clôture (10 min)",
             "Faites lire 3 phrases du jour à voix haute, avec geste."),
        ],
        "freedom": (
            "Bel exercice à mener dehors si la météo le permet : la cour "
            "offre un meilleur terrain de jeu pour les distances."
        ),
        "student_intro": (
            "« Ici », « là », « là-bas » : trois mots tout simples mais "
            "indispensables pour situer ce dont on parle."
        ),
        "student_activities": [
            ("Activité 1 — Pointer",
             "Pour chaque phrase, pointe physiquement la zone évoquée."),
            ("Activité 2 — Compléter",
             "Sur le modèle « il y a X ___ », choisis ici/là/là-bas selon "
             "la position de l'objet."),
            ("Activité 3 — Décrire la classe",
             "Décris à l'oral 3 objets en utilisant un démonstratif spatial."),
        ],
        "memo": (
            "Les démonstratifs spatiaux distinguent souvent trois zones : "
            "près de moi, près de toi, loin de tous les deux."
        ),
    },
    # === Module VII — Gestion du quotidien Niveau 1 (4e, 25h) ============
    {
        "id": "VII-1",
        "code": "VII.1",
        "module": "M7-quotidien-1",
        "moduleTitle": "Module VII — Gestion du quotidien (Niveau 1)",
        "title": "Saluer, se présenter, prendre congé",
        "duration": "60 min",
        "level": "4e",
        "objectives": [
            "Échanger des salutations en bulu adaptées au moment de la journée",
            "Se présenter brièvement (nom, âge, lieu d'habitation)",
            "Clore un échange par une formule de prise de congé",
        ],
        "filter": dict(fr_pattern=r"\b(bonjour|bonsoir|salut|au revoir|merci|s'il te plaît|comment t'appelles|je m'appelle)\b", max_n=10),
        "teacher_steps": [
            ("Mise en route (5 min)",
             "Saluez la classe en bulu (mbolo). Faites répéter. Demandez aux "
             "élèves de saluer leur voisin en bulu sans aucune autre instruction. "
             "Observez les hésitations."),
            ("Présentation des formules (15 min)",
             "Au tableau, listez les formules de salutation selon le moment "
             "de la journée et le statut (aîné/cadet). Faites observer que la "
             "politesse passe aussi par la posture, pas seulement par les mots."),
            ("Modélisation (15 min)",
             "Jouez avec un élève une mini-saynette : se croiser, saluer, "
             "demander des nouvelles, prendre congé. Décomposez chaque réplique."),
            ("Pratique en binôme (15 min)",
             "Chaque élève joue la saynette avec son voisin. Variantes : matin/"
             "soir, ami/aîné. Circulez et corrigez la prononciation et la posture."),
            ("Clôture (10 min)",
             "Trois binômes volontaires passent devant la classe. La classe "
             "valide ou suggère. Bilan : « ce que j'ai appris à dire ». "),
        ],
        "freedom": (
            "Adaptez aux usages locaux : si vos élèves ont une variante "
            "particulière (régionale, familiale), valorisez-la. Vous pouvez "
            "filmer une saynette et la rejouer à la séance suivante."
        ),
        "student_intro": (
            "Saluer, c'est le premier pas vers une vraie conversation. En "
            "bulu, la salutation tient compte du moment de la journée et du "
            "respect dû à l'aîné. Aujourd'hui, tu apprends ces gestes simples."
        ),
        "student_activities": [
            ("Activité 1 — Choisir la bonne formule",
             "Pour chaque situation (matin, soir, aîné, cadet), choisis la "
             "formule appropriée parmi celles vues en classe."),
            ("Activité 2 — Mini-saynette",
             "Avec un camarade, joue une rencontre : salutation → présentation "
             "→ congé. 4 répliques chacun."),
            ("Activité 3 — Carnet",
             "Recopie dans ton cahier 5 formules que tu t'engages à utiliser "
             "à la maison cette semaine."),
        ],
        "memo": (
            "Saluer en bulu, c'est tenir compte du moment et du statut. "
            "On ne s'adresse pas à un aîné comme à un camarade. "
            "Les formules de prise de congé sont aussi importantes que celles "
            "d'accueil."
        ),
    },
    {
        "id": "VII-2",
        "code": "VII.2",
        "module": "M7-quotidien-1",
        "moduleTitle": "Module VII — Gestion du quotidien (Niveau 1)",
        "title": "À la maison : objets et activités",
        "duration": "60 min",
        "level": "4e",
        "objectives": [
            "Nommer 8 à 10 objets et lieux courants de la maison en bulu",
            "Décrire en une phrase une activité domestique simple",
            "Comprendre une consigne courte donnée à la maison",
        ],
        "filter": dict(fr_pattern=r"\b(maison|cuisine|chambre|cour|porte|table|chaise|lit|eau|feu|balayer|cuisiner|laver|dormir|manger)\b", max_n=12),
        "teacher_steps": [
            ("Mise en route (5 min)",
             "Demandez : « citez 5 objets que vous voyez chez vous tous les "
             "matins ». Recueillez en français au tableau."),
            ("Vocabulaire (15 min)",
             "Présentez 8 à 10 mots bulu : maison, cuisine, eau, feu, balai, "
             "etc. Pour chaque mot, prononcez deux fois, faites répéter, "
             "écrivez au tableau en AGLC."),
            ("Activités domestiques (15 min)",
             "Reliez chaque objet à un verbe d'action : balai → balayer, "
             "feu → cuisiner, eau → laver. Faites construire des couples."),
            ("Production de phrases (15 min)",
             "Modèle : « je [verbe] [objet] dans [lieu] ». Chaque élève "
             "produit 3 phrases simples, les présente à son voisin."),
            ("Clôture (10 min)",
             "Tour de table : chaque élève dit une activité qu'il fait "
             "vraiment chez lui. Encouragez l'usage du bulu réel."),
        ],
        "freedom": (
            "Adaptez à la réalité de vos élèves : urbain/rural, maison "
            "traditionnelle/moderne. Le bulu n'a pas une seule manière de "
            "dire « maison » selon le contexte. Soyez à l'écoute."
        ),
        "student_intro": (
            "Ta maison est pleine de mots à découvrir. Aujourd'hui, tu vas "
            "apprendre à nommer ce qui t'entoure quand tu rentres chez toi, "
            "et à décrire ce que tu y fais."
        ),
        "student_activities": [
            ("Activité 1 — Étiqueter",
             "Sur le dessin de la maison fourni, écris en bulu le nom de "
             "chaque objet ou lieu indiqué."),
            ("Activité 2 — Apparier",
             "Relie chaque objet (colonne A) à l'action qui lui correspond "
             "(colonne B)."),
            ("Activité 3 — Mes 3 phrases",
             "Écris 3 phrases vraies sur ce que tu fais à la maison, en "
             "utilisant les mots du jour."),
        ],
        "memo": (
            "Le vocabulaire de la maison est une porte d'entrée naturelle "
            "vers le bulu de tous les jours. Apprends d'abord les mots que "
            "tu peux réutiliser dès ce soir."
        ),
    },
    {
        "id": "VII-3",
        "code": "VII.3",
        "module": "M7-quotidien-1",
        "moduleTitle": "Module VII — Gestion du quotidien (Niveau 1)",
        "title": "Au marché : acheter et vendre",
        "duration": "60 min",
        "level": "4e",
        "objectives": [
            "Demander un prix et nommer 6 à 8 produits courants en bulu",
            "Comprendre une réponse de marchand (prix, quantité)",
            "Conduire un mini-dialogue d'achat de bout en bout",
        ],
        "filter": dict(fr_pattern=r"\b(combien|prix|cher|cher|acheter|vendre|argent|marché|francs|donner|prendre|peu|beaucoup)\b", max_n=12),
        "teacher_steps": [
            ("Mise en route (5 min)",
             "Demandez aux élèves : « quand êtes-vous allé(e) au marché pour "
             "la dernière fois ? Avez-vous parlé en français ou en langue ? ». "
             "Recueillez quelques témoignages."),
            ("Vocabulaire produits (15 min)",
             "Présentez 6 à 8 noms de produits du marché (banane plantain, "
             "huile, tomate, poisson, pain, etc.). Prononcez et faites "
             "répéter. Écrivez en AGLC au tableau."),
            ("Vocabulaire transaction (15 min)",
             "Présentez les formules : « combien ça coûte ? », « c'est trop "
             "cher », « je prends », « merci ». Modélisez avec un élève."),
            ("Jeu de rôle (15 min)",
             "Organisez un mini-marché : 4 vendeurs, le reste de la classe "
             "achète. Chaque transaction dure ~1 min. Tournez les rôles."),
            ("Clôture (10 min)",
             "Bilan : qu'est-ce qui a été facile, difficile ? Recensez les "
             "formules à retenir absolument."),
        ],
        "freedom": (
            "Le marché est un terrain extraordinaire pour la langue vivante. "
            "Si vous le pouvez, organisez une vraie sortie ; à défaut, "
            "demandez aux élèves d'enregistrer (audio) un échange réel "
            "avec accord, et apportez-le en classe la séance d'après."
        ),
        "student_intro": (
            "Au marché, on parle, on négocie, on rit. C'est l'un des lieux "
            "où le bulu est le plus vivant. Aujourd'hui, tu vas apprendre "
            "à acheter quelque chose en bulu de bout en bout."
        ),
        "student_activities": [
            ("Activité 1 — Liste de courses",
             "Choisis 5 produits que tu veux « acheter » et écris leur nom "
             "en bulu."),
            ("Activité 2 — Demander le prix",
             "Pour chaque produit, écris la phrase « combien coûte X ? » "
             "en bulu (modèle au tableau)."),
            ("Activité 3 — Mini-dialogue",
             "Avec un camarade, joue un échange : tu demandes, il/elle "
             "répond, tu décides. 6 répliques au total."),
        ],
        "memo": (
            "Au marché, la politesse compte autant que le prix. Saluer le "
            "vendeur avant de demander, c'est déjà une marque de respect "
            "qu'on apprend dès l'enfance."
        ),
    },

    # === Module VIII — Gestion du quotidien Niveau 2 (3e, 25h) ============
    {
        "id": "VIII-1",
        "code": "VIII.1",
        "module": "M8-quotidien-2",
        "moduleTitle": "Module VIII — Gestion du quotidien (Niveau 2)",
        "title": "Comparer et opposer",
        "duration": "60 min",
        "level": "3e",
        "objectives": [
            "Construire des phrases qui mettent deux choses en parallèle",
            "Comprendre une phrase comportant « les uns / les autres »",
            "Produire une comparaison simple",
        ],
        "filter": dict(fr_pattern=r"\b(plus|moins|aussi|que|les uns|les autres|alors que|tandis que|mais|comme)\b", max_n=8),
        "teacher_steps": [
            ("Mise en route (5 min)",
             "Demandez : « qu'est-ce qui est plus grand : un éléphant ou une "
             "souris ? ». Recueillez les réponses en français."),
            ("Présentation (15 min)",
             "Phrases du jour. Repérez les marqueurs de comparaison ou "
             "d'opposition."),
            ("Analyse (15 min)",
             "Pour les phrases « les uns…, les autres… », faites identifier les "
             "deux groupes. C'est typique du bulu narratif."),
            ("Production (15 min)",
             "Chaque élève construit une comparaison simple à partir du "
             "vocabulaire vu (animaux, objets, personnes)."),
            ("Clôture (10 min)",
             "Lecture de 3 productions. Encouragez la prise de risque."),
        ],
        "freedom": (
            "C'est un sujet de niveau 3e : si vos élèves sont plus jeunes, "
            "limitez-vous au repérage. La production peut être collective "
            "plutôt qu'individuelle."
        ),
        "student_intro": (
            "Comparer, c'est mettre deux choses en relation. En bulu, la "
            "structure « les uns…, les autres… » revient souvent dans les contes."
        ),
        "student_activities": [
            ("Activité 1 — Repérer",
             "Souligne dans chaque phrase les deux choses qu'on compare."),
            ("Activité 2 — Compléter",
             "Sur le modèle « les uns X, les autres Y », place deux verbes "
             "que tu connais."),
            ("Activité 3 — Inventer",
             "Compare deux animaux en français, puis en bulu (avec les mots "
             "que tu connais)."),
        ],
        "memo": (
            "« les uns…, les autres… » est une structure idiomatique du bulu "
            "narratif. La répétition du démonstratif est volontaire."
        ),
    },
    {
        "id": "VIII-2",
        "code": "VIII.2",
        "module": "M8-quotidien-2",
        "moduleTitle": "Module VIII — Gestion du quotidien (Niveau 2)",
        "title": "Petits récits : raconter une scène",
        "duration": "60 min",
        "level": "3e",
        "objectives": [
            "Comprendre une mini-narration en bulu",
            "Identifier sujet, verbe et compléments dans une phrase complexe",
            "Produire une phrase racontant une action",
        ],
        "filter": dict(min_tokens=5, max_tokens=12),
        "teacher_steps": [
            ("Mise en route (5 min)",
             "Demandez : « racontez en une phrase ce que vous avez fait hier ». "
             "Recueillez 2-3 récits en français."),
            ("Présentation (15 min)",
             "Phrases du jour. Pour chacune : qui ? quoi ? où ? quand ? "
             "Faites les repérer collectivement."),
            ("Analyse fine (15 min)",
             "Reprenez une phrase plus longue. Identifiez les marques de temps "
             "(passé, présent), de personne, et les éventuelles particules."),
            ("Production guidée (15 min)",
             "Chaque élève transforme une phrase du jour en changeant le sujet "
             "ou l'action. C'est l'occasion d'expérimenter."),
            ("Clôture (10 min)",
             "Trois élèves volontaires racontent en une phrase ce qu'ils ont "
             "compris d'une phrase du jour."),
        ],
        "freedom": (
            "Récit = liberté. Si vos élèves veulent inventer plus, laissez-les. "
            "Si la phrase « modèle » est trop dense, restez en compréhension."
        ),
        "student_intro": (
            "Raconter, c'est l'une des choses les plus naturelles. En bulu, "
            "tu vas découvrir comment se fabrique une phrase qui raconte."
        ),
        "student_activities": [
            ("Activité 1 — Décortiquer",
             "Pour chaque phrase, écris : qui ? fait quoi ? où ?"),
            ("Activité 2 — Transformer",
             "Change le sujet d'une phrase et adapte le verbe."),
            ("Activité 3 — Inventer",
             "À l'oral, raconte en une phrase ce que tu vois autour de toi."),
        ],
        "memo": (
            "Une phrase complexe en bulu suit l'ordre Sujet-Verbe-Complément, "
            "avec des marques de temps préfixées au verbe."
        ),
    },
    {
        "id": "VIII-3",
        "code": "VIII.3",
        "module": "M8-quotidien-2",
        "moduleTitle": "Module VIII — Gestion du quotidien (Niveau 2)",
        "title": "Demander, répondre, dialoguer",
        "duration": "60 min",
        "level": "3e",
        "objectives": [
            "Reconnaître une phrase interrogative",
            "Comprendre une réponse",
            "Reproduire un mini-dialogue",
        ],
        "filter": dict(fr_pattern=r"[?]|qui|quoi|que|que faire|comment|pourquoi|quand", max_n=8),
        "teacher_steps": [
            ("Mise en route (5 min)",
             "Demandez : « comment pose-t-on une question en français ? ». "
             "Listez les mots interrogatifs : qui, quoi, où, quand, comment, "
             "pourquoi."),
            ("Présentation des phrases (15 min)",
             "Phrases du jour : repérez les questions et les réponses. "
             "Faites observer la prosodie particulière des questions."),
            ("Mémorisation (15 min)",
             "Jeu en binôme : un élève pose une question simple, l'autre "
             "répond. Vous fournissez le modèle."),
            ("Mini-dialogue (15 min)",
             "Quatre élèves au tableau, jouent une saynette à partir de phrases "
             "du jour. Le reste de la classe valide."),
            ("Clôture (10 min)",
             "Bilan oral : qu'avez-vous appris ce trimestre ? Recueillez les "
             "réponses en bulu autant que possible."),
        ],
        "freedom": (
            "Idéale pour conclure un trimestre. Si vous voulez aller plus loin, "
            "filmez un mini-dialogue à partager (avec accord) sur l'ENT de "
            "l'établissement."
        ),
        "student_intro": (
            "Une langue, c'est avant tout un dialogue. Aujourd'hui, tu apprends "
            "à poser une question simple et à y répondre."
        ),
        "student_activities": [
            ("Activité 1 — Question ou réponse ?",
             "Pour chaque phrase, dis si c'est une question ou une réponse."),
            ("Activité 2 — Apparier",
             "Relie chaque question à sa réponse possible."),
            ("Activité 3 — Jouer",
             "Avec un camarade, joue un mini-dialogue de 4 répliques."),
        ],
        "memo": (
            "L'intonation montante marque souvent la question. Certains "
            "marqueurs interrogatifs sont placés en fin de phrase."
        ),
    },
]


def build_lesson(plan, items):
    """Construit la fiche complète à partir du plan et des items filtrés."""
    flt = dict(plan["filter"])
    max_n = flt.pop("max_n", 8)
    selected = select(items, max_n=max_n, **flt)
    teacher_plan = [
        {"title": title, "instruction": instr}
        for (title, instr) in plan["teacher_steps"]
    ]
    student_acts = [
        {"title": title, "instruction": instr}
        for (title, instr) in plan["student_activities"]
    ]
    return {
        "id": plan["id"],
        "code": plan["code"],
        "module": plan["module"],
        "moduleTitle": plan["moduleTitle"],
        "title": plan["title"],
        "duration": plan["duration"],
        "level": plan["level"],
        "objectives": plan["objectives"],
        "vocabulary": [trim(it) for it in selected],
        "teacher": {
            "intro": (
                "Cette leçon dure environ " + plan["duration"] +
                ". Le plan est en cinq étapes : il vous laisse libre de "
                "moduler la durée, l'ordre et la profondeur selon votre classe. "
                "Le vocabulaire ci-contre est extrait du corpus ALCAM."
            ),
            "steps": teacher_plan,
            "freedom": plan["freedom"],
            "tips": (
                "Si vous n'êtes pas locuteur natif, faites systématiquement "
                "écouter l'audio en référence avant de prononcer vous-même. "
                "Si vous l'êtes, partagez vos variantes avec la classe : "
                "elles enrichissent l'apprentissage."
            ),
        },
        "student": {
            "intro": plan["student_intro"],
            "activities": student_acts,
            "memo": plan["memo"],
        },
    }


def main():
    items = load_bulu()
    lessons = [build_lesson(plan, items) for plan in LESSONS_PLAN]

    counts = Counter(l["module"] for l in lessons)
    voc_total = sum(len(l["vocabulary"]) for l in lessons)

    out = {
        "language": "bulu",
        "lessons": lessons,
        "stats": {
            "total_lessons": len(lessons),
            "by_module": dict(counts),
            "vocabulary_items": voc_total,
        },
    }

    out_path = DATA_DIR / "lessons_bulu.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2),
                        encoding="utf-8")

    print(f"Wrote {out_path}: {len(lessons)} leçons, {voc_total} items de vocabulaire")
    for code, count in counts.items():
        print(f"  {code}: {count} leçon(s)")


if __name__ == "__main__":
    main()
