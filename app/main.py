from fastapi import FastAPI
from .routers import reviews
from .database import init_db

# Create an instance of the FastAPI application
app = FastAPI()

# Initialize the database and create all tables if they don't exist
init_db()


# Register the `reviews` router under the `/reviews` prefix
# The `tags` argument categorizes the routes under "Reviews" in the API documentation
app.include_router(reviews.router, prefix="/reviews", tags=["Reviews"])

@app.get("/")
async def root():
    """
    Root endpoint of the application.

    Returns:
        dict: A welcome message for the FastAPI Reviews App.
    """
    return {"message": "Welcome to the FastAPI Reviews App!"}
