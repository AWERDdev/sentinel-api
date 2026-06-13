import json
import logging

import dotenv
from fastapi import APIRouter, Depends, HTTPException, status

from config import ratelimiter, redis_connect

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
# 2. FETCH BY ID ENDPOINT
# ==========================================
@router.get("/fetch/id/{token_id}", dependencies=[Depends(ratelimiter)])
def fetch_canary_token_by_id(token_id: str):
    """Fetches full token configurations directly via their tracking UUID strings."""
    logger.info(f"fetch canary token by id route called for: {token_id}")

    raw_token_data = redis_connect.get(f"canary:token:{token_id}")
    
    if not raw_token_data:
        logger.warning(f"Token lookup failed for ID: {token_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="canary token not found"
        )
    
    # Robust decoding: ensure bytes are converted to string before JSON parsing
    if isinstance(raw_token_data, bytes):
        raw_token_data = raw_token_data.decode('utf-8')
        
    logger.info("canary token raw data fetched")
    return json.loads(raw_token_data)


# ==========================================
# 3. FETCH BY NAME ENDPOINT
# ==========================================
@router.get("/fetch/name/{name}", dependencies=[Depends(ratelimiter)])
def fetch_canary_token_by_name(name: str):
    """Resolves name mappings to discover the active tracking payload data."""
    logger.info(f"fetch canary token by name route called for: {name}")

    # Step 1: Look up the string token_id linked to this name secondary key index
    name_key = f"canary:name:{name.replace(' ', '_').lower()}"
    token_id = redis_connect.get(name_key)
    
    if not token_id:
        logger.warning(f"Token lookup failed for name: {name}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="canary token name not found"
        )
        
    # Python Redis client returns bytes, we decode it safely to match string lookup formatting
    token_id_str = token_id.decode('utf-8') if isinstance(token_id, bytes) else token_id

    # Step 2: Use the found ID to grab the full profile model data from Redis
    raw_token_data = redis_connect.get(f"canary:token:{token_id_str}")
    
    if not raw_token_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="canary token payload data missing"
        )

    # Decode if necessary and return
    if isinstance(raw_token_data, bytes):
        raw_token_data = raw_token_data.decode('utf-8')

    return json.loads(raw_token_data)