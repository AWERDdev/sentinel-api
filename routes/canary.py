import json
import logging
import os
from uuid import uuid4

import dotenv
from fastapi import APIRouter, Body, Depends, HTTPException, Request, status

from ..config import ratelimiter, redis_connect
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
            alert_email=data.alert_email,
            auth_string=generated_auth
        )
        
        # Redis Primary Key Storage
        token_key = f"canary:token:{token_id}"
        redis_connect.set(token_key, newCanary.model_dump_json())

        # Redis Secondary Index Lookup Mapping
        name_key = f"canary:name:{data.name.replace(' ', '_').lower()}"
        redis_connect.set(name_key, token_id)

        return {
            "message": "your token has been generated successfully",
            "Canary_Token": generated_auth,
            "Token_ID": token_id,
            "Token_Name": data.name
        }

    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        logger.error(f"failed to generate token error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


# ==========================================
# 3. FETCH BY ID ENDPOINT
# ==========================================
@router.get("/fetch/id/{token_id}")
def fetch_canary_token_by_id(token_id: str):
    """Fetches full token configurations directly via their tracking UUID strings."""
    logger.info(f"fetch canary token by id route called for: {token_id}")

    raw_data = redis_connect.get(f"canary:token:{token_id}")
    logger.info("canary token raw data fetched")
    
    if not raw_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="canary token not found")
    
    return json.loads(raw_data)


# ==========================================
# 4. FETCH BY NAME ENDPOINT
# ==========================================
@router.get("/fetch/name/{name}")
def fetch_canary_token_by_name(name: str):
    """Resolves name mappings to discover the active tracking payload data."""
    logger.info(f"fetch canary token by name route called for: {name}")

    # Step 1: Look up the string token_id linked to this name secondary key index
    token_id = redis_connect.get(f"canary:name:{name.replace(' ', '_').lower()}")
    logger.info("canary token name pointer index lookup complete")
    
    if not token_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="canary token name not found")
        
    # Python Redis client returns bytes, we decode it safely to match string lookup formatting
    token_id_str = token_id.decode('utf-8') if isinstance(token_id, bytes) else token_id

    # Step 2: Use the found ID to grab the full profile model data from Redis
    raw_data = redis_connect.get(f"canary:token:{token_id_str}")
    if not raw_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="canary token payload data missing")

    return json.loads(raw_data)