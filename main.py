from fastapi import FastAPI, Request, HTTPException, Depends
import logging

from logger_config import setupLogger
setupLogger()


from config import ratelimiter

# Fetch the general app logger
logger = logging.getLogger("app")

app = FastAPI()

@app.get('/')
def welcome_message(request: Request, protected = Depends(ratelimiter)):
    logger.info("API Root endpoint has been called")
    return {"message": "welcome to canary token generator API"}

@app.get('/canary/DOCS')
def CanaryDOCS():
    logger.info("canary DOCS have been called")