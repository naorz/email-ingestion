---
description: Perform an adversarial code review against project skills and best practices
---

Load and execute the workflow defined in `{project-root}/.agents/workflows/code-review.md`.

Review scope: $ARGUMENTS

If no scope is provided, review all recent changes (git diff or unstaged changes). Follow every phase in the workflow document. Check against all project skills defined in `.agents/skills/`.
