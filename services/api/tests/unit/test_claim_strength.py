"""Claim-strength drift between a source and its translation (FR-TERM-003), with ar/fr/en fixtures."""

from __future__ import annotations

import pytest

from research_api.contracts.enums import LanguageCode as L
from research_api.modules.knowledge_memory.claim_strength import compare, profile

# (source language, source, translation language, translation, expected drifts as (axis, direction))
CASES = [
    # association -> causation, the canonical failure
    (
        L.EN,
        "Mentoring is associated with higher retention.",
        L.FR,
        "Le mentorat entraîne une meilleure rétention.",
        {("relation", "STRENGTHENED")},
    ),
    (
        L.EN,
        "Mentoring is associated with higher retention.",
        L.AR,
        "الإرشاد يؤدي إلى ارتفاع الاستبقاء.",
        {("relation", "STRENGTHENED")},
    ),
    (
        L.AR,
        "يرتبط الإرشاد بارتفاع الاستبقاء.",
        L.EN,
        "Mentoring causes higher retention.",
        {("relation", "STRENGTHENED")},
    ),
    (
        L.EN,
        "Mentoring may be associated with retention.",
        L.FR,
        "Le mentorat pourrait être associé à une meilleure rétention.",
        set(),
    ),
    (L.EN, "Buddies are linked to attendance.", L.FR, "Les binômes sont liées aux présences.", set()),
    (L.FR, "Le mentorat est corrélé à la rétention.", L.EN, "Mentoring is correlated with retention.", set()),
    # causation -> association
    (
        L.EN,
        "Pay freezes cause disengagement.",
        L.FR,
        "Le gel des salaires est lié à un désengagement.",
        {("relation", "WEAKENED")},
    ),
    # dropped hedge / added certainty
    (
        L.EN,
        "The pilot suggests buddies may help.",
        L.FR,
        "Le pilote prouve que les binômes aident.",
        {("certainty", "STRENGTHENED")},
    ),
    (L.EN, "Buddies may reduce absence.", L.AR, "قد يقلل الزملاء من الغياب.", set()),
    (L.EN, "Buddies may reduce absence.", L.AR, "يثبت أن الزملاء يقللون الغياب.", {("certainty", "STRENGTHENED")}),
    (L.EN, "The study demonstrates the effect.", L.FR, "L'étude suggère l'effet.", {("certainty", "WEAKENED")}),
    # scope generalisation
    (
        L.EN,
        "Some apprentices disengage in year two.",
        L.FR,
        "Tous les apprentis se désengagent en deuxième année.",
        {("scope", "STRENGTHENED")},
    ),
    (L.FR, "Certains apprentis se désengagent.", L.AR, "جميع المتدربين ينسحبون.", {("scope", "STRENGTHENED")}),
    (L.AR, "بعض المتدربين ينسحبون.", L.EN, "Some apprentices withdraw.", set()),
]


@pytest.mark.parametrize(("src_lang", "source", "dst_lang", "translation", "expected"), CASES)
def test_drift(src_lang: L, source: str, dst_lang: L, translation: str, expected: set[tuple[str, str]]) -> None:
    drifts = compare(profile(source, src_lang), profile(translation, dst_lang))
    assert {(d.axis, d.direction) for d in drifts} == expected


def test_arabic_normalisation_ignores_diacritics_and_attached_particles() -> None:
    vowelled = profile("وَيُؤَدِّي إِلَى نَتَائِجَ", L.AR)
    assert vowelled.relation == "CAUSAL"
    assert profile("قدم الفريق تقريرا", L.AR).certainty == "NEUTRAL", "'qad' only as a whole word"


def test_markers_are_reported_for_the_reviewer() -> None:
    result = profile("Mentoring may lead to retention in some cases.", L.EN)
    assert result.relation == "CAUSAL" and result.certainty == "HEDGED" and result.scope == "PARTIAL"
    assert "leads to" not in result.markers["relation.CAUSAL"] and "lead to" in result.markers["relation.CAUSAL"]


def test_mixed_certainty_signals_stay_neutral() -> None:
    assert profile("It may always happen.", L.EN).certainty == "NEUTRAL"
