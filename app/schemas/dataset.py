from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class DatasetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    file_path: str
    table_name: Optional[str] = None  # Optional because service generates it
    uploaded_by: int

class DatasetResponse(BaseModel):
    id: int
    name: str
    file_path: str
    table_name: str
    uploaded_by: int
    created_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }
