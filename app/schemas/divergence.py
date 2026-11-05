from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any

class DivergenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    session_id: int
    field_name: str
    kind: str
    category: Optional[str] = None
    severity: str = "medium"
    evidence_json: Dict[str, Any]
    review_status: str
    fingerprint: str
    created_at: Optional[datetime] = None
