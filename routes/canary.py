from fastapi import APIRouter , Request, HTTPException, Depends, Body
from uuid import uuid4
from ..models.canary_model import CanaryToken
from ..config import ratelimiter
import logging
import os

import dotenv
dotenv.load_dotenv()

logger = logging.getLogger("app")

router = APIRouter(
    prefix="/canary",
    tags=["canary","token generator"],
    responses={404:{"description":"Not found"},200:{"desciption":"Canary Token Handler"}}
)

@router.get('/', dependencies=[Depends(ratelimiter)])
def welcome_message():
    logger.info("Canary route Has been called")
    return{"message":"Welcome to canary route this is where you create fetch your canary tokens"}

@router.post('/generate-token',dependencies=[Depends(ratelimiter)])
async def generate_token(data:CanaryToken= Body(...)):
    try:
        logger.info("A request for creating a new token has been made")
        logger.info(f"Retreving canary model {CanaryToken}")
        token_id = str(uuid4())
        logger.info(f"Created canary token ID {token_id}")
        generated_auth = ""

        if data.token_type == "http":
            # Construct the tracking link the attacker will accidentally click
            generated_auth = f"https://{os.getenv("DOMAIN",'http://127.0.0.1:8000')}/canary/trigger/{token_id}"

        elif data.token_type == "aws":
            # Construct a fake AWS credential block using the ID so you can track it
            generated_auth = f"aws_access_key_id=AKIA_{token_id[:16].upper()}\naws_secret_access_key=fake_secret_{token_id}"


        newCanary = CanaryToken(
            token_ID = token_id,
            token_type = data.token_type,
            name =  data.name,
            alert_email =  data.alert_email
        )

    except Exception as e:
        logger.error(f"failed to generate toke error:{e}")

