from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from ..database import SessionLocal
from ..models import ReviewHistory, Category
from ..celery_tasks import log_access_task,llm_sentiment_prediction
from app.schemas import ReviewSchema, CategorySchemaResponse ,PaginatedReviewsResponse
from sqlalchemy.orm import aliased
from datetime import datetime
router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/trends",response_model=list[CategorySchemaResponse])
async def get_review_trends(db: Session = Depends(get_db)):
    log_access_task.delay("GET /reviews/trends")
    
      # Subquery: Get the latest review for each review_id
    latest_reviews_subquery = (
        db.query(
            ReviewHistory.review_id,
            func.max(ReviewHistory.created_at).label("latest_created_at"),
        )
        .group_by(ReviewHistory.review_id)
        .subquery()
    )
    # Alias for joining the subquery with ReviewHistory
    latest_reviews = aliased(ReviewHistory)
    # Fetch top 5 categories by average stars
     # Main query: Join latest reviews with Category and calculate aggregates
    query = (
        db.query(
            Category.id.label("id"),
            Category.name.label("name"),
            Category.description.label("description"),
            func.avg(latest_reviews.stars).label("average_stars"),
            func.count(latest_reviews.id).label("total_reviews"),
        )
        .join(
            latest_reviews_subquery,
            (latest_reviews.review_id == latest_reviews_subquery.c.review_id)
            & (latest_reviews.created_at == latest_reviews_subquery.c.latest_created_at),
        )
        .join(Category, Category.id == latest_reviews.category_id)
        .group_by(Category.id)
        .order_by(func.avg(latest_reviews.stars).desc())
        .limit(5)
    )
    results = query.all()
    print(results)
    if not results:
        raise HTTPException(status_code=404, detail="No categories found")
       # Convert results to Pydantic schema manually
    print(results[0].average_stars)
    response = [
    {
        "id": category.id,
        "name": category.name,
        "description": category.description,
        "average_stars": round(category.average_stars, 2),
        "total_reviews": category.total_reviews,
    }
    for category in results
]
    print(response)
    return response


@router.get("/", response_model=PaginatedReviewsResponse)
async def get_reviews_by_category(
    category_id: int, cursor: str = None, db: Session = Depends(get_db)
):
    # Log the access asynchronously
    log_access_task.delay(f"GET /reviews/?category_id={category_id}")

    # Define the page size
    page_size = 15

    # Subquery to get the latest `created_at` for each `review_id`
    latest_reviews_subquery = (
        db.query(
            ReviewHistory.review_id,
            func.max(ReviewHistory.created_at).label("latest_created_at"),
        )
        .group_by(ReviewHistory.review_id)
        .subquery()
    )

    # Alias for ReviewHistory to join with the subquery
    latest_reviews = aliased(ReviewHistory)

    # Main query: Fetch reviews for the category using the latest entries
    query = (
        db.query(latest_reviews)
        .join(
            latest_reviews_subquery,
            (latest_reviews.review_id == latest_reviews_subquery.c.review_id)
            & (latest_reviews.created_at == latest_reviews_subquery.c.latest_created_at),
        )
        .filter(latest_reviews.category_id == category_id)
    )

    # Apply cursor-based pagination if the cursor is provided
    if cursor:
        cursor_datetime = datetime.fromisoformat(cursor)
        query = query.filter(latest_reviews.created_at < cursor_datetime)

    # Sort reviews by `created_at` and limit to `page_size`
    reviews = query.order_by(latest_reviews.created_at.desc()).limit(page_size).all()

    if not reviews:
        raise HTTPException(status_code=404, detail="No reviews found")

    # Queue Celery tasks for missing tone/sentiment
    for review in reviews:
        if not review.tone and not review.sentiment:
            # Both tone and sentiment are missing
            llm_sentiment_prediction.delay(
                id=review.id, missing_var="both", text=review.text, stars=review.stars
            )
        elif not review.tone:
            # Only tone is missing
            llm_sentiment_prediction.delay(
                id=review.id, missing_var="tone", text=review.text, stars=review.stars
            )
        elif not review.sentiment:
            # Only sentiment is missing
            llm_sentiment_prediction.delay(
                id=review.id, missing_var="sentiment", text=review.text, stars=review.stars
            )

    # Construct the response
    response = [ReviewSchema.model_validate(review) for review in reviews]

    # Add the next cursor to the response if there are more results
    next_cursor = reviews[-1].created_at.isoformat() if len(reviews) == page_size else None

    return {"reviews": response, "next_cursor": next_cursor}
