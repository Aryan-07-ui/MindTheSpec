from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List, Any

class SessionCreate(BaseModel):
    version_id: Optional[int] = None
    mode: str = Field(default="standard", pattern="^(standard|self_comparison)$")

class InterpretationCreate(BaseModel):
    perspective: str = Field(min_length=2, max_length=100)
    actor: Optional[str] = Field(default=None, max_length=100)
    expected_behavior: str = Field(min_length=5)
    trigger_conditions: Optional[str] = None
    delivery_hours: Optional[int] = Field(default=None, gt=0, le=10000)
    constraints: Optional[str] = None
    acceptance_criteria: Optional[str] = None

class InterpretationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    session_id: int
    user_id: int
    perspective: str
    actor: Optional[str] = None
    expected_behavior: str
    trigger_conditions: Optional[str] = None
    delivery_hours: Optional[int] = None
    constraints: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    submitted_at: Optional[datetime] = None

class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    requirement_version_id: int
    created_by: int
    status: str
    mode: str
    locked_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

class ParticipationSummary(BaseModel):
    session_id: int
    status: str
    mode: str
    total_submissions: int
