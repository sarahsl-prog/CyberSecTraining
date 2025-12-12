"""Local DataStore implementation using SQLite.

This implementation is for single-user mode where all data is stored
locally. The user_id is always "local" in this implementation.
"""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.preference import Preference
from app.models.progress import Progress
from app.models.scan import Scan
from app.services.datastore.base import DataStore


class LocalDataStore(DataStore):
    """SQLite-based DataStore for single-user local storage."""

    def _get_session(self) -> Session:
        """Get a database session."""
        return SessionLocal()

    # ==================== Progress Tracking ====================

    def save_progress(
        self,
        user_id: str,
        scenario_id: str,
        completed: bool = False,
        score: Optional[int] = None,
        hints_used: int = 0,
        time_spent: int = 0,
    ) -> None:
        """Save or update user progress for a scenario."""
        with self._get_session() as session:
            progress = (
                session.query(Progress)
                .filter(Progress.user_id == user_id, Progress.scenario_id == scenario_id)
                .first()
            )

            if progress:
                # Update existing
                progress.completed = completed
                if score is not None:
                    progress.score = score
                progress.hints_used = hints_used
                progress.time_spent = time_spent
                if completed:
                    progress.completed_at = datetime.utcnow()
            else:
                # Create new
                progress = Progress(
                    user_id=user_id,
                    scenario_id=scenario_id,
                    completed=completed,
                    score=score,
                    hints_used=hints_used,
                    time_spent=time_spent,
                    completed_at=datetime.utcnow() if completed else None,
                )
                session.add(progress)

            session.commit()

    def get_progress(self, user_id: str, scenario_id: str) -> Optional[dict[str, Any]]:
        """Get user progress for a specific scenario."""
        with self._get_session() as session:
            progress = (
                session.query(Progress)
                .filter(Progress.user_id == user_id, Progress.scenario_id == scenario_id)
                .first()
            )

            if not progress:
                return None

            return {
                "id": progress.id,
                "scenario_id": progress.scenario_id,
                "completed": progress.completed,
                "score": progress.score,
                "hints_used": progress.hints_used,
                "time_spent": progress.time_spent,
                "completed_at": progress.completed_at.isoformat() if progress.completed_at else None,
            }

    def get_all_progress(self, user_id: str) -> list[dict[str, Any]]:
        """Get all progress records for a user."""
        with self._get_session() as session:
            records = session.query(Progress).filter(Progress.user_id == user_id).all()

            return [
                {
                    "id": p.id,
                    "scenario_id": p.scenario_id,
                    "completed": p.completed,
                    "score": p.score,
                    "hints_used": p.hints_used,
                    "time_spent": p.time_spent,
                    "completed_at": p.completed_at.isoformat() if p.completed_at else None,
                }
                for p in records
            ]

    # ==================== Preferences ====================

    def save_preference(self, user_id: str, key: str, value: str) -> None:
        """Save a user preference."""
        with self._get_session() as session:
            pref = (
                session.query(Preference)
                .filter(Preference.user_id == user_id, Preference.key == key)
                .first()
            )

            if pref:
                pref.value = value
            else:
                pref = Preference(user_id=user_id, key=key, value=value)
                session.add(pref)

            session.commit()

    def get_preference(self, user_id: str, key: str) -> Optional[str]:
        """Get a user preference."""
        with self._get_session() as session:
            pref = (
                session.query(Preference)
                .filter(Preference.user_id == user_id, Preference.key == key)
                .first()
            )

            return pref.value if pref else None

    def get_all_preferences(self, user_id: str) -> dict[str, str]:
        """Get all preferences for a user."""
        with self._get_session() as session:
            prefs = session.query(Preference).filter(Preference.user_id == user_id).all()
            return {p.key: p.value for p in prefs}

    def delete_preference(self, user_id: str, key: str) -> bool:
        """Delete a user preference."""
        with self._get_session() as session:
            pref = (
                session.query(Preference)
                .filter(Preference.user_id == user_id, Preference.key == key)
                .first()
            )

            if pref:
                session.delete(pref)
                session.commit()
                return True
            return False

    # ==================== Scan History ====================

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
        """Save or update a scan record."""
        with self._get_session() as session:
            scan = session.query(Scan).filter(Scan.id == scan_id).first()

            if scan:
                # Update existing scan
                scan.scan_type = scan_type
                scan.status = status
                scan.target_range = target_range
                scan.port_range = port_range
                scan.started_at = started_at
                scan.completed_at = completed_at
                scan.progress = progress
                scan.scanned_hosts = scanned_hosts
                scan.total_hosts = total_hosts
                scan.results_summary = results_summary
            else:
                # Create new scan
                scan = Scan(
                    id=scan_id,
                    scan_type=scan_type,
                    status=status,
                    target_range=target_range,
                    port_range=port_range,
                    started_at=started_at,
                    completed_at=completed_at,
                    progress=progress,
                    scanned_hosts=scanned_hosts,
                    total_hosts=total_hosts,
                    results_summary=results_summary,
                    timestamp=datetime.utcnow(),
                )
                session.add(scan)

            session.commit()

    def get_scan(self, user_id: str, scan_id: str) -> Optional[dict[str, Any]]:
        """Get a scan record by ID."""
        with self._get_session() as session:
            scan = session.query(Scan).filter(Scan.id == scan_id).first()

            if not scan:
                return None

            return {
                "scan_id": scan.id,
                "scan_type": scan.scan_type,
                "status": scan.status,
                "target_range": scan.target_range,
                "port_range": scan.port_range,
                "started_at": scan.started_at.isoformat() if scan.started_at else None,
                "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
                "progress": scan.progress,
                "scanned_hosts": scan.scanned_hosts,
                "total_hosts": scan.total_hosts,
                "results_summary": scan.results_summary,
                "timestamp": scan.timestamp.isoformat() if scan.timestamp else None,
            }

    def list_scans(
        self,
        user_id: str,
        limit: int = 10,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List scan records for a user."""
        with self._get_session() as session:
            scans = (
                session.query(Scan)
                .order_by(Scan.timestamp.desc())
                .limit(limit)
                .offset(offset)
                .all()
            )

            return [
                {
                    "scan_id": s.id,
                    "scan_type": s.scan_type,
                    "status": s.status,
                    "target_range": s.target_range,
                    "port_range": s.port_range,
                    "started_at": s.started_at.isoformat() if s.started_at else None,
                    "completed_at": s.completed_at.isoformat() if s.completed_at else None,
                    "progress": s.progress,
                    "scanned_hosts": s.scanned_hosts,
                    "total_hosts": s.total_hosts,
                    "results_summary": s.results_summary,
                    "timestamp": s.timestamp.isoformat() if s.timestamp else None,
                }
                for s in scans
            ]

    def delete_scan(self, user_id: str, scan_id: str) -> bool:
        """Delete a scan record."""
        with self._get_session() as session:
            scan = session.query(Scan).filter(Scan.id == scan_id).first()

            if scan:
                session.delete(scan)
                session.commit()
                return True
            return False

    def count_scans(self, user_id: str) -> int:
        """Get total count of scans for a user."""
        with self._get_session() as session:
            return session.query(Scan).count()

    # ==================== Leaderboard ====================

    def get_leaderboard(self, scenario_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """Get leaderboard for a scenario.

        In single-user mode, this returns the user's own best score.
        """
        with self._get_session() as session:
            records = (
                session.query(Progress)
                .filter(Progress.scenario_id == scenario_id, Progress.completed == True)
                .order_by(Progress.score.desc(), Progress.time_spent.asc())
                .limit(limit)
                .all()
            )

            return [
                {
                    "user_id": p.user_id,
                    "score": p.score,
                    "time_spent": p.time_spent,
                    "completed_at": p.completed_at.isoformat() if p.completed_at else None,
                }
                for p in records
            ]

    # ==================== Data Management ====================

    def delete_all_user_data(self, user_id: str) -> None:
        """Delete all data for a user."""
        with self._get_session() as session:
            # Delete progress
            session.query(Progress).filter(Progress.user_id == user_id).delete()
            # Delete preferences
            session.query(Preference).filter(Preference.user_id == user_id).delete()
            # Delete scans (all scans in single-user mode)
            session.query(Scan).delete()
            session.commit()

    def export_user_data(self, user_id: str) -> dict[str, Any]:
        """Export all data for a user."""
        return {
            "user_id": user_id,
            "progress": self.get_all_progress(user_id),
            "preferences": self.get_all_preferences(user_id),
            "scans": self.list_scans(user_id, limit=1000),
            "exported_at": datetime.utcnow().isoformat(),
        }
