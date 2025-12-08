"""DataStore abstraction layer for user data management."""

from app.services.datastore.base import DataStore
from app.services.datastore.local import LocalDataStore

__all__ = ["DataStore", "LocalDataStore"]
