from fastapi import APIRouter, UploadFile, File, HTTPException
from services.swagger_service import SwaggerService
from schemas.swagger_schema import SwaggerAnalysisResponse

router = APIRouter()
swagger_service = SwaggerService()

@router.post("/analyze/swagger", response_model=SwaggerAnalysisResponse)
async def analyze_swagger_file(file: UploadFile = File(...)):
    if not file.filename.endswith(('.json', '.yaml', '.yml')):
         raise HTTPException(status_code=400, detail="Invalid file format. Please upload .json or .yaml/.yml file")
    
    try:
        content = await file.read()
        findings = await swagger_service.analyze_swagger(content, file.filename)
        return SwaggerAnalysisResponse(findings=findings, total_findings=len(findings))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
