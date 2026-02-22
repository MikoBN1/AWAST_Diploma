from typing import Dict, Optional

from pydantic import BaseModel


class RequestBody(BaseModel):
    target: str
    cookies: Optional[Dict[str, str]] = None