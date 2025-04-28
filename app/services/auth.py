import msal
import requests
import time
import logging
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class MSGraphAuth:
    """Microsoft Graph API authentication utility."""
    
    def __init__(self):
        """Initialize with settings."""
        self.client_id = settings.CLIENT_ID
        self.client_secret = settings.CLIENT_SECRET
        self.authority = settings.AUTHORITY
        self.scope = settings.SCOPE
        self.token_cache = {}  # Simple cache to avoid frequent token requests
    
    def get_access_token(self):
        """Acquire an access token for Microsoft Graph API using client credentials flow.
        
        Returns:
            str or None: The access token if successful, None otherwise.
        """
        # Check if we have a cached token that's still valid
        current_time = time.time()
        if self.token_cache and self.token_cache.get('expires_at', 0) > current_time:
            return self.token_cache.get('access_token')
        
        try:
            # Create a confidential client application
            app = msal.ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=self.authority
            )
            
            # Acquire token for the application
            result = app.acquire_token_for_client(scopes=self.scope)
            # result = app.acquire_token_silent(scopes=self.scope, account=None)

            
            if "access_token" in result:
                logger.info(result['access_token'])
                # Cache the token with expiration time
                self.token_cache = {
                    'access_token': result['access_token'],
                    'expires_at': current_time + result.get('expires_in', 3600) - 300  # Buffer of 5 minutes
                }
                return result["access_token"]
            else:
                error_message = f"Error acquiring token: {result.get('error')}"
                error_description = f"Error description: {result.get('error_description')}"
                logger.error(error_message)
                logger.error(error_description)
                return None
                
        except Exception as e:
            logger.exception(f"Exception during token acquisition: {str(e)}")
            return None