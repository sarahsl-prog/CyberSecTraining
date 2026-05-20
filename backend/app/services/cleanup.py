"""
Old scan data cleanup service.

This module provides functionality to clean up old scan data and maintain
database performance by removing outdated records.
"""

from datetime import datetime, timedelta, UTC
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import SessionLocal
from app.models.scan import Scan
from app.models.device import Device
from app.models.vulnerability import Vulnerability
from app.core.logging import get_logger

logger = get_logger("cleanup")


class DataCleanupService:
    """
    Service for cleaning up old data and maintaining database performance.
    
    This service handles:
    - Removal of old scan records
    - Cleanup of orphaned devices
    - Removal of old vulnerabilities
    - Database maintenance operations
    """
    
    # Default retention periods (Fix Issue #18)
    DEFAULT_SCAN_RETENTION_DAYS = 30
    DEFAULT_DEVICE_RETENTION_DAYS = 90
    DEFAULT_VULNERABILITY_RETENTION_DAYS = 180
    
    def __init__(
        self,
        scan_retention_days: int = DEFAULT_SCAN_RETENTION_DAYS,
        device_retention_days: int = DEFAULT_DEVICE_RETENTION_DAYS,
        vulnerability_retention_days: int = DEFAULT_VULNERABILITY_RETENTION_DAYS,
    ):
        """
        Initialize the cleanup service.
        
        Args:
            scan_retention_days: Number of days to keep scan records
            device_retention_days: Number of days to keep device records
            vulnerability_retention_days: Number of days to keep vulnerability records
        """
        self.scan_retention_days = scan_retention_days
        self.device_retention_days = device_retention_days
        self.vulnerability_retention_days = vulnerability_retention_days
    
    def cleanup_old_scans(
        self,
        before_date: Optional[datetime] = None,
        dry_run: bool = False,
    ) -> dict[str, int]:
        """
        Remove old scan records from the database.
        
        Args:
            before_date: Cutoff date for deletion (default: retention_days ago)
            dry_run: If True, only count records without deleting
            
        Returns:
            Dictionary with counts of deleted records
        """
        with SessionLocal() as session:
            if before_date is None:
                before_date = datetime.now(UTC) - timedelta(days=self.scan_retention_days)
            
            # Count scans to be deleted
            scan_count = session.query(Scan).filter(
                Scan.created_at < before_date
            ).count()
            
            device_count = 0
            vulnerability_count = 0
            
            if not dry_run:
                # Get scan IDs before deletion
                old_scans = session.query(Scan.id).filter(
                    Scan.created_at < before_date
                ).all()
                scan_ids = [s[0] for s in old_scans]
                
                # Delete vulnerabilities for old scans
                vuln_result = session.query(Vulnerability).filter(
                    Vulnerability.scan_id.in_(scan_ids)
                ).delete()
                vulnerability_count = vuln_result
                
                # Delete devices for old scans
                device_result = session.query(Device).filter(
                    Device.scan_id.in_(scan_ids)
                ).delete()
                device_count = device_result
                
                # Delete scans
                scan_result = session.query(Scan).filter(
                    Scan.created_at < before_date
                ).delete()
                scan_count = scan_result
                
                session.commit()
                logger.info(
                    f"Deleted old scans: {scan_count} scans, "
                    f"{device_count} devices, {vulnerability_count} vulnerabilities"
                )
            else:
                logger.info(
                    f"Dry run: Would delete {scan_count} scans from before {before_date}"
                )
            
            return {
                "scans": scan_count,
                "devices": device_count,
                "vulnerabilities": vulnerability_count,
            }
    
    def cleanup_orphaned_devices(self, dry_run: bool = False) -> int:
        """
        Remove devices that are no longer associated with any scan.
        
        Args:
            dry_run: If True, only count records without deleting
            
        Returns:
            Number of deleted devices
        """
        with SessionLocal() as session:
            # Find devices whose scan_id doesn't exist in scans table
            orphaned_devices = session.query(Device).filter(
                ~Device.scan_id.in_(session.query(Scan.id))
            )
            
            count = orphaned_devices.count()
            
            if not dry_run and count > 0:
                orphaned_devices.delete()
                session.commit()
                logger.info(f"Deleted {count} orphaned devices")
            else:
                logger.info(f"Dry run: Would delete {count} orphaned devices")
            
            return count
    
    def get_database_size(self) -> dict[str, int]:
        """
        Get current database size statistics.
        
        Returns:
            Dictionary with counts of records in each table
        """
        with SessionLocal() as session:
            counts = {
                "scans": session.query(Scan).count(),
                "devices": session.query(Device).count(),
                "vulnerabilities": session.query(Vulnerability).count(),
            }
            
            # Get oldest scan date
            oldest_scan = session.query(func.min(Scan.created_at)).scalar()
            counts["oldest_scan_date"] = oldest_scan
            
            return counts
    
    def vacuum_database(self) -> bool:
        """
        Run VACUUM on SQLite database to reclaim space.
        
        Note: This is SQLite-specific. For PostgreSQL, use different approach.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with SessionLocal() as session:
                session.execute("VACUUM")
                session.commit()
                logger.info("Database vacuum completed successfully")
                return True
        except Exception as e:
            logger.error(f"Failed to vacuum database: {e}")
            return False


# Global cleanup service instance
_cleanup_service: Optional[DataCleanupService] = None


def get_cleanup_service() -> DataCleanupService:
    """
    Get the global cleanup service instance.
    
    Returns:
        DataCleanupService instance
    """
    global _cleanup_service
    if _cleanup_service is None:
        _cleanup_service = DataCleanupService()
    return _cleanup_service