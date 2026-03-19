---
name: Architecture Best Practices
description: High-level architectural patterns and principles for scalable and maintainable systems. Language-agnostic.
---

# Architecture Best Practices

## 1. Design Principles

- **SOLID Principles**: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, and Dependency Inversion.
- **DRY (Don't Repeat Yourself)**: Avoid duplication, but don't over-abstract prematurely.
- **KISS (Keep It Simple, Stupid)**: Start simple and only add complexity when necessary.
- **YAGNI (You Aren't Gonna Need It)**: Don't build for hypothetical future requirements.

## 2. Layered Architecture

Requests and data flow through clearly separated layers:

```text
Input → Entry Point → Middleware / Guards → Router / Dispatcher → Handler / Controller → Service / Use Case → Data Access → External Service
```

| Layer             | Responsibility                                      |
|-------------------|-----------------------------------------------------|
| Entry Point       | Bootstrap, configuration, error boundary             |
| Middleware/Guards  | Auth, validation, logging, rate limiting             |
| Router/Dispatcher  | Route resolution, request parsing, dispatch          |
| Handler/Controller | Orchestrate use case, map request to domain call     |
| Service/Use Case   | Core business logic, domain rules                   |
| Data Access        | Persistence via repository pattern (see skill)       |
| External Service   | Third-party API calls, message queues, etc.          |

### Rules

- **No layer may skip another.** Entry point → middleware → router → handler → service. A handler MUST NOT call middleware directly.
- **Dependencies point inward.** Handlers depend on services, NOT the other way around. Services depend on abstractions (interfaces), NOT concrete implementations.
- **Each layer has a single concern.** The router does NOT format responses. Handlers do NOT parse raw request bodies. Services do NOT know about HTTP.

## 3. Patterns

- **Separation of Concerns**: Divide the application into layers (see above).
- **Dependency Injection**: Pass dependencies to components rather than hardcoding them, making code more testable and flexible.
- **Singleton Configuration**: Configure shared services (logger, DB connection, config) once at the entry point, NOT inside individual handlers.
- **Event-Driven Architecture**: Use events/queues for background work and decoupling where appropriate.
- **Fail Fast**: Validate inputs and preconditions early; return errors before doing expensive work.

## 4. Scalability and Reliability

- **Horizontal Scaling**: Design services that can run in multiple instances without shared in-memory state.
- **Statelessness**: Avoid storing state in application memory; use external stores (databases, caches, queues).
- **Graceful Degradation**: Ensure the system stays partially functional if one component fails.
- **Idempotency**: Design operations (especially writes) to be safely retried without side effects.

## 5. Observability

- **Structured Logging**: Use a logging library with structured output (JSON). Include context (request ID, user ID, operation).
- **Error Boundaries**: Wrap top-level dispatch in try/catch to catch unhandled errors and log them.
- **Fail-Safe Operations**: Individual operations should catch their own errors to prevent one failure from cascading through the entire flow.
