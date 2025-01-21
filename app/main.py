from fastapi import FastAPI
from .routers import reviews
from .database import init_db

app = FastAPI()

# Initializing the database
init_db()

# Registering routers
app.include_router(reviews.router, prefix="/reviews", tags=["Reviews"])

@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI Reviews App!"}
