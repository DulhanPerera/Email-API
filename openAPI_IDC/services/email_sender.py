import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime
from fastapi import BackgroundTasks
import jinja2  # For rendering HTML templates with placeholders

from utils.logger import SingletonLogger
from utils.connectionMongo import MongoDBConnectionSingleton
from utils.Custom_Exceptions import DatabaseConnectionError, DatabaseUpdateError
from utils.core_utils import get_config
from openAPI_IDC.models.email_sender_model import EmailSenderRequest

# Get logger
logger = SingletonLogger.get_logger('appLogger')

# Load config (env-aware)
config = get_config()

SMTP_HOST = os.getenv("SMTP_Host", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("EMAIL_USER", "")
SMTP_PASSWORD = os.getenv("EMAIL_PASS", "")
FROM_EMAIL = SMTP_USER or "no-reply@example.com"

# Set up Jinja2 environment
template_dir = os.path.join(os.path.dirname(__file__), 'html_templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))

template_mapping = {
    "Template-Mediation": "mediation_board_template",
    "Template-Defaulted-Cases": "defaulted_cases_template",
    "Template-Defaulted-Customers": "defaulted_customers_template",
    "Template-Plain": "plain_template",
    "Template-Table": "table_template",
}

def send_emails_process(request: EmailSenderRequest, background_tasks: BackgroundTasks = None):
    """
    Process email sending request and handle it in the background if needed.
    
    Args:
        request: The email sending request
        background_tasks: Optional FastAPI BackgroundTasks instance for async processing
        
    Returns:
        dict: Result of the email sending operation
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

def send_email_function(request: EmailSenderRequest):
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

    for attachment in request.Attachments:
        if os.path.exists(attachment):
            with open(attachment, 'rb') as f:
                part = MIMEApplication(f.read(), Name=os.path.basename(attachment))
                part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment)}"'
                msg.attach(part)
        else:
            logger.warning(f"Attachment file not found: {attachment}")

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

def build_html_table(data: list[dict]) -> str:
    """Convert list of dicts into a responsive HTML table with formatted list values."""
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