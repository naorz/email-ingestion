---
name: General Best Practices
description: General coding best practices for clean, maintainable, and robust code. Language-agnostic.
---

# General Best Practices

## 1. Code Quality

- **Meaningful Names**: Variables, functions, and classes should reveal intent. Avoid abbreviations unless universally understood (e.g., `id`, `url`).
- **Small Functions**: Each function should do one thing. If a function needs a comment explaining what a block does, extract that block into a named function.
- **Early Returns**: Use guard clauses to handle edge cases early and reduce nesting.
- **No Magic Values**: Use named constants instead of hardcoded strings or numbers.

## 2. Error Handling

- **Catch specific exceptions**: Never use bare `except:` or `catch(e)`. Catch the specific error type you expect.
- **Fail loudly at boundaries**: At system boundaries (user input, external APIs, file I/O), validate aggressively and raise clear errors.
- **Trust internal code**: Within your own call stack, don't defensively check for impossible states. Trust your own contracts.
- **Custom exceptions**: Define a project-specific exception hierarchy. Avoid relying solely on built-in exception types for domain errors.

## 3. Logging

- **Use a logging framework**: Never use raw `print()` or `console.log()` in production code. Use structured logging (Python: `logging` or `structlog`).
- **Log at appropriate levels**: DEBUG for dev, INFO for operational events, WARNING for recoverable issues, ERROR for failures.
- **Include context**: Always log with enough context to debug (operation name, IDs, relevant parameters).

## 4. Independence & Coupling

- **Features should be independent**: Ensure features remain loosely coupled. Feature A should not directly import internals of Feature B.
- **Communicate through interfaces**: When features need to interact, use shared abstractions (interfaces, events, or a mediator).
- **No global mutable state**: Avoid module-level mutable variables. Pass state explicitly through function parameters or dependency injection.

## 5. Data Structures

- **Use typed data models**: Prefer dataclasses, Pydantic models, TypedDicts, or equivalent over raw dicts/objects for structured data.
- **Immutability by default**: Prefer immutable data structures. Use `frozen=True` on dataclasses. Only allow mutation where explicitly needed.
- **No JSON templates with placeholders**: Never use string templates with `{{PLACEHOLDER}}` substitution for structured data. Build objects programmatically with typed constructors/builders.

## 6. Documentation

- **Code should be self-documenting**: Good names and structure reduce the need for comments.
- **Comment the "why", not the "what"**: Only add comments when the reason behind a decision isn't obvious from the code.
- **Docstrings for public API**: All public functions, classes, and modules should have docstrings explaining purpose, parameters, and return values.
