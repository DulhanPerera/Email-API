from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, status
from fastapi.responses import JSONResponse
from utils.logger import SingletonLogger
from openAPI_IDC.services.email_sender import send_emails_process
from openAPI_IDC.models.email_sender_model import EmailSenderRequest
from utils.Custom_Exceptions import BaseCustomException, DatabaseConnectionError


SingletonLogger.configure()

logger = SingletonLogger.get_logger('appLogger')


# Create an instance of APIRouter for defining API routes
router = APIRouter()



@router.post("/send-emails",
             summary="Send emails",
             description="Send emails with the provided template and data",
             status_code=status.HTTP_202_ACCEPTED)
async def send_emails(
    request: EmailSenderRequest,
    background_tasks: BackgroundTasks
):
    """
    Endpoint to send emails with the provided template and data.

    Args:
        request: The email sending request containing all necessary details.
        background_tasks: FastAPI's background tasks handler

    Returns:
        dict: A dictionary containing the result of the email sending operation.
    """
    try:
        # Call the service function to send the email
        result = send_emails_process(request, background_tasks)
        
        return {
            "status": result.get("status"),
            "message": result.get("message"),
            "details": {
                "template_used": request.EmailType,
                "recipient": request.RecieverMail,
                "cc_recipients": request.CarbonCopyTo or [],
                "has_attachments": len(request.Attachments or []) > 0,
                "sent_at": datetime.now().isoformat()
            }
        }
            
    except BaseCustomException as e:
        # Handle custom exceptions and return appropriate HTTP response
        raise e.to_http_exception()

    except Exception as e:
        # Handle unexpected exceptions and log the error
        logger.error(f"Unexpected error: {str(e)}")
        raise DatabaseConnectionError(f"Unexpected server error, {str(e)}")