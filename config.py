from fastapi import Request, HTTPException, status
from models.redis_settings_model import redis_Settings
import redis
import logging

redis_logger = logging.getLogger("app.redis")
rate_limiter_logger = logging.getLogger("app.rate_limiter")

settings = redis_Settings()

# 1. Corrected Redis connection initialization
try:
    redis_connect = redis.Redis(
        host=settings.HOST, 
        port=settings.PORT, 
        decode_responses=settings.DECODE_RESPONSE,
        encoding=settings.ENCODING
    )
    redis_logger.info(f"Successfully connected to Redis on port {settings.PORT}")
except Exception as e:
    redis_logger.error(f"Connecting to Redis failed {e}")

# rate limiter

def ratelimiter(request: Request):
    forwarded_for = request.headers.get("X-Forwarded-For")
    client_IP = forwarded_for.split(",")[0].strip() if forwarded_for else request.client.host

    # 2. Corrected environment fetching with proper type casting
    MAX_REQUESTS = settings.MAX_REQUESTS
    WINDOW_SECONDS = settings.WINDOW_SECONDS

    # Added a colon for clean Redis namespace formatting
    redis_key = f"rate_limit:{client_IP}"

    current_requests = redis_connect.incr(redis_key)

    if current_requests == 1:
        redis_connect.expire(redis_key, WINDOW_SECONDS)

    # 3. This will now work perfectly because both sides are integers!
    if current_requests > MAX_REQUESTS:
        rate_limiter_logger.warning(f"user with this IP {client_IP} has made too many requests")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later."
        )