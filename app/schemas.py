# app/schemas.py
from pydantic import BaseModel,ConfigDict
from typing import Optional
from datetime import datetime


# Schema for Category
class CategorySchema(BaseModel):
    id: int
    name: str
    description: Optional[str]

    class Config:
        orm_mode = True


# Schema for Review History
class ReviewSchema(BaseModel):
    id: int
    text: Optional[str]
    stars: int
    review_id: str
    tone: Optional[str]
    sentiment: Optional[str]
    category_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
