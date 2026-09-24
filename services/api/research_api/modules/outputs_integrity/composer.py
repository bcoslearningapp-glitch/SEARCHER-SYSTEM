"""Deterministic composition of output blocks from canonical project state (PRD §37, FR-OUT-004).

Every statement block traces to the canonical entity it comes from. Exact quotes are copied
from their source (a verified excerpt, the approved Qur'an text, or a Hadith record) and
marked protected. Nothing here calls a model: the composer only arranges what the project
already records. AI drafting (a later step) edits a draft version, and that edit is checked.
"""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from sqlalchemy.orm import Session

from research_api.contracts.enums import (
    DecisionStatus,
    DesignConceptStatus,
    EvidenceTargetType,
    LanguageCode,
    OutputBlockKind,
    OutputType,
    QuoteSourceKind,
    ReferenceReasoningLayer,
)
from research_api.modules.claims_evidence import service as claims
from research_api.modules.design_experiments import experiment_service as experiments
from research_api.modules.design_experiments import service as design
from research_api.modules.design_experiments.experiment_schemas import ExperimentOut
from research_api.modules.governance_audit import service as governance
from research_api.modules.hypothesis_lab import service as hypotheses
from research_api.modules.knowledge_memory import service as knowledge
from research_api.modules.outputs_integrity.schemas import Block, Quote, Trace
from research_api.modules.project_workflow import service as projects
from research_api.modules.reference_governance import service as reference
from research_api.modules.sources_library import service as sources

K = OutputBlockKind
HEADINGS: dict[str, dict[LanguageCode, str]] = {
    "question": {
        LanguageCode.EN: "Research question",
        LanguageCode.FR: "Question de recherche",
        LanguageCode.AR: "سؤال البحث",
    },
    "findings": {
        LanguageCode.EN: "Established findings",
        LanguageCode.FR: "Constats établis",
        LanguageCode.AR: "النتائج الثابتة",
    },
    "claims": {
        LanguageCode.EN: "Claims and evidence",
        LanguageCode.FR: "Affirmations et preuves",
        LanguageCode.AR: "الادعاءات والأدلة",
    },
    "hypotheses": {LanguageCode.EN: "Hypotheses", LanguageCode.FR: "Hypothèses", LanguageCode.AR: "الفرضيات"},
    "open": {LanguageCode.EN: "Open questions", LanguageCode.FR: "Questions ouvertes", LanguageCode.AR: "أسئلة مفتوحة"},
    "reservations": {
        LanguageCode.EN: "Reservations and blockers",
        LanguageCode.FR: "Réserves et blocages",
        LanguageCode.AR: "التحفظات والعوائق",
    },
    "decisions": {LanguageCode.EN: "Decisions", LanguageCode.FR: "Décisions", LanguageCode.AR: "القرارات"},
    "next": {LanguageCode.EN: "Next step", LanguageCode.FR: "Prochaine étape", LanguageCode.AR: "الخطوة التالية"},
    "reference": {
        LanguageCode.EN: "Reference review",
        LanguageCode.FR: "Revue de référence",
        LanguageCode.AR: "المراجعة المرجعية",
    },
    "requirements": {
        LanguageCode.EN: "Design requirements",
        LanguageCode.FR: "Exigences de conception",
        LanguageCode.AR: "متطلبات التصميم",
    },
    "concepts": {
        LanguageCode.EN: "Design concepts",
        LanguageCode.FR: "Concepts de conception",
        LanguageCode.AR: "تصورات التصميم",
    },
    "hypothesis": {
        LanguageCode.EN: "Design hypothesis",
        LanguageCode.FR: "Hypothèse de conception",
        LanguageCode.AR: "فرضية التصميم",
    },
    "protocol": {LanguageCode.EN: "Protocol", LanguageCode.FR: "Protocole", LanguageCode.AR: "البروتوكول"},
    "impact": {
        LanguageCode.EN: "Human-impact review",
        LanguageCode.FR: "Revue d'impact humain",
        LanguageCode.AR: "مراجعة الأثر البشري",
    },
    "observations": {LanguageCode.EN: "Observations", LanguageCode.FR: "Observations", LanguageCode.AR: "الملاحظات"},
    "results": {
        LanguageCode.EN: "Analysed results",
        LanguageCode.FR: "Résultats analysés",
        LanguageCode.AR: "النتائج المحللة",
    },
    "interpretations": {
        LanguageCode.EN: "Interpretations",
        LanguageCode.FR: "Interprétations",
        LanguageCode.AR: "التفسيرات",
    },
    "learning": {
        LanguageCode.EN: "What was learned",
        LanguageCode.FR: "Ce qui a été appris",
        LanguageCode.AR: "ما تم تعلّمه",
    },
    "closure": {LanguageCode.EN: "Closure", LanguageCode.FR: "Clôture", LanguageCode.AR: "الإغلاق"},
    "knowledge": {
        LanguageCode.EN: "Local knowledge",
        LanguageCode.FR: "Connaissances locales",
        LanguageCode.AR: "المعرفة المحلية",
    },
}


class Composer:
    def __init__(self, session: Session, project_id: UUID, language: LanguageCode) -> None:
        self.session, self.project_id, self.language = session, project_id, language
        self.blocks: list[Block] = []

    def heading(self, key: str, level: int = 2, text: str | None = None) -> None:
        self.blocks.append(Block(kind=K.HEADING, text=text or HEADINGS[key][self.language], level=level))

    def add(self, kind: K, text: str, trace: list[tuple[str, UUID]], label: str | None = None) -> None:
        if not text.strip():
            return
        self.blocks.append(
            Block(kind=kind, text=text, label=label, trace=[Trace(entity_type=t, entity_id=i) for t, i in trace])
        )

    def items(self, key: str, items: list[str], trace: list[tuple[str, UUID]]) -> None:
        if not items:
            return
        self.heading(key)
        traced = [Trace(entity_type=t, entity_id=i) for t, i in trace]
        self.blocks.append(Block(kind=K.LIST, items=items, trace=traced))

    def excerpt_quote(self, excerpt_id: UUID, trace: list[tuple[str, UUID]]) -> None:
        excerpt = sources.excerpt_in_project(self.session, self.project_id, excerpt_id)
        if not excerpt.is_exact_quote:
            return  # paraphrased or unverified text is never presented as a quotation
        quote = Quote(
            source_kind=QuoteSourceKind.EXCERPT, excerpt_id=excerpt.id, text=excerpt.text, language=excerpt.language
        )
        traces = [Trace(entity_type=t, entity_id=i) for t, i in trace]
        traces.append(Trace(entity_type="SourceExcerpt", entity_id=excerpt.id))
        self.blocks.append(Block(kind=K.QUOTE, text=excerpt.text, trace=traces, quote=quote))

    def evidence(self, target_type: EvidenceTargetType, target_id: UUID) -> None:
        emap = claims.evidence_map(self.session, self.project_id, target_type, target_id)
        for role, items in emap.by_role.items():
            for item in items:
                self.add(K.EVIDENCE, item.finding, [("Evidence", item.id)], label=role)
                self.excerpt_quote(item.excerpt_id, [("Evidence", item.id)])


# --- builders ---


def _state(c: Composer) -> None:
    state = projects.get_research_state(c.session, c.project_id)
    if state.current_question:
        c.heading("question")
        c.add(K.PARAGRAPH, state.current_question, [("Project", c.project_id)])
    c.items("findings", state.established_findings, [("ResearchState", c.project_id)])


def _claims(c: Composer, *, with_evidence: bool = True) -> None:
    rows = claims.list_claims(c.session, c.project_id)
    if not rows:
        return
    c.heading("claims")
    for claim in rows:
        c.add(K.CLAIM, claim.statement, [("Claim", claim.id)], label=claim.epistemic_strength.value)
        if with_evidence:
            c.evidence(EvidenceTargetType.CLAIM, claim.id)


def _hypotheses(c: Composer, *, with_evidence: bool = True) -> None:
    rows = hypotheses.list_hypotheses(c.session, c.project_id)
    if not rows:
        return
    c.heading("hypotheses")
    for h in rows:
        label = f"{h.lifecycle_state.value} · {h.epistemic_state.value}"
        c.add(K.CLAIM, h.content.statement, [("Hypothesis", h.id)], label=label)
        if with_evidence:
            c.evidence(EvidenceTargetType.HYPOTHESIS, h.id)


def _open(c: Composer) -> None:
    questions = [q for q in claims.list_questions(c.session, c.project_id) if q.status.value == "OPEN"]
    c.items("open", [q.question for q in questions], [("OpenQuestion", q.id) for q in questions])
    state = projects.get_research_state(c.session, c.project_id)
    c.items("reservations", state.reservations + state.blockers, [("ResearchState", c.project_id)])


def _decisions(c: Composer, *, open_too: bool = True) -> None:
    rows = governance.list_decisions(c.session, c.project_id)
    rows = [d for d in rows if open_too or d.status is DecisionStatus.DECIDED]
    if not rows:
        return
    c.heading("decisions")
    for d in rows:
        c.heading("decisions", level=3, text=d.question)
        if d.options:
            c.blocks.append(Block(kind=K.LIST, items=d.options, trace=[Trace(entity_type="Decision", entity_id=d.id)]))
        if d.ai_recommendation is not None:
            c.add(K.NOTE, d.ai_recommendation.model_dump_json(), [("Decision", d.id)], label="AI_RECOMMENDATION")
        if d.final_decision:
            text = d.final_decision + (f" — {d.human_justification}" if d.human_justification else "")
            c.add(K.CLAIM, text, [("Decision", d.id)], label=d.status.value)
        else:
            c.add(K.NOTE, d.status.value, [("Decision", d.id)], label="BLOCKING" if d.blocking else None)


def _reference_reviews(c: Composer, target: tuple[EvidenceTargetType, UUID] | None = None) -> None:
    reviews = reference.list_reviews(
        c.session, c.project_id, target_type=target[0] if target else None, target_id=target[1] if target else None
    )
    if not reviews:
        return
    c.heading("reference")
    for review in reviews:
        c.heading("reference", level=3, text=review.question)
        for entry in review.entries:
            trace = [Trace(entity_type="ReferenceEntry", entity_id=entry.id)]
            if entry.layer is ReferenceReasoningLayer.SOURCE_TEXT:
                quote = _entry_quote(entry.source_excerpt_id, entry.quran_ref, entry.hadith_record_id, entry.content)
                if quote is not None:
                    c.blocks.append(
                        Block(kind=K.QUOTE, text=entry.content, label=entry.layer.value, trace=trace, quote=quote)
                    )
                    continue
            c.blocks.append(Block(kind=K.PARAGRAPH, text=entry.content, label=entry.layer.value, trace=trace))
        judgment = review.current_judgment
        if judgment is not None:
            c.add(K.CLAIM, judgment.rationale, [("ReferenceJudgment", judgment.id)], label=judgment.state.value)


def _entry_quote(excerpt_id: UUID | None, quran_ref: str | None, hadith_id: UUID | None, text: str) -> Quote | None:
    if quran_ref:
        return Quote(source_kind=QuoteSourceKind.QURAN, quran_ref=quran_ref, text=text, language="ar")
    if hadith_id:
        return Quote(source_kind=QuoteSourceKind.HADITH, hadith_record_id=hadith_id, text=text)
    if excerpt_id:
        return Quote(source_kind=QuoteSourceKind.EXCERPT, excerpt_id=excerpt_id, text=text)
    return None


def research_report(c: Composer, _: UUID | None) -> None:
    _state(c)
    _claims(c)
    _hypotheses(c)
    _reference_reviews(c)
    _decisions(c, open_too=False)
    _open(c)


def executive_summary(c: Composer, _: UUID | None) -> None:
    _state(c)
    important = [cl for cl in claims.list_claims(c.session, c.project_id) if cl.important]
    if important:
        c.heading("claims")
        for claim in important:
            c.add(K.CLAIM, claim.statement, [("Claim", claim.id)], label=claim.epistemic_strength.value)
    _hypotheses(c, with_evidence=False)
    state = projects.get_research_state(c.session, c.project_id)
    if state.next_action:
        c.heading("next")
        c.add(K.PARAGRAPH, state.next_action, [("ResearchState", c.project_id)], label=state.next_action_reason)


def decision_brief(c: Composer, _: UUID | None) -> None:
    _state(c)
    _decisions(c)
    _open(c)


def reference_review(c: Composer, _: UUID | None) -> None:
    _reference_reviews(c)


def evidence_map(c: Composer, _: UUID | None) -> None:
    _claims(c)
    _hypotheses(c)


def hypothesis_dossier(c: Composer, subject: UUID | None) -> None:
    assert subject is not None  # noqa: S101 - validated by OutputIn
    h = hypotheses.get_hypothesis(c.session, c.project_id, subject)
    trace = [("Hypothesis", h.id)]
    c.heading("hypotheses")
    c.add(K.CLAIM, h.content.statement, trace, label=f"{h.lifecycle_state.value} · {h.epistemic_state.value}")
    for text in (h.content.context, h.content.expected_outcome, h.content.proposed_mechanism):
        c.add(K.PARAGRAPH, text, trace)
    for label, items in (
        ("ASSUMPTIONS", h.content.assumptions),
        ("BOUNDARY_CONDITIONS", h.content.boundary_conditions),
        ("FALSIFICATION_CONDITIONS", h.content.falsification_conditions),
    ):
        if items:
            c.blocks.append(
                Block(kind=K.LIST, items=items, label=label, trace=[Trace(entity_type="Hypothesis", entity_id=h.id)])
            )
    c.evidence(EvidenceTargetType.HYPOTHESIS, h.id)
    _reference_reviews(c, (EvidenceTargetType.HYPOTHESIS, h.id))


def design_specification(c: Composer, _: UUID | None) -> None:
    requirements = design.list_requirements(c.session, c.project_id)
    if requirements:
        c.heading("requirements")
        for r in requirements:
            c.add(K.CLAIM, r.statement, [("DesignRequirement", r.id)], label=f"{r.priority.value} · {r.status.value}")
    concepts = design.list_concepts(c.session, c.project_id)
    if concepts:
        c.heading("concepts")
    for concept in concepts:
        c.heading("concepts", level=3, text=concept.title)
        c.add(
            K.PARAGRAPH,
            concept.description,
            [("DesignConcept", concept.id)],
            label=f"{concept.status.value} · {concept.origin.value}",
        )
        for cov in concept.coverage:
            c.add(
                K.NOTE,
                cov.coverage.value,
                [("DesignConcept", concept.id), ("DesignRequirement", cov.requirement_id)],
                label="COVERAGE",
            )
        if concept.status is DesignConceptStatus.REJECTED and concept.rejection:
            c.add(
                K.NOTE,
                str(concept.rejection.get("reason", "")),
                [("DesignConcept", concept.id)],
                label=f"REJECTED · {concept.rejection.get('ground')}",
            )


def _experiment_header(c: Composer, experiment_id: UUID) -> ExperimentOut:
    experiment = experiments.get_experiment(c.session, c.project_id, experiment_id)
    dh = experiments.get_design_hypothesis(c.session, c.project_id, experiment.design_hypothesis_id)
    c.heading("hypothesis")
    trace = [("DesignHypothesis", dh.id)]
    c.add(K.CLAIM, f"{dh.content.intervention} → {dh.content.expected_outcome}", trace, label=dh.epistemic_state.value)
    for label, value in dh.content.model_dump().items():
        if isinstance(value, list) and value:
            c.blocks.append(
                Block(
                    kind=K.LIST,
                    items=value,
                    label=label.upper(),
                    trace=[Trace(entity_type="DesignHypothesis", entity_id=dh.id)],
                )
            )
    return experiment


def experiment_protocol(c: Composer, subject: UUID | None) -> None:
    assert subject is not None  # noqa: S101 - validated by OutputIn
    experiment = _experiment_header(c, subject)
    c.heading("protocol")
    for field, value in experiment.protocol.model_dump().items():
        c.add(K.PARAGRAPH, value, [("Experiment", experiment.id)], label=field.upper())
    record = experiments.experiment_record(c.session, c.project_id, experiment.id)
    if record.human_impact:
        c.heading("impact")
        for a in record.human_impact:
            c.add(K.NOTE, a.note, [("HumanImpactAssessment", a.id)], label=f"{a.dimension.value} · {a.finding.value}")


def learning_review(c: Composer, subject: UUID | None) -> None:
    assert subject is not None  # noqa: S101 - validated by OutputIn
    experiment = _experiment_header(c, subject)
    record = experiments.experiment_record(c.session, c.project_id, experiment.id)
    if record.observations:
        c.heading("observations")
        for o in record.observations:
            c.add(K.PARAGRAPH, o.description, [("Observation", o.id)], label=o.observed_at.date().isoformat())
    if record.results:
        c.heading("results")
        for r in record.results:
            c.add(
                K.CLAIM,
                f"{r.method}: {r.summary}",
                [("ExperimentResult", r.id)] + [("Observation", i) for i in r.observation_ids],
            )
    if record.interpretations:
        c.heading("interpretations")
        for i in record.interpretations:
            c.add(
                K.CLAIM,
                i.statement,
                [("Interpretation", i.id)] + [("ExperimentResult", r) for r in i.result_ids],
                label=i.outcome.value,
            )
    if record.learning_reviews:
        c.heading("learning")
        for lr in record.learning_reviews:
            c.add(K.CLAIM, lr.learned, [("LearningReview", lr.id)])
            c.add(K.PARAGRAPH, lr.hypothesis_effect, [("LearningReview", lr.id)])
            if lr.limitations:
                c.blocks.append(
                    Block(
                        kind=K.LIST,
                        items=lr.limitations,
                        label="LIMITATIONS",
                        trace=[Trace(entity_type="LearningReview", entity_id=lr.id)],
                    )
                )


def closure_report(c: Composer, _: UUID | None) -> None:
    for closure in projects.list_closures(c.session, c.project_id):
        c.heading("closure", text=f"{HEADINGS['closure'][c.language]} · {closure.closure_type}")
        record = closure.record
        c.add(
            K.CLAIM, str(record.get("confidence_scope", "")), [("ProjectClosure", closure.id)], label="CONFIDENCE_SCOPE"
        )
        for key in ("resolved", "unresolved", "limitations", "open_questions", "reopen_triggers"):
            if record.get(key):
                c.blocks.append(
                    Block(
                        kind=K.LIST,
                        items=list(record[key]),
                        label=key.upper(),
                        trace=[Trace(entity_type="ProjectClosure", entity_id=closure.id)],
                    )
                )
    items = knowledge.list_items(c.session, c.project_id)
    if items:
        c.heading("knowledge")
        for item in items:
            c.add(
                K.CLAIM,
                item.statement,
                [("KnowledgeItem", item.id)],
                label=f"{item.stage.value} · {item.effective_status.value}",
            )


BUILDERS: dict[OutputType, Callable[[Composer, UUID | None], None]] = {
    OutputType.RESEARCH_REPORT: research_report,
    OutputType.EXECUTIVE_SUMMARY: executive_summary,
    OutputType.DECISION_BRIEF: decision_brief,
    OutputType.REFERENCE_REVIEW: reference_review,
    OutputType.EVIDENCE_MAP: evidence_map,
    OutputType.HYPOTHESIS_DOSSIER: hypothesis_dossier,
    OutputType.DESIGN_SPECIFICATION: design_specification,
    OutputType.EXPERIMENT_PROTOCOL: experiment_protocol,
    OutputType.LEARNING_REVIEW: learning_review,
    OutputType.CLOSURE_REPORT: closure_report,
}


def compose(
    session: Session, project_id: UUID, output_type: OutputType, language: LanguageCode, subject_id: UUID | None
) -> list[Block]:
    composer = Composer(session, project_id, language)
    BUILDERS[output_type](composer, subject_id)
    return composer.blocks
