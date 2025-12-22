"""
Network scanning API routes.

This module provides REST API endpoints for:
- Starting network scans
- Checking scan status
- Getting scan results
- Listing network interfaces
- Validating network targets

All scans require user consent to confirm network ownership.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from app.core.logging import get_logger
from app.schemas.network import (
    ScanRequest,
    ScanResponse,
    ScanStatusResponse,
    DeviceResponse,
    NetworkInterfaceResponse,
    NetworkValidationRequest,
    NetworkValidationResponse,
    PaginatedScanResponse,
)
from app.services.scanner.orchestrator import get_scan_orchestrator
from app.services.scanner.network_validator import NetworkValidationError
from app.services.scanner.base import ScanResult, DeviceInfo, PortInfo

logger = get_logger("api")

router = APIRouter(prefix="/network", tags=["Network Scanning"])


def _scan_result_to_response(result: ScanResult) -> ScanResponse:
    """
    Convert internal ScanResult to API response.

    Args:
        result: Internal scan result object

    Returns:
        ScanResponse for API
    """
    return ScanResponse(
        scan_id=result.scan_id,
        target_range=result.target_range,
        scan_type=result.scan_type.value,
        status=result.status.value,
        devices=[_device_to_response(d) for d in result.devices],
        started_at=result.started_at,
        completed_at=result.completed_at,
        error_message=result.error_message,
        progress=result.progress,
        scanned_hosts=result.scanned_hosts,
        total_hosts=result.total_hosts,
        device_count=len(result.devices),
    )


def _device_to_response(device: DeviceInfo) -> DeviceResponse:
    """
    Convert internal DeviceInfo to API response.

    Args:
        device: Internal device info object

    Returns:
        DeviceResponse for API
    """
    from app.schemas.network import PortResponse

    return DeviceResponse(
        ip=device.ip,
        mac=device.mac,
        hostname=device.hostname,
        vendor=device.vendor,
        os=device.os,
        os_accuracy=device.os_accuracy,
        device_type=device.device_type,
        open_ports=[
            PortResponse(
                port=p.port,
                protocol=p.protocol,
                state=p.state,
                service=p.service,
                version=p.version,
                banner=p.banner,
            )
            for p in device.open_ports
        ],
        last_seen=device.last_seen,
        is_up=device.is_up,
    )


@router.post("/scan", response_model=ScanResponse)
async def start_scan(request: ScanRequest) -> ScanResponse:
    """
    Start a new network scan.

    This endpoint initiates a network scan of the specified target.
    User consent is required to confirm network ownership.

    **Important Security Notes:**
    - Only private network ranges are allowed (10.x, 172.16-31.x, 192.168.x)
    - User must confirm they own or have permission to scan the network
    - All scans are logged for audit purposes

    **Scan Types:**
    - `quick`: Fast scan of common ports (1-1024)
    - `deep`: Comprehensive scan of all ports (takes longer)
    - `discovery`: Host discovery only, no port scanning
    - `custom`: User-defined port range

    Args:
        request: Scan request with target, type, and consent

    Returns:
        ScanResponse with scan ID and initial status

    Raises:
        400: Invalid target or port range
        403: User consent not provided
        429: Another scan is already running or cooldown active
        500: Internal scanner error
    """
    logger.info(f"Scan request received: {request.target} ({request.scan_type.value})")

    try:
        orchestrator = get_scan_orchestrator()
        result = await orchestrator.start_scan(
            target=request.target,
            scan_type=request.scan_type,
            port_range=request.port_range,
            user_consent=request.user_consent,
        )

        return _scan_result_to_response(result)

    except NetworkValidationError as e:
        logger.warning(f"Network validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except PermissionError as e:
        logger.warning(f"Permission denied: {e}")
        raise HTTPException(status_code=403, detail=str(e))

    except RuntimeError as e:
        # Rate limiting or concurrent scan errors
        logger.warning(f"Scan blocked: {e}")
        raise HTTPException(status_code=429, detail=str(e))

    except Exception as e:
        logger.exception(f"Scan error: {e}")
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


@router.get("/scan/{scan_id}", response_model=ScanResponse)
async def get_scan(scan_id: str) -> ScanResponse:
    """
    Get scan results by ID.

    Returns the full scan results including all discovered devices.

    Args:
        scan_id: Unique identifier of the scan

    Returns:
        ScanResponse with full results

    Raises:
        404: Scan not found
    """
    logger.debug(f"Getting scan: {scan_id}")

    orchestrator = get_scan_orchestrator()
    result = await orchestrator.get_scan_status(scan_id)

    if not result:
        raise HTTPException(status_code=404, detail=f"Scan not found: {scan_id}")

    return _scan_result_to_response(result)


@router.get("/scan/{scan_id}/status", response_model=ScanStatusResponse)
async def get_scan_status(scan_id: str) -> ScanStatusResponse:
    """
    Get scan status (lightweight endpoint for polling).

    This endpoint returns minimal information for efficient status polling
    during a running scan.

    Args:
        scan_id: Unique identifier of the scan

    Returns:
        ScanStatusResponse with status and progress

    Raises:
        404: Scan not found
    """
    orchestrator = get_scan_orchestrator()
    result = await orchestrator.get_scan_status(scan_id)

    if not result:
        raise HTTPException(status_code=404, detail=f"Scan not found: {scan_id}")

    return ScanStatusResponse(
        scan_id=result.scan_id,
        status=result.status.value,
        progress=result.progress,
        device_count=len(result.devices),
        error_message=result.error_message,
    )


@router.get("/scan/{scan_id}/devices", response_model=list[DeviceResponse])
async def get_scan_devices(
    scan_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> list[DeviceResponse]:
    """
    Get devices from a scan.

    Returns paginated list of devices discovered during the scan.

    Args:
        scan_id: Unique identifier of the scan
        limit: Maximum number of devices to return
        offset: Number of devices to skip

    Returns:
        List of DeviceResponse objects

    Raises:
        404: Scan not found
    """
    orchestrator = get_scan_orchestrator()
    result = await orchestrator.get_scan_status(scan_id)

    if not result:
        raise HTTPException(status_code=404, detail=f"Scan not found: {scan_id}")

    devices = result.devices[offset : offset + limit]
    return [_device_to_response(d) for d in devices]


@router.post("/scan/{scan_id}/cancel")
async def cancel_scan(scan_id: str) -> dict:
    """
    Cancel a running scan.

    Args:
        scan_id: Unique identifier of the scan to cancel

    Returns:
        Success message

    Raises:
        404: Scan not found or already completed
    """
    logger.info(f"Cancel request for scan: {scan_id}")

    orchestrator = get_scan_orchestrator()
    cancelled = await orchestrator.cancel_scan(scan_id)

    if not cancelled:
        raise HTTPException(
            status_code=404,
            detail=f"Scan not found or already completed: {scan_id}",
        )

    return {"message": "Scan cancelled", "scan_id": scan_id}


@router.get("/scans", response_model=PaginatedScanResponse)
async def list_scans(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=10, ge=1, le=100, description="Items per page"),
) -> PaginatedScanResponse:
    """
    List scan history with pagination.

    Returns paginated list of past scans, most recent first.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page

    Returns:
        PaginatedScanResponse with scan history
    """
    orchestrator = get_scan_orchestrator()

    # Calculate offset from page number
    offset = (page - 1) * page_size

    # Get scans and total count
    scans = await orchestrator.get_scan_history(limit=page_size, offset=offset)
    total = orchestrator._datastore.count_scans("local")

    # Calculate total pages
    pages = (total + page_size - 1) // page_size if total > 0 else 0

    return PaginatedScanResponse(
        items=[_scan_result_to_response(s) for s in scans],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/interfaces", response_model=list[NetworkInterfaceResponse])
async def list_interfaces() -> list[NetworkInterfaceResponse]:
    """
    List available network interfaces.

    Returns information about network interfaces on this machine
    that can be used for scanning.

    Returns:
        List of NetworkInterfaceResponse objects
    """
    orchestrator = get_scan_orchestrator()
    interfaces = orchestrator.get_network_interfaces()

    return [
        NetworkInterfaceResponse(
            name=iface["name"],
            ip=iface["ip"],
            netmask=iface["netmask"],
            network=iface["network"],
            is_private=iface["is_private"],
        )
        for iface in interfaces
    ]


@router.get("/detect")
async def detect_local_network() -> dict:
    """
    Auto-detect the local network range.

    This endpoint attempts to detect the local network range
    based on the default gateway interface.

    Returns:
        Dictionary with detected network or error message
    """
    orchestrator = get_scan_orchestrator()
    network = orchestrator.detect_local_network()

    if network:
        return {
            "detected": True,
            "network": network,
            "message": f"Detected local network: {network}",
        }
    else:
        return {
            "detected": False,
            "network": None,
            "message": "Could not auto-detect local network. Please enter manually.",
        }


@router.post("/validate", response_model=NetworkValidationResponse)
async def validate_target(request: NetworkValidationRequest) -> NetworkValidationResponse:
    """
    Validate a network target before scanning.

    This endpoint checks if a target is valid for scanning:
    - Valid IP address or CIDR notation
    - Within a private network range
    - Within size limits

    Args:
        request: NetworkValidationRequest with target

    Returns:
        NetworkValidationResponse with validation result
    """
    orchestrator = get_scan_orchestrator()

    try:
        info = orchestrator.validate_target(request.target)
        return NetworkValidationResponse(
            valid=True,
            target=request.target,
            is_private=info.get("is_private", True),
            num_hosts=info.get("num_hosts", 1),
            type=info.get("type", "unknown"),
            error=None,
        )
    except NetworkValidationError as e:
        return NetworkValidationResponse(
            valid=False,
            target=request.target,
            is_private=False,
            num_hosts=0,
            type="unknown",
            error=str(e),
        )
    except Exception as e:
        return NetworkValidationResponse(
            valid=False,
            target=request.target,
            is_private=False,
            num_hosts=0,
            type="unknown",
            error=f"Validation error: {str(e)}",
        )
