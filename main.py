import logging

from fastapi import FastAPI, Depends

# Import your local configuration and modules
from config import ratelimiter
from logger_config.logs_handler import setupLogger
from routes.canary import router as canary_router  # Renamed here!

# 1. Initialization
setupLogger()
logger = logging.getLogger("app")

app = FastAPI()

# 2. Register Routers
app.include_router(canary_router)

# 3. Main Endpoints
@app.get('/', dependencies=[Depends(ratelimiter)])
def welcome_message():
    """Root health check for the Canary API."""
    logger.info("API Root endpoint has been called")
    return {"message": "welcome to canary token generator API"}

@app.get('/canary/docs', dependencies=[Depends(ratelimiter)])
def canary_docs():
    """Example endpoint for documentation access."""
    logger.info("canary DOCS have been called")
    return {"message": "Docs endpoint reached"}

# Note: In production, you would run this via: uvicorn main:app --reload