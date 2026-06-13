from fastapi import FastAPI, Request, HTTPException, Depends
import logging

from logger_config.logs_handler import setupLogger
setupLogger()


from config import ratelimiter

# Fetch the general app logger
logger = logging.getLogger("app")

app = FastAPI()

@app.get('/',dependencies=[Depends(ratelimiter)])
def welcome_message():
    logger.info("API Root endpoint has been called")
    return {"message": "welcome to canary token generator API"}

@app.get('/canary/docs',dependencies=[Depends(ratelimiter)])
def CanaryDOCS():
    logger.info("canary DOCS have been called")

# fastapi dev main.py