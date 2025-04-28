from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from typing import List, Optional, Dict, Any
import base64
import datetime
import logging
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_async_database
from app.services.email_service import MSGraphEmailService
from app.models.email import EmailModel
from app.schemas.email import (
    SendEmailRequest, 
    EmailResponse, 
    ApiResponse,
    RetrieveEmailsRequest,
    EmailFilterRequest,
    EmailSearchRequest,
    EmailListResponse,
    EmailSearchResponse,
    RetrieveEmailsResponse,
    EmailStats
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/email",
    tags=["email"],
    responses={404: {"description": "Not found"}},
)

@router.post("/send", response_model=ApiResponse)
async def send_email(
    request: SendEmailRequest,
    background_tasks: BackgroundTasks
):
    """Send an email using the Microsoft Graph API."""
    try:
        # Initialize the email service
        email_service = MSGraphEmailService()
        
        # Process attachments if any
        processed_attachments = []
        for attachment in request.attachments:
            try:
                # For API requests, content should already be base64 encoded
                processed_attachments.append({
                    "name": attachment.name,
                    "content": base64.b64decode(attachment.content)
                })
            except Exception as e:
                logger.error(f"Error processing attachment: {str(e)}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid attachment format: {str(e)}"
                )
        
        # Send the email
        success, message = email_service.send_email(
            to_recipients=request.to,
            subject=request.subject,
            body=request.body,
            cc_recipients=request.cc,
            bcc_recipients=request.bcc,
            attachments=processed_attachments if request.attachments else None
        )
        
        if success:
            return {
                "status": "success",
                "message": message,
                "data": None
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=message
            )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error sending email: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error sending email: {str(e)}"
        )

@router.get("/retrieve", response_model=RetrieveEmailsResponse)
async def retrieve_emails(
    background_tasks: BackgroundTasks,
    hours_ago: int = Query(24, gt=0, le=168),
    force_refresh: bool = Query(False),
    unread_only: bool = Query(False)
):
    """Retrieve emails from the past specified hours."""
    try:
        if force_refresh:
            # Force a new fetch from Microsoft Graph API
            email_service = MSGraphEmailService()
            success, result = email_service.retrieve_emails(hours_ago=hours_ago)
            
            if success:
                # If result is a list of emails, return them
                return {
                    "message": f"Retrieved {len(result)} emails",
                    "emails": result
                }
            else:
                # If result is an error message
                raise HTTPException(
                    status_code=500,
                    detail=result
                )
        else:
            # Retrieve from MongoDB
            since_time = datetime.datetime.utcnow() - datetime.timedelta(hours=hours_ago)
            emails = EmailModel.get_emails_since(since_time, unread_only=unread_only)
            
            return {
                "message": f"Retrieved {len(emails)} emails from database",
                "emails": emails
            }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error retrieving emails: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving emails: {str(e)}"
        )

@router.get("/list", response_model=EmailListResponse)
async def list_emails(
    limit: int = Query(20, gt=0, le=100),
    skip: int = Query(0, ge=0),
    sort_by: str = Query("received_at"),
    sort_order: int = Query(-1),
    unread_only: bool = Query(False),
    has_attachments: Optional[bool] = None,
    sender: Optional[str] = None,
    date_from: Optional[datetime.date] = None,
    date_to: Optional[datetime.date] = None
):
    """List stored emails with pagination and filtering."""
    try:
        # Build filter query
        filter_query = {}
        
        if unread_only:
            filter_query['is_read'] = False
            
        if has_attachments is not None:
            filter_query['has_attachments'] = has_attachments
            
        if sender:
            filter_query['sender'] = {'$regex': sender, '$options': 'i'}
            
        if date_from or date_to:
            date_filter = {}
            
            if date_from:
                # Convert date to datetime at the start of the day
                from_datetime = datetime.datetime.combine(date_from, datetime.time.min)
                date_filter['$gte'] = from_datetime
                    
            if date_to:
                # Convert date to datetime at the end of the day
                to_datetime = datetime.datetime.combine(date_to, datetime.time.max)
                date_filter['$lte'] = to_datetime
                    
            if date_filter:
                filter_query['received_at'] = date_filter
        
        # List emails from MongoDB with filtering
        emails = EmailModel.list_emails(
            limit=limit, 
            skip=skip, 
            sort_by=sort_by, 
            sort_order=sort_order,
            filter_query=filter_query
        )
        
        # Get total count with the same filters (for pagination)
        total_count = EmailModel.count_emails(filter_query=filter_query)
        
        return {
            "count": len(emails), 
            "total": total_count,
            "skip": skip,
            "limit": limit,
            "emails": emails
        }
    except Exception as e:
        logger.exception(f"Error listing emails: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing emails: {str(e)}"
        )

@router.get("/search", response_model=EmailSearchResponse)
async def search_emails(
    q: str = Query(..., min_length=2),
    limit: int = Query(20, gt=0, le=100)
):
    """Search emails by text content."""
    try:
        if not q:
            raise HTTPException(
                status_code=400,
                detail="Search query is required"
            )
        
        # Search emails
        emails = EmailModel.search_emails(q, limit=limit)
        
        return {
            "count": len(emails), 
            "emails": emails
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error searching emails: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error searching emails: {str(e)}"
        )

@router.get("/stats", response_model=EmailStats)
async def email_stats():
    """Get email statistics."""
    try:
        # Get email statistics
        stats = EmailModel.get_email_stats()
        
        return stats
    except Exception as e:
        logger.exception(f"Error getting email stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting email stats: {str(e)}"
        )

@router.get("/{email_id}", response_model=EmailResponse)
async def email_detail(email_id: str):
    """Get a single email by its Microsoft Graph message ID."""
    try:
        # Get the email from MongoDB
        email = EmailModel.get_by_message_id(email_id)
        
        if email:
            return email
        else:
            raise HTTPException(
                status_code=404,
                detail="Email not found"
            )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error retrieving email: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving email: {str(e)}"
        )

@router.get("/{email_id}/attachment/{attachment_id}")
async def get_attachment(email_id: str, attachment_id: str):
    """Get the content of a specific attachment."""
    try:
        # Initialize the email service
        email_service = MSGraphEmailService()
        
        # Get attachment content
        attachment = email_service.get_attachment_content(email_id, attachment_id)
        
        if attachment:
            # Return file data with proper content type
            content_type = attachment.get('contentType', 'application/octet-stream')
            file_name = attachment.get('name', 'attachment')
            content_bytes = base64.b64decode(attachment.get('contentBytes', ''))
            
            return {
                "status": "success",
                "message": "Attachment retrieved successfully",
                "data": {
                    "name": file_name,
                    "content_type": content_type,
                    "size": len(content_bytes),
                    "content": attachment.get('contentBytes', '')  # Return base64 content
                }
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Attachment not found"
            )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error retrieving attachment: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving attachment: {str(e)}"
        )