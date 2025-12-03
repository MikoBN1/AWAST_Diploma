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


class VulnerabilityReport(BaseModel):
    vulns: List[Vulnerability]
