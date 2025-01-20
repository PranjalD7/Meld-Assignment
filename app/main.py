from fastapi import FastAPI
from .routers import reviews
from .database import init_db

app = FastAPI()

# Initialize the database
init_db()

# Register routers
app.include_router(reviews.router, prefix="/reviews", tags=["Reviews"])

@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI Reviews App!"}
