"""Import every ORM model so Alembic sees the full metadata."""

from research_api.modules.governance_audit.models import (
    ApprovalRecord,
    AuditEventRecord,
    DecisionRecord,
    QualityGateEvaluationRecord,
    ResearchEventRecord,
)
from research_api.modules.project_workflow.models import (
    ProblemFrameVersion,
    Project,
    ProjectClosure,
    ResearchState,
    ScratchNote,
)
from research_api.modules.sources_library.models import (
    ProjectSource,
    SourceAccessRequest,
    SourceAsset,
    SourceChunk,
    SourceEdition,
    SourceExcerpt,
    SourceLead,
    SourcePage,
    SourceWork,
)
from research_api.platform.db import Base
from research_api.platform.jobs import BackgroundJob

__all__ = [
    "ApprovalRecord",
    "AuditEventRecord",
    "BackgroundJob",
    "Base",
    "DecisionRecord",
    "ProblemFrameVersion",
    "Project",
    "ProjectClosure",
    "ProjectSource",
    "QualityGateEvaluationRecord",
    "ResearchEventRecord",
    "ResearchState",
    "ScratchNote",
    "SourceAccessRequest",
    "SourceAsset",
    "SourceChunk",
    "SourceEdition",
    "SourceExcerpt",
    "SourceLead",
    "SourcePage",
    "SourceWork",
]
