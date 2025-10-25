from typing import Dict, Any, Optional
from datetime import datetime

class MemoryStore:
    def __init__(self):
        self._store: Dict[str, Any] = {}
        self._created_at: Dict[str, datetime] = {}

    def set(self, key: str, value: Any) -> None:
        """Store a value with the given key."""
        self._store[key] = value
        self._created_at[key] = datetime.now()

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value by key."""
        return self._store.get(key)

    def delete(self, key: str) -> bool:
        """Delete a value by key. Returns True if key existed."""
        if key in self._store:
            del self._store[key]
            del self._created_at[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all stored data."""
        self._store.clear()
        self._created_at.clear()

    def get_all(self) -> Dict[str, Any]:
        """Get all stored key-value pairs."""
        return self._store.copy()

    def get_created_at(self, key: str) -> Optional[datetime]:
        """Get creation timestamp for a key."""
        return self._created_at.get(key)

    def exists(self, key: str) -> bool:
        """Check if a key exists."""
        return key in self._store