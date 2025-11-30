from pydantic import BaseModel


class RequestBody(BaseModel):
    target: str