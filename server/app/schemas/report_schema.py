from typing import List, Optional
from pydantic import BaseModel, HttpUrl


class Vulnerability(BaseModel):
    name: str
    description: str
    risk: str
    cweid: Optional[str]
    url: HttpUrl
    method: str
    tags: dict[str, str]
    solution: Optional[str]
    references: Optional[List[str]] = None  # строки ссылок после split('\n')
    
    # New AI and context fields
    parameter: Optional[str] = None
    payload: Optional[str] = None
    request: Optional[str] = None
    response: Optional[str] = None
    ai_status: Optional[str] = None
    ai_reasoning: Optional[str] = None
    confidence_score: Optional[int] = None

class VulnerabilityReport(BaseModel):
    vulns: List[Vulnerability]

class ReportRequest(BaseModel):
    scan_id: str

class DownloadReportRequest(BaseModel):
    report_id: str
