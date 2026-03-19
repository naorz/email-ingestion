---
description: Implement a feature from an existing planning document
---

The user wants to implement a planned feature: $ARGUMENTS

1. Look for the planning document in `docs/planning-features/`. If the user specified a feature name, find the matching file.
2. Read the planning document and identify the next incomplete step (first step with unchecked sub-steps).
3. Implement all sub-steps in that step, marking each `[x]` as you complete it.
4. After completing a step, update the plan file and present the handoff prompt.
5. If `--turbo` is specified or the plan has <= 2 steps, continue through all steps without pausing.

Follow all project skills defined in `.agents/skills/` during implementation.
