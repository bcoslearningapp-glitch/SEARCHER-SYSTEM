"""Deterministic claim-strength profile and translation drift check (PRD FR-TERM-003, Core §53).

A translation must not silently change how strong a scientific claim is, for example by
turning association into causation or dropping a hedge. Each text gets a profile on
three axes, using a curated ar/fr/en marker lexicon:
- relation: CAUSAL > ASSOCIATIVE > NONE;
- certainty: CERTAIN > NEUTRAL > HEDGED;
- scope: UNIVERSAL > NEUTRAL > PARTIAL.
The source and translation profiles are then compared. This is a deterministic screen,
not a semantic judge: findings go to a person, and a clean result is not proof of
fidelity.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from research_api.contracts.enums import LanguageCode as L

RELATION = {"NONE": 0, "ASSOCIATIVE": 1, "CAUSAL": 2}
CERTAINTY = {"HEDGED": 0, "NEUTRAL": 1, "CERTAIN": 2}
SCOPE = {"PARTIAL": 0, "NEUTRAL": 1, "UNIVERSAL": 2}

# Markers are matched after normalisation (see _normalise). Arabic markers match inside words so that
# attached conjunctions and prepositions (و، ف، ب) do not hide them; Latin markers match whole words.
LEXICON: dict[L, dict[str, dict[str, tuple[str, ...]]]] = {
    L.EN: {
        "relation": {
            "CAUSAL": (
                "causes",
                "caused",
                "cause",
                "causing",
                "leads to",
                "led to",
                "lead to",
                "results in",
                "resulted in",
                "drives",
                "driven by",
                "produces",
                "is responsible for",
                "because of",
                "due to",
                "effect of",
                "impact of",
            ),
            "ASSOCIATIVE": (
                "associated with",
                "association",
                "correlated with",
                "correlates with",
                "correlation",
                "linked to",
                "linked with",
                "related to",
                "relationship between",
                "co-occurs",
            ),
        },
        "certainty": {
            "CERTAIN": (
                "proves",
                "proven",
                "proof",
                "demonstrates",
                "demonstrated",
                "confirms",
                "confirmed",
                "establishes",
                "established",
                "definitely",
                "certainly",
                "always",
                "undoubtedly",
                "clearly shows",
            ),
            "HEDGED": (
                "may",
                "might",
                "could",
                "suggests",
                "suggested",
                "possibly",
                "possible",
                "likely",
                "probably",
                "appears to",
                "seems to",
                "indicates",
                "tentative",
                "preliminary",
            ),
        },
        "scope": {
            "UNIVERSAL": ("all", "every", "everyone", "always", "in every case", "universally"),
            "PARTIAL": ("some", "several", "in some cases", "a few", "many", "most"),
        },
    },
    L.FR: {
        "relation": {
            "CAUSAL": (
                "cause",
                "causent",
                "cause par",
                "provoque*",
                "entraine*",
                "conduit a",
                "conduisent a",
                "mene a",
                "aboutit a",
                "est responsable de",
                "en raison de",
                "a cause de",
                "effet de",
            ),
            "ASSOCIATIVE": (
                "associe*",
                "association",
                "correle*",
                "correlation",
                "lie a",
                "lie aux",
                "liee aux",
                "lies aux",
                "liees aux",
                "liees a",
                "liee a",
                "lies a",
                "en lien avec",
                "relation entre",
                "rapport avec",
            ),
        },
        "certainty": {
            "CERTAIN": (
                "prouve*",
                "preuve",
                "demontre*",
                "confirme",
                "confirment",
                "etablit",
                "etabli",
                "certainement",
                "toujours",
                "sans aucun doute",
                "incontestablement",
            ),
            "HEDGED": (
                "pourrait",
                "pourraient",
                "peut",
                "peuvent",
                "suggere*",
                "semble",
                "semblent",
                "probablement",
                "possiblement",
                "eventuellement",
                "peut-etre",
                "indique",
                "preliminaire",
            ),
        },
        "scope": {
            "UNIVERSAL": ("tous", "toutes", "chaque", "tout le monde", "dans tous les cas", "toujours"),
            "PARTIAL": ("certains", "certaines", "quelques", "plusieurs", "dans certains cas", "la plupart"),
        },
    },
    L.AR: {
        "relation": {
            "CAUSAL": (
                "يسبب",
                "تسبب",
                "يسببه",
                "سبب",
                "يودي الي",
                "تودي الي",
                "ادي الي",
                "ادت الي",
                "ينتج عن",
                "ينتج عنه",
                "نتيجه ل",
                "بسبب",
                "مسوول عن",
                "اثر",
            ),
            "ASSOCIATIVE": (
                "يرتبط",
                "ترتبط",
                "مرتبط",
                "مرتبطه",
                "ارتباط",
                "علاقه ب",
                "علاقه بين",
                "مقترن",
                "يقترن",
                "متلازم",
            ),
        },
        "certainty": {
            "CERTAIN": (
                "يثبت",
                "تثبت",
                "اثبت",
                "اثبتت",
                "يبرهن",
                "يوكد",
                "توكد",
                "اكد",
                "قطعا",
                "دايما",
                "بلا شك",
                "حتما",
            ),
            "HEDGED": (
                "قد",
                "ربما",
                "يشير الي",
                "تشير الي",
                "يبدو",
                "من المحتمل",
                "يحتمل",
                "يرجح",
                "اوليه",
                "مبدييا",
            ),
        },
        "scope": {
            "UNIVERSAL": ("جميع", "كل ", "كافه", "دايما"),
            "PARTIAL": ("بعض", "عدد من", "احيانا", "معظم", "اغلب"),
        },
    },
}

_ARABIC_DIACRITICS = re.compile("[ؐ-ًؚ-ٰٟۖ-ۭـ]")
# Hamza-carrying alef forms -> alef, alef maqsura -> ya, ta marbuta -> ha, hamza on waw/ya -> waw/ya.
_ARABIC_FOLD = str.maketrans("أإآٱىةؤئ", "اااايهوي")
# Short Arabic particles only count as whole words (e.g. "قد" but not inside "قدم").
_ARABIC_WHOLE_WORD = frozenset({"قد", "اثر", "سبب", "كل "})


def normalise(text: str, language: L) -> str:
    if language is L.AR:
        folded = _ARABIC_DIACRITICS.sub("", text).translate(_ARABIC_FOLD)
        return " " + re.sub(r"\s+", " ", folded) + " "
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return " " + re.sub(r"[^\w'-]+", " ", stripped) + " "


def _matches(text: str, marker: str, language: L) -> bool:
    if language is L.AR and marker not in _ARABIC_WHOLE_WORD:
        return marker in text
    if marker.endswith("*"):  # word prefix, for inflected forms (associe*, associees ...)
        return f" {marker[:-1]}" in text
    return f" {marker.strip()} " in text


@dataclass(frozen=True)
class Profile:
    relation: str
    certainty: str
    scope: str
    markers: dict[str, list[str]] = field(default_factory=dict)


def profile(text: str, language: L) -> Profile:
    normalised = normalise(text, language)
    found: dict[str, list[str]] = {}
    levels: dict[str, str] = {}
    defaults = {"relation": "NONE", "certainty": "NEUTRAL", "scope": "NEUTRAL"}
    scales = {"relation": RELATION, "certainty": CERTAINTY, "scope": SCOPE}
    for axis, categories in LEXICON[language].items():
        hits = {
            level: [m for m in markers if _matches(normalised, m, language)] for level, markers in categories.items()
        }
        present = [level for level, markers in hits.items() if markers]
        for level in present:
            found[f"{axis}.{level}"] = hits[level]
        if axis == "relation":
            # The strongest relation stated is the claim's relation.
            levels[axis] = max(present, key=lambda lv: scales[axis][lv]) if present else defaults[axis]
        elif len(present) == 1:
            levels[axis] = present[0]
        else:
            # Mixed signals (e.g. "may always") are left neutral rather than guessed.
            levels[axis] = defaults[axis]
    return Profile(levels["relation"], levels["certainty"], levels["scope"], found)


@dataclass(frozen=True)
class Drift:
    axis: str
    direction: str  # STRENGTHENED | WEAKENED
    source_level: str
    translation_level: str
    message: str


_MESSAGES = {
    ("relation", "STRENGTHENED"): "The translation states a stronger relation (e.g. association became causation).",
    ("relation", "WEAKENED"): "The translation states a weaker relation (e.g. causation became association).",
    ("certainty", "STRENGTHENED"): "The translation is more certain than the source (a hedge was dropped or hardened).",
    ("certainty", "WEAKENED"): "The translation is less certain than the source (a hedge was added).",
    ("scope", "STRENGTHENED"): "The translation generalises beyond the source's scope.",
    ("scope", "WEAKENED"): "The translation narrows the source's scope.",
}


def compare(source: Profile, translation: Profile) -> list[Drift]:
    drifts = []
    for axis, scale in (("relation", RELATION), ("certainty", CERTAINTY), ("scope", SCOPE)):
        a, b = getattr(source, axis), getattr(translation, axis)
        if scale[a] == scale[b]:
            continue
        direction = "STRENGTHENED" if scale[b] > scale[a] else "WEAKENED"
        drifts.append(Drift(axis, direction, a, b, _MESSAGES[(axis, direction)]))
    return drifts
