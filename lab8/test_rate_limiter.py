import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException, Request
from datetime import datetime, timedelta
import json
from rate_limiter import check_request_limit, ANONYMOUS_LIMIT, AUTHENTICATED_LIMIT


@pytest.fixture
def mock_redis():
    with patch("rate_limiter.redis_client") as mock_client:
        yield mock_client


@pytest.fixture
def mock_request():
    request = MagicMock(spec=Request)
    request.client = MagicMock()
    request.client.host = "192.168.1.100"
    request.url = MagicMock()
    request.url.path = "/api/v1/books"
    return request


@pytest.mark.asyncio
async def test_anonymous_user_under_limit(mock_redis, mock_request):
    current_time = datetime.utcnow()
    old_request = (current_time - timedelta(seconds=30)).isoformat()

    mock_redis.get.return_value = json.dumps([old_request])
    mock_redis.setex.return_value = True

    await check_request_limit(mock_request, user_id=None)

    expected_key = f"rate_limit:ip:{mock_request.client.host}"
    mock_redis.get.assert_called_once_with(expected_key)
    mock_redis.setex.assert_called_once()

    call_args = mock_redis.setex.call_args
    assert call_args[0][0] == expected_key
    assert call_args[0][1] == 70
    stored_data = json.loads(call_args[0][2])
    assert len(stored_data) == 2


@pytest.mark.asyncio
async def test_anonymous_user_at_limit(mock_redis, mock_request):
    current_time = datetime.utcnow()
    requests_in_window = [
        (current_time - timedelta(seconds=30)).isoformat(),
        (current_time - timedelta(seconds=10)).isoformat()
    ]

    mock_redis.get.return_value = json.dumps(requests_in_window)

    with pytest.raises(HTTPException) as exc_info:
        await check_request_limit(mock_request, user_id=None)

    assert exc_info.value.status_code == 429
    assert f"Limit: {ANONYMOUS_LIMIT} requests per minute" in exc_info.value.detail

    mock_redis.setex.assert_not_called()


@pytest.mark.asyncio
async def test_authenticated_user_under_limit(mock_redis, mock_request):
    user_id = 123

    current_time = datetime.utcnow()
    requests_in_window = [
        (current_time - timedelta(seconds=i * 10)).isoformat()
        for i in range(5)
    ]

    mock_redis.get.return_value = json.dumps(requests_in_window)
    mock_redis.setex.return_value = True

    await check_request_limit(mock_request, user_id=user_id)

    expected_key = f"rate_limit:user:{user_id}"
    mock_redis.get.assert_called_once_with(expected_key)
    mock_redis.setex.assert_called_once()

    call_args = mock_redis.setex.call_args
    stored_data = json.loads(call_args[0][2])
    assert len(stored_data) == 6


@pytest.mark.asyncio
async def test_authenticated_user_at_limit(mock_redis, mock_request):
    user_id = 123

    current_time = datetime.utcnow()
    requests_in_window = [
        (current_time - timedelta(seconds=i * 5)).isoformat()
        for i in range(AUTHENTICATED_LIMIT)
    ]

    mock_redis.get.return_value = json.dumps(requests_in_window)

    with pytest.raises(HTTPException) as exc_info:
        await check_request_limit(mock_request, user_id=user_id)

    assert exc_info.value.status_code == 429
    assert f"Limit: {AUTHENTICATED_LIMIT} requests per minute" in exc_info.value.detail

    mock_redis.setex.assert_not_called()
