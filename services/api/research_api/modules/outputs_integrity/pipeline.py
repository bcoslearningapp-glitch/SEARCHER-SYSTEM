"""The eight-step output integrity pipeline (FR-OUT-002, FR-OUT-003, Core §54).

The steps run in order on one output version:
1. claim verification — CLAIM blocks trace to existing entities; wording changes and weak or
   refuted standing are flagged;
2. citation verification — EVIDENCE blocks cite accepted evidence, never candidates;
3. exact quote verification — each quote equals its source, byte for byte;
4. reference integrity — source-text layers are quotes, and inference is never shown as source text;
5. terminology check — reworded claims keep approved terms;
6. translation-semantic check — reworded claims keep their strength;
7. language editing — edits after quote verification left every protected quote unchanged;
8. final rendering — every quote appears verbatim in the rendered document.
A FAIL makes the version FAILED, and a FAILED version cannot be approved. WARN findings need a
person's acknowledgement.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy.orm import Session

from research_api.contracts.enums import (
    EvidenceStatus,
    EvidenceStrength,
    EvidenceTargetType,
    HypothesisEpistemicState,
    IntegrityStatus,
    IntegrityStep,
    IntegrityStepStatus,
    LanguageCode,
    OutputBlockKind,
    OutputMode,
    ReferenceReasoningLayer,
)
from research_api.modules import targets
from research_api.modules.claims_evidence import service as claims
from research_api.modules.hypothesis_lab import service as hypotheses
from research_api.modules.knowledge_memory import terminology
from research_api.modules.knowledge_memory.terminology_schemas import TranslationCheckIn
from research_api.modules.outputs_integrity import quotes, render
from research_api.modules.outputs_integrity.schemas import Block
from research_api.platform.errors import DomainError, NotFoundError

K = OutputBlockKind
P = IntegrityStepStatus
TARGETS = {
    "Claim": EvidenceTargetType.CLAIM,
    "Hypothesis": EvidenceTargetType.HYPOTHESIS,
    "Mechanism": EvidenceTargetType.MECHANISM,
    "DesignConcept": EvidenceTargetType.DESIGN_CONCEPT,
    "DesignHypothesis": EvidenceTargetType.DESIGN_HYPOTHESIS,
}
WEAK = frozenset({EvidenceStrength.UNSUBSTANTIATED, EvidenceStrength.WEAK})


@dataclass
class StepResult:
    step: IntegrityStep
    status: IntegrityStepStatus = P.PASS
    findings: list[dict[str, object]] = field(default_factory=list)

    def flag(self, severity: IntegrityStepStatus, code: str, message: str, block: int | None = None) -> None:
        finding: dict[str, object] = {"code": code, "message": message}
        if block is not None:
            finding["block"] = block
        self.findings.append(finding)
        order = [P.PASS, P.SKIPPED, P.WARN, P.FAIL]
        if order.index(severity) > order.index(self.status):
            self.status = severity


@dataclass(frozen=True)
class Context:
    session: Session
    project_id: UUID
    language: LanguageCode
    source_language: LanguageCode
    blocks: list[Block]
    previous_blocks: list[Block] | None
    edited: bool


def _claims(ctx: Context) -> StepResult:
    result = StepResult(IntegrityStep.CLAIM_VERIFICATION)
    for i, block in enumerate(ctx.blocks):
        if block.kind is not K.CLAIM:
            continue
        for trace in block.trace:
            target = TARGETS.get(trace.entity_type)
            if target is None:
                continue
            try:
                targets.require(ctx.session, ctx.project_id, target, trace.entity_id)
            except NotFoundError:
                result.flag(P.FAIL, "trace.missing", f"{trace.entity_type} {trace.entity_id} does not exist", i)
                continue
            if target is EvidenceTargetType.CLAIM:
                claim = claims.get_claim(ctx.session, ctx.project_id, trace.entity_id)
                if claim.epistemic_strength in WEAK:
                    result.flag(P.WARN, "claim.weak", f"Stated claim is only {claim.epistemic_strength.value}", i)
                if block.text != claim.statement:
                    result.flag(P.WARN, "claim.reworded", "Claim wording differs from the recorded claim", i)
            elif target is EvidenceTargetType.HYPOTHESIS:
                state = hypotheses.get_hypothesis(ctx.session, ctx.project_id, trace.entity_id).epistemic_state
                if state is HypothesisEpistemicState.REFUTED:
                    result.flag(P.WARN, "hypothesis.refuted", "A refuted hypothesis is stated; check it is labelled", i)
    return result


def _citations(ctx: Context) -> StepResult:
    result = StepResult(IntegrityStep.CITATION_VERIFICATION)
    for i, block in enumerate(ctx.blocks):
        if block.kind is not K.EVIDENCE:
            continue
        cited = [t for t in block.trace if t.entity_type == "Evidence"]
        if not cited:
            result.flag(P.FAIL, "evidence.uncited", "Evidence block cites no evidence record", i)
        for trace in cited:
            try:
                item = claims.get_evidence(ctx.session, ctx.project_id, trace.entity_id)
            except NotFoundError:
                result.flag(P.FAIL, "evidence.missing", f"Evidence {trace.entity_id} does not exist", i)
                continue
            if item.status is not EvidenceStatus.ACCEPTED:
                result.flag(P.FAIL, "evidence.not_accepted", f"Evidence is {item.status.value}, not accepted", i)
    return result


def _quotes(ctx: Context) -> StepResult:
    result = StepResult(IntegrityStep.EXACT_QUOTE_VERIFICATION)
    for i, block in enumerate(ctx.blocks):
        if block.kind is K.QUOTE and block.quote is not None:
            reason = quotes.mismatch(ctx.session, ctx.project_id, block.quote)
            if reason is None and block.text != block.quote.text:
                reason = "block text differs from its protected quote"
            if reason:
                result.flag(P.FAIL, "quote.mismatch", reason, i)
    return result


def _reference(ctx: Context) -> StepResult:
    result = StepResult(IntegrityStep.REFERENCE_INTEGRITY)
    layers = {layer.value for layer in ReferenceReasoningLayer}
    for i, block in enumerate(ctx.blocks):
        if block.label not in layers:
            continue
        if block.label == ReferenceReasoningLayer.SOURCE_TEXT.value and block.kind is not K.QUOTE:
            result.flag(P.FAIL, "layer.source_not_quoted", "Source text is shown without its protected quote", i)
        if block.label != ReferenceReasoningLayer.SOURCE_TEXT.value and block.kind is K.QUOTE:
            result.flag(P.FAIL, "layer.inference_as_source", "Interpretation or inference is shown as source text", i)
    return result


def _reworded(ctx: Context) -> list[tuple[int, str, str]]:
    """(block index, recorded claim, output wording) for claims rendered with different wording."""
    pairs = []
    for i, block in enumerate(ctx.blocks):
        if block.kind is not K.CLAIM:
            continue
        for trace in block.trace:
            if trace.entity_type != "Claim":
                continue
            try:
                statement = claims.get_claim(ctx.session, ctx.project_id, trace.entity_id).statement
            except DomainError:
                continue
            if statement != block.text:
                pairs.append((i, statement, block.text))
    return pairs


def _terminology_and_translation(ctx: Context) -> tuple[StepResult, StepResult]:
    terms = StepResult(IntegrityStep.TERMINOLOGY_CHECK)
    semantic = StepResult(IntegrityStep.TRANSLATION_SEMANTIC_CHECK)
    pairs = _reworded(ctx)
    if not pairs:
        terms.status = semantic.status = P.SKIPPED
        return terms, semantic
    for i, source, rendered in pairs:
        check = terminology.check_translation(
            ctx.session,
            TranslationCheckIn(
                source_text=source,
                source_language=ctx.source_language,
                translated_text=rendered,
                target_language=ctx.language,
            ),
        )
        for finding in check.terminology:
            if not finding.found:
                terms.flag(P.WARN, "term.not_approved", f"'{finding.term}': {finding.message}", i)
        for drift in check.strength_drift:
            semantic.flag(P.WARN, f"strength.{drift.axis}", drift.message, i)
    return terms, semantic


def _editing(ctx: Context) -> StepResult:
    """Editing comes after quote verification and never changes a protected quote (FR-OUT-003)."""
    result = StepResult(IntegrityStep.LANGUAGE_EDITING)
    if not ctx.edited or ctx.previous_blocks is None:
        result.status = P.SKIPPED
        return result
    before = {_quote_key(b): b.quote.text for b in ctx.previous_blocks if b.quote is not None}
    for i, block in enumerate(ctx.blocks):
        if block.quote is not None and before.get(_quote_key(block), block.quote.text) != block.quote.text:
            result.flag(P.FAIL, "edit.changed_quote", "An edit changed a protected quote", i)
    return result


def _quote_key(block: Block) -> str:
    q = block.quote
    assert q is not None  # noqa: S101 - callers filter
    return f"{q.source_kind.value}:{q.excerpt_id or q.quran_ref or q.hadith_record_id}"


def _rendering(ctx: Context) -> StepResult:
    result = StepResult(IntegrityStep.FINAL_RENDERING)
    doc = render.Document("check", ctx.language.value, OutputMode.AUDIT, ctx.blocks, 0, "DRAFT")
    rendered = render.markdown(ctx.session, ctx.project_id, doc)
    for i, block in enumerate(ctx.blocks):
        if block.quote is None:
            continue
        for line in block.quote.text.split("\n"):
            if f"> {line}" not in rendered:
                result.flag(P.FAIL, "render.quote_altered", "The rendered document does not reproduce the quote", i)
                break
    return result


def run(ctx: Context) -> tuple[IntegrityStatus, list[StepResult]]:
    steps = [_claims(ctx), _citations(ctx), _quotes(ctx), _reference(ctx)]
    steps += list(_terminology_and_translation(ctx))
    steps += [_editing(ctx), _rendering(ctx)]
    if any(s.status is P.FAIL for s in steps):
        return IntegrityStatus.FAILED, steps
    if any(s.status is P.WARN for s in steps):
        return IntegrityStatus.VERIFIED_WITH_WARNINGS, steps
    return IntegrityStatus.VERIFIED, steps
