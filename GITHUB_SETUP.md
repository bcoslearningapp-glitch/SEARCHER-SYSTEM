# GITHUB_SETUP.md — Product B / Claude Code Development

This file defines the recommended GitHub configuration before autonomous Claude Code development begins.

## 1. Repository

Create one private GitHub repository for Product B v1.

Recommended initial repository files committed before implementation:

- `docs/product/PRD_PRODUCT_B.md`
- `docs/product/RESEARCH_CORE_V1.md`
- `CLAUDE.md`
- `GITHUB_SETUP.md`
- `.gitignore`
- `README.md`

Use `main` as the default branch.

## 2. Claude Code prerequisites

Install Claude Code and GitHub CLI on the development environment.

Authenticate GitHub CLI:

```bash
gh auth login
```

Run Claude Code from the repository root:

```bash
claude
```

Claude Code reads the project `CLAUDE.md` at session startup. Keep the root file concise; put domain-specific rules under `.claude/rules/` if they become large.

## 3. Optional Claude Code GitHub Action

Anthropic currently supports a Claude Code GitHub Action that can respond to `@claude` in issues and pull requests and can automate issue-to-PR workflows.

Quick setup from Claude Code:

```text
/install-github-app
```

This requires repository admin access and works with github.com repositories.

Authentication can use either:

- `ANTHROPIC_API_KEY`
- `CLAUDE_CODE_OAUTH_TOKEN`

For subscription-token authentication, generate the token locally with:

```bash
claude setup-token
```

Never commit either credential.

If GitHub Action integration is not needed, Claude Code can still work locally/cloud-side with normal git and `gh` commands.

## 4. Shared Claude Code configuration

Commit project-wide settings only in:

```text
.claude/settings.json
```

Keep personal/local overrides in:

```text
.claude/settings.local.json
```

and ensure they are ignored.

Use `.claude/rules/` for path-scoped instructions if frontend/backend/database rules become too large for the root CLAUDE.md.

Do not place secrets in committed Claude configuration.

## 5. Branch/ruleset policy

Protect `main`.

Recommended rules:

- require pull request before merge;
- require status checks;
- require conversation resolution;
- block force pushes;
- block branch deletion;
- require linear history if using squash/rebase merges;
- optionally prevent bypass.

Prefer a GitHub ruleset when available rather than creating overlapping branch-protection rules.

For the autonomous build, human approval is not required for every routine PR. Claude may merge after all required checks pass. Product/constitutional/security decisions outside the PRD remain escalation points.

## 6. Merge strategy

Recommended: squash merge.

Reason:
- one GitHub issue maps cleanly to one main-branch commit;
- keeps `main` readable;
- individual branch work remains visible in the PR.

Delete merged feature branches automatically.

## 7. Branch naming

```text
feat/<issue>-<slug>
fix/<issue>-<slug>
refactor/<issue>-<slug>
docs/<issue>-<slug>
test/<issue>-<slug>
chore/<issue>-<slug>
```

Example:

```text
feat/42-problem-frame-versioning
```

## 8. Commit convention

Use Conventional Commits:

```text
feat:
fix:
refactor:
test:
docs:
chore:
perf:
security:
```

Examples:

```text
feat(sources): add SourceWork and SourceEdition identity
test(reference): cover blocking reservation gate
fix(portability): preserve metadata-only source verification
```

## 9. GitHub issue labels

Create:

### Type
- `type:feature`
- `type:bug`
- `type:refactor`
- `type:docs`
- `type:test`
- `type:security`

### Domain
- `domain:project`
- `domain:reference`
- `domain:sources`
- `domain:evidence`
- `domain:hypothesis`
- `domain:research`
- `domain:design`
- `domain:experiments`
- `domain:knowledge`
- `domain:outputs`
- `domain:ai`
- `domain:portability`
- `domain:infra`

### Priority
- `P0`
- `P1`
- `P2`
- `P3`

### Decisions
- `needs-product-decision`
- `needs-architecture-decision`
- `blocked`

## 10. Issue template

Every implementation issue should include:

```markdown
## Objective

## PRD requirements
- FR-...

## Research Core impact

## Dependencies

## Acceptance criteria
- [ ]

## Tests required

## Data migration impact

## Security/privacy impact

## Notes
```

## 11. Pull-request template

Create `.github/PULL_REQUEST_TEMPLATE.md`:

```markdown
## Summary

Closes #

## PRD / Research Core requirements
- FR-...

## Architecture impact

## Data / migration impact

## Security / privacy impact

## Tests
- [ ] unit
- [ ] integration
- [ ] e2e where applicable
- [ ] migration/contract check

## UI evidence
Screenshots/video if applicable.

## Known limitations

## Documentation updated
- [ ]
```

## 12. Required CI workflows

### `ci.yml`

Trigger:
- pull request to `main`
- push to `main`

Run:
- frontend lint/type/unit;
- backend lint/type/unit;
- backend integration;
- Research Core schema/contract validation;
- migration checks;
- Docker build.

### `e2e.yml`

Run browser/API end-to-end flows against isolated Docker services.

### `security.yml`

Run dependency and static/security checks.

### `provider-contract.yml`

Manual and/or scheduled.

Uses live Anthropic/OpenAI credentials from a protected GitHub environment.

Must have:
- strict request count;
- strict budget;
- no sensitive research fixtures;
- deterministic contract assertions where possible.

### `release.yml`

Triggered on semantic-version tags.

Run all mandatory checks and generate release assets.

### `claude.yml`

Optional Claude Code GitHub Action.

Use it for issue/PR tasks and `@claude` comments if desired.

## 13. Required status check names

Make job names unique across workflows.

Recommended:

```text
frontend-lint
frontend-typecheck
frontend-unit
backend-lint
backend-typecheck
backend-unit
backend-integration
migration-check
contract-check
e2e-smoke
docker-build
```

Configure these as required before `main` merge.

## 14. Secrets

Do not run real model calls in ordinary CI.

Use mocks by default.

For protected provider-contract tests, configure environment/repository secrets such as:

```text
ANTHROPIC_API_KEY
OPENAI_API_KEY
```

For Claude Code GitHub Action, configure one of:

```text
ANTHROPIC_API_KEY
CLAUDE_CODE_OAUTH_TOKEN
```

Never put credentials into `.env.example`.

Use placeholders only:

```text
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
```

## 15. GitHub environments

Create:

```text
integration
```

Store live provider test secrets there.

If the GitHub plan supports environment protection, restrict access appropriately.

Later hosted deployments may add:

```text
staging
production
```

but Product B must remain fully usable locally.

## 16. Claude's autonomous GitHub authority

Within the approved PRD scope, Claude Code is authorized to:

- create issues;
- create branches;
- edit source/docs/tests;
- create migrations;
- run commands;
- commit;
- push non-protected branches;
- open PRs;
- respond to CI;
- update PRs;
- merge routine PRs when all required checks pass;
- create release tags only when release acceptance conditions are met.

Claude Code is not authorized to:

- force-push protected/shared branches;
- bypass status checks;
- expose/rotate secrets without authorization;
- delete repository history;
- disable tests because they fail;
- rewrite Research Core constitutional requirements;
- introduce a destructive migration without an explicit migration/backup strategy;
- silently change product scope.

## 17. Implementation plan

Before feature development, Claude Code should create:

```text
docs/implementation/MASTER_PLAN.md
docs/implementation/STATUS.md
```

`MASTER_PLAN.md` should decompose the PRD into phases, issues, dependencies, and acceptance milestones.

`STATUS.md` should remain short and current:
- current milestone;
- completed;
- in progress;
- blocked;
- next.

GitHub Issues remain the execution backlog; the docs provide the durable overview.

## 18. ADR discipline

Create architecture decisions in:

```text
docs/adr/ADR-NNN-title.md
```

Use ADRs for technical choices that future maintainers need to understand.

Do not use ADRs to bypass or rewrite product requirements.

## 19. Release strategy

Use semantic versions.

Recommended progression:

```text
v0.1.0 foundation
v0.2.0 framing-library
v0.3.0 reference-evidence-hypothesis
v0.4.0 AI-research
v0.5.0 design-experiment
v0.9.0 beta
v1.0.0 release
```

Only tag from green `main`.

## 20. Final handoff requirement

Before declaring the repository ready for download and local execution, Claude Code must verify from a clean checkout:

1. prerequisites are documented;
2. `.env.example` is complete;
3. no secrets are committed;
4. Docker-based startup works;
5. migrations run;
6. seed/demo setup is documented;
7. tests pass;
8. the browser application opens;
9. at least one provider can be configured;
10. backup/restore is documented;
11. README contains exact local run commands.

The final GitHub release should contain release notes describing completed PRD scope, known limitations, and migration instructions.
