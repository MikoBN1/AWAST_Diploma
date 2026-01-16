from pydantic import BaseModel
from typing import List, Optional

class VulnerabilityFinding(BaseModel):
    title: str
    description: str
    severity: str
    location: str  # e.g., "GET /api/users/{id}"
    remediation: Optional[str] = None

class SwaggerAnalysisResponse(BaseModel):
    findings: List[VulnerabilityFinding]
    total_findings: int

class SwaggerAnalysisRequest(BaseModel):
    # This might be used if we allow sending JSON content directly in body instead of file upload
    content: str
