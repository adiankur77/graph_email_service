import requests
import datetime
import base64
import time
import logging
from typing import List, Dict, Any, Tuple, Optional, Union
from app.config import get_settings
from app.services.auth import MSGraphAuth
from app.models.email import EmailModel

logger = logging.getLogger(__name__)
settings = get_settings()

class MSGraphEmailService:
    """Service to interact with Microsoft Graph API for emails."""
    
    def __init__(self):
        """Initialize the service with authentication."""
        self.auth = MSGraphAuth()
        self.token = self.auth.get_access_token()
        self.user_email = settings.USER_EMAIL
        self.graph_endpoint = f"{settings.GRAPH_API_ENDPOINT}/{settings.GRAPH_API_VERSION}"
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test the connection to Microsoft Graph API.
        
        Returns:
            tuple: (success (bool), message (str))
        """
        try:
            # Ensure we have a token
            if not self.token:
                self.token = self.auth.get_access_token()
                if not self.token:
                    return False, "Failed to acquire authentication token"
            
            # Test API connection using the /me endpoint
            url = f"{self.graph_endpoint}/users/{self.user_email}"
            response = requests.get(url, headers=self._get_headers())
            
            if response.status_code == 200:
                user_info = response.json()
                return True, f"Connected successfully as {user_info.get('displayName', self.user_email)}"
            else:
                error_message = f"Connection test failed: {response.status_code} - {response.text}"
                logger.error(error_message)
                return False, error_message
                
        except Exception as e:
            error_message = f"Exception during connection test: {str(e)}"
            logger.exception(error_message)
            return False, error_message
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Microsoft Graph API requests.
        
        Returns:
            dict: Headers including authorization token
        """
        if not self.token:
            # Refresh token if it's not available
            self.token = self.auth.get_access_token()
            if not self.token:
                logger.error("Failed to acquire token for Microsoft Graph API")
                
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Prefer': 'outlook.timezone="UTC"'
        }
    
    def send_email(self, 
                  to_recipients: List[str], 
                  subject: str, 
                  body: str, 
                  cc_recipients: Optional[List[str]] = None, 
                  bcc_recipients: Optional[List[str]] = None, 
                  attachments: Optional[List[Dict[str, Any]]] = None) -> Tuple[bool, str]:
        """Send an email using Microsoft Graph API.
        
        Args:
            to_recipients (list): List of recipient email addresses
            subject (str): Email subject
            body (str): Email body content (can be HTML)
            cc_recipients (list, optional): List of CC recipient email addresses
            bcc_recipients (list, optional): List of BCC recipient email addresses
            attachments (list, optional): List of attachment objects
            
        Returns:
            tuple: (success (bool), message (str))
        """
        try:
            # Ensure we have a valid token
            if not self.token:
                self.token = self.auth.get_access_token()
                if not self.token:
                    return False, "Failed to acquire authentication token"
            
            # API endpoint for sending mail
            url = f"{self.graph_endpoint}/users/adityaankur55@outlook.com/sendMail"
            
            # Format recipients
            to_recipients_list = [{"emailAddress": {"address": email}} for email in to_recipients]
            
            cc_recipients_list = []
            if cc_recipients:
                cc_recipients_list = [{"emailAddress": {"address": email}} for email in cc_recipients]
                
            bcc_recipients_list = []
            if bcc_recipients:
                bcc_recipients_list = [{"emailAddress": {"address": email}} for email in bcc_recipients]
            
            # Prepare email message
            email_data = {
                "message": {
                    "subject": subject,
                    "body": {
                        "contentType": "HTML",
                        "content": body
                    },
                    "toRecipients": to_recipients_list,
                    "ccRecipients": cc_recipients_list,
                    "bccRecipients": bcc_recipients_list
                },
                "saveToSentItems": "true"
            }
            
            
            # Log the request (without sensitive data)
            logger.info(f"Sending email to {to_recipients} with subject: {subject}")
            
            # Send the email
            headers = self._get_headers()
            response = requests.post(url, headers=headers, json=email_data)
            
            if response.status_code == 202:  # 202 Accepted
                logger.info(f"Email sent successfully to {to_recipients}")
                return True, "Email sent successfully"
            elif response.status_code == 401:  # Unauthorized - token may have expired
                logger.warning("Token expired, attempting to refresh...")
                self.token = self.auth.get_access_token()  # Get a fresh token
                
                if self.token:
                    # Retry with new token
                    headers = self._get_headers()
                    response = requests.post(url, headers=headers, json=email_data)
                    
                    if response.status_code == 202:  # 202 Accepted
                        logger.info(f"Email sent successfully after token refresh to {to_recipients}")
                        return True, "Email sent successfully"
                
                error_message = f"Failed to send email after token refresh: {response.status_code} - {response.text}"
                logger.error(error_message)
                return False, error_message
            else:
                error_message = f"Failed to send email: {response.status_code} - {response.text}"
                logger.error(error_message)
                
                # Log more details for troubleshooting
                try:
                    response_json = response.json()
                    if 'error' in response_json:
                        error_details = response_json['error']
                        logger.error(f"Error code: {error_details.get('code')}")
                        logger.error(f"Error message: {error_details.get('message')}")
                except Exception:
                    pass
                    
                return False, error_message
                
        except Exception as e:
            error_message = f"Exception sending email: {str(e)}"
            logger.exception(error_message)
            return False, error_message
    
    def retrieve_emails(self, hours_ago: int = 24) -> Tuple[bool, Union[str, List[Dict[str, Any]]]]:
        """Retrieve emails from the past specified hours and store in MongoDB.
        
        Args:
            hours_ago (int): Number of hours to look back
            
        Returns:
            tuple: (success (bool), message (str) or emails (list))
        """
        try:
            # Ensure we have a valid token
            if not self.token:
                self.token = self.auth.get_access_token()
                if not self.token:
                    return False, "Failed to acquire authentication token"
            
            # Calculate the timestamp for hours_ago
            time_filter = datetime.datetime.utcnow() - datetime.timedelta(hours=hours_ago)
            time_filter_str = time_filter.strftime("%Y-%m-%dT%H:%M:%SZ")
            
            # Build query parameters to filter emails by received time
            # Using $filter with receivedDateTime and ordering by receivedDateTime descending
            query_params = {
                "$filter": f"receivedDateTime ge {time_filter_str}",
                "$orderby": "receivedDateTime desc",
                "$top": settings.EMAIL_BATCH_SIZE,  # Limit to configured batch size to avoid timeout
                "$select": "id,subject,bodyPreview,from,toRecipients,ccRecipients,receivedDateTime,hasAttachments,importance,isRead"
            }
            
            # Build URL with query parameters for user's inbox
            #url = f"{self.graph_endpoint}/users/{self.user_email}/mailFolders/inbox/messages"
            
            url = f"{self.graph_endpoint}/users/04005212-8484-428c-a47b-133d8099a915/mailFolders/inbox/messages"
            
            logger.info(f"Retrieving emails since {time_filter_str} for {self.user_email}")
            
            all_emails = []
            next_link = None
            
            # Make initial request
            headers = self._get_headers()
            response = requests.get(url, headers=headers)
            
            if response.status_code == 401:  # Token expired
                logger.warning("Token expired during email retrieval, refreshing...")
                self.token = self.auth.get_access_token()
                if not self.token:
                    return False, "Failed to refresh authentication token"
                headers = self._get_headers()
                response = requests.get(url, headers=headers, params=query_params)
            
            if response.status_code != 200:
                error_message = f"Failed to retrieve emails: {response.status_code} - {response.text}"
                logger.error(error_message)
                return False, error_message
            
            # Process initial response
            response_data = response.json()
            emails_data = response_data.get('value', [])
            next_link = response_data.get('@odata.nextLink')
            
            # Process initial batch of emails
            processed_emails = self._process_emails(emails_data)
            all_emails.extend(processed_emails)
            
            # Handle pagination if more emails are available
            while next_link:
                logger.info(f"Retrieving next page of emails with link: {next_link}")
                response = requests.get(next_link, headers=headers)
                
                if response.status_code != 200:
                    logger.error(f"Failed to retrieve next page: {response.status_code} - {response.text}")
                    break
                
                response_data = response.json()
                emails_data = response_data.get('value', [])
                next_link = response_data.get('@odata.nextLink')
                
                # Process next batch of emails
                processed_emails = self._process_emails(emails_data)
                all_emails.extend(processed_emails)
                
                # Avoid hitting rate limits
                time.sleep(1)
            
            logger.info(f"Retrieved and processed a total of {len(all_emails)} emails")
            return True, all_emails
                
        except Exception as e:
            error_message = f"Exception retrieving emails: {str(e)}"
            logger.exception(error_message)
            return False, error_message
    
    def _process_emails(self, emails_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process a batch of emails and store in MongoDB.
        
        Args:
            emails_data (list): List of email data from Microsoft Graph API
            
        Returns:
            list: Processed email documents
        """
        processed_emails = []
        
        for email in emails_data:
            try:
                # Process each email and prepare for MongoDB storage
                email_doc = {
                    "message_id": email.get('id'),
                    "subject": email.get('subject', ''),
                    "body_preview": email.get('bodyPreview', ''),
                    "sender": email.get('from', {}).get('emailAddress', {}).get('address', '') if email.get('from') else '',
                    "sender_name": email.get('from', {}).get('emailAddress', {}).get('name', '') if email.get('from') else '',
                    "recipients": [r.get('emailAddress', {}).get('address', '') for r in email.get('toRecipients', [])],
                    "cc_recipients": [r.get('emailAddress', {}).get('address', '') for r in email.get('ccRecipients', [])],
                    "received_at": datetime.datetime.strptime(email.get('receivedDateTime', ''), "%Y-%m-%dT%H:%M:%SZ") 
                               if email.get('receivedDateTime') else datetime.datetime.utcnow(),
                    "has_attachments": email.get('hasAttachments', False),
                    "importance": email.get('importance', 'normal'),
                    "is_read": email.get('isRead', False),
                    "processed_at": datetime.datetime.utcnow()
                }
                
                # Check if we need to get the full email body
                if self._should_fetch_body(email):
                    email_detail = self.get_email_detail(email.get('id'))
                    if email_detail:
                        email_doc["body"] = email_detail.get('body', {}).get('content', '')
                        email_doc["body_type"] = email_detail.get('body', {}).get('contentType', 'text')
                
                # Check if we need to get attachments and we're configured to retrieve them
                if email.get('hasAttachments', False) and settings.EMAIL_RETRIEVE_ATTACHMENTS:
                    attachment_info = self.get_attachments(email.get('id'))
                    if attachment_info:
                        email_doc["attachment_info"] = []
                        for attachment in attachment_info:
                            email_doc["attachment_info"].append({
                                "id": attachment.get('id', ''),
                                "name": attachment.get('name', ''),
                                "content_type": attachment.get('contentType', ''),
                                "size": attachment.get('size', 0),
                                "is_inline": attachment.get('isInline', False)
                            })
                
                # Store email in MongoDB if it doesn't already exist
                existing_email = EmailModel.get_by_message_id(email.get('id'))
                if not existing_email:
                    # New email
                    logger.info(f"Storing new email: '{email_doc['subject']}' from {email_doc['sender']}")
                    EmailModel.create(email_doc)
                    processed_emails.append(email_doc)
                else:
                    # Email already exists - update if needed
                    if email_doc.get("is_read") != existing_email.get("is_read"):
                        # Update read status if changed
                        logger.debug(f"Updating read status for email: {email_doc['message_id']}")
                        EmailModel.update_read_status(email_doc['message_id'], email_doc["is_read"])
            except Exception as e:
                # Log the error but continue processing other emails
                logger.error(f"Error processing email {email.get('id', 'unknown')}: {str(e)}")
        
        return processed_emails
        
    def _should_fetch_body(self, email: Dict[str, Any]) -> bool:
        """Determine if we should fetch the full email body.
        
        Args:
            email (dict): Email data from Microsoft Graph API
            
        Returns:
            bool: True if we should fetch the body, False otherwise
        """
        # If EMAIL_RETRIEVE_BODY is False, don't fetch any bodies
        if not settings.EMAIL_RETRIEVE_BODY:
            return False
            
        # Implement logic to decide which emails need full body retrieval
        # For example, fetch body for unread emails or important emails
        is_important = email.get('importance') == 'high'
        is_unread = not email.get('isRead', True)
        has_short_preview = len(email.get('bodyPreview', '')) < 50
        
        # Get full body for important or unread emails with short preview
        return is_important or (is_unread and has_short_preview)
    
    def get_email_detail(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed email content by message ID.
        
        Args:
            message_id (str): The Microsoft Graph message ID
            
        Returns:
            dict or None: The detailed email data or None if failed
        """
        try:
            url = f"{self.graph_endpoint}/users/{self.user_email}/messages/{message_id}"
            response = requests.get(url, headers=self._get_headers())
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get email detail: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.exception(f"Exception getting email detail: {str(e)}")
            return None
    
    def get_attachments(self, message_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get attachments for a specific email.
        
        Args:
            message_id (str): The Microsoft Graph message ID
            
        Returns:
            list or None: List of attachments or None if failed
        """
        try:
            url = f"{self.graph_endpoint}/users/{self.user_email}/messages/{message_id}/attachments"
            response = requests.get(url, headers=self._get_headers())
            
            if response.status_code == 200:
                return response.json().get('value', [])
            else:
                logger.error(f"Failed to get attachments: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.exception(f"Exception getting attachments: {str(e)}")
            return None
    
    def get_attachment_content(self, message_id: str, attachment_id: str) -> Optional[Dict[str, Any]]:
        """Get the content of a specific attachment.
        
        Args:
            message_id (str): The Microsoft Graph message ID
            attachment_id (str): The attachment ID
            
        Returns:
            dict or None: The attachment data or None if failed
        """
        try:
            url = f"{self.graph_endpoint}/users/{self.user_email}/messages/{message_id}/attachments/{attachment_id}"
            response = requests.get(url, headers=self._get_headers())
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get attachment content: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.exception(f"Exception getting attachment content: {str(e)}")
            return None
