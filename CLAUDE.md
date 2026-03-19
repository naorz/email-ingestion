# Project: Flexor — Email File Ingestion Pipeline

## Language & Runtime

- **Python 3.10+**
- Package management via `pyproject.toml`
- Linting & formatting: `ruff`
- Testing: `pytest`

## Agent Skills (always active)

The following skills define coding standards and patterns for this project. They are loaded from `.agents/skills/` and must be followed in all code generation, reviews, and planning.

| Skill | File | Scope |
|-------|------|-------|
| Architecture Best Practices | `.agents/skills/architecture-best-practices/SKILL.md` | Layered architecture, SOLID, scalability |
| Project Structure | `.agents/skills/project-structure/SKILL.md` | Folder organization, module boundaries |
| General Best Practices | `.agents/skills/best-practices/SKILL.md` | Code quality, error handling, logging |
| Repository Pattern | `.agents/skills/repository-pattern/SKILL.md` | Abstract interfaces, providers, DI |
| Python Best Practices | `.agents/skills/python-best-practices/SKILL.md` | Type hints, dataclasses, Pathlib, idioms |

| Skill (on demand) | File | Scope |
|--------------------|------|-------|
| Test Architect | `.agents/skills/test-architect/SKILL.md` | Testing strategy, pytest, fixtures |

## Agent Workflows

| Workflow | File | Trigger |
|----------|------|---------|
| Plan Feature | `.agents/workflows/new-feature.md` | `/plan-feature <description>` |
| Code Review | `.agents/workflows/code-review.md` | `/code-review [scope]` |

## Slash Commands

| Command | Description |
|---------|-------------|
| `/plan-feature` | Plan a new feature with step-by-step guide |
| `/implement-feature` | Implement from an existing plan in `docs/planning-features/` |
| `/code-review` | Adversarial code review against project skills |
| `/test` | Design or review tests per Test Architect skill |

## Core Rules

1. **Always read skills before generating code.** Load the relevant `.agents/skills/*/SKILL.md` files before writing or reviewing any code.
2. **Repository pattern is mandatory** for all data access and external service integrations. See the Repository Pattern skill.
3. **Type hints on every function signature.** No exceptions.
4. **Dataclasses or Pydantic models** for all structured data. No raw dicts for domain objects.
5. **Pathlib for all file operations.** Never use `os.path`.
6. **Custom exception hierarchy.** All domain errors extend a project-specific base exception.
7. **pytest for all tests.** Follow the Test Architect skill when writing tests.
8. **Feature-based folder structure.** Group code by domain feature, not by technical layer.
9. **Dependencies injected at composition root.** Services accept abstractions, never concrete implementations.
10. **No global mutable state.** Pass state explicitly.

## Project Structure (target)

```
src/<package_name>/
├── main.py              # Entry point
├── config.py            # Configuration
├── core/                # Interfaces, exceptions, shared types
├── features/            # Feature modules (discovery, unpacking, dedup, etc.)
├── providers/           # Concrete implementations of core interfaces
└── utils/               # Generic stateless helpers

tests/
├── conftest.py          # Shared fixtures
├── unit/
├── integration/
└── fixtures/            # Test data files

docs/planning-features/  # Feature planning documents
```
