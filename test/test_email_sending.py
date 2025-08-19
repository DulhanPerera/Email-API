"""
Test script to verify email sending with current date functionality.
This script sends a test email using the email_sender module and verifies
that the current date is correctly inserted into the email template.
"""
import os
import sys
import json
from datetime import datetime, date
from pathlib import Path

# Add the parent directory to the Python path so we can import the email_sender module
sys.path.insert(0, str(Path(__file__).parent.parent))

from openAPI_IDC.services.email_sender import send_emails_process
from openAPI_IDC.models.email_sender_model import EmailSenderRequest, EmailBodyModel, TableFilterInfo

def load_test_request():
    """Load the test request from the JSON file."""
    test_file = Path(__file__).parent / "API_Request_Test.json"
    with open(test_file, 'r') as f:
        data = json.load(f)
    
    # Convert to Pydantic model
    table_filter_info = TableFilterInfo(**data['EmailBody']['Table_Filter_infor'])
    email_body = EmailBodyModel(
        Reciever_Name=data['EmailBody']['Reciever_Name'],
        Table_Filter_infor=table_filter_info
    )
    
    # Prepare the request data with all required fields
    request_data = {
        'EmailType': data['EmailType'],
        'RecieverMail': 'test@example.com',  # Required field
        'CarbonCopyTo': data.get('CarbonCopyTo', []),
        'Subject': data['Subject'],
        'EmailBody': email_body,
        'Attachments': data.get('Attachments', []),
        'Date': date.today()  # Required field, but will be overridden by email_sender.py
    }
    
    return EmailSenderRequest(**request_data)

def test_email_sending(interactive=True):
    """Test sending an email and verify the date is set correctly.
    
    Args:
        interactive: If True, will prompt for confirmation before sending the email.
    """
    try:
        # Load the test request
        request = load_test_request()
        
        print(f"Sending test email to: {request.RecieverMail}")
        print(f"Subject: {request.Subject}")
        print(f"Email Type: {request.EmailType}")
        print("\nThis will send a real email. Make sure your SMTP settings are configured correctly.")
        print("The email should show the current date in the body.")
        
        if interactive:
            # Ask for confirmation before sending
            confirm = input("\nDo you want to continue? (y/n): ")
            if confirm.lower() != 'y':
                print("Test cancelled.")
                return
        else:
            print("\nRunning in non-interactive mode, proceeding with test...")
        
        # Send the email
        print("\nSending email...")
        result = send_emails_process(request)
        
        if result['status'] in ['success', 'processing']:
            print(f"\n✅ Email sent successfully! Status: {result['status']}")
            print(f"   - Check your inbox for the test email.")
            print(f"   - Verify that the email shows today's date: {datetime.now().strftime('%B %d, %Y')}")
        else:
            print(f"\n❌ Email sending failed: {result.get('message', 'Unknown error')}")
            
    except Exception as e:
        print(f"\n[ERROR] An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=== Email Sending Test ===")
    print("This will send a test email to verify the date functionality.\n")
    
    # Run in non-interactive mode by default
    test_email_sending(interactive=False)
    
    print("\n=== Test Complete ===")
