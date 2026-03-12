from pydantic import BaseModel


class AnalyzeChainRequest(BaseModel):
    alerts: list[dict]
