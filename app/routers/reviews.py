from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from ..database import SessionLocal
from ..models import ReviewHistory, Category
from ..celery_tasks import log_access_task,llm_sentiment_prediction
from app.schemas import ReviewSchema, CategorySchema
router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/trends",response_model=list[CategorySchema])
async def get_review_trends(db: Session = Depends(get_db)):
    log_access_task.delay("GET /reviews/trends")
    # Fetch top 5 categories by average stars
    query = (
        db.query(
            Category.id.label("id"),
            Category.name.label("name"),
            Category.description.label("description"),
            func.avg(ReviewHistory.stars).label("average_stars"),
            func.count(ReviewHistory.id).label("total_reviews"),
        )
        .join(ReviewHistory, Category.id == ReviewHistory.category_id)
        .group_by(Category.id)
        .order_by(func.avg(ReviewHistory.stars).desc())
        .limit(5)
    )
    results = query.all()
       # Convert results to Pydantic schema manually
    response = [
        {
            "id": category.id,
            "name": category.name,
            "description": category.description,
            "average_star": round(category.average_stars, 2),
            "total_reviews": category.total_reviews,
        }
        for category in results
    ]

    return response



@router.get("/",response_model=list[ReviewSchema])
async def get_reviews_by_category(
    category_id: int, page: int = 1, db: Session = Depends(get_db)
):
    log_access_task.delay(f"GET /reviews/?category_id={category_id}")
    page_size = 15
    offset = (page - 1) * page_size

    # Get reviews for a category, sorted by the latest review's created_at
    reviews = (
        db.query(ReviewHistory)
        .filter(ReviewHistory.category_id == category_id)
        .order_by(ReviewHistory.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )
    if not reviews:
        raise HTTPException(status_code=404, detail="No reviews found")

  # Queue Celery tasks for missing tone/sentiment
    for review in reviews:
        if not review.tone and not review.sentiment:
            print("we are here boi")
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
    return [ReviewSchema.model_validate(review) for review in reviews]
