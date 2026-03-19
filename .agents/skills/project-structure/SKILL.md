---
name: Project Structure & Architecture
description: Guidelines for project structuring, folder organization, and module boundaries. Language-agnostic with Python specifics.
---

# Project Structure & Architecture Guidelines

## 1. Exports & Public API

- **Explicit Public API**: Every module/package should have a clear public interface. Only expose what consumers need.
- **Re-export through entry points**: Use `__init__.py` (Python) or `index.ts` (TypeScript) as barrel files to define the public API of a package.
- **No implementation in entry files**: Entry/barrel files should only re-export — never contain business logic.

## 2. Folder Organization

- **Feature-Based Architecture**: Group logic into folders by feature, domain, or capability (e.g., `features/ingestion/`, `features/dedup/`) rather than broadly aggregating all handlers, models, or services globally.
- **Utils Context**: The `utils/` directory is reserved _exclusively_ for generic, stateless helpers that are not bound to any specific business domain (e.g., hashing, date formatting, file path helpers).
- **Shared / Common**: Cross-cutting concerns (logging, configuration, error types) belong in a `core/` or `common/` directory.

## 3. Recommended Python Project Structure

```
project_root/
├── src/
│   └── <package_name>/
│       ├── __init__.py
│       ├── main.py                  # Entry point / CLI
│       ├── config.py                # Configuration loading
│       ├── core/                    # Shared abstractions, interfaces, base classes
│       │   ├── __init__.py
│       │   ├── interfaces.py        # ABCs and protocols
│       │   ├── exceptions.py        # Custom exception hierarchy
│       │   └── types.py             # Shared type aliases, dataclasses, enums
│       ├── features/                # Feature modules (domain logic)
│       │   ├── __init__.py
│       │   ├── discovery/
│       │   │   ├── __init__.py
│       │   │   ├── service.py
│       │   │   └── models.py
│       │   └── processing/
│       │       ├── __init__.py
│       │       ├── service.py
│       │       └── models.py
│       ├── providers/               # Concrete implementations of core interfaces
│       │   ├── __init__.py
│       │   ├── filesystem.py
│       │   └── database.py
│       └── utils/                   # Generic, stateless helpers
│           ├── __init__.py
│           └── hashing.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # Shared fixtures
│   ├── unit/
│   │   └── ...
│   ├── integration/
│   │   └── ...
│   └── fixtures/                    # Test data files
│       └── ...
├── docs/
│   └── planning-features/
├── pyproject.toml
├── README.md
└── .gitignore
```

## 4. Key Rules

- **Flat is better than nested**: Avoid deeply nested directories. If a feature folder has only one file, keep it flat.
- **One module, one concern**: Each `.py` file should have a focused responsibility. If a file exceeds ~300 lines, consider splitting.
- **No circular imports**: Dependencies must flow in one direction. Use dependency injection or interfaces to break cycles.
- **Configuration at the boundary**: Load config at the entry point, inject it into components. Never import config deep inside business logic.
