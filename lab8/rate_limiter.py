import redis
from fastapi import HTTPException, Request
from datetime import datetime, timedelta
import json
import os
from typing import Optional

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=int(os.getenv("REDIS_DB", 0)),
    decode_responses=True
)

RATE_LIMIT_WINDOW = 60
ANONYMOUS_LIMIT = 2
AUTHENTICATED_LIMIT = 10


async def check_request_limit(request: Request, user_id: Optional[int] = None):
    current_time = datetime.utcnow()

    if user_id:
        key = f"rate_limit:user:{user_id}"
        limit = AUTHENTICATED_LIMIT
    else:
        key = f"rate_limit:ip:{request.client.host}"
        limit = ANONYMOUS_LIMIT

    window_start = current_time - timedelta(seconds=RATE_LIMIT_WINDOW)

    try:
        requests_data = redis_client.get(key)

        if requests_data:
            requests_list = json.loads(requests_data)
            requests_list = [
                req_time for req_time in requests_list
                if datetime.fromisoformat(req_time) > window_start
            ]
        else:
            requests_list = []

        if len(requests_list) >= limit:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Limit: {limit} requests per minute"
            )

        requests_list.append(current_time.isoformat())

        redis_client.setex(
            key,
            RATE_LIMIT_WINDOW + 10,
            json.dumps(requests_list)
        )

    except redis.RedisError as e:
        pass
