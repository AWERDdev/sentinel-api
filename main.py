from fastapi import FastAPI , requests , HTTPException
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),     # Sends logs to the console
        logging.FileHandler("app.log") # Also saves logs to a file
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI()


@app.get('/')
def welcome_message():
    logger.info("API Root endpoint has been called")
    return({"message":"welcome to canary token generator API"})

@app.get('/canary/DOCS')
def CanaryDOCS():
    logger.info("canary DOCS have been called")



# fastapi dev main.py
# uvicorn main:app --reload