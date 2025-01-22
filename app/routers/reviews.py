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
    """
    Provides a database session for dependency injection.
    Ensures the session is closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/trends",response_model=list[CategorySchemaResponse])
async def get_review_trends(db: Session = Depends(get_db)):
    """
    Retrieves the top 5 categories based on the average stars of the latest reviews.
    
    - The latest review is determined for each review_id.
    - Categories are ranked by the descending average of stars from their latest reviews.
    - Saves an access log asynchronously.

    Args:
        db (Session): Database session.

    Returns:
        List[CategorySchemaResponse]: A list of top 5 categories with their average stars and total reviews.
    """
    
    # Log the access event asynchronously
    log_access_task.delay("GET /reviews/trends")
    
    
    # Subquery to get the latest review for each review_id
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
    
    # Fetching top 5 categories by average stars
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
    
    # Execute the query and fetch results
    results = query.all()
    
    
    if not results:
        raise HTTPException(status_code=404, detail="No categories found")
    
    # Converting results to Pydantic schema manually
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
    category_id: int, cursor: str = None, db: Session = Depends(get_db)):
    
    """
    Fetches reviews for a specific category using cursor-based pagination.
    
    - Retrieves the latest version of each review.
    - Supports pagination with a cursor (based on `created_at` timestamp).
    - Logs access events asynchronously.
    - Initiates Celery tasks to calculate tone and sentiment if they are missing.

    Args:
        category_id (int): The ID of the category to fetch reviews for.
        cursor (str, optional): ISO timestamp of the last review in the previous page.
        db (Session): Database session.

    Returns:
        PaginatedReviewsResponse: A list of reviews and the next cursor for pagination.
    """

    # Logging the access asynchronously
    log_access_task.delay(f"GET /reviews/?category_id={category_id}")

    # Defining the page size
    page_size = 3

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

    # Main query: Fetching reviews for the category using the latest entries
    query = (
        db.query(latest_reviews)
        .join(
            latest_reviews_subquery,
            (latest_reviews.review_id == latest_reviews_subquery.c.review_id)
            & (latest_reviews.created_at == latest_reviews_subquery.c.latest_created_at),
        )
        .filter(latest_reviews.category_id == category_id)
    )

    # Applying cursor-based pagination if the cursor is provided
    if cursor:
        cursor_datetime = datetime.fromisoformat(cursor)
        query = query.filter(latest_reviews.created_at < cursor_datetime)

    # Sorting reviews by `created_at` and limit to `page_size`
    reviews = query.order_by(latest_reviews.created_at.desc()).limit(page_size).all()

    if not reviews:
        raise HTTPException(status_code=404, detail="No reviews found")

    # Queueing Celery tasks for missing tone/sentiment
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

    # Constructing the response
    response = [ReviewSchema.model_validate(review) for review in reviews]

    # Adding the next cursor to the response if there are more results
    next_cursor = reviews[-1].created_at.isoformat() if len(reviews) == page_size else None

    return {"reviews": response, "next_cursor": next_cursor}
