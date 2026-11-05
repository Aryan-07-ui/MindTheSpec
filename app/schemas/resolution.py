from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional

class ResolutionCreate(BaseModel):
    statement: str = Field(min_length=5)
    rationale: str = Field(min_length=5)

class ResolutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    session_id: int
    statement: str
    rationale: str
    decided_by: int
    decided_at: Optional[datetime] = None
