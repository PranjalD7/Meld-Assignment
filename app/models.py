from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

# Declarative base for SQLAlchemy ORM models
Base = declarative_base()


class Category(Base):
    """
    Represents a category in the application.
    
    Attributes:
        id (int): Primary key, auto-incremented.
        name (str): Name of the category (must be unique).
        description (str): Detailed description of the category.
        reviews (list[ReviewHistory]): Relationship to ReviewHistory, representing all reviews under this category.
    """
    __tablename__ = "Category"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)

    reviews = relationship("ReviewHistory", back_populates="category")


class ReviewHistory(Base):
    """
    Represents the history of reviews for products or services.
    
    Attributes:
        id (int): Primary key, auto-incremented.
        text (str): Review text (can be null).
        stars (int): Star rating (required).
        review_id (str): Unique identifier for the review; may have multiple entries for historical edits.
        tone (str): The tone of the review (e.g., positive, negative, neutral).
        sentiment (str): The sentiment of the review (e.g., happy, disappointed).
        category_id (int): Foreign key linking to the category of the review.
        created_at (datetime): Timestamp when the review was created.
        updated_at (datetime): Timestamp when the review was last updated.
        category (Category): Relationship to the Category model.
    """
    __tablename__ = "ReviewHistory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(String, nullable=True)
    stars = Column(Integer, nullable=False)
    review_id = Column(String(255), nullable=False)
    tone = Column(String(255), nullable=True)
    sentiment = Column(String(255), nullable=True)
    category_id = Column(Integer, ForeignKey("Category.id"))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    category = relationship("Category", back_populates="reviews")


class AccessLog(Base):
    """
    Represents an access log entry for tracking API calls or events.
    
    Attributes:
        id (int): Primary key, auto-incremented.
        text (str): Description of the log event (required).
    """
    __tablename__ = "AccessLog"

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(String, nullable=False)
