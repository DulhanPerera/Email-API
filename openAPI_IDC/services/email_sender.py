#region-Details_Template
"""
API : Email Sending Service
Name : Email_Sender   
Description : Handles sending of HTML emails with dynamic content and attachments
Created By : Dulhan Perera (vicksurap@gmail.com)
Created Date : 2024-08-13

Version: 2.0

Input Parameters:
    * request: EmailSenderRequest object containing email details
    * background_tasks: Optional FastAPI BackgroundTasks for async processing

Input:
    * Email content (HTML/plain text)
    * Recipient information
    * Template selection
    * Optional attachments
    * CC/BCC recipients

Output:
    * Sends email via SMTP
    * Logs email details to MongoDB
    * Returns status of email sending operation

Operation:
    * Validates email request
    * Renders HTML template with provided data
    * Processes and attaches files
    * Sends email via configured SMTP server
    * Logs the operation for tracking

Dependencies:
    * Python 3.12.4+
    * FastAPI
    * Jinja2
    * pymongo
    * python-dotenv
"""

"""
Version: 2.0
Dependencies: 
    * fastapi
    * jinja2
    * pymongo
    * python-dotenv
    * email-validator

Related Files:
    * models/email_sender_model.py - Request/response models
    * services/html_templates/ - Email templates
    * Attachments/ - Directory for email attachments

Purpose: 
    Provides a robust email sending service with template support and logging

Version History:
    * 2.0 (2024-08-13) - Major update with template support and attachments
      - Added HTML template rendering
      - Added attachment handling
      - Improved error handling and logging
    * 1.0 (2024-05-28) - Initial version
      - Basic email sending functionality

Notes:
    * SMTP configuration is loaded from environment variables
    * Email templates use Jinja2 syntax
    * Attachments are stored in the project's Attachments directory
"""
#endregion-Details_Template

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from fastapi import BackgroundTasks
import jinja2  # For rendering HTML templates with placeholders
from pathlib import Path

# Custom imports
from utils.logger import SingletonLogger
from utils.connectionMongo import MongoDBConnectionSingleton
from utils.Custom_Exceptions import DatabaseConnectionError, DatabaseUpdateError
from utils.core_utils import get_config
from openAPI_IDC.models.email_sender_model import EmailSenderRequest

# Initialize logger for application-wide logging
logger = SingletonLogger.get_logger('appLogger')

# Load environment-specific configuration
config = get_config()

# SMTP server configuration
SMTP_HOST = os.getenv("SMTP_Host", "localhost")  # SMTP server hostname
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))      # SMTP server port (default: 587 for TLS)
SMTP_USER = os.getenv("EMAIL_USER", "")           # SMTP authentication username
SMTP_PASSWORD = os.getenv("EMAIL_PASS", "")       # SMTP authentication password
FROM_EMAIL = SMTP_USER or "no-reply@example.com"   # Default sender email

# Configure file system paths
# Path to directory containing HTML email templates
template_dir = os.path.join(os.path.dirname(__file__), 'html_templates')
# Path to directory for storing email attachments (3 directories up from current file)
attachments_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'Attachments')

# Ensure attachments directory exists
os.makedirs(attachments_dir, exist_ok=True)

# Initialize Jinja2 template environment with file system loader
jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(template_dir),
    autoescape=jinja2.select_autoescape(['html', 'xml'])
)

# Map template names to their corresponding HTML files
template_mapping = {
    "Template-Mediation": "mediation_board_template",
    "Template-Defaulted-Cases": "defaulted_cases_template",
    "Template-Defaulted-Customers": "defaulted_customers_template",
    "Template-Plain": "plain_template",
    "Template-Table": "table_template",
}

def send_emails_process(request: EmailSenderRequest, background_tasks: BackgroundTasks = None) -> Dict[str, str]:
    """
    Process email sending request, either immediately or as a background task.
    
    Args:
        request: EmailSenderRequest object containing email details
        background_tasks: Optional FastAPI BackgroundTasks instance for async processing
        
    Returns:
        dict: Status and message indicating the result of the operation
        
    Example:
        >>> request = EmailSenderRequest(...)
        >>> result = send_emails_process(request)
        >>> print(result)
        {'status': 'success', 'message': 'Email sent successfully'}
    """
    try:
        if background_tasks:
            # Add to background tasks if background_tasks is provided
            background_tasks.add_task(send_email_function, request)
            return {"status": "processing", "message": "Email queued for sending"}
        else:
            # Process synchronously
            send_email_function(request)
            return {"status": "success", "message": "Email sent successfully"}
    except Exception as e:
        logger.error(f"Error processing email request: {str(e)}")
        raise

def send_email_function(request: EmailSenderRequest) -> None:
    """
    Core function to build and send an email with the given request parameters.
    
    This function handles:
    - Template selection and rendering
    - Email message construction
    - Attachment processing
    - SMTP delivery
    - Database logging
    
    Args:
        request: EmailSenderRequest object containing all email details
        
    Raises:
        ValueError: If template name is invalid or template file is not found
        DatabaseConnectionError: If unable to connect to MongoDB
        DatabaseUpdateError: If email log cannot be written to database
        Exception: For any other unexpected errors during email sending
    """
    if request.Type.lower() != 'email':
        logger.info(f"Ignoring request with type: {request.Type}")
        return

    template_file = template_mapping.get(request.TemplateName)
    if not template_file:
        raise ValueError(f"Invalid TemplateName or no template file defined: {request.TemplateName}")

    try:
        template = jinja_env.get_template(f"{template_file}.html")
        render_context = request.EmailBody.model_dump()
        render_context["Date"] = datetime.now().strftime("%B %d, %Y")
        render_context["Subject"] = request.Subject  # Add subject to template context
        logger.info(f"Render context: {render_context}")

        # Process Table_Filter_infor for Template-Table and Template-Mediation
        if request.TemplateName in ["Template-Table", "Template-Mediation"] and hasattr(request.EmailBody, 'Table_Filter_infor'):
            # Get the data dictionary from Table_Filter_infor
            table_data = request.EmailBody.Table_Filter_infor.data
            logger.info(f"Table data: {table_data}")
            
            # Convert the data dictionary to a list with a single item for the table
            table_html = build_html_table([table_data])
            logger.info(f"Generated table HTML: {table_html}")
            render_context["DYNAMIC_TABLE"] = table_html

        html_body = template.render(**render_context)
        # logger.info(f"Rendered HTML: {html_body}")
    except jinja2.exceptions.TemplateNotFound as e:
        logger.error(f"Template file not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to render template: {e}")
        raise

    msg = MIMEMultipart()
    # Use Sender_Name in From header (standard email format: Name <email>)
    # To use only email address, change to: msg['From'] = FROM_EMAIL
    msg['From'] = f"{request.EmailBody.Sender_Name} <{FROM_EMAIL}>" if request.EmailBody.Sender_Name else FROM_EMAIL
    msg['To'] = request.SendersMail
    msg['Cc'] = ', '.join(request.CarbonCopyTo or [])
    msg['Subject'] = request.Subject
    msg.attach(MIMEText(html_body, 'html'))

    # Process attachments if any
    if hasattr(request, 'Attachments') and request.Attachments:
        for attachment_name in request.Attachments:
            attachment_path = os.path.join(attachments_dir, attachment_name)
            try:
                if os.path.exists(attachment_path):
                    with open(attachment_path, 'rb') as f:
                        part = MIMEApplication(f.read(), Name=os.path.basename(attachment_name))
                        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_name)}"'
                        msg.attach(part)
                    logger.info(f"Attachment added: {attachment_name}")
                else:
                    logger.warning(f"Attachment file not found in attachments folder: {attachment_name}")
            except Exception as e:
                logger.error(f"Error attaching file {attachment_name}: {str(e)}")
                continue

    status = 'success'
    sent_at = datetime.now()
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            if SMTP_USER and SMTP_PASSWORD:
                server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        logger.info(f"Email sent successfully to {request.SendersMail}")
    except Exception as e:
        status = 'failed'
        logger.error(f"Failed to send email: {e}")
        raise
    finally:
        try:
            db_instance = MongoDBConnectionSingleton()
            # if db_instance.database is None:
            #     raise DatabaseConnectionError("MongoDB connection is not established.")
            # db = db_instance.get_database()
            # db.email_logs.insert_one({
            #     'type': request.Type,
            #     'to': request.SendersMail,
            #     'cc': request.CarbonCopyTo,
            #     'subject': request.Subject,
            #     'template': request.TemplateName,
            #     'body': request.EmailBody.dict(),
            #     'attachments': request.Attachments,
            #     'date': request.Date,
            #     'sent_at': str(sent_at),
            #     'status': status
            # })
            logger.info("Email log inserted to DB")
        except DatabaseConnectionError as e:
            logger.error(f"Database connection error: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to insert email log to DB: {e}")
            raise DatabaseUpdateError(f"Failed to update database: {e}")

def build_html_table(data: List[Dict[str, Any]]) -> str:
    """
    Convert a list of dictionaries into an HTML table string.
    
    Args:
        data: List of dictionaries where each dict represents a table row
        
    Returns:
        str: HTML string containing the formatted table
        
    Example:
        >>> data = [{'name': 'John', 'age': 30}, {'name': 'Jane', 'age': 25}]
        >>> html = build_html_table(data)
    """
    if not data:
        return "<p>No data available.</p>"

    headers = data[0].keys()
    table_html = ['<table style="width:100%; border-collapse: collapse;" border="1" cellpadding="8" cellspacing="0">']

    # Header row
    table_html.append('<tr style="background-color: #f2f2f2;">')
    for h in headers:
        table_html.append(f"<th style='text-align:left'>{h}</th>")
    table_html.append('</tr>')

    # Data rows
    for row in data:
        table_html.append('<tr>')
        for h in headers:
            value = row[h]
            if isinstance(value, list) and len(value) == 2:
                # Format list of two items as "item1 - item2"
                value = f"{value[0]} - {value[1]}"
            table_html.append(f"<td>{value}</td>")
        table_html.append('</tr>')

    table_html.append('</table>')
    return ''.join(table_html)