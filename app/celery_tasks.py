from celery import Celery
from .database import SessionLocal
from .models import AccessLog
from .models import ReviewHistory
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM

template = """You will be asked to generate either sentiment or tone(positive,negative or neutral) for a review. Use the
            text provided to you and stars(stars are equivalent to the rating,1 being the lowest and 10 being the highest) to determine the sentiment or tone"""

prompt = ChatPromptTemplate.from_template(template)

model = OllamaLLM(model="llama3.2")

chain = prompt | model


celery = Celery(
    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)


@celery.task
def log_access_task(log_text: str):
    db = SessionLocal()
    try:
        log = AccessLog(text=log_text)
        db.add(log)
        db.commit()
    finally:
        db.close()
        
@celery.task
def llm_sentiment_prediction(id: int, missing_var: str, text: str, stars: int):
    """Predict tone, sentiment, or both using LLM, and update the database."""
    db = SessionLocal()
    try:
        # Fetching the review entry
        review = db.query(ReviewHistory).filter(ReviewHistory.id == id).first()

        if not review:
            raise ValueError(f"No review found with id: {id}")

        # Generating tone or sentiment as needed
        if missing_var == "tone":
            review.tone = chain.invoke(
                {"question": f"Generate the tone for this review. The text of the review '{text}' and the rating given is {stars}."}
            )
        elif missing_var == "sentiment":
            review.sentiment = chain.invoke(
                {"question": f"Generate the sentiment for this review. The text of the review is '{text}' and the rating given is {stars}."}
            )
        elif missing_var == "both":
            review.tone = chain.invoke(
                 {"question": f"Generate the tone for this review. The text of the review '{text}' and the rating given is {stars}."}
            )
            review.sentiment = chain.invoke(
                {"question": f"Generate the sentiment for this review. The text of the review is '{text}' and the rating given is {stars}."}
            )

        # Commit the changes to the database
        db.commit()

    except Exception as e:
        print(f"Error in LLM prediction task: {e}")
        raise
    finally:
        db.close()
