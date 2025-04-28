from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
import logging
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

def get_sync_database():
    """Get a synchronous MongoDB client and database."""
    try:
        client = MongoClient(settings.MONGODB_URI)
        db = client[settings.MONGODB_DB_NAME]
        # Test the connection
        client.admin.command('ping')
        logger.info(f"Connected to MongoDB (sync): {settings.MONGODB_URI}")
        return db
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB (sync): {str(e)}")
        raise

# Async MongoDB client - used by FastAPI endpoints
async def get_async_database():
    """Get an async MongoDB client and database."""
    try:
        client = AsyncIOMotorClient(settings.MONGODB_URI)
        db = client[settings.MONGODB_DB_NAME]
        # We can't test the connection easily in async mode
        # but we'll log the attempt
        logger.info(f"Connecting to MongoDB (async): {settings.MONGODB_URI}")
        return db
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB (async): {str(e)}")
        raise

def init_mongodb():
    """Initialize MongoDB with required indexes."""
    try:
        db = get_sync_database()
        
        # Create indexes for email collection
        email_collection = db['emails']
        
        # Create unique index on message_id
        email_collection.create_index([("message_id", 1)], unique=True)
        
        # Create index on received_at for sorting and filtering
        email_collection.create_index([("received_at", -1)])
        
        # Create index on sender for filtering
        email_collection.create_index([("sender", 1)])
        
        # Create index on is_read for filtering
        email_collection.create_index([("is_read", 1)])
        
        # Create text index on subject and body for searching
        email_collection.create_index([
            ("subject", "text"), 
            ("body", "text"),
            ("body_preview", "text")
        ])
        
        logger.info("MongoDB indexes created successfully")
    except Exception as e:
        logger.error(f"Error creating MongoDB indexes: {str(e)}")
        raise