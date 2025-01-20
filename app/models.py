from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Category(Base):
    __tablename__ = "Category"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)

    reviews = relationship("ReviewHistory", back_populates="category")


class ReviewHistory(Base):
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
    __tablename__ = "AccessLog"

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(String, nullable=False)
