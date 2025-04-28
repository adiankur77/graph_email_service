from fastapi import APIRouter, Depends, HTTPException
import datetime
from app.services.email_service import MSGraphEmailService
from app.schemas.email import ApiResponse

router = APIRouter(
    prefix="/health",
    tags=["health"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=ApiResponse)
async def health_check():
    """Simple health check endpoint."""
    return {
        "status": "OK",
        "message": "Service is running",
        "data": {
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
    }

@router.get("/graph", response_model=ApiResponse)
async def test_graph_connection():
    """Test the connection to Microsoft Graph API."""
    # Initialize the email service
    email_service = MSGraphEmailService()
    
    # Test the connection
    success, message = email_service.test_connection()
    
    if success:
        return {
            "status": "OK",
            "message": message,
            "data": {
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
        }
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Connection to Microsoft Graph API failed: {message}"
        )