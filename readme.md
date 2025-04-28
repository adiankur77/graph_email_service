Microsoft Graph Email Service
A FastAPI-based service that integrates with Microsoft Graph API to send and retrieve emails, storing them in MongoDB.
Features

Send Emails: Send emails via Microsoft Graph API with support for attachments
Retrieve Emails: Automatically fetch emails from Microsoft Graph API and store in MongoDB
Scheduled Retrieval: Configurable scheduler for periodic email retrieval
Search & Filter: Search and filter emails by various criteria
Statistics: Get email statistics such as counts and top senders
Attachments: Retrieve attachment metadata and content

Technology Stack

FastAPI: Modern, high-performance web framework for building APIs
MongoDB: NoSQL database for storing email data
Motor: Asynchronous MongoDB driver for Python and asyncio
APScheduler: Advanced Python scheduler for periodic tasks
MSAL: Microsoft Authentication Library for OAuth2 authentication
Pydantic: Data validation and settings management
Uvicorn: ASGI server implementation

Project Structure
graph_email_service/
│
├── app/                           # Main application package
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry point
│   ├── config.py                  # Configuration settings
│   ├── database.py                # MongoDB connection
│   │
│   ├── api/                       # API routes
│   │   ├── __init__.py
│   │   ├── email.py               # Email routes
│   │   └── health.py              # Health check routes
│   │
│   ├── models/                    # Data models
│   │   ├── __init__.py
│   │   └── email.py               # Email models
│   │
│   ├── services/                  # Business logic
│   │   ├── __init__.py
│   │   ├── auth.py                # Authentication with Microsoft Graph
│   │   ├── email_service.py       # Email service
│   │   └── scheduler.py           # Scheduler service
│   │
│   ├── schemas/                   # Pydantic schemas
│   │   ├── __init__.py
│   │   └── email.py               # Email schemas
│   │
│   └── utils/                     # Utility functions
│       ├── __init__.py
│       └── helpers.py             # Helper functions
│
├── tests/                         # Test modules
├── scripts/                       # Scripts for utility tasks
├── .env                           # Environment variables (not in repo)
├── .env.template                  # Environment variables template
├── requirements.txt               # Project dependencies
├── Dockerfile                     # Docker configuration
├── docker-compose.yml             # Docker compose configuration
└── README.md                      # Project documentation
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
bashuvicorn app.main:app --reload
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
GET /email/search: Search emails by content
GET /email/stats: Get email statistics
GET /email/{email_id}: Get a specific email by ID
GET /email/{email_id}/attachment/{attachment_id}: Get attachment content

Testing
Run the tests with pytest:
bashpytest
Configuration Options
All configuration options are set in the .env file. Key settings include:

EMAIL_FETCH_INTERVAL_MINUTES: How often to fetch emails (default: 60)
EMAIL_FETCH_HOURS: How far back to look for emails (default: 24)
EMAIL_BATCH_SIZE: Number of emails to process per batch (default: 50)
EMAIL_RETRIEVE_ATTACHMENTS: Whether to retrieve attachment metadata (default: True)
EMAIL_RETRIEVE_BODY: Whether to retrieve full email body (default: True)

Examples
Sending an Email
pythonimport requests
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
Searching Emails
pythonimport requests

url = "http://localhost:8000/email/search"
params = {"q": "important", "limit": 10}

response = requests.get(url, params=params)
print(f"Found {len(response.json()['emails'])} matching emails")