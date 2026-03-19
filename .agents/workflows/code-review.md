---
description: Perform an adversarial code review against project skills and best practices
---

# Code Review Workflow

## Overview

Perform a thorough, adversarial code review of changed or specified files. The review validates code against the project's skills (architecture, best practices, patterns) and surfaces issues ranked by severity.

---

## Phase 1: Identify Scope

Determine what to review:

- If the user specifies files/directories, review those.
- If no scope is given, review recent changes (`git diff` against the base branch, or unstaged changes).
- List all files in scope before proceeding.

---

## Phase 2: Review Against Skills

For each file in scope, check against ALL project skills:

### Architecture Best Practices
- [ ] Layered architecture respected? No layer skipping?
- [ ] Dependencies point inward? Services don't depend on handlers?
- [ ] Single concern per layer?

### Repository Pattern
- [ ] Data access goes through abstract interfaces?
- [ ] No direct persistence calls in business logic?
- [ ] Dependencies injected, not hardcoded?

### Project Structure
- [ ] Files in the correct directory for their concern?
- [ ] No business logic in entry/barrel files?
- [ ] Feature-based organization followed?

### General Best Practices
- [ ] Meaningful names? No magic values?
- [ ] Error handling catches specific exceptions?
- [ ] No global mutable state?
- [ ] Typed data models instead of raw dicts?

### Python Best Practices (if Python)
- [ ] Type hints on all function signatures?
- [ ] Dataclasses/Pydantic for data models?
- [ ] Pathlib for file operations?
- [ ] Custom exceptions with proper chaining?
- [ ] Generators for large data processing?

### Test Quality (if tests in scope)
- [ ] AAA pattern followed?
- [ ] Descriptive test names?
- [ ] No test interdependence?
- [ ] Mocks only at boundaries?

---

## Phase 3: Produce Findings

Organize findings by severity:

### Severity Levels

| Level | Label | Description |
|-------|-------|-------------|
| 1 | **CRITICAL** | Security vulnerability, data loss risk, or broken functionality |
| 2 | **HIGH** | Architecture violation, missing error handling, or logic bug |
| 3 | **MEDIUM** | Pattern deviation, poor naming, or missing types |
| 4 | **LOW** | Style issue, minor improvement, or suggestion |

### Output Format

For each finding:

```
### [SEVERITY] Short description

**File**: `path/to/file.py:line`
**Skill**: Which skill/rule this violates
**Issue**: What's wrong and why it matters
**Fix**: Concrete suggestion for how to fix it
```

---

## Phase 4: Summary

After all findings, provide:

1. **Score**: Overall assessment (Pass / Pass with notes / Needs changes / Fail)
2. **Stats**: Count of findings by severity
3. **Top 3 priorities**: The most important things to fix
4. **Positive notes**: What was done well (always include at least one)

---

## Rules

- Be adversarial but constructive — the goal is to improve code quality, not to criticize.
- Always reference the specific skill being violated.
- Provide concrete fix suggestions, not just "this is wrong".
- If the code is clean, say so. Don't invent problems.
