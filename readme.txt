Microsoft Graph Email Service
A FastAPI-based service that integrates with Microsoft Graph API to send and retrieve emails, storing them in MongoDB.


### Features

Send Emails: Send emails via Microsoft Graph API
Retrieve Emails: Automatically fetch emails from Microsoft Graph API and store in MongoDB
Scheduled Retrieval: Configurable scheduler for periodic email retrieval

Technology Stack

FastAPI: Modern, high-performance web framework for building APIs
MongoDB: NoSQL database for storing email data
APScheduler: Advanced Python scheduler for periodic tasks
MSAL: Microsoft Authentication Library for OAuth2 authentication
Pydantic: Data validation and settings management
Uvicorn: ASGI server implementation
            

# Project documentation
Setup
Prerequisites

Python 3.8+
MongoDB
Microsoft Azure account

Register Microsoft Application

Sign in to the Azure Portal
Navigate to "Azure Active Directory" > "App registrations" > "New registration"
Provide a name for your application (e.g., "Email Service")
Set the redirect URI to http://localhost:8000/callback
Note the "Application (client) ID" and "Directory (tenant) ID"
Create a client secret under "Certificates & secrets"
Under "API permissions", add these Microsoft Graph API permissions:

Mail.Read
Mail.Send
Mail.ReadBasic


Grant admin consent for these permissions

Environment Setup

Clone the repository:
git clone <repository-url>
cd graph_email_service

Create a virtual environment:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

Install dependencies:
pip install -r requirements.txt

Create .env file from template:
cp .env.template .env

Update the .env file with your Microsoft Graph API credentials and MongoDB settings

Running the Application
Local Development
bash uvicorn app.main:app --reload
The API will be available at http://localhost:8000
Docker
bashdocker-compose up -d
API Documentation
Once the application is running, you can access the API documentation:

Swagger UI: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc

Main Endpoints

POST /email/send: Send an email
GET /email/retrieve: Retrieve emails from Microsoft Graph API
GET /email/list: List emails from the database with filtering

Configuration Options
All configuration options are set in the .env file. Key settings include:

EMAIL_FETCH_INTERVAL_MINUTES: How often to fetch emails (default: 60)
EMAIL_FETCH_HOURS: How far back to look for emails (default: 24)
EMAIL_BATCH_SIZE: Number of emails to process per batch (default: 50)
EMAIL_RETRIEVE_ATTACHMENTS: Whether to retrieve attachment metadata (default: True)
EMAIL_RETRIEVE_BODY: Whether to retrieve full email body (default: True)

# Microsoft Graph API credentials (use environment variables to store them)
export TENANT_ID='YOUR_TENANT_ID'
export CLIENT_ID='YOUR_CLIENT_ID'
export CLIENT_SECRET='YOUR_CLIENt_SECRET'
export USER_EMAIL='YOUR_EMAIL_ID'

# The redirect URI registered in your Azure app
REDIRECT_URI=http://localhost:8000/callback


Examples
Sending an Email

import requests
import json

url = "http://localhost:8000/email/send"
payload = {
    "to": ["recipient@example.com"],
    "subject": "Test Email",
    "body": "<p>This is a test email from Microsoft Graph API.</p>",
    "cc": [],
    "bcc": [],
    "attachments": []
}
headers = {"Content-Type": "application/json"}

response = requests.post(url, json=payload, headers=headers)
print(response.json())
Retrieving Emails
pythonimport requests

url = "http://localhost:8000/email/retrieve"
params = {"hours_ago": 24, "force_refresh": True}

response = requests.get(url, params=params)
print(f"Retrieved {len(response.json()['emails'])} emails")


## Use of AI
1. AI was used for generating the structure of the code for FAST API python framework.
2. AI was used to learn more about Microsoft Authentication Library.
3. AI was used to learn more about Microsoft Graph API and what parameters to use.
4. AI was used to setup app and app permissions in Entra Microsoft ID.
