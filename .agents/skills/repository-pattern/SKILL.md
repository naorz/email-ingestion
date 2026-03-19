---
name: Architectural Abstraction & Repository Pattern
description: Decouple business logic from data persistence and external services using abstract interfaces and concrete providers.
---

# Architectural Abstraction & Repository Pattern

Always decouple business logic from data persistence or external services using abstract interfaces and concrete providers.

## 1. Define the Contract

Before writing logic, create an Abstract Base Class (ABC), Protocol, or Interface in a `core/` or `core/interfaces.py` file.

### Python Example

```python
# core/interfaces.py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")

class IStorageProvider(ABC, Generic[T]):
    """Abstract contract for any storage backend."""

    @abstractmethod
    def save(self, data: T) -> str:
        """Persist data and return its unique identifier."""
        ...

    @abstractmethod
    def find(self, id: str) -> T | None:
        """Retrieve data by identifier, or None if not found."""
        ...

    @abstractmethod
    def delete(self, id: str) -> bool:
        """Delete data by identifier. Return True if deleted."""
        ...

    @abstractmethod
    def exists(self, id: str) -> bool:
        """Check if an item exists by identifier."""
        ...
```

### Generic Guidance (Any Language)

- Use your language's abstraction mechanism: `ABC` (Python), `interface` (TypeScript/Java/Go), `trait` (Rust), `protocol` (Swift).
- Define the contract with generic, domain-neutral method signatures.
- Place contracts in a central location (`core/`, `interfaces/`, `contracts/`).

## 2. Implement the Provider

Create a concrete implementation in a `providers/` directory that handles the technical details.

```python
# providers/filesystem.py
import json
from pathlib import Path
from core.interfaces import IStorageProvider

class FileStorageProvider(IStorageProvider[dict]):
    def __init__(self, base_dir: Path):
        self._base_dir = base_dir
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, data: dict) -> str:
        id = data.get("id") or self._generate_id()
        path = self._base_dir / f"{id}.json"
        path.write_text(json.dumps(data, indent=2))
        return id

    def find(self, id: str) -> dict | None:
        path = self._base_dir / f"{id}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text())

    def delete(self, id: str) -> bool:
        path = self._base_dir / f"{id}.json"
        if path.exists():
            path.unlink()
            return True
        return False

    def exists(self, id: str) -> bool:
        return (self._base_dir / f"{id}.json").exists()
```

## 3. Feature-Specific Wrappers

For specific features, create a feature-specific service or wrapper that uses the provider but exposes high-level, domain-specific methods.

```python
# features/ingestion/service.py
from core.interfaces import IStorageProvider
from features.ingestion.models import EmailRecord

class IngestionService:
    def __init__(self, storage: IStorageProvider[dict]):
        self._storage = storage

    def ingest_email(self, email: EmailRecord) -> str:
        if self._storage.exists(email.unique_id):
            return email.unique_id  # Already ingested (dedup)
        return self._storage.save(email.to_dict())

    def get_email(self, email_id: str) -> EmailRecord | None:
        data = self._storage.find(email_id)
        return EmailRecord.from_dict(data) if data else None
```

## 4. Dependency Injection

The main application logic depends only on the abstraction, never the concrete implementation.

```python
# main.py
from pathlib import Path
from providers.filesystem import FileStorageProvider
from features.ingestion.service import IngestionService

def create_app():
    # Wire dependencies at the composition root
    storage = FileStorageProvider(base_dir=Path("./output"))
    ingestion = IngestionService(storage=storage)
    return ingestion
```

### Rules

- **Composition root**: Wire all dependencies in one place (entry point / factory function). Never instantiate providers inside business logic.
- **Depend on abstractions**: Services accept interfaces in their constructors, not concrete classes.
- **Easy swapping**: To switch from filesystem to database, only change the composition root — no business logic changes needed.
- **Testability**: In tests, pass mock/fake implementations of the interface. No patching needed.

## 5. Checklist

When implementing any data access or external service integration:

- [ ] Abstract interface defined in `core/interfaces.py`?
- [ ] Concrete provider in `providers/`?
- [ ] Feature service depends on interface, not provider?
- [ ] Dependencies wired at the composition root?
- [ ] Tests use a fake/mock implementation of the interface?
