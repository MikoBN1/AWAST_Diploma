from fastapi import APIRouter, BackgroundTasks, Depends

from core.security import get_current_user
from models.users_model import User
from schemas.zap_scanner_schema import RequestBody
import services.scanner_service as scanner_service

router = APIRouter(prefix="/zap", tags=["scanner"])


@router.post("/spider")
async def zap_spider(target: RequestBody):
    return await scanner_service.start_spider(target.target)


@router.get("/spider_status/{scan_id}")
async def zap_spider_status(scan_id: str):
    return await scanner_service.get_spider_status(scan_id)


@router.post("/scan")
async def zap_scan(
    target: RequestBody,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
):
    result = await scanner_service.start_scan(target.target, user.user_id)
    background_tasks.add_task(
        scanner_service.run_scan,
        result["scan_id"],
        target.target,
        result["zap_index"],
    )
    return {"scan_id": result["scan_id"], "scan_index": result["scan_index"]}


@router.get("/scan_status/{scan_id}")
async def zap_scan_status(scan_id: str):
    return await scanner_service.get_scan_status(scan_id)


@router.get("/alerts")
async def zap_alerts():
    return await scanner_service.get_alerts()


@router.get("/alerts/target")
async def zap_alerts_with_evidence(baseurl: str = None):
    return await scanner_service.get_alerts_with_evidence(baseurl)


@router.get("/alerts/summary")
async def zap_alerts_summary():
    return await scanner_service.get_alerts_summary()


@router.get("/abort/scan/{scan_id}")
async def zap_abort(scan_id: str):
    return await scanner_service.abort_scan(scan_id)
