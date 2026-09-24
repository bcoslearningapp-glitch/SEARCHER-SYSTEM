"""Import every ORM model so Alembic sees the full metadata."""

from research_api.modules.ai_gateway.models import AIRequestRecord, ProjectAIPolicy
from research_api.modules.ai_reliability.models import AIEvaluation
from research_api.modules.ai_tools.models import AIToolCall
from research_api.modules.claims_evidence.models import (
    Assumption,
    Claim,
    Evidence,
    OpenQuestion,
    ResearchTrackRun,
    SourceLineage,
)
from research_api.modules.design_experiments.models import (
    ConceptCoverage,
    DesignConcept,
    DesignHypothesis,
    DesignHypothesisVersion,
    DesignRequirement,
    Experiment,
    ExperimentResult,
    ExperimentTransition,
    HumanImpactAssessment,
    Interpretation,
    Observation,
)
from research_api.modules.governance_audit.models import (
    ApprovalRecord,
    AuditEventRecord,
    DecisionRecord,
    QualityGateEvaluationRecord,
    ResearchEventRecord,
)
from research_api.modules.hypothesis_lab.models import (
    Hypothesis,
    HypothesisCompetition,
    HypothesisMechanism,
    HypothesisVersion,
    Mechanism,
)
from research_api.modules.operational_constraints.models import OperationalConstraint
from research_api.modules.project_workflow.models import (
    ProblemFrameVersion,
    Project,
    ProjectClosure,
    ResearchState,
    ScratchNote,
)
from research_api.modules.reference_governance.models import (
    FoundationalSource,
    HadithRecord,
    QuranAyah,
    QuranSurah,
    ReferenceEntry,
    ReferenceJudgmentRecord,
    ReferenceReview,
)
from research_api.modules.research_planning.models import ResearchPlan, SearchRecord, SufficiencyAssessment
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
    "AIEvaluation",
    "AIRequestRecord",
    "AIToolCall",
    "ApprovalRecord",
    "Assumption",
    "AuditEventRecord",
    "BackgroundJob",
    "Base",
    "Claim",
    "ConceptCoverage",
    "DecisionRecord",
    "DesignConcept",
    "DesignHypothesis",
    "DesignHypothesisVersion",
    "DesignRequirement",
    "Evidence",
    "Experiment",
    "ExperimentResult",
    "ExperimentTransition",
    "FoundationalSource",
    "HadithRecord",
    "HumanImpactAssessment",
    "Hypothesis",
    "HypothesisCompetition",
    "HypothesisMechanism",
    "HypothesisVersion",
    "Interpretation",
    "Mechanism",
    "Observation",
    "OpenQuestion",
    "OperationalConstraint",
    "ProblemFrameVersion",
    "Project",
    "ProjectAIPolicy",
    "ProjectClosure",
    "ProjectSource",
    "QualityGateEvaluationRecord",
    "QuranAyah",
    "QuranSurah",
    "ReferenceEntry",
    "ReferenceJudgmentRecord",
    "ReferenceReview",
    "ResearchEventRecord",
    "ResearchPlan",
    "ResearchState",
    "ResearchTrackRun",
    "ScratchNote",
    "SearchRecord",
    "SourceAccessRequest",
    "SourceAsset",
    "SourceChunk",
    "SourceEdition",
    "SourceExcerpt",
    "SourceLead",
    "SourceLineage",
    "SourcePage",
    "SourceWork",
    "SufficiencyAssessment",
]
