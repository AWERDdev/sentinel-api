import logging

from fastapi import FastAPI, Depends

# Import your local configuration and modules
from config import ratelimiter
from logger_config.logs_handler import setupLogger
from routes.canary_generation import router as canary_generation_router  # Renamed here!
from routes.canary_fetching import router as canary_featch_router  # Renamed here!
from routes.canary_trigger import router as canary_trigger_router  # Renamed here!
from routes.canary_delete import router as canary_delete_router

# 1. Initialization
setupLogger()
logger = logging.getLogger("app")

app = FastAPI()

# 2. Register Routers
app.include_router(canary_generation_router)
app.include_router(canary_featch_router)
app.include_router(canary_trigger_router)
app.include_router(canary_delete_router)
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
    return {"message": "Docs endpoint reached","GitRepo":"https://github.com/AWERDdev/sentinel-api"}

#  uvicorn main:app --reload