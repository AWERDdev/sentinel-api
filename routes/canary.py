import logging
import os
from uuid import uuid4

import dotenv
from fastapi import APIRouter, Body, Depends, HTTPException, Request, status

from ..config import ratelimiter
from ..models.canary_model import CanaryToken

# Load environment variables
dotenv.load_dotenv()

# Setup route logging
logger = logging.getLogger("app")

# Initialize router with clean metadata mappings
router = APIRouter(
    prefix="/canary",
    tags=["canary", "token generator"],
    responses={
        404: {"description": "Not found"},
        200: {"description": "Canary Token Handler"}
    }
)

# ==========================================
# 1. WELCOME ENDPOINT
# ==========================================
@router.get('/', dependencies=[Depends(ratelimiter)])
def welcome_message():
    """Simple health check and welcome route for the canary setup."""
    logger.info("Canary route Has been called")
    return {"message": "Welcome to canary route this is where you create fetch your canary tokens"}


# ==========================================
# 2. TOKEN GENERATION ENDPOINT
# ==========================================
@router.post('/generate-token', dependencies=[Depends(ratelimiter)], status_code=status.HTTP_201_CREATED)
async def generate_token(data: CanaryToken = Body(...)):
    """Validates input payload and generates specific high-fidelity decoy configurations."""
    try:
        logger.info("A request for creating a new token has been made")
        logger.info(f"Retreving canary model {CanaryToken}")
        
        # Unique identification token assignment
        token_id = str(uuid4())
        logger.info(f"Created canary token ID {token_id}")
        
        # Enforce validation on supported honeypot structures
        allowed_types = ["http", "https", "aws"]
        if data.token_type not in allowed_types:
            logger.warning(f"Invalid token type attempted: {data.token_type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid token type. Choose from: {', '.join(allowed_types)}"
            )
            
        generated_auth = ""

        # Construct specific payloads depending on honey token classification
        if data.token_type == "http":
            # Construct the tracking link the attacker will accidentally click
            generated_auth = f"https://{os.getenv('DOMAIN', 'http://127.0.0.1:8000')}/canary/trigger/{token_id}"

        elif data.token_type == "aws":
            # Construct a fake AWS credential block using the ID so you can track it
            generated_auth = f"aws_access_key_id=AKIA_{token_id[:16].upper()}\naws_secret_access_key=fake_secret_{token_id}"

        # Initialize the final model instance with system-generated IDs and payload metadata
        newCanary = CanaryToken(
            token_ID=token_id,
            token_type=data.token_type,
            name=data.name,
            alert_email=data.alert_email
        )

    except Exception as e:
        logger.error(f"failed to generate toke error:{e}")