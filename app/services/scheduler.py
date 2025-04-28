import logging
import datetime
from typing import Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.services.email_service import MSGraphEmailService
from app.models.email import EmailModel
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

def retrieve_emails_job():
    """Job to retrieve emails from Microsoft Graph API."""
    try:
        job_start_time = datetime.datetime.utcnow()
        logger.info(f"Running email retrieval job at {job_start_time.isoformat()}")
        
        # Initialize the email service
        email_service = MSGraphEmailService()
        
        # Get hours from settings
        hours_to_retrieve = settings.EMAIL_FETCH_HOURS
        
        # Retrieve emails
        success, result = email_service.retrieve_emails(hours_ago=hours_to_retrieve)
        
        if success:
            email_count = len(result) if isinstance(result, list) else 0
            logger.info(f"Successfully retrieved {email_count} emails")
            
            # Get email stats
            try:
                stats = EmailModel.get_email_stats()
                logger.info(f"Email stats: {stats['total_count']} total, {stats['unread_count']} unread, "
                           f"{stats['attachment_count']} with attachments")
            except Exception as stats_e:
                logger.error(f"Error getting email stats: {str(stats_e)}")
        else:
            logger.error(f"Failed to retrieve emails: {result}")
            
        # Calculate job duration
        job_duration = (datetime.datetime.utcnow() - job_start_time).total_seconds()
        logger.info(f"Email retrieval job completed in {job_duration:.2f} seconds")
            
    except Exception as e:
        logger.exception(f"Exception in email retrieval job: {str(e)}")

class EmailScheduler:
    """Scheduler for email-related tasks."""
    
    def __init__(self):
        """Initialize the scheduler."""
        self.scheduler = None
    
    def start(self) -> Optional[BackgroundScheduler]:
        """Start the background scheduler for periodic tasks.
        
        Returns:
            Optional[BackgroundScheduler]: The scheduler instance or None if failed
        """
        try:
            logger.info("Starting the email scheduler...")
            
            # Create a scheduler instance
            self.scheduler = BackgroundScheduler()
            
            # Get the interval from settings
            interval_minutes = settings.EMAIL_FETCH_INTERVAL_MINUTES
            
            # Add the email retrieval job with the specified interval
            self.scheduler.add_job(
                retrieve_emails_job,
                trigger=IntervalTrigger(minutes=interval_minutes),
                id='retrieve_emails_job',
                name='Retrieve Emails Job',
                replace_existing=True,
                max_instances=1,  # Ensure only one instance runs at a time
                misfire_grace_time=15*60  # Allow job to be delayed up to 15 minutes if scheduler is busy
            )
            
            # Also run the job immediately on startup with a slight delay
            self.scheduler.add_job(
                retrieve_emails_job,
                id='retrieve_emails_startup_job',
                name='Retrieve Emails Startup Job',
                next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=15)  # Slight delay to ensure app is fully started
            )
            
            # Start the scheduler
            self.scheduler.start()
            logger.info(f"Email scheduler started. Will run every {interval_minutes} minutes.")
            
            return self.scheduler
            
        except Exception as e:
            logger.exception(f"Failed to start scheduler: {str(e)}")
            return None
    
    def shutdown(self):
        """Shutdown the scheduler."""
        if self.scheduler:
            try:
                self.scheduler.shutdown()
                logger.info("Email scheduler shutdown.")
            except Exception as e:
                logger.exception(f"Error shutting down scheduler: {str(e)}")

# Global scheduler instance
scheduler_instance = None

def get_scheduler() -> EmailScheduler:
    """Get or create the email scheduler instance."""
    global scheduler_instance
    if scheduler_instance is None:
        scheduler_instance = EmailScheduler()
    return scheduler_instance