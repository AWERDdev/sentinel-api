from datetime import datetime
import json
import logging
import os
import resend

import dotenv
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status

from config import ratelimiter, redis_connect

# Load environment variables
dotenv.load_dotenv()
resend.api_key = os.getenv("RESEND_API_KEY")

# Setup route logging
logger = logging.getLogger("app")

# Initialize router with clean metadata mappings
router = APIRouter(
     prefix="/canary",
     tags=["canary", "Trigger handler"],
     responses={
         404: {"description": "Not found"},
         200: {"description": "Canary Token Trigger Handler"}
     }
)


# ==========================================
# HELPER FUNCTIONS
# ==========================================
def send_security_alert(user_email: str, token_name: str, attacker_ip: str, user_agent: str):
     """Asynchronously dispatches a clean HTML breach alert notification via Resend."""
     try:
         html_content = f"""
         <h1>🚨 Security Alert: Your Canary Tripwire Was Triggered!</h1>
         <p>Your token <strong>{token_name}</strong> has been accessed by an unauthorized third party.</p>
         <hr />
         <h3>Attacker Details:</h3>
         <ul>
            <li><strong>IP Address:</strong> {attacker_ip}</li>
            <li><strong>User Agent:</strong> {user_agent}</li>
            <li><strong>Timestamp:</strong> {datetime.utcnow().isoformat()}</li>
         </ul>
         <p>Secure your systems immediately.</p>
         """
     
         resend.Emails.send({
            "from": "CanaryBox <onboarding@resend.dev>",  # Free tier default sender
            "to": user_email,
            "subject": f"🚨 BREACH DETECTED: {token_name}",
            "html": html_content
         })
         logger.info(f"Security alert email successfully dispatched to {user_email}")
     
     except Exception as e:
         # Prevent an email infrastructure failure from breaking background processes
         logger.error(f"Failed to send email alert: {e}")


# ==========================================
# 1. WELCOME ENDPOINT
# ==========================================
@router.get('/', dependencies=[Depends(ratelimiter)])
def welcome_message():
     """Simple health check and welcome route for the canary setup."""
     logger.info("Canary route Has been called")
     return {"message": "Welcome to canary route this is where you create fetch your canary tokens"}


# ==========================================
# 2. CANARY TRIGGER / HONEYPOT ENDPOINT
# ==========================================
@router.get("/trigger/{token_id}", dependencies=[Depends(ratelimiter)])
async def trigger_canary(token_id: str, request: Request, background_tasks: BackgroundTasks):
    try:
     """Intercepts unauthorized interaction hits, extracts tracking data, updates Redis state, and fires alerts."""
     
     # Fetch raw data payload out of Redis
     raw_token_data = redis_connect.get(f"canary:token:{token_id}")

     if not raw_token_data:
         logger.warning(f"failed to find token with this ID: {token_id}")
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Failed to find redis token"
         )
     
     if isinstance(raw_token_data, bytes):
         raw_token_data = raw_token_data.decode('utf-8')
     token_data = json.loads(raw_token_data)
     
     # Extract client network identity fingerprints safely
     forwarded_ip = request.headers.get("x-forwarded-for")
     attacker_ip = forwarded_ip.split(",")[0] if forwarded_ip else request.client.host
     user_agent = request.headers.get("user-agent", "Unknown")

     # Update token status values inside tracking state dictionary
     token_data["status"] = "COMPROMISED"
     token_data["breach_count"] = token_data.get("breach_count", 0) + 1
     
     log_entry = {
         "ip": attacker_ip,
         "user_agent": user_agent,
         "timestamp": datetime.utcnow().isoformat()
     }

     if "logs" not in token_data:
         token_data["logs"] = []

     token_data["logs"].append(log_entry)
     
     # BUG FIX 2: Correct target lookup key name from 'email' to match your schema 'alert_email'
     user_email = token_data.get("alert_email")

     # Sync modified tracking profile payload block state dictionary directly back into Redis storage
     redis_connect.set(f"canary:token:{token_id}", json.dumps(token_data))
     
     # Queue up background mail worker execution block safely
     if user_email:
         background_tasks.add_task(
            send_security_alert, 
            user_email, 
            token_data.get("name", "Unknown Token"), 
            attacker_ip, 
            user_agent
         )
     
     # Return a completely deceptive response to keep the intruder clueless
         return {
  "status": "panik",
  "code": "SERVER_HAS_LEFT_THE_CHAT",
  "message": "Something went horribly wrong. We blamed the intern, but honestly, it was probably your payload :).",
  "Your_Problem_not_mine": "It worked on my machine. ¯\\_(ツ)_/¯"
}
    except Exception as e:
        logger.error(f"failed to trigger canary token {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="failed to trigger canary token"
        )