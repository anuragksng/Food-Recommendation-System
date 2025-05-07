import os
import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError, OperationalError

# Get database connection URL from environment variable
DATABASE_URL = "postgresql://postgres:123@localhost:5432/myprojectdb"

# Create the database engine with connection pool settings
engine = None
Session = None

def get_db_engine():
    """Get database engine with retry logic for connection issues"""
    global engine
    
    if engine is not None:
        return engine
        
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Create a database engine with proper connection settings
            engine = create_engine(
                DATABASE_URL,
                connect_args={
                    'connect_timeout': 10,
                    'keepalives': 1,
                    'keepalives_idle': 30,
                    'keepalives_interval': 10,
                    'keepalives_count': 5
                },
                pool_pre_ping=True,  # Check if connection is alive before using
                pool_recycle=3600,   # Recycle connections after 1 hour
                pool_timeout=30,     # Wait up to 30 seconds for a connection
                max_overflow=10      # Allow up to 10 extra connections beyond pool size
            )
            
            # Test the connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                
            print("Database connection established successfully")
            return engine
            
        except OperationalError as e:
            retry_count += 1
            wait_time = 2 ** retry_count  # Exponential backoff
            print(f"Database connection failed, retry {retry_count}/{max_retries} after {wait_time}s. Error: {e}")
            time.sleep(wait_time)
        except Exception as e:
            print(f"Database connection error: {e}")
            raise
            
    raise Exception("Failed to connect to database after multiple retries")

def get_session_factory():
    """Get a session factory for creating database sessions"""
    global Session
    
    if Session is not None:
        return Session
        
    # Get the engine
    engine = get_db_engine()
    
    # Create a session factory
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)
    
    return Session