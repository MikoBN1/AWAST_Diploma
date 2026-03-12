from fastapi import APIRouter, HTTPException, Depends

from core.security import get_current_user
from schemas.chain_schema import AnalyzeChainRequest
from services.chain_service import ChainAnalysisService

router = APIRouter(prefix="/chains", tags=["chains"])

chain_service = ChainAnalysisService()


@router.post("/analyze", dependencies=[Depends(get_current_user)])
async def analyze_chains(body: AnalyzeChainRequest):
    if not body.alerts:
        raise HTTPException(status_code=400, detail="No alerts provided")
    return chain_service.analyze(body.alerts)
