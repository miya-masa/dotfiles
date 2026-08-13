# Specification and plan contract

This reference is shared by `product-discovery` and `implementation-planning`.
The workflow artifact under `.aidocs/workflows/<workflow-id>/` is the durable handoff:
`context.json` is the machine-readable state authority; `spec.md`, `plan.md`,
`reviews/`, `tasks/`, and `progress.md` are evidence and handoff artifacts.
Never advance a phase from a report alone.

## Discovery packet and specification

The controller records the request, repository evidence, current behavior, user
decisions, assumptions, and unknowns in an evidence packet. A specification
must separate facts, inferences, assumptions, and open decisions and contain:

- Goal/users, context, constraints, scope and non-goals;
- normative external behavior, main flow, state/error/permission/boundary rules,
  compatibility/protected-contract constraints;
- Given/When/Then acceptance criteria, validation evidence, assumptions, and no
  unresolved decision that can change an in-scope outcome.

Ask at most one decision question per turn after its dependencies are settled.
Offer 2–3 options, a recommendation, and the trade-off; record the answer and
re-evaluate downstream dependencies. Do not ask users for facts discoverable in
code, tests, docs, schema, or a public interface.

### Specification review

After the draft is complete, dispatch independent fresh Sol High reviewers in
parallel. They receive the same approved-scope artifact and evidence, but never
互いの結論を共有しない（each other's prompts, conclusions, or findings）:

| reviewer | required lens |
| --- | --- |
| 1 | Completeness: states, boundaries, errors, compatibility, AC |
| 2 | Simplicity: scope creep, unnecessary requirements/abstraction |
| conditional | Risk: protected contract, security, migration, concurrency/distribution |

Each returns findings with evidence, impact, smallest correction or verification,
and a verdict. The controller records every finding as `adopted`, `rejected`
with reason, or `user_decision_required`; it does not silently merge conclusions.
Apply adopted findings, then repeat only the affected review scope. A normative
gap returns to discovery/specification. Do not hand off to planning until the
user explicitly approves the review-reflected spec; record that approval.

## Planning packet and plan

Planning consumes only an explicitly approved spec and its evidence. The named
`planning` agent compares viable approaches only as needed, chooses the smallest
supported approach, and emits an ordered plan. A plan is **decision-complete**
for a Luna Max worker and does not redesign the product or architecture.

Each independently reviewable vertical-slice task records:

| field | requirement |
| --- | --- |
| goal | one observable outcome |
| owned paths | exact files/directories the worker may change |
| deliverables | code/docs/tests or mechanical output |
| dependencies | prior task, evidence, and ordering |
| interfaces | inputs/outputs, symbols, external boundaries |
| acceptance criteria | objective Given/When/Then or equivalent |
| validation | exact command and expected result |
| RED reason | why the focused test should fail before implementation |
| stop conditions | conflict, protected contract, scope, or untrusted validation |

Task-internal actions are task-specific 2–5 minute units: test target, expected
RED reason, command, and minimal implementation boundary. Do not paste production
code wholesale or duplicate a common RED/GREEN/refactor recipe in every task.

### Plan review and execution choice

Run one fresh independent Sol High plan reviewer against the spec, plan, and
evidence. It checks spec coverage, scope, decision completeness, dependencies,
interfaces, and verification feasibility only; it does not redesign architecture.
Record adopted/rejected/user-decision findings. A normative spec gap returns to
`product-discovery`, not a plan workaround. After an approved plan review, stop
and require one explicit user choice:

- `execute-plan`: execute tasks, reviews, and local verification, then stop;
- `execute-and-ship`: do the same and continue with the separately authorized
  commit, push, MR, and in-scope CI flow.

Explain that the choice adds shipping authority only; it does not expand the
approved scope. Do not start implementation before the choice is recorded（実装を開始しない）.

## Short path

The controller may bypass normal discovery/spec/plan only when every condition
holds: request, external behavior, acceptance criteria, and validation are clear;
the change is local (normally 1–2 files); no protected contract, migration,
architecture decision, or complex concurrency/distribution is involved; and
existing uncommitted changes can be safely separated.

The short-path transitions are `SHORT_TASK_DRAFT -> SHORT_TASK_PREFLIGHT -> EXECUTION_CHOICE`.
Create `.aidocs/workflows/<workflow-id>/tasks/01-short-path.md` as the sole task
artifact. It contains Goal, Non-goals, acceptance criteria, owned paths, test
target, expected RED reason (or a documented reviewer-approved TDD exception),
validation command, stop conditions, and the user's execution choice. Dispatch a
fresh Luna Max `task-reviewer` preflight before offering either execution choice;
it checks clarity, scope, decisions, owned paths, test/RED, validation, and the
TDD exception. A normative gap or important preflight finding cancels the short
path: return to discovery, or revise and re-review the task artifact first.

## Artifact and handoff invariants

Write `spec.md` and `plan.md` under the workflow artifact, retain reviewer
reports under `reviews/`, and append audit evidence to `progress.md`. The
controller's packet names absolute artifact paths, fixed scope, reviewer role/
model, validation commands, and stop conditions; it does not paste long diffs.
At every handoff verify the artifact revision and `context.json` phase. Missing,
stale, contradictory, or ahead-of-state evidence is a stop condition.
