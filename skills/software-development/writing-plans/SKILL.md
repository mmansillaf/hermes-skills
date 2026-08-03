---
name: writing-plans
description: "Write implementation plans: bite-sized tasks, paths, code."
version: 1.2.0
author: Hermes Agent (adapted from obra/superpowers)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [planning, design, implementation, workflow, documentation]
    related_skills: [plan, subagent-driven-development, test-driven-development, requesting-code-review]
---

# Writing Implementation Plans

## Overview

Write comprehensive implementation plans assuming the implementer has zero context for the codebase and questionable taste. Document everything they need: which files to touch, complete code, testing commands, docs to check, how to verify. Give them bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

Assume the implementer is a skilled developer but knows almost nothing about the toolset or problem domain. Assume they don't know good test design very well.

**Core principle:** A good plan makes implementation obvious. If someone has to guess, the plan is incomplete.

## Reference Files

This skill includes reference files for common architecture patterns:

- `references/multi-provider-api-pattern.md` — How to support OpenAI, Groq, DeepSeek, etc. using a single client library. Provider pricing table, Whisper transcription pattern, config structure. Key insight: no adapter classes needed — the OpenAI client IS the abstraction.
- `references/sqlite-persistence-hooks.md` — How to add SQLite to an existing Python project using hook pattern with lazy imports. Schema template, dedup by hash, upsert pattern, deadlock avoidance with RLock.
- `references/backtest-simulation-methodology.md` — How to validate quantitative/algorithmic plans: multi-scenario simulation, one-variable-at-a-time optimization, honest evaluation with losing cases shown, fee/capital sensitivity, synthetic vs real data gap reporting.

When designing a plan that involves external APIs or persistence, check these references for proven patterns and known pitfalls.

## When to Use

**Always use before:**
- Designing multi-component systems (architecture, logic, artifacts)
- Implementing multi-step features
- Breaking down complex requirements
- Delegating to subagents via subagent-driven-development

**Don't skip when:**
- Feature seems simple (assumptions cause bugs)
- You plan to implement it yourself (future you needs guidance)
- Working alone (documentation matters)

---

## Design Phase (before any code)

When the user asks for a **design document first** — architecture, logic, artifacts,
evaluation criteria, risks — produce this before writing implementation tasks.
Design phase = no code. Save the design document, let the user review it,
then iterate before moving to implementation.

### Design Document Structure

A complete design document covers 5 sections per component:

```markdown
## [Component Name]

### 1. Diagram
Architecture or flow diagram (Excalidraw JSON + ASCII fallback).

### 2. System Logic
Pipeline steps, data flow, decision points, component interactions.
For each significant design decision, use a comparison table:

| Decision | Option A | Option B | Chosen | Why |
|----------|----------|----------|--------|-----|
| Framework | LangChain | CrewAI | LangChain | More mature RAG |

### 3. Artifact List
Every file to create, with its purpose listed in a tree.

### 4. Evaluation Criteria

| Criterion | Metric | Minimum | How to measure |
|-----------|--------|---------|----------------|
| Precision | % correct | 85% | Test with labeled data |

### 5. Risks & Audit Points

| Risk | Probability | Impact | Detection | Mitigation |
|------|------------|--------|-----------|------------|
| LLM hallucinations | High | High | Rule engine validation | Human review required |

Audit checklist:
- [ ] Every LLM response must cite its source
- [ ] High-risk results need human confirmation required
- [ ] Log every API call (prompt → response → cost)
```

### When to use Design Phase

**Always start here when the user says:**
- "disena primero, no codifiques"
- "plan de desarrollo con diagramas, logica, artefactos"
- "evalua, revisa y audita la logica en esta fase"
- "disena el plan de desarrollo, diagrama, logica, lista de artefactos"

**Proceed to Implementation Phase only after:**
1. Design document saved and presented
2. User reviews and approves
3. Any corrections applied

### Pitfalls

- **Jumping to code during design phase**: If the user said "no code", don't write any. The design phase validates assumptions first.
- **Skipping evaluation criteria**: Without metrics, you can't tell if the implementation succeeded. Define pass/fail before coding.
- **Omitting risks**: Every design has failure modes. Document them before committing to implementation.
- **Diagrams as an afterthought**: Place the diagram at the top of each component section. It's the fastest way for the user to validate the architecture.

---

## Bite-Sized Task Granularity

**Each task = 2-5 minutes of focused work.**

Every step is one action:
- "Write the failing test" — step
- "Run it to make sure it fails" — step
- "Implement the minimal code to make the test pass" — step
- "Run the tests and make sure they pass" — step
- "Commit" — step

**Too big:**
```markdown
### Task 1: Build authentication system
[50 lines of code across 5 files]
```

**Right size:**
```markdown
### Task 1: Create User model with email field
[10 lines, 1 file]

### Task 2: Add password hash field to User
[8 lines, 1 file]

### Task 3: Create password hashing utility
[15 lines, 1 file]
```

## Plan Document Structure

### Header (Required)

Every plan MUST start with:

```markdown
# [Feature Name] Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

---
```

### Output Format Preferences (User: mmansillaf)

When saving research results, reports, or plans, ALWAYS produce **dual-format output**:
- `.md` for readability (tables, headers, formatting, links)
- `.txt` for portability (same content, stripped markdown, plain text)

Both files go in the same directory. The `.md` is the primary; the `.txt` is a copy with minimal formatting.

When the user's language context is Spanish:
- Variable names, comments, and docstrings in Spanish where appropriate
- Headers with purpose in each file (e.g. `# FactCheck Report - [description]`)
- Methodology sections before results (what was done, how, sources used)
- Tables for comparison data
- Acronyms defined on first use

### Task Structure

Each task follows this format:

````markdown
### Task N: [Descriptive Name]

**Objective:** What this task accomplishes (one sentence)

**Files:**
- Create: `exact/path/to/new_file.py`
- Modify: `exact/path/to/existing.py:45-67` (line numbers if known)
- Test: `tests/path/to/test_file.py`

**Step 1: Write failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

**Step 2: Run test to verify failure**

Run: `pytest tests/path/test.py::test_specific_behavior -v`
Expected: FAIL — "function not defined"

**Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

**Step 4: Run test to verify pass**

Run: `pytest tests/path/test.py::test_specific_behavior -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

## Writing Process

### Step 1: Understand Requirements

Read and understand:
- Feature requirements
- Design documents or user description
- Acceptance criteria
- Constraints

### Step 2: Explore the Codebase

Use Hermes tools to understand the project:

```python
# Understand project structure
search_files("*.py", target="files", path="src/")

# Look at similar features
search_files("similar_pattern", path="src/", file_glob="*.py")

# Check existing tests
search_files("*.py", target="files", path="tests/")

# Read key files
read_file("src/app.py")
```

### Step 3: Design Approach

Decide:
- Architecture pattern
- File organization
- Dependencies needed
- Testing strategy

### Step 4: Write Tasks

Create tasks in order:
1. Setup/infrastructure
2. Core functionality (TDD for each)
3. Edge cases
4. Integration
5. Cleanup/documentation

### Step 5: Add Complete Details

For each task, include:
- **Exact file paths** (not "the config file" but `src/config/settings.py`)
- **Complete code examples** (not "add validation" but the actual code)
- **Exact commands** with expected output
- **Verification steps** that prove the task works

### Step 6: Review the Plan

Check:
- [ ] Tasks are sequential and logical
- [ ] Each task is bite-sized (2-5 min)
- [ ] File paths are exact
- [ ] Code examples are complete (copy-pasteable)
- [ ] Commands are exact with expected output
- [ ] No missing context
- [ ] DRY, YAGNI, TDD principles applied

### Step 6.5 (RECOMMENDED): Validate with Simulations

Before saving, run lightweight simulations to stress-test critical assumptions in the plan. This catches wrong estimates, blocked API endpoints, broken URLs, and over-optimistic timing before they become "implement first, discover blocker second."

**What to simulate (pick what applies):**
- API calls: do endpoints exist? Return real data? What's the actual rate limit?
- Content extraction: can you pull text from target URLs? Are they JS-heavy, WAF-protected, or paywalled?
- Timing: how long does a full scan actually take? Adjust estimates based on real measurements.
- Fallbacks: if the primary method fails, does the fallback produce useful results?

**For quantitative/algorithmic plans** (trading strategies, optimization, ranking, scoring, anything with measurable performance):

Run **multi-scenario simulations** — never test only the happy path. Simulate across contrasting regimes:

| Regime | Purpose | Example |
|--------|---------|---------|
| **Bullish / favorable** | Confirm it works when conditions are ideal | Strong uptrend, low noise |
| **Bearish / adverse** | Find the breaking point | Downtrend, high volatility |
| **Sideways / neutral** | Test for whipsaw and false signals | Range-bound, choppy |
| **Mixed (all of the above)** | Blended real-world approximation | Cyclical, regime switches |

**Apply "one variable at a time" (OVAT) optimization** (Lewis Jackson method):
- Vary ONE parameter while holding all others fixed
- Measure impact on the primary metric (Sharpe, accuracy, profit factor, etc.)
- Document which parameters matter and which have negligible impact
- Avoid the common trap: "I changed 3 things and it improved — but I don't know which one fixed it"

**Synthetic vs real data — document the gap explicitly:**
```markdown
| Metric | Synthetic (optimistic) | Real data | Gap |
|--------|----------------------|-----------|-----|
| Win rate | 47% | 27% | -20pp |
| Avg frequency | 40/yr | 15/yr | -62% |
```
Synthetic data almost always overestimates frequency and win rate. Report the gap. If the gap flips a go/no-go decision, flag it.

**Evaluate honestly — show losing cases, not just winners:**
- Report trade-by-trade or case-by-case results (dates, decisions, outcomes)
- Show losing trades explicitly with reasons (e.g. "exit condition triggered prematurely")
- Calculate: win rate, avg win, avg loss, profit factor, max drawdown
- Include fee/cost sensitivity: does the strategy survive realistic transaction costs at the target scale?

**Capital/fee sensitivity check for financial plans:**
```markdown
| Capital Level | Profit Factor | Viability |
|--------------|--------------|-----------|
| $200         | 0.24         | ❌ Fees eat gains |
| $1,000       | 0.8          | ⚠️ Marginal |
| $5,000       | 1.5          | ✅ Viable |
```
A strategy that works at scale may fail at small capital because fixed costs (fees, slippage, spreads) consume the returns.

**Simulation scope (keep lean):**
- Multi-source research: test 1-2 sources per category (~6 queries total)
- Scraping/extraction: test 3-5 real target URLs across different site types
- API-dependent plans: test 2-3 endpoints with realistic queries
- Algorithmic plans: test across 3+ regimes + OVAT parameter sweep + fee sensitivity

**Document findings as a "Validation Results" section in the plan:**
```markdown
## Validation Results

| # | Simulation | Result | Impact on plan |
|---|-----------|--------|---------------|
| 1 | API coverage | 32/32 OK | Confirmed |
| 2 | Bullish regime | Sharpe -3.9 | Strategy fails in uptrends — add regime detection |
| 3 | OVAT: EMA fast | 15 > 9 across 3 regimes | Changed default from 9 to 15 |
```

**Pitfalls:**
- Never skip validation when the plan has external dependencies (APIs, third-party sites, rate-limited services).
- Synthetic data over-optimism: always validate with at least one real data source. The gap between synthetic and real performance is routinely 10-30 percentage points.
- "One variable at a time" is not optional for optimization plans. Changing 3 things and measuring improvement teaches nothing. Encode the OVAT constraint explicitly in the plan.
- Fee blindness: for any plan with monetary transactions, simulation must include realistic fee structures. Strategies that work gross of fees often fail net of fees at small scale.

### Step 7: Save the Plan

```bash
mkdir -p docs/plans
# Save plan to docs/plans/YYYY-MM-DD-feature-name.md
git add docs/plans/
git commit -m "docs: add implementation plan for [feature]"
```

## Principles

### DRY (Don't Repeat Yourself)
### YAGNI (You Aren't Gonna Need It)
### TDD (Test-Driven Development) - every task includes RED-GREEN-REFACTOR cycle
### Frequent Commits - commit after every task

## Common Mistakes

- **Vague tasks**: "Add auth" → "Create User model with email and password_hash fields"
- **Incomplete code**: Not actual code but "add validation"
- **Missing verification**: No command to run to confirm success
- **Missing file paths**: "the model file" → `src/models/user.py`

## Execution Handoff

After saving the plan, offer the execution approach: dispatch a subagent per task with two-stage review.

## Remember

```
Bite-sized tasks (2-5 min each)
Exact file paths
Complete code (copy-pasteable)
Exact commands with expected output
Verification steps
DRY, YAGNI, TDD
Frequent commits
```

**A good plan makes implementation obvious.**
