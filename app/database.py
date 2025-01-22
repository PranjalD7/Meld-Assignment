from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

# Path to the SQLite database file
DATABASE_URL = "sqlite:///./test.db" 

# Create a database engine to manage connections to the SQLite database
# "check_same_thread" is set to False to allow connections across multiple threads
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create a session factory for managing database sessions
# - autocommit=False: Transactions are manually committed
# - autoflush=False: Prevents automatic flushing of changes to the database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Initialize the database by creating all tables defined in the Base metadata.

    This function should be called at the start of the application to ensure
    that the database schema is created if it does not already exist.
    """
    Base.metadata.create_all(bind=engine)
