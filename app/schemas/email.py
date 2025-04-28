from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import base64

class Attachment(BaseModel):
    """Schema for email attachments."""
    name: str
    content: str  # Base64 encoded content

    @validator('content')
    def validate_base64(cls, v):
        try:
            base64.b64decode(v)
            return v
        except Exception:
            raise ValueError('Invalid base64 content')

class AttachmentInfo(BaseModel):
    """Schema for attachment metadata."""
    id: str
    name: str
    content_type: str
    size: int
    is_inline: bool

class SendEmailRequest(BaseModel):
    """Schema for sending emails."""
    to: List[EmailStr]
    subject: str
    body: str
    cc: Optional[List[EmailStr]] = Field(default_factory=list)
    bcc: Optional[List[EmailStr]] = Field(default_factory=list)
    attachments: Optional[List[Attachment]] = Field(default_factory=list)

class EmailResponse(BaseModel):
    """Schema for email response."""
    message_id: str
    subject: str
    body_preview: str
    sender: str
    sender_name: Optional[str] = None
    recipients: List[str]
    cc_recipients: List[str] = Field(default_factory=list)
    received_at: datetime
    has_attachments: bool
    is_read: Optional[bool] = True
    importance: Optional[str] = "normal"
    body: Optional[str] = None
    body_type: Optional[str] = None
    attachment_info: Optional[List[AttachmentInfo]] = None
    processed_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class RetrieveEmailsRequest(BaseModel):
    """Schema for retrieving emails."""
    hours_ago: Optional[int] = 24
    force_refresh: Optional[bool] = False
    unread_only: Optional[bool] = False

class EmailFilterRequest(BaseModel):
    """Schema for filtering emails."""
    limit: Optional[int] = 20
    skip: Optional[int] = 0
    sort_by: Optional[str] = "received_at"
    sort_order: Optional[int] = -1
    unread_only: Optional[bool] = False
    has_attachments: Optional[bool] = None
    sender: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

class EmailSearchRequest(BaseModel):
    """Schema for searching emails."""
    q: str
    limit: Optional[int] = 20

class EmailStats(BaseModel):
    """Schema for email statistics."""
    total_count: int
    unread_count: int
    attachment_count: int
    top_senders: List[Dict[str, Any]]
    emails_per_day: List[Dict[str, Any]]

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class ApiResponse(BaseModel):
    """Generic API response schema."""
    status: str
    message: str
    data: Optional[Any] = None

class EmailListResponse(BaseModel):
    """Schema for listing emails response."""
    count: int
    total: int
    skip: int
    limit: int
    emails: List[EmailResponse]

class EmailSearchResponse(BaseModel):
    """Schema for search results."""
    count: int
    emails: List[EmailResponse]

class RetrieveEmailsResponse(BaseModel):
    """Schema for email retrieval response."""
    message: str
    emails: List[EmailResponse]