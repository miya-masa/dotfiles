---
name: context-budget
description: Audit context usage across agents, skills, and MCP servers; recommend token savings.
origin: ECC
ecc-source:
  upstream-commit: 4e66b2882da9afb9747468b08a253ca2f09c85f3
  upstream-path: skills/context-budget/SKILL.md
  imported-at: "2026-04-27T00:00:00+09:00"
  adapted: true
---


# Context Budget

Analyze token overhead across every loaded component in a Claude Code session and surface actionable optimizations to reclaim context space.

## When to Use

- Session performance feels sluggish or output quality is degrading
- You've recently added many skills, agents, or MCP servers
- You want to know how much context headroom you actually have
- Planning to add more components and need to know if there's room
- Running `/context-budget` command (this skill backs it)

## How It Works

### Phase 1: Inventory

Scan all component directories and estimate token consumption.

**Delegate the raw scan to a haiku subagent** (token-economy: the scan reads many files
whose contents you never reference again — keep them out of the main context). Use the
`Agent` tool with `subagent_type="general-purpose", model="haiku"` and instruct it to
*measure and normalize, not to judge*. The subagent does the file walk / line+token
counting / symlink resolution and returns structured data; the main context does Phase 2–4
(meaning-making). This mirrors the skill-stocktake precedent (mechanical work → haiku).

The haiku subagent prompt MUST include these instructions verbatim:

> **Symlink rule (apply to EVERY file before counting)**: run `readlink` / `ls -la` on each
> file first. If it is a symlink, attribute it to its target's canonical path and **do not
> count it again**. The same applies to symlinked directories
> (e.g. `.claude/skills/foo -> .agents/skills/foo`). This avoids DUPE false-positives in
> chezmoi-style setups that cross-link via symlinks.
>
> **Return only measured/normalized data — make NO value judgments** (no Always/Sometimes/
> Rarely bucketing; that is the caller's job). Return:
> 1. Normalized inventory rows: `canonical_path | type(agent|skill|mcp|claude.md) | lines | est_tokens | is_symlink | symlink_target` (symlinks already collapsed onto their target, no double counts).
> 2. Flag candidates as RAW data only: agents >200 lines, descriptions >30 words, skills >400 lines, MCP servers >20 tools, CLAUDE.md chain total >300 lines.
> 3. Category subtotals + grand total tokens.

Scope the subagent over these surfaces:
- **Agents** (`agents/*.md`): lines + tokens (words × 1.3) per file, `description` frontmatter length.
- **Skills** (`skills/*/SKILL.md`): tokens per SKILL.md (symlinks collapsed onto target first).
- **MCP Servers** (`.mcp.json` / active MCP config): server count + total tool count (~500 tok/tool rough; spread ~80–1.8k).
- **CLAUDE.md** (project + user-level): tokens per file, follow `@imports` recursively.

**Preferred source of truth (applied in the main context, not delegated)**: run the
built-in `/context` command first. It reports authoritative live token counts per component
(system prompt, system tools, MCP tools, custom agents, memory files, skills, messages, free
space) for the *current* session. Treat the haiku subagent's `words × 1.3` heuristics only as
a supplement (per-file breakdown, redundancy hints) — never override `/context` numbers with
heuristic estimates.

### Phase 2: Classify

Sort every component into a bucket:

| Bucket | Criteria | Action |
|--------|----------|--------|
| **Always needed** | Referenced in CLAUDE.md, backs an active command, or matches current project type | Keep |
| **Sometimes needed** | Domain-specific (e.g. language patterns), not referenced in CLAUDE.md | Consider on-demand activation |
| **Rarely needed** | No command reference, overlapping content, or no obvious project match | Remove or lazy-load |

### Phase 3: Detect Issues

Identify the following problem patterns:

- **Bloated agent descriptions** — description >30 words in frontmatter loads into every Task tool invocation
- **Heavy agents** — files >200 lines inflate Task tool context on every spawn
- **Redundant components** — skills that duplicate agent logic, or skills that duplicate
  CLAUDE.md / AGENTS.md instructions. **Exclude symlink pairs** (same canonical inode = not
  redundant) — only flag when two genuinely independent files have overlapping content.
- **MCP over-subscription** — >10 servers, or servers wrapping CLI tools available for free
- **CLAUDE.md bloat** — verbose explanations, outdated sections, instructions that belong in a skill or AGENTS.md

### Phase 4: Report

Produce the context budget report:

```
Context Budget Report
═══════════════════════════════════════

Total estimated overhead: ~XX,XXX tokens
Context model: Claude Sonnet (200K window)
Effective available context: ~XXX,XXX tokens (XX%)

Component Breakdown:
┌─────────────────┬────────┬───────────┐
│ Component       │ Count  │ Tokens    │
├─────────────────┼────────┼───────────┤
│ Agents          │ N      │ ~X,XXX    │
│ Skills          │ N      │ ~X,XXX    │
│ MCP tools       │ N      │ ~XX,XXX   │
│ CLAUDE.md       │ N      │ ~X,XXX    │
└─────────────────┴────────┴───────────┘

WARNING: Issues Found (N):
[ranked by token savings]

Top 3 Optimizations:
1. [action] → save ~X,XXX tokens
2. [action] → save ~X,XXX tokens
3. [action] → save ~X,XXX tokens

Potential savings: ~XX,XXX tokens (XX% of current overhead)
```

In verbose mode, additionally output per-file token counts, line-by-line breakdown of the heaviest files, specific redundant lines between overlapping components, and MCP tool list with per-tool schema size estimates.

## Examples

**Basic audit**
```
User: /context-budget
Skill: Scans setup → 16 agents (12,400 tokens), 28 skills (6,200), 87 MCP tools (43,500), 2 CLAUDE.md (1,200)
       Flags: 3 heavy agents, 14 MCP servers (3 CLI-replaceable)
       Top saving: remove 3 MCP servers → -27,500 tokens (47% overhead reduction)
```

**Verbose mode**
```
User: /context-budget --verbose
Skill: Full report + per-file breakdown showing planner.md (213 lines, 1,840 tokens),
       MCP tool list with per-tool sizes, duplicated rule lines side by side
```

**Pre-expansion check**
```
User: I want to add 5 more MCP servers, do I have room?
Skill: Current overhead 33% → adding 5 servers (~50 tools) would add ~25,000 tokens → pushes to 45% overhead
       Recommendation: remove 2 CLI-replaceable servers first to stay under 40%
```

## Best Practices

- **Prefer `/context` over heuristics**: the built-in `/context` slash command gives
  authoritative live token counts. Use this skill for *what to do about them*, not for
  re-estimating numbers `/context` already knows.
- **Resolve symlinks before any duplicate check**: hash-comparing two paths that point
  at the same inode always returns "identical". Call `readlink` / `ls -la` first and
  attribute symlinks to their canonical target. Without this, every dotfiles repo that
  cross-references rules via symlinks will produce false "DUPE" warnings.
- **Token estimation fallback**: when `/context` isn't available, use `words × 1.3` for
  prose, `chars / 4` for code-heavy files. Treat these as ±30% rough.
- **MCP is the biggest lever**: per-tool schema cost varies wildly (~80–1.8k tokens).
  A 30-tool server can outweigh all your skills combined — use `/context` to see the
  real per-tool numbers before recommending cuts.
- **Skills are lazy-loaded; agents have two surfaces**: only the *name + description*
  of each skill is auto-loaded (~20–200 tok each). For agents, both the frontmatter
  (always loaded into the Agent tool) and the body (loaded only on invoke) cost
  context — report them separately.
- **Verbose mode for debugging**: use when you need to pinpoint the exact files driving overhead, not for regular audits
- **Audit after changes**: run after adding any agent, skill, or MCP server to catch creep early
