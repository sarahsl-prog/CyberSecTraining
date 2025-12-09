"""
Device management API routes.

This module provides REST API endpoints for:
- Listing devices from scans
- Getting device details
- Updating device information
- Deleting devices
"""

from typing import Optional
import json
from math import ceil

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.session import get_db
from app.models.device import Device
from app.schemas.device import (
    DeviceResponse,
    DeviceListResponse,
    DeviceUpdate,
    PortSchema,
)

logger = get_logger("api")

router = APIRouter(prefix="/devices", tags=["Devices"])


def _device_to_response(device: Device) -> DeviceResponse:
    """
    Convert a Device model to API response.

    Args:
        device: Device model instance

    Returns:
        DeviceResponse schema
    """
    open_ports = []
    if device.open_ports_json:
        try:
            ports_data = json.loads(device.open_ports_json)
            open_ports = [PortSchema(**p) for p in ports_data]
        except (json.JSONDecodeError, TypeError):
            logger.warning(f"Invalid ports JSON for device {device.id}")

    return DeviceResponse(
        id=device.id,
        scan_id=device.scan_id,
        ip=device.ip,
        mac=device.mac,
        hostname=device.hostname,
        vendor=device.vendor,
        device_type=device.device_type,
        os=device.os,
        os_accuracy=device.os_accuracy,
        is_up=device.is_up,
        last_seen=device.last_seen,
        open_ports=open_ports,
        vulnerability_count=len(device.vulnerabilities) if device.vulnerabilities else 0,
        created_at=device.created_at,
        updated_at=device.updated_at,
    )


@router.get("", response_model=DeviceListResponse)
async def list_devices(
    scan_id: Optional[str] = Query(None, description="Filter by scan ID"),
    device_type: Optional[str] = Query(None, description="Filter by device type"),
    has_vulnerabilities: Optional[bool] = Query(None, description="Filter by vulnerability presence"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> DeviceListResponse:
    """
    List devices with optional filtering and pagination.

    Args:
        scan_id: Optional scan ID to filter by
        device_type: Optional device type to filter by
        has_vulnerabilities: Filter devices with/without vulnerabilities
        page: Page number (1-indexed)
        page_size: Number of items per page

    Returns:
        Paginated list of devices
    """
    logger.debug(f"Listing devices: scan_id={scan_id}, device_type={device_type}")

    # Build query
    query = db.query(Device)

    if scan_id:
        query = query.filter(Device.scan_id == scan_id)

    if device_type:
        query = query.filter(Device.device_type == device_type)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    devices = query.order_by(Device.created_at.desc()).offset(offset).limit(page_size).all()

    # Filter by vulnerability presence (post-query for simplicity)
    if has_vulnerabilities is not None:
        if has_vulnerabilities:
            devices = [d for d in devices if len(d.vulnerabilities) > 0]
        else:
            devices = [d for d in devices if len(d.vulnerabilities) == 0]

    return DeviceListResponse(
        items=[_device_to_response(d) for d in devices],
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total > 0 else 1,
    )


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: str,
    db: Session = Depends(get_db),
) -> DeviceResponse:
    """
    Get a device by ID.

    Args:
        device_id: Device ID

    Returns:
        Device details

    Raises:
        404: Device not found
    """
    logger.debug(f"Getting device: {device_id}")

    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(status_code=404, detail=f"Device not found: {device_id}")

    return _device_to_response(device)


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: str,
    update: DeviceUpdate,
    db: Session = Depends(get_db),
) -> DeviceResponse:
    """
    Update a device.

    Only certain fields can be updated (hostname, device_type, os).

    Args:
        device_id: Device ID
        update: Update data

    Returns:
        Updated device

    Raises:
        404: Device not found
    """
    logger.info(f"Updating device: {device_id}")

    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(status_code=404, detail=f"Device not found: {device_id}")

    # Apply updates
    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(device, field, value)

    db.commit()
    db.refresh(device)

    logger.info(f"Device updated: {device_id}")

    return _device_to_response(device)


@router.delete("/{device_id}")
async def delete_device(
    device_id: str,
    db: Session = Depends(get_db),
) -> dict:
    """
    Delete a device and its associated vulnerabilities.

    Args:
        device_id: Device ID

    Returns:
        Success message

    Raises:
        404: Device not found
    """
    logger.info(f"Deleting device: {device_id}")

    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(status_code=404, detail=f"Device not found: {device_id}")

    db.delete(device)
    db.commit()

    logger.info(f"Device deleted: {device_id}")

    return {"message": "Device deleted", "device_id": device_id}


@router.get("/{device_id}/vulnerabilities")
async def get_device_vulnerabilities(
    device_id: str,
    severity: Optional[str] = Query(None, description="Filter by severity"),
    is_fixed: Optional[bool] = Query(None, description="Filter by fix status"),
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    Get vulnerabilities for a specific device.

    Args:
        device_id: Device ID
        severity: Optional severity filter
        is_fixed: Optional fix status filter

    Returns:
        List of vulnerabilities

    Raises:
        404: Device not found
    """
    logger.debug(f"Getting vulnerabilities for device: {device_id}")

    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(status_code=404, detail=f"Device not found: {device_id}")

    vulnerabilities = device.vulnerabilities

    # Apply filters
    if severity:
        vulnerabilities = [v for v in vulnerabilities if v.severity == severity]

    if is_fixed is not None:
        vulnerabilities = [v for v in vulnerabilities if v.is_fixed == is_fixed]

    return [v.to_dict() for v in vulnerabilities]
