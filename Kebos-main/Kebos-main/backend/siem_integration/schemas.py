from pydantic import BaseModel
from typing import Optional

class SIEMEvent(BaseModel):
    name: str
    description: Optional[str] = None

class SIEMEventResponse(BaseModel):
    status: str
    event: Optional[SIEMEvent] = None
