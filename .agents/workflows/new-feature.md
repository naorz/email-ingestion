---
description: Plan a new feature and create a step-by-step development guide for another agent to implement
---

# New Feature Planning Workflow

## Overview

When the user asks to plan a new feature, follow this workflow to create a comprehensive, step-by-step development plan. The plan is saved as a markdown file under `docs/planning-features/` and is designed to guide another agent (or developer) through implementation like a **senior principal engineer mentoring a junior**.

---

## Phase 1: Clarify Requirements

Before writing anything, **ask clarifying questions** if ANY of the following are unclear:

- What is the feature's purpose and end goal?
- Who is the target user or consumer of this feature?
- Are there any existing files, modules, or patterns this feature should follow or integrate with?
- Are there any constraints (performance, security, backwards compatibility)?
- What is the expected scope — small utility, new endpoint, full module, etc.?
- Are there any dependencies on external services or packages?

**Do NOT proceed until you have enough clarity to write a confident plan.** If the user provides a clear and complete description, you may skip asking and proceed directly.

---

## Phase 2: Plan the Feature

Break the feature down using **divide and conquer** principles:

1. **Identify the main goal** — one sentence describing what "done" looks like.
2. **Break into major steps** — each step is a logical milestone (e.g., "Create the data model", "Add the service layer", "Write tests").
3. **Break each major step into sub-steps** — granular, actionable tasks that can each be completed in a single focused session.
4. **Order steps by dependency** — earlier steps should not depend on later ones.
5. **Estimate complexity** — if a step has more than 5 sub-steps, consider splitting it into multiple major steps.

---

## Phase 3: Write the Planning Document

Create the file at: `docs/planning-features/<feature_name>.md`

- Use `kebab-case` for the filename (e.g., `container-unpacking.md`).
- Follow the **exact template** below.

### Template

````markdown
# Feature: <Feature Name>

> **Status**: Planning | In Progress | Complete | Blocked
> **Created**: <date>
> **Last Updated**: <date>

## Goal

<One clear sentence describing what "done" looks like.>

## Context

<Brief background — why this feature is needed, any relevant architecture notes, links to docs, or related files. Mention specific files/modules the implementer should be aware of.>

## Fast Mode

> If this plan has **2 or fewer major steps**, the implementing agent should execute all steps in a single session without breaks or handoffs.
>
> To **skip breaks between steps** even when there are more than 2, append the keyword **`--turbo`** to your prompt when starting or continuing work. This tells the agent to proceed through all steps continuously without pausing for confirmation between steps.

---

## Steps

### Step 1: <Step Title>

> <Brief description of what this step accomplishes and why it matters>

- [ ] **1.1** <Sub-step description>
  - Files: `<relevant file paths>`
  - Details: <what exactly to do, patterns to follow, edge cases to handle>

- [ ] **1.2** <Sub-step description>
  - Files: `<relevant file paths>`
  - Details: <what exactly to do>

<details>
<summary>Step 1 Handoff Prompt (click to expand)</summary>

```
I'm continuing work on the "<Feature Name>" feature.
Plan location: docs/planning-features/<feature_name>.md

Step 1 ("<Step Title>") is complete. Please:
1. Read the plan file and verify Step 1 sub-steps are all marked [x]
2. Proceed with Step 2: "<Next Step Title>"
3. Follow the plan closely and mark sub-steps as [x] when done
4. When Step 2 is complete, update the plan file and provide the next handoff prompt
```

</details>

---

### Step N: Verify & Finalize

> Final validation — make sure everything works end-to-end

- [ ] **N.1** Run all relevant tests and ensure they pass
- [ ] **N.2** Verify the feature works as described in the Goal section
- [ ] **N.3** Update the Status at the top of this file to Complete

<details>
<summary>Final Handoff Prompt (click to expand)</summary>

```
The "<Feature Name>" feature is complete.
Plan location: docs/planning-features/<feature_name>.md

Please:
1. Read the plan file and verify all steps are marked [x]
2. Run a final check — tests, lint, build
3. Mark the status as Complete
4. Summarize what was implemented
```

</details>
````

---

## Phase 4: Review with the User

After creating the plan file:

1. Present a **summary** of the plan to the user (list of major steps with one-line descriptions).
2. Ask if they want to **adjust, add, or remove** any steps.
3. Confirm the plan is approved before considering the workflow complete.

---

## Rules & Guidelines

1. **Always ask questions first** if the feature scope is ambiguous. Don't guess.
2. **Be specific in sub-steps** — mention exact file paths, function names, patterns to follow, and edge cases.
3. **Each sub-step should be independently verifiable** — the implementer should know when it's done.
4. **Handoff prompts are mandatory** at the end of each major step (unless fast mode applies).
5. **Fast mode** (no breaks): Automatically enabled when the plan has <= 2 major steps. Can also be forced by the user appending `--turbo` to their prompt.
6. **Mark progress**: When implementing, mark sub-steps with `[x]` as they are completed. Never remove or skip steps.
7. **Include a "Verify & Finalize" step** as the last step in every plan.
8. **Reference existing code**: If the project has established patterns, reference them so the implementer follows the same conventions.
9. **Follow project skills**: All planned code must adhere to the skills defined in `.agents/skills/` (architecture, repository pattern, Python best practices, etc.).
10. **Keep the plan living**: The plan file is the single source of truth for feature progress. Update it as work progresses.
