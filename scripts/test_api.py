#!/usr/bin/env python
"""
Test script for the Microsoft Graph Email Service API.

This script tests various API endpoints to ensure they are functioning correctly.
"""

import requests
import json
import time
import base64
from datetime import datetime
import argparse
from typing import Dict, Any, List, Optional

def test_health_check(base_url: str) -> bool:
    """Test the health check endpoint."""
    print("\n=== Testing Health Check ===")
    
    try:
        response = requests.get(f"{base_url}/health")
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Exception: {str(e)}")
        return False

def test_graph_connection(base_url: str) -> bool:
    """Test the Microsoft Graph API connection."""
    print("\n=== Testing Graph API Connection ===")
    
    try:
        response = requests.get(f"{base_url}/health/graph")
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Exception: {str(e)}")
        return False

def test_send_email(base_url: str, recipient: str) -> bool:
    """Test sending an email."""
    print(f"\n=== Testing Send Email to {recipient} ===")
    
    try:
        url = f"{base_url}/email/send"
        payload = {
            "to": [recipient],
            "subject": f"Test Email - {datetime.now().isoformat()}",
            "body": f"<h1>Test Email</h1><p>This is a test email sent at {datetime.now().isoformat()} from the Microsoft Graph Email Service API.</p>",
            "cc": [],
            "bcc": [],
            "attachments": []
        }
        
        # Create a simple text attachment
        attachment_content = "This is a test attachment.\nLine 2\nLine 3"
        encoded_content = base64.b64encode(attachment_content.encode()).decode()
        
        payload["attachments"] = [
            {
                "name": "test_attachment.txt",
                "content": encoded_content
            }
        ]
        
        headers = {"Content-Type": "application/json"}
        
        print("Sending email...")
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Exception: {str(e)}")
        return False

def test_retrieve_emails(base_url: str, force_refresh: bool = True) -> Optional[List[Dict[str, Any]]]:
    """Test retrieving emails."""
    print("\n=== Testing Retrieve Emails ===")
    print(f"Force refresh: {force_refresh}")
    
    try:
        url = f"{base_url}/email/retrieve"
        params = {
            "hours_ago": 24,
            "force_refresh": str(force_refresh).lower(),
            "unread_only": "false"
        }
        
        print("Retrieving emails...")
        start_time = time.time()
        response = requests.get(url, params=params)
        elapsed_time = time.time() - start_time
        
        print(f"Status Code: {response.status_code}")
        print(f"Request took {elapsed_time:.2f} seconds")
        
        if response.status_code == 200:
            data = response.json()
            emails = data.get("emails", [])
            print(f"Retrieved {len(emails)} emails")
            
            if len(emails) > 0:
                # Print sample email information
                sample_email = emails[0]
                print("\nSample Email:")
                print(f"  Subject: {sample_email.get('subject', 'N/A')}")
                print(f"  From: {sample_email.get('sender_name', 'N/A')} <{sample_email.get('sender', 'N/A')}>")
                print(f"  Received: {sample_email.get('received_at', 'N/A')}")
                print(f"  Has Attachments: {sample_email.get('has_attachments', False)}")
            
            return emails
        else:
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"Exception: {str(e)}")
        return None

def test_list_emails(base_url: str, limit: int = 5) -> Optional[List[Dict[str, Any]]]:
    """Test listing emails with filtering."""
    print("\n=== Testing List Emails ===")
    
    try:
        url = f"{base_url}/email/list"
        params = {
            "limit": limit,
            "skip": 0,
            "sort_by": "received_at",
            "sort_order": -1
        }
        
        print(f"Listing up to {limit} emails...")
        response = requests.get(url, params=params)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            emails = data.get("emails", [])
            total = data.get("total", 0)
            print(f"Retrieved {len(emails)} of {total} total emails")
            
            return emails
        else:
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"Exception: {str(e)}")
        return None

def test_email_search(base_url: str, query: str) -> Optional[List[Dict[str, Any]]]:
    """Test searching emails."""
    print(f"\n=== Testing Email Search for '{query}' ===")
    
    try:
        url = f"{base_url}/email/search"
        params = {
            "q": query,
            "limit": 10
        }
        
        print(f"Searching emails for '{query}'...")
        response = requests.get(url, params=params)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            emails = data.get("emails", [])
            print(f"Found {len(emails)} matching emails")
            
            return emails
        else:
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"Exception: {str(e)}")
        return None

def test_email_stats(base_url: str) -> Optional[Dict[str, Any]]:
    """Test getting email statistics."""
    print("\n=== Testing Email Statistics ===")
    
    try:
        url = f"{base_url}/email/stats"
        
        print("Getting email statistics...")
        response = requests.get(url)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            stats = response.json()
            
            print(f"Total emails: {stats.get('total_count', 0)}")
            print(f"Unread emails: {stats.get('unread_count', 0)}")
            print(f"Emails with attachments: {stats.get('attachment_count', 0)}")
            
            # Show top senders
            top_senders = stats.get('top_senders', [])
            if top_senders:
                print("\nTop senders:")
                for sender in top_senders:
                    print(f"  {sender.get('_id', 'Unknown')}: {sender.get('count', 0)}")
            
            return stats
        else:
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"Exception: {str(e)}")
        return None

def test_email_detail(base_url: str, email_id: str) -> Optional[Dict[str, Any]]:
    """Test getting email details."""
    print(f"\n=== Testing Email Detail for ID: {email_id} ===")
    
    try:
        url = f"{base_url}/email/{email_id}"
        
        print("Getting email details...")
        response = requests.get(url)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            email = response.json()
            
            print(f"Subject: {email.get('subject', 'N/A')}")
            print(f"From: {email.get('sender_name', 'N/A')} <{email.get('sender', 'N/A')}>")
            print(f"Received: {email.get('received_at', 'N/A')}")
            print(f"Has Attachments: {email.get('has_attachments', False)}")
            
            # Print body preview
            body_preview = email.get('body_preview', '')
            if body_preview:
                print(f"\nBody Preview: {body_preview[:100]}...")
            
            return email
        else:
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"Exception: {str(e)}")
        return None

def main():
    """Main function to run tests."""
    parser = argparse.ArgumentParser(description='Test the Microsoft Graph Email Service API')
    parser.add_argument('--base-url', default='http://localhost:8000/api', help='Base URL of the API')
    parser.add_argument('--recipient', default='test@example.com', help='Email recipient for send test')
    parser.add_argument('--search-query', default='test', help='Search query for email search test')
    parser.add_argument('--email-id', help='Email ID for detail test')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    parser.add_argument('--health', action='store_true', help='Run health check test')
    parser.add_argument('--connection', action='store_true', help='Run Graph API connection test')
    parser.add_argument('--send', action='store_true', help='Run send email test')
    parser.add_argument('--retrieve', action='store_true', help='Run retrieve emails test')
    parser.add_argument('--list', action='store_true', help='Run list emails test')
    parser.add_argument('--search', action='store_true', help='Run email search test')
    parser.add_argument('--stats', action='store_true', help='Run email stats test')
    parser.add_argument('--detail', action='store_true', help='Run email detail test')
    
    args = parser.parse_args()
    
    # If no specific tests are selected, default to all
    if not (args.all or args.health or args.connection or args.send or 
            args.retrieve or args.list or args.search or args.stats or args.detail):
        args.all = True
    
    print(f"Testing API at {args.base_url}")
    
    # Track overall success
    all_tests_passed = True
    
    # Run health check test
    if args.all or args.health:
        success = test_health_check(args.base_url)
        all_tests_passed = all_tests_passed and success
    
    # Run connection test
    if args.all or args.connection:
        success = test_graph_connection(args.base_url)
        all_tests_passed = all_tests_passed and success
    
    # Run send email test
    if args.all or args.send:
        success = test_send_email(args.base_url, args.recipient)
        all_tests_passed = all_tests_passed and success
    
    # Run retrieve emails test
    if args.all or args.retrieve:
        emails = test_retrieve_emails(args.base_url)
        success = emails is not None
        all_tests_passed = all_tests_passed and success
        
        # Save first email ID for detail test
        if success and emails and not args.email_id:
            args.email_id = emails[0].get('message_id')
    
    # Run list emails test
    if args.all or args.list:
        success = test_list_emails(args.base_url) is not None
        all_tests_passed = all_tests_passed and success
    
    # Run search test
    if args.all or args.search:
        success = test_email_search(args.base_url, args.search_query) is not None
        all_tests_passed = all_tests_passed and success
    
    # Run stats test
    if args.all or args.stats:
        success = test_email_stats(args.base_url) is not None
        all_tests_passed = all_tests_passed and success
    
    # Run detail test
    if (args.all or args.detail) and args.email_id:
        success = test_email_detail(args.base_url, args.email_id) is not None
        all_tests_passed = all_tests_passed and success
    elif args.all or args.detail:
        print("\n=== Skipping Email Detail Test (no email ID provided) ===")
    
    # Print overall result
    print("\n=== Test Summary ===")
    if all_tests_passed:
        print("All tests passed successfully!")
    else:
        print("Some tests failed. Check the output for details.")

if __name__ == "__main__":
    main()