from pydantic import BaseModel, Field, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional, List

class ProjectCreate(BaseModel):
    title: str = Field(min_length=2, max_length=150)
    description: Optional[str] = Field(default=None, max_length=5000)

class MemberAddRequest(BaseModel):
    email: EmailStr
    role: str = Field(default="developer", pattern="^(analyst|developer|tester|observer)$")

class MemberResponse(BaseModel):
    user_id: int
    name: str
    email: str
    role: str
    joined_at: Optional[datetime] = None

class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: Optional[str] = None
    owner_id: int
    status: str
    created_at: Optional[datetime] = None
