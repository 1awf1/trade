"""
Rate limiting middleware for API endpoints.
Uses Redis to track request counts per user/IP.
"""
from typing import Optional, Callable
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timedelta
import time
from utils.cache import cache
from utils.logger import logger
from utils.errors import RateLimitException


class RateLimiter:
    """
    Rate limiter using sliding window algorithm with Redis.
    """
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        requests_per_day: int = 10000
    ):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Max requests per minute
            requests_per_hour: Max requests per hour
            requests_per_day: Max requests per day
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.requests_per_day = requests_per_day
    
    def _get_client_id(self, request: Request) -> str:
        """
        Get unique client identifier from request.
        
        Args:
            request: FastAPI request
        
        Returns:
            Client identifier (user_id or IP address)
        """
        # Try to get user_id from auth (if implemented)
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"
        
        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        
        return f"ip:{ip}"
    
    def _get_rate_limit_key(self, client_id: str, window: str) -> str:
        """
        Generate Redis key for rate limit tracking.
        
        Args:
            client_id: Client identifier
            window: Time window (minute, hour, day)
        
        Returns:
            Redis key
        """
        return f"rate_limit:{client_id}:{window}"
    
    def _check_limit(
        self,
        client_id: str,
        window: str,
        limit: int,
        ttl: int
    ) -> tuple[bool, int, int]:
        """
        Check if client has exceeded rate limit for a time window.
        
        Args:
            client_id: Client identifier
            window: Time window name
            limit: Request limit
            ttl: Time to live in seconds
        
        Returns:
            Tuple of (is_allowed, current_count, retry_after)
        """
        key = self._get_rate_limit_key(client_id, window)
        
        try:
            # Get current count
            current = cache.get(key)
            count = int(current) if current else 0
            
            # Check if limit exceeded
            if count >= limit:
                # Get TTL to calculate retry_after
                ttl_remaining = cache.get_ttl(key)
                retry_after = max(ttl_remaining, 0)
                return False, count, retry_after
            
            # Increment counter
            if count == 0:
                # First request in window, set with TTL
                cache.set(key, 1, ttl)
            else:
                # Increment existing counter
                cache.client.incr(key)
            
            return True, count + 1, 0
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # On error, allow the request (fail open)
            return True, 0, 0
    
    def check_rate_limit(self, request: Request) -> Optional[dict]:
        """
        Check all rate limits for a request.
        
        Args:
            request: FastAPI request
        
        Returns:
            None if allowed, dict with error info if rate limited
        """
        client_id = self._get_client_id(request)
        
        # Check minute limit
        allowed, count, retry_after = self._check_limit(
            client_id,
            "minute",
            self.requests_per_minute,
            60
        )
        
        if not allowed:
            logger.warning(
                f"Rate limit exceeded for {client_id}: {count} requests in last minute"
            )
            return {
                "window": "minute",
                "limit": self.requests_per_minute,
                "current": count,
                "retry_after": retry_after
            }
        
        # Check hour limit
        allowed, count, retry_after = self._check_limit(
            client_id,
            "hour",
            self.requests_per_hour,
            3600
        )
        
        if not allowed:
            logger.warning(
                f"Rate limit exceeded for {client_id}: {count} requests in last hour"
            )
            return {
                "window": "hour",
                "limit": self.requests_per_hour,
                "current": count,
                "retry_after": retry_after
            }
        
        # Check day limit
        allowed, count, retry_after = self._check_limit(
            client_id,
            "day",
            self.requests_per_day,
            86400
        )
        
        if not allowed:
            logger.warning(
                f"Rate limit exceeded for {client_id}: {count} requests in last day"
            )
            return {
                "window": "day",
                "limit": self.requests_per_day,
                "current": count,
                "retry_after": retry_after
            }
        
        return None
    
    def get_rate_limit_headers(self, request: Request) -> dict:
        """
        Get rate limit headers for response.
        
        Args:
            request: FastAPI request
        
        Returns:
            Dict of headers
        """
        client_id = self._get_client_id(request)
        
        headers = {}
        
        try:
            # Get current counts
            minute_key = self._get_rate_limit_key(client_id, "minute")
            hour_key = self._get_rate_limit_key(client_id, "hour")
            day_key = self._get_rate_limit_key(client_id, "day")
            
            minute_count = int(cache.get(minute_key) or 0)
            hour_count = int(cache.get(hour_key) or 0)
            day_count = int(cache.get(day_key) or 0)
            
            # Add headers
            headers["X-RateLimit-Limit-Minute"] = str(self.requests_per_minute)
            headers["X-RateLimit-Remaining-Minute"] = str(
                max(0, self.requests_per_minute - minute_count)
            )
            
            headers["X-RateLimit-Limit-Hour"] = str(self.requests_per_hour)
            headers["X-RateLimit-Remaining-Hour"] = str(
                max(0, self.requests_per_hour - hour_count)
            )
            
            headers["X-RateLimit-Limit-Day"] = str(self.requests_per_day)
            headers["X-RateLimit-Remaining-Day"] = str(
                max(0, self.requests_per_day - day_count)
            )
            
        except Exception as e:
            logger.error(f"Error getting rate limit headers: {e}")
        
        return headers


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce rate limits on API requests.
    """
    
    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        requests_per_day: int = 10000,
        exclude_paths: Optional[list] = None
    ):
        """
        Initialize rate limit middleware.
        
        Args:
            app: FastAPI application
            requests_per_minute: Max requests per minute
            requests_per_hour: Max requests per hour
            requests_per_day: Max requests per day
            exclude_paths: List of paths to exclude from rate limiting
        """
        super().__init__(app)
        self.rate_limiter = RateLimiter(
            requests_per_minute=requests_per_minute,
            requests_per_hour=requests_per_hour,
            requests_per_day=requests_per_day
        )
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable):
        """
        Process request and check rate limits.
        
        Args:
            request: FastAPI request
            call_next: Next middleware/handler
        
        Returns:
            Response
        """
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            response = await call_next(request)
            return response
        
        # Check rate limit
        rate_limit_error = self.rate_limiter.check_rate_limit(request)
        
        if rate_limit_error:
            # Rate limit exceeded
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "message": f"Rate limit exceeded: {rate_limit_error['current']} requests in last {rate_limit_error['window']}",
                    "details": {
                        "window": rate_limit_error["window"],
                        "limit": rate_limit_error["limit"],
                        "current": rate_limit_error["current"],
                        "retry_after": rate_limit_error["retry_after"]
                    },
                    "timestamp": datetime.utcnow().isoformat()
                },
                headers={
                    "Retry-After": str(rate_limit_error["retry_after"]),
                    "X-RateLimit-Limit": str(rate_limit_error["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + rate_limit_error["retry_after"])
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        headers = self.rate_limiter.get_rate_limit_headers(request)
        for key, value in headers.items():
            response.headers[key] = value
        
        return response


# Create default rate limiter instance
default_rate_limiter = RateLimiter()
