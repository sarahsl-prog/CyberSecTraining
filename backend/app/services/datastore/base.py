"""Abstract base class for DataStore implementations.

This abstraction layer enables future multi-user support by defining
a consistent interface for data operations. The LocalDataStore
implementation uses SQLite for single-user mode, while a future
RemoteDataStore can use a remote API for multi-user features.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class DataStore(ABC):
    """Abstract base class defining the DataStore interface.

    All user data operations should go through this interface to enable
    easy switching between local (single-user) and remote (multi-user) modes.
    """

    # ==================== Progress Tracking ====================

    @abstractmethod
    def save_progress(
        self,
        user_id: str,
        scenario_id: str,
        completed: bool = False,
        score: Optional[int] = None,
        hints_used: int = 0,
        time_spent: int = 0,
    ) -> None:
        """Save or update user progress for a scenario.

        Args:
            user_id: User identifier ("local" for single-user mode)
            scenario_id: Scenario identifier
            completed: Whether the scenario is completed
            score: Score achieved (0-100)
            hints_used: Number of hints used
            time_spent: Time spent in seconds
        """
        pass

    @abstractmethod
    def get_progress(self, user_id: str, scenario_id: str) -> Optional[dict[str, Any]]:
        """Get user progress for a specific scenario.

        Args:
            user_id: User identifier
            scenario_id: Scenario identifier

        Returns:
            Progress data dict or None if not found
        """
        pass

    @abstractmethod
    def get_all_progress(self, user_id: str) -> list[dict[str, Any]]:
        """Get all progress records for a user.

        Args:
            user_id: User identifier

        Returns:
            List of progress data dicts
        """
        pass

    # ==================== Preferences ====================

    @abstractmethod
    def save_preference(self, user_id: str, key: str, value: str) -> None:
        """Save a user preference.

        Args:
            user_id: User identifier
            key: Preference key
            value: Preference value (stored as string, typically JSON)
        """
        pass

    @abstractmethod
    def get_preference(self, user_id: str, key: str) -> Optional[str]:
        """Get a user preference.

        Args:
            user_id: User identifier
            key: Preference key

        Returns:
            Preference value or None if not found
        """
        pass

    @abstractmethod
    def get_all_preferences(self, user_id: str) -> dict[str, str]:
        """Get all preferences for a user.

        Args:
            user_id: User identifier

        Returns:
            Dict of key-value pairs
        """
        pass

    @abstractmethod
    def delete_preference(self, user_id: str, key: str) -> bool:
        """Delete a user preference.

        Args:
            user_id: User identifier
            key: Preference key

        Returns:
            True if deleted, False if not found
        """
        pass

    # ==================== Scan History ====================

    @abstractmethod
    def save_scan(
        self,
        user_id: str,
        scan_id: str,
        scan_type: str,
        status: str,
        target_range: Optional[str] = None,
        port_range: Optional[str] = None,
        started_at: Optional[Any] = None,
        completed_at: Optional[Any] = None,
        progress: float = 0.0,
        scanned_hosts: int = 0,
        total_hosts: int = 0,
        results_summary: Optional[str] = None,
    ) -> None:
        """Save or update a scan record.

        Args:
            user_id: User identifier ("local" for single-user mode)
            scan_id: Unique scan identifier
            scan_type: Type of scan (quick, deep, discovery, custom)
            status: Scan status (pending, running, completed, failed, cancelled)
            target_range: Network range scanned (e.g., "192.168.1.0/24")
            port_range: Port range scanned (e.g., "1-1024")
            started_at: Scan start timestamp
            completed_at: Scan completion timestamp
            progress: Scan progress percentage (0.0-100.0)
            scanned_hosts: Number of hosts scanned
            total_hosts: Total hosts to scan
            results_summary: JSON string of scan results
        """
        pass

    @abstractmethod
    def get_scan(self, user_id: str, scan_id: str) -> Optional[dict[str, Any]]:
        """Get a scan record by ID.

        Args:
            user_id: User identifier
            scan_id: Unique scan identifier

        Returns:
            Scan data dict or None if not found
        """
        pass

    @abstractmethod
    def list_scans(
        self,
        user_id: str,
        limit: int = 10,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List scan records for a user.

        Args:
            user_id: User identifier
            limit: Maximum number of scans to return
            offset: Number of scans to skip

        Returns:
            List of scan data dicts, most recent first
        """
        pass

    @abstractmethod
    def delete_scan(self, user_id: str, scan_id: str) -> bool:
        """Delete a scan record.

        Args:
            user_id: User identifier
            scan_id: Unique scan identifier

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    def count_scans(self, user_id: str) -> int:
        """Get total count of scans for a user.

        Args:
            user_id: User identifier

        Returns:
            Total number of scans
        """
        pass

    # ==================== Leaderboard (Future) ====================

    @abstractmethod
    def get_leaderboard(self, scenario_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """Get leaderboard for a scenario.

        Args:
            scenario_id: Scenario identifier
            limit: Maximum number of entries to return

        Returns:
            List of leaderboard entries (user_id, score, time)
        """
        pass

    # ==================== Data Management ====================

    @abstractmethod
    def delete_all_user_data(self, user_id: str) -> None:
        """Delete all data for a user.

        Args:
            user_id: User identifier
        """
        pass

    @abstractmethod
    def export_user_data(self, user_id: str) -> dict[str, Any]:
        """Export all data for a user.

        Args:
            user_id: User identifier

        Returns:
            Dict containing all user data
        """
        pass
