from celery import Celery
from .database import SessionLocal
from .models import AccessLog
from .models import ReviewHistory
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM


# Define the LLM template and model
template = """You will be asked to generate either sentiment or tone(positive,negative or neutral) for a review. Use the
            text provided to you and stars(stars are equivalent to the rating,1 being the lowest and 10 being the highest) to determine the sentiment or tone"""

prompt = ChatPromptTemplate.from_template(template)

model = OllamaLLM(model="llama3.2")

# Combine the prompt and model into a processing chain
chain = prompt | model


# Celery configuration
celery = Celery(
    "tasks",
    broker="redis://localhost:6379/0", # Redis as the message broker
    backend="redis://localhost:6379/0", #Redis as the result backend
)


@celery.task
def log_access_task(log_text: str):
    """
    Celery task to log an access event asynchronously.

    Args:
        log_text (str): The access log message to save.

    Saves the log entry into the AccessLog table.
    """
    
    db = SessionLocal()
    try:
        # Create a new log entry and save it to the database
        log = AccessLog(text=log_text)
        db.add(log)
        db.commit()
    finally:
        # Ensure the database session is closed
        db.close()
        
@celery.task
def llm_sentiment_prediction(id: int, missing_var: str, text: str, stars: int):
    """
    Celery task to predict the tone, sentiment, or both using an LLM.

    Args:
        id (int): The ID of the ReviewHistory entry to update.
        missing_var (str): Specifies whether to generate "tone", "sentiment", or "both".
        text (str): The review text to analyze.
        stars (int): The rating given for the review (1 to 10).

    Fetches the review entry from the database, performs LLM-based prediction, 
    and updates the tone or sentiment fields.
    """
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
