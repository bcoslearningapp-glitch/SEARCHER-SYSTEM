# Changelog

Milestones follow PRD §76. Each release is tagged by the owner from a green `main` (#28). The release workflow reads the section for its tag as the release notes.

## [Unreleased] — M6 Hardening toward v1.0
- Adapter contract suite, a PRD §73 coverage map, and page loading and error states. An API outage no longer shows as "not found" (#54).
- Security review. Host allow-lists and refusal of cross-site writes close CSRF and DNS rebinding. Security headers on every response. A threat model (#55).
- Whole-installation backup and restore with checksummed archives (#58).
- The installation audit completes the blocking AI evaluation dimensions (#56).
- Performance benchmark against PRD §70, and removal of N+1 queries in the library listing (#57).
- User guide, a verified clean-machine setup, and the project AI policy on the Desk (#59).
- Release images and the v1.0 Definition of Done checklist (#60).

## [v0.6.0] — M5 Outputs, portability, cloud workspace
- Output composer: ten output types and three modes, with claims traced and exact quotes protected (#43).
- Eight-step output integrity pipeline; Markdown and HTML export (#44, #45).
- Research Core Package export and import. Import never raises trust (#46).
- Selective cloud workspace with a disclosure manifest (#47).
- DOCX and PDF export with Arabic shaping and verifiable quotes (#52).

## [v0.5.0] — M4 Design, experiments, knowledge
- Design requirements, concepts, and the Design Readiness Gate (#33).
- Design hypotheses, the experiment workflow, human-impact review, and observations, results and interpretations kept distinct (#34).
- Learning reviews and local knowledge lifecycle, promotion and reuse (#35).
- Terminology and the translation-integrity check (#36).
- Project Closure Gate (#41).

## [v0.4.0] — M3 AI gateway and research orchestration
- Provider-neutral AI gateway with Anthropic and OpenAI adapters, disclosure policy and budgets (#21).
- Research Orchestrator: draft, detect assumptions, and "Challenge this" (#22).
- Research plans, audited search, web results as leads, and sufficiency (#25).
- Controlled AI tool registry (#29).
- AI reliability registry and golden fixtures (#30).

## [v0.3.0] — M2 Evidence, hypotheses, reference governance
- Claims, assumptions and open questions. The evidence pipeline with exact quotes and lineage. Hypotheses and mechanisms (#11–#16).
- Foundational library with human-approved Qur'an datasets, and layered reference review (#12, #13).

## [v0.2.0] — M1 Projects and sources
- Policy Engine, project lifecycle, Research State, Problem Frames and approvals (#2–#4).
- Source identity, sandboxed storage, Hybrid Source Access, ingestion and search, and the trilingual UI (#5–#7).

## [v0.1.0] — M0 Foundation
- Modular monolith scaffold, contracts, CI, containers (#1).
