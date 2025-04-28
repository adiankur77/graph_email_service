import logging
import datetime
from typing import List, Dict, Any, Optional, Union
from bson import ObjectId
from app.database import get_sync_database

logger = logging.getLogger(__name__)

class EmailModel:
    """Model class for email documents in MongoDB."""
    
    COLLECTION_NAME = 'emails'
    
    @classmethod
    def get_collection(cls):
        """Get the MongoDB collection for emails."""
        db = get_sync_database()
        return db[cls.COLLECTION_NAME]
    
    @classmethod
    def create(cls, email_data: Dict[str, Any]) -> Optional[str]:
        """Create a new email document in MongoDB.
        
        Args:
            email_data (dict): The email data to store
            
        Returns:
            str: The ID of the inserted document, or None if insertion failed
        """
        collection = cls.get_collection()
        try:
            result = collection.insert_one(email_data)
            return str(result.inserted_id)
        except Exception as e:
            if "duplicate key error" in str(e):
                # Document with this message_id already exists
                logger.warning(f"Attempt to insert duplicate email with message_id: {email_data.get('message_id')}")
                return None
            else:
                # Re-raise other exceptions
                logger.error(f"Error creating email: {str(e)}")
                return None
    
    @classmethod
    def get_by_id(cls, email_id: str) -> Optional[Dict[str, Any]]:
        """Get an email by its MongoDB ID.
        
        Args:
            email_id (str): The MongoDB ObjectId as string
            
        Returns:
            dict: The email document, or None if not found
        """
        collection = cls.get_collection()
        try:
            return collection.find_one({"_id": ObjectId(email_id)})
        except Exception as e:
            logger.error(f"Error getting email by ID: {str(e)}")
            return None
    
    @classmethod
    def get_by_message_id(cls, message_id: str) -> Optional[Dict[str, Any]]:
        """Get an email by its Microsoft Graph message ID.
        
        Args:
            message_id (str): The Microsoft Graph message ID
            
        Returns:
            dict: The email document, or None if not found
        """
        collection = cls.get_collection()
        try:
            return collection.find_one({"message_id": message_id})
        except Exception as e:
            logger.error(f"Error getting email by message ID: {str(e)}")
            return None
    
    @classmethod
    def update_read_status(cls, message_id: str, is_read: bool) -> bool:
        """Update the read status of an email.
        
        Args:
            message_id (str): The Microsoft Graph message ID
            is_read (bool): The new read status
            
        Returns:
            bool: True if updated successfully, False otherwise
        """
        collection = cls.get_collection()
        try:
            result = collection.update_one(
                {"message_id": message_id},
                {"$set": {"is_read": is_read, "updated_at": datetime.datetime.utcnow()}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating read status: {str(e)}")
            return False
    
    @classmethod
    def list_emails(cls, 
                    limit: int = 100, 
                    skip: int = 0, 
                    sort_by: str = 'received_at', 
                    sort_order: int = -1, 
                    filter_query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """List emails with pagination and filtering.
        
        Args:
            limit (int): Maximum number of emails to return
            skip (int): Number of emails to skip
            sort_by (str): Field to sort by
            sort_order (int): Sort order (1 for ascending, -1 for descending)
            filter_query (dict): MongoDB query filter
            
        Returns:
            list: A list of email documents
        """
        collection = cls.get_collection()
        query = filter_query or {}
        
        try:
            cursor = collection.find(query).sort(sort_by, sort_order).skip(skip).limit(limit)
            return list(cursor)
        except Exception as e:
            logger.error(f"Error listing emails: {str(e)}")
            return []
    
    @classmethod
    def count_emails(cls, filter_query: Optional[Dict[str, Any]] = None) -> int:
        """Count emails matching a filter.
        
        Args:
            filter_query (dict): MongoDB query filter
            
        Returns:
            int: The count of matching emails
        """
        collection = cls.get_collection()
        query = filter_query or {}
        
        try:
            return collection.count_documents(query)
        except Exception as e:
            logger.error(f"Error counting emails: {str(e)}")
            return 0
    
    @classmethod
    def get_emails_since(cls, since_datetime: datetime.datetime, unread_only: bool = False) -> List[Dict[str, Any]]:
        """Get emails received since a specific datetime.
        
        Args:
            since_datetime (datetime): The datetime to filter from
            unread_only (bool): If True, only return unread emails
            
        Returns:
            list: A list of email documents
        """
        collection = cls.get_collection()
        query = {"received_at": {"$gte": since_datetime}}
        
        if unread_only:
            query["is_read"] = False
        
        try:
            cursor = collection.find(query).sort("received_at", -1)
            return list(cursor)
        except Exception as e:
            logger.error(f"Error getting emails since {since_datetime}: {str(e)}")
            return []
    
    @classmethod
    def search_emails(cls, search_text: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Search emails by text in subject or body.
        
        Args:
            search_text (str): The text to search for
            limit (int): Maximum number of results to return
            
        Returns:
            list: A list of email documents
        """
        collection = cls.get_collection()
        
        # Create a text search query
        query = {
            "$or": [
                {"subject": {"$regex": search_text, "$options": "i"}},
                {"body": {"$regex": search_text, "$options": "i"}},
                {"body_preview": {"$regex": search_text, "$options": "i"}},
                {"sender": {"$regex": search_text, "$options": "i"}},
                {"sender_name": {"$regex": search_text, "$options": "i"}}
            ]
        }
        
        try:
            cursor = collection.find(query).sort("received_at", -1).limit(limit)
            return list(cursor)
        except Exception as e:
            logger.error(f"Error searching emails: {str(e)}")
            return []
    
    @classmethod
    def get_email_stats(cls) -> Dict[str, Any]:
        """Get statistics about stored emails.
        
        Returns:
            dict: Statistics about the emails collection
        """
        collection = cls.get_collection()
        pipeline = [
            {
                "$facet": {
                    "totalCount": [{"$count": "count"}],
                    "unreadCount": [{"$match": {"is_read": False}}, {"$count": "count"}],
                    "hasAttachmentCount": [{"$match": {"has_attachments": True}}, {"$count": "count"}],
                    "topSenders": [
                        {"$group": {"_id": "$sender", "count": {"$sum": 1}}},
                        {"$sort": {"count": -1}},
                        {"$limit": 5}
                    ],
                    "emailsPerDay": [
                        {
                            "$group": {
                                "_id": {
                                    "$dateToString": {"format": "%Y-%m-%d", "date": "$received_at"}
                                },
                                "count": {"$sum": 1}
                            }
                        },
                        {"$sort": {"_id": -1}},
                        {"$limit": 7}
                    ]
                }
            }
        ]
        
        try:
            result = list(collection.aggregate(pipeline))
            
            if result and len(result) > 0:
                stats = result[0]
                
                # Extract values from nested structures
                total_count = stats["totalCount"][0]["count"] if stats["totalCount"] else 0
                unread_count = stats["unreadCount"][0]["count"] if stats["unreadCount"] else 0
                attachment_count = stats["hasAttachmentCount"][0]["count"] if stats["hasAttachmentCount"] else 0
                
                return {
                    "total_count": total_count,
                    "unread_count": unread_count,
                    "attachment_count": attachment_count,
                    "top_senders": stats["topSenders"],
                    "emails_per_day": stats["emailsPerDay"]
                }
        except Exception as e:
            logger.error(f"Error getting email stats: {str(e)}")
        
        # Return empty stats if no results or error
        return {
            "total_count": 0,
            "unread_count": 0,
            "attachment_count": 0,
            "top_senders": [],
            "emails_per_day": []
        }