"""
Vulnerability management API routes.

This module provides REST API endpoints for:
- Listing vulnerabilities
- Getting vulnerability details
- Updating vulnerability status
- Getting vulnerability statistics
"""

from typing import Optional
from datetime import datetime, UTC
from math import ceil

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app.core.logging import get_logger
from app.db.session import get_db
from app.models.vulnerability import Vulnerability, Severity
from app.models.device import Device
from app.schemas.vulnerability import (
    VulnerabilityResponse,
    VulnerabilityListResponse,
    VulnerabilityUpdate,
    VulnerabilityMarkFixed,
    VulnerabilitySummary,
    SeverityLevel,
)

logger = get_logger("vulnerability")

router = APIRouter(prefix="/vulnerabilities", tags=["Vulnerabilities"])


def _vuln_to_response(vuln: Vulnerability) -> VulnerabilityResponse:
    """
    Convert a Vulnerability model to API response.

    Args:
        vuln: Vulnerability model instance

    Returns:
        VulnerabilityResponse schema
    """
    return VulnerabilityResponse(
        id=vuln.id,
        device_id=vuln.device_id,
        vuln_type=vuln.vuln_type,
        severity=SeverityLevel(vuln.severity),
        title=vuln.title,
        description=vuln.description,
        cve_id=vuln.cve_id,
        affected_service=vuln.affected_service,
        affected_port=vuln.affected_port,
        remediation=vuln.remediation,
        is_fixed=vuln.is_fixed,
        verified_fixed=vuln.verified_fixed,
        discovered_at=vuln.discovered_at,
        fixed_at=vuln.fixed_at,
        created_at=vuln.created_at,
        updated_at=vuln.updated_at,
    )


@router.get("", response_model=VulnerabilityListResponse)
async def list_vulnerabilities(
    device_id: Optional[str] = Query(None, description="Filter by device ID"),
    scan_id: Optional[str] = Query(None, description="Filter by scan ID (via device)"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    vuln_type: Optional[str] = Query(None, description="Filter by vulnerability type"),
    is_fixed: Optional[bool] = Query(None, description="Filter by fix status"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> VulnerabilityListResponse:
    """
    List vulnerabilities with optional filtering and pagination.

    Args:
        device_id: Optional device ID to filter by
        scan_id: Optional scan ID to filter by (via device relationship)
        severity: Optional severity to filter by
        vuln_type: Optional vulnerability type to filter by
        is_fixed: Optional fix status to filter by
        page: Page number (1-indexed)
        page_size: Number of items per page

    Returns:
        Paginated list of vulnerabilities
    """
    logger.debug(
        f"Listing vulnerabilities: device_id={device_id}, "
        f"severity={severity}, is_fixed={is_fixed}"
    )

    # Build query
    query = db.query(Vulnerability)

    if device_id:
        query = query.filter(Vulnerability.device_id == device_id)

    if scan_id:
        # Join with device to filter by scan_id
        query = query.join(Device).filter(Device.scan_id == scan_id)

    if severity:
        query = query.filter(Vulnerability.severity == severity)

    if vuln_type:
        query = query.filter(Vulnerability.vuln_type == vuln_type)

    if is_fixed is not None:
        query = query.filter(Vulnerability.is_fixed == is_fixed)

    # Get total count
    total = query.count()

    # Apply pagination and ordering (critical first)
    offset = (page - 1) * page_size
    vulnerabilities = (
        query
        .order_by(
            # Sort by severity (critical first)
            case(
                (Vulnerability.severity == Severity.CRITICAL, 0),
                (Vulnerability.severity == Severity.HIGH, 1),
                (Vulnerability.severity == Severity.MEDIUM, 2),
                (Vulnerability.severity == Severity.LOW, 3),
                (Vulnerability.severity == Severity.INFO, 4),
                else_=5
            ),
            Vulnerability.discovered_at.desc(),
        )
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return VulnerabilityListResponse(
        items=[_vuln_to_response(v) for v in vulnerabilities],
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total > 0 else 1,
    )


@router.get("/summary", response_model=VulnerabilitySummary)
async def get_vulnerability_summary(
    scan_id: Optional[str] = Query(None, description="Filter by scan ID"),
    device_id: Optional[str] = Query(None, description="Filter by device ID"),
    db: Session = Depends(get_db),
) -> VulnerabilitySummary:
    """
    Get vulnerability statistics summary.

    Args:
        scan_id: Optional scan ID to filter by
        device_id: Optional device ID to filter by

    Returns:
        Summary statistics
    """
    logger.debug(f"Getting vulnerability summary: scan_id={scan_id}, device_id={device_id}")

    # Build base query
    query = db.query(Vulnerability)

    if device_id:
        query = query.filter(Vulnerability.device_id == device_id)

    if scan_id:
        query = query.join(Device).filter(Device.scan_id == scan_id)

    # Get counts
    total = query.count()
    fixed = query.filter(Vulnerability.is_fixed == True).count()
    unfixed = total - fixed

    # Count by severity
    severity_counts = {}
    for sev in Severity.ALL:
        severity_counts[sev] = query.filter(Vulnerability.severity == sev).count()

    return VulnerabilitySummary(
        total=total,
        critical=severity_counts.get(Severity.CRITICAL, 0),
        high=severity_counts.get(Severity.HIGH, 0),
        medium=severity_counts.get(Severity.MEDIUM, 0),
        low=severity_counts.get(Severity.LOW, 0),
        info=severity_counts.get(Severity.INFO, 0),
        fixed=fixed,
        unfixed=unfixed,
    )


@router.get("/{vulnerability_id}", response_model=VulnerabilityResponse)
async def get_vulnerability(
    vulnerability_id: str,
    db: Session = Depends(get_db),
) -> VulnerabilityResponse:
    """
    Get a vulnerability by ID.

    Args:
        vulnerability_id: Vulnerability ID

    Returns:
        Vulnerability details

    Raises:
        404: Vulnerability not found
    """
    logger.debug(f"Getting vulnerability: {vulnerability_id}")

    vuln = db.query(Vulnerability).filter(Vulnerability.id == vulnerability_id).first()

    if not vuln:
        raise HTTPException(
            status_code=404,
            detail=f"Vulnerability not found: {vulnerability_id}",
        )

    return _vuln_to_response(vuln)


@router.put("/{vulnerability_id}", response_model=VulnerabilityResponse)
async def update_vulnerability(
    vulnerability_id: str,
    update: VulnerabilityUpdate,
    db: Session = Depends(get_db),
) -> VulnerabilityResponse:
    """
    Update a vulnerability.

    Args:
        vulnerability_id: Vulnerability ID
        update: Update data

    Returns:
        Updated vulnerability

    Raises:
        404: Vulnerability not found
    """
    logger.info(f"Updating vulnerability: {vulnerability_id}")

    vuln = db.query(Vulnerability).filter(Vulnerability.id == vulnerability_id).first()

    if not vuln:
        raise HTTPException(
            status_code=404,
            detail=f"Vulnerability not found: {vulnerability_id}",
        )

    # Apply updates
    update_data = update.model_dump(exclude_unset=True)

    # Handle is_fixed specially - set fixed_at timestamp
    if "is_fixed" in update_data:
        if update_data["is_fixed"] and not vuln.is_fixed:
            vuln.fixed_at = datetime.now(UTC)
        elif not update_data["is_fixed"]:
            vuln.fixed_at = None
            vuln.verified_fixed = False

    for field, value in update_data.items():
        setattr(vuln, field, value)

    db.commit()
    db.refresh(vuln)

    logger.info(f"Vulnerability updated: {vulnerability_id}")

    return _vuln_to_response(vuln)


@router.post("/{vulnerability_id}/mark-fixed", response_model=VulnerabilityResponse)
async def mark_vulnerability_fixed(
    vulnerability_id: str,
    data: VulnerabilityMarkFixed,
    db: Session = Depends(get_db),
) -> VulnerabilityResponse:
    """
    Mark a vulnerability as fixed or unfixed.

    Args:
        vulnerability_id: Vulnerability ID
        data: Fix status data

    Returns:
        Updated vulnerability

    Raises:
        404: Vulnerability not found
    """
    logger.info(f"Marking vulnerability {vulnerability_id} as fixed={data.is_fixed}")

    vuln = db.query(Vulnerability).filter(Vulnerability.id == vulnerability_id).first()

    if not vuln:
        raise HTTPException(
            status_code=404,
            detail=f"Vulnerability not found: {vulnerability_id}",
        )

    vuln.is_fixed = data.is_fixed
    vuln.verified_fixed = data.verified

    if data.is_fixed:
        vuln.fixed_at = datetime.now(UTC)
    else:
        vuln.fixed_at = None
        vuln.verified_fixed = False

    db.commit()
    db.refresh(vuln)

    logger.info(f"Vulnerability {vulnerability_id} marked as fixed={data.is_fixed}")

    return _vuln_to_response(vuln)


@router.get("/types/list")
async def list_vulnerability_types(
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    Get list of distinct vulnerability types in the database.

    Returns:
        List of vulnerability types with counts
    """
    results = (
        db.query(
            Vulnerability.vuln_type,
            func.count(Vulnerability.id).label("count"),
        )
        .group_by(Vulnerability.vuln_type)
        .all()
    )

    return [{"vuln_type": r[0], "count": r[1]} for r in results]
