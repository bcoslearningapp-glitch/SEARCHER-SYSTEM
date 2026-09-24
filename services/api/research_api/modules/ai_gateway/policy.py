"""Disclosure policy by project sensitivity (PRD §54). Pure, deterministic."""

from __future__ import annotations

from dataclasses import dataclass

from research_api.contracts.enums import SensitivityLevel as S


@dataclass(frozen=True)
class DisclosureDecision:
    allowed: bool
    reason: str


def cloud_disclosure(sensitivity: S, *, project_consent: bool, provider_is_local: bool) -> DisclosureDecision:
    if provider_is_local:
        return DisclosureDecision(True, "local provider: no external disclosure")
    if sensitivity in (S.PUBLIC, S.NORMAL):
        return DisclosureDecision(True, f"{sensitivity.value} projects may use cloud AI")
    if sensitivity is S.CONFIDENTIAL:
        if project_consent:
            return DisclosureDecision(True, "CONFIDENTIAL: explicit cloud-AI consent; selective context only")
        return DisclosureDecision(False, "CONFIDENTIAL projects need explicit cloud-AI consent in project settings")
    return DisclosureDecision(
        False, f"{sensitivity.value} projects never send content to cloud AI; use Product C or an authorized exception"
    )
