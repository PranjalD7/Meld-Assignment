# app/schemas.py
from pydantic import BaseModel,ConfigDict
from typing import Optional
from datetime import datetime
from typing import List, Optional

# Schema for Category api response
class CategorySchemaResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    average_stars:float
    total_reviews:int

    class Config:
        orm_mode = True


# Schema for Review History api response
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
#schema to accomodate next_cursor in response
class PaginatedReviewsResponse(BaseModel):
    reviews: List[ReviewSchema]
    next_cursor: Optional[str]  