from pydantic import BaseModel


class HealthResponse(BaseModel):
    ok: bool
    version: str
    service: str
