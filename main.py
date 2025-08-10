from fastapi import FastAPI
import uvicorn
import os
from utils.logger import SingletonLogger
from openAPI_IDC.routes.email_sender_routes import router as email_router

# Initialize FastAPI app
app = FastAPI(
    title="Email API",
    description="API for sending emails with templates",
    version="1.0.0"
)

# Configure logger
SingletonLogger.configure()
logger = SingletonLogger.get_logger('appLogger')


# Include routers
app.include_router(email_router, prefix="/api/v1", tags=["Email"])

@app.get("/", tags=["Health Check"])
async def root():
    """Root endpoint for health check"""
    return {
        "status": "running",
        "service": "Email API",
        "version": "1.0.0"
    }

def main():
    """Main function to run the FastAPI application"""
    try:
        # Default configuration
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", 8000))
        
        logger.info(f"Starting Email API on {host}:{port}")
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=True,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise

if __name__ == "__main__":
    main()
