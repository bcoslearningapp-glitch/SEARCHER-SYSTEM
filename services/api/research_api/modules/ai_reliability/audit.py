"""Installation audit for the blocking evaluation dimensions measured from canonical state (#56, QUALITY_GATES).

The golden fixtures measure what a model does with synthetic inputs. These dimensions are properties of what
the installation actually holds, so they are measured on the real records:
- `exact_quote_fidelity`: every quote in every output version equals its source, byte for byte;
- `quran_hadith_integrity`: Qur'an and Hadith quotes that do not match the approved text (count);
- `claim_source_separation`: layer-labelled blocks where source text is quoted and inference is not;
- `tool_use_correctness`: tool calls that ran outside their task's allow-list, or for an unregistered tool (count).

Results are recorded under provider `installation` and model `audit`, because no single model produced them.
"""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from research_api.modules.ai_reliability import service as reliability
from research_api.modules.ai_reliability.dimensions import INSTALLATION
from research_api.modules.ai_reliability.schemas import EvaluationIn, EvaluationOut
from research_api.modules.ai_tools import registry
from research_api.modules.governance_audit.context import authorized
from research_api.modules.governance_audit.principal import Principal
from research_api.modules.outputs_integrity import service as outputs
from research_api.modules.research_orchestrator.service import TASK_TOOLS
from research_api.platform import jobs

PROVIDER, MODEL = INSTALLATION, "audit"


def _tool_violations(session: Session) -> tuple[int, int, int]:
    """(calls that ran, violations, calls with no job to attribute them to)."""
    executed = registry.executed_calls(session)
    tasks: dict[UUID, str | None] = {}
    violations = unattributed = 0
    for tool, job_id in executed:
        if tool not in registry.TOOLS:
            violations += 1
            continue
        if job_id is not None and job_id not in tasks:
            try:
                tasks[job_id] = jobs.get_job(session, job_id).params.get("task")
            except jobs.JobNotFoundError:  # e.g. calls imported with a project; jobs are not exported
                tasks[job_id] = None
        task = tasks.get(job_id) if job_id is not None else None
        if task is None:
            unattributed += 1
        elif tool not in TASK_TOOLS.get(task, frozenset()):
            violations += 1
    return len(executed), violations, unattributed


def run(session: Session, principal: Principal) -> list[EvaluationOut]:
    authorized(principal, "ai_evaluation.record")  # the Methodology Steward or the system; never an AI
    quotes = outputs.audit_quotes(session)
    executed, violations, unattributed = _tool_violations(session)
    run_id = uuid4()
    measures = [
        (
            "exact_quote_fidelity",
            quotes.exact / quotes.quotes if quotes.quotes else 1.0,
            quotes.quotes,
            {"quotes": quotes.quotes, "exact": quotes.exact, "failures": quotes.failures},
        ),
        (
            "quran_hadith_integrity",
            float(quotes.sacred_not_matching),
            quotes.sacred,
            {"checked": quotes.sacred, "not_matching": quotes.sacred_not_matching},
        ),
        (
            "claim_source_separation",
            quotes.layered_correct / quotes.layered_blocks if quotes.layered_blocks else 1.0,
            quotes.layered_blocks,
            {"labelled_blocks": quotes.layered_blocks, "correct": quotes.layered_correct},
        ),
        (
            "tool_use_correctness",
            float(violations),
            executed,
            {"executed": executed, "violations": violations, "unattributed": unattributed},
        ),
    ]
    return [
        reliability.record_evaluation(
            session,
            principal,
            EvaluationIn(
                provider=PROVIDER,
                model=MODEL,
                dimension=dimension,
                score=score,
                sample_size=max(sample, 1),
                method="AUTOMATED_AUDIT",
                fixture_set="installation",
                notes=None if sample else "nothing to measure yet; recorded as vacuously passing",
                details=details,
            ),
            run_id=run_id,
        )
        for dimension, score, sample, details in measures
    ]
