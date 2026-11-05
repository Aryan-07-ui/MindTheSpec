from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List

class RequirementCreate(BaseModel):
    req_code: str = Field(min_length=2, max_length=50)
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=5)
    acceptance_criteria: Optional[str] = None
    acceptance_notes: Optional[str] = None
    priority: Optional[str] = "medium"  # low, medium, high, critical

class RequirementUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, min_length=5)
    acceptance_criteria: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None

class RevisionCreate(BaseModel):
    body: str = Field(min_length=5)
    acceptance_notes: Optional[str] = None

class VersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    version_no: int
    body: str
    acceptance_notes: Optional[str] = None
    created_by: int
    created_at: Optional[datetime] = None

class RequirementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_id: int
    req_code: str
    title: str
    description: str
    acceptance_criteria: Optional[str] = None
    priority: str = "medium"
    status: str
    version: int
    current_version_id: Optional[int] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
