# app/schemas.py
from pydantic import BaseModel,ConfigDict
from typing import Optional
from datetime import datetime
from typing import List, Optional

# Schema for Category api response
class CategorySchemaResponse(BaseModel):
    """
    Represents the response structure for category-related API endpoints.

    Attributes:
        id (int): Unique identifier for the category.
        name (str): Name of the category.
        description (Optional[str]): A detailed description of the category.
        average_stars (float): The average star rating of reviews in this category.
        total_reviews (int): The total number of reviews in this category.
    """
    id: int
    name: str
    description: Optional[str]
    average_stars:float
    total_reviews:int

    class Config:
        orm_mode = True


# Schema for Review History api response
class ReviewSchema(BaseModel):
    """
    Represents the structure of a review in the API response.

    Attributes:
        id (int): Unique identifier for the review record.
        text (Optional[str]): The textual content of the review.
        stars (int): The star rating of the review.
        review_id (str): The unique identifier for the review (used for grouping historical edits).
        tone (Optional[str]): The tone of the review (e.g., positive, negative, neutral).
        sentiment (Optional[str]): The sentiment of the review (e.g., happy, frustrated).
        category_id (int): The ID of the category associated with the review.
        created_at (datetime): Timestamp indicating when the review was created.
        updated_at (datetime): Timestamp indicating when the review was last updated.
    """
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
    """
    Represents the response structure for paginated review results.

    Attributes:
        reviews (List[ReviewSchema]): A list of reviews included in the current page.
        next_cursor (Optional[str]): The cursor for the next page of results, or None if there are no more results.
    """
    reviews: List[ReviewSchema]
    next_cursor: Optional[str]  