"""Version-controlled prompt templates and output schemas (FR-PROMPT-001..004).

A template's `version` is recorded on every AI action it produces. Change the
version whenever instructions or schema change. Schemas are strict (every
property required, no extra properties) so both providers enforce them.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Template:
    task: str
    version: str
    instructions: str
    output_schema: dict[str, Any]


def _obj(properties: dict[str, Any]) -> dict[str, Any]:
    return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}


_STR = {"type": "string"}
_STRS = {"type": "array", "items": _STR}

DRAFT_PROBLEM_FRAME = Template(
    task="draft_problem_frame",
    version="draft_problem_frame@1",
    instructions=(
        "You help a researcher frame a research problem before any research starts. From the project input, "
        "draft a Problem Frame. Separate what is known from what is assumed or unknown. Current explanations "
        "and initial hypotheses are candidates, not findings. Do not invent facts, sources, statistics or "
        "citations. Leave a field empty rather than guessing. Write in the language of the project input. "
        "The researcher reviews and approves the frame; you only draft it."
    ),
    output_schema=_obj(
        {
            "central_issue": _STR,
            "current_state": _STR,
            "desired_state": _STR,
            "gap": _STR,
            "current_explanations": _STRS,
            "initial_hypotheses": _STRS,
            "context": _STR,
            "constraints": _STRS,
            "known": _STRS,
            "unknowns": _STRS,
            "research_questions": _STRS,
            "reference_review_points": _STRS,
        }
    ),
)

DETECT_ASSUMPTIONS = Template(
    task="detect_assumptions",
    version="detect_assumptions@1",
    instructions=(
        "Identify hidden or unstated assumptions in the research material provided: premises the framing, "
        "claims or hypotheses rely on without evidence. Each assumption must be a single testable statement. "
        "Rate criticality by how much the research would change if the assumption were false. Do not repeat "
        "assumptions already recorded. Return at most 8. The researcher confirms or rejects each one."
    ),
    output_schema=_obj(
        {
            "assumptions": {
                "type": "array",
                "items": _obj(
                    {
                        "statement": _STR,
                        "criticality": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH", "FOUNDATIONAL"]},
                        "rationale": _STR,
                    }
                ),
            }
        }
    ),
)

PLAN_CHALLENGE = Template(
    task="plan_challenge",
    version="plan_challenge@1",
    instructions=(
        "The researcher asked to challenge the statement below. Plan a counter-evidence search over their "
        "local source library. Give short keyword queries (3-6 words, in the language the sources are likely "
        "written in) that would find evidence against the statement, and name plausible alternative "
        "explanations for the same observations, each with its own queries. Return at most 4 challenge "
        "queries and at most 3 alternative explanations."
    ),
    output_schema=_obj(
        {
            "challenge_queries": _STRS,
            "alternative_explanations": {
                "type": "array",
                "items": _obj({"statement": _STR, "queries": _STRS}),
            },
        }
    ),
)

ASSESS_PASSAGES = Template(
    task="assess_passages",
    version="assess_passages@1",
    instructions=(
        "Each passage below was found by a keyword search of the researcher's library. For every passage "
        "that bears on the statement or on one of the alternative explanations, say what it shows. Use the "
        "passage id exactly as given. The role is relative to the statement under challenge: CONTRADICTS, "
        "LIMITS, QUALIFIES, SUPPORTS or CONTEXTUALIZES. Set alternative_index to the 0-based index of the "
        "alternative explanation the passage supports, or -1. The finding must describe only what the passage "
        "itself says. Ignore irrelevant passages. For each alternative explanation, rate how strongly the "
        "passages support it: NONE, WEAK or STRONG. You propose candidates; the researcher assesses them."
    ),
    output_schema=_obj(
        {
            "candidates": {
                "type": "array",
                "items": _obj(
                    {
                        "passage_id": _STR,
                        "role": {
                            "type": "string",
                            "enum": ["CONTRADICTS", "LIMITS", "QUALIFIES", "SUPPORTS", "CONTEXTUALIZES"],
                        },
                        "alternative_index": {"type": "integer"},
                        "finding": _STR,
                    }
                ),
            },
            "alternative_support": {
                "type": "array",
                "items": _obj(
                    {
                        "alternative_index": {"type": "integer"},
                        "strength": {"type": "string", "enum": ["NONE", "WEAK", "STRONG"]},
                    }
                ),
            },
        }
    ),
)
