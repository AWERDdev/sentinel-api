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
     tags=["canary", "token management"],
     responses={
          404: {"description": "Not found"},
          200: {"description": "Canary Token Handler"}
     }
)

# ==========================================
# 1. DELETE BY TOKEN ID
# ==========================================
@router.delete('/delete/id/{token_id}', dependencies=[Depends(ratelimiter)])
def delete_canary_by_id(token_id: str): 
    try:   
        logger.info(f"Token delete request received starting delete process for Token With ID: {token_id}")
             
        token_key = f"canary:token:{token_id}"
        raw_token_data = redis_connect.get(token_key)
             
        if not raw_token_data:
            logger.warning(f"Canary token with this id wasn't found: {token_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Canary token wasn't found"
            )
             
        if isinstance(raw_token_data, bytes):
            raw_token_data = raw_token_data.decode('utf-8')
            
        # FIX: Changed json.load() to json.loads()
        data_dict = json.loads(raw_token_data)
        token_name = data_dict.get("name")

        name_key = f"canary:name:{token_name.replace(' ', '_').lower()}"

        redis_connect.delete(token_key)
        redis_connect.delete(name_key)
             
        logger.info(f"Token {token_id} and index {name_key} deleted successfully.")
        return {"message": f"Token with ID {token_id} deleted successfully."}

    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        logger.error(f"Failed to delete canary token by id {token_id}. Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred during deletion"
        )


# ==========================================
# 2. DELETE BY TOKEN NAME
# ==========================================
@router.delete('/delete/name/{token_name}', dependencies=[Depends(ratelimiter)])
def delete_canary_by_name(token_name: str):
    try:
        logger.info(f"Token delete request received starting delete process for Token With Name: {token_name}")
             
        name_key = f"canary:name:{token_name.replace(' ', '_').lower()}"
        
        # Look up the ID first from the secondary name index
        token_id = redis_connect.get(name_key)
             
        if not token_id:
            logger.warning(f"Canary token index with this name wasn't found: {token_name}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Canary token name index wasn't found"
            )
            
        if isinstance(token_id, bytes):
            token_id = token_id.decode('utf-8')

        token_key = f"canary:token:{token_id}"

        redis_connect.delete(token_key)
        redis_connect.delete(name_key)
             
        logger.info(f"Token {token_id} and index {name_key} deleted successfully.")
        return {"message": f"Token '{token_name}' deleted successfully."}

    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        logger.error(f"Failed to delete canary token by name {token_name}. Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred during deletion"
        )   