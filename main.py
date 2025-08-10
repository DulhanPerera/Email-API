from fastapi import FastAPI
import uvicorn
from utils.logger import SingletonLogger


app = FastAPI()

logger = SingletonLogger.get_logger('dbLogger')
SingletonLogger.configure()

# Include router
app.include_router(router)

@app.get("/")
def root():
    return {"message": "API is running"}


def main():
    try:
        host,port = ServerConfigLoader.load_server_config()
    except Exception as e:
        logger.debug(f"Error loading server configuration: {e}")
        return
    uvicorn.run("main:app", host=host, port=port, reload=True)
    

if __name__ == "__main__":
    main()
