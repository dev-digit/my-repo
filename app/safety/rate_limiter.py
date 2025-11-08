"""
Rate limiting for Pombi AI Assistant
"""

import time
import asyncio
from typing import Dict, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta

from app.config import settings
from app.utils.logging import setup_logging

logger = setup_logging(__name__)


class RateLimiter:
    """Rate limiting implementation using sliding window"""

    def __init__(self):
        self.requests_per_minute = settings.rate_limit_per_minute
        self.requests_per_hour = settings.rate_limit_per_minute * 10  # 10x hourly limit
        self.user_requests: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.global_requests: deque = deque(maxlen=10000)
        self.blocked_users: Dict[str, datetime] = {}
        self._cleanup_task = None
        self._start_cleanup_task()

    async def is_allowed(self, user_id: str, resource: str = "chat") -> tuple[bool, Dict[str, int]]:
        """
        Check if request is allowed

        Args:
            user_id: User identifier
            resource: Type of resource being requested

        Returns:
            tuple: (is_allowed, rate_limit_info)
        """
        current_time = time.time()

        # Check if user is temporarily blocked
        if user_id in self.blocked_users:
            if datetime.utcnow() < self.blocked_users[user_id]:
                return False, self._get_rate_limit_info(user_id, current_time)
            else:
                del self.blocked_users[user_id]

        # Record request
        self.user_requests[user_id].append(current_time)
        self.global_requests.append(current_time)

        # Check rate limits
        minute_limit_ok = self._check_limit(self.user_requests[user_id], 60, self.requests_per_minute)
        hour_limit_ok = self._check_limit(self.user_requests[user_id], 3600, self.requests_per_hour)
        global_limit_ok = self._check_limit(self.global_requests, 60, self.requests_per_minute * 100)  # Global limit

        if not minute_limit_ok:
            logger.warning(
                "User exceeded minute rate limit",
                extra={
                    "user_id": user_id,
                    "resource": resource,
                    "requests_per_minute": self._count_requests(self.user_requests[user_id], 60)
                }
            )
            return False, self._get_rate_limit_info(user_id, current_time)

        if not hour_limit_ok:
            logger.warning(
                "User exceeded hour rate limit",
                extra={
                    "user_id": user_id,
                    "resource": resource,
                    "requests_per_hour": self._count_requests(self.user_requests[user_id], 3600)
                }
            )
            # Block user for 5 minutes
            self.blocked_users[user_id] = datetime.utcnow() + timedelta(minutes=5)
            return False, self._get_rate_limit_info(user_id, current_time)

        if not global_limit_ok:
            logger.warning(
                "Global rate limit exceeded",
                extra={
                    "user_id": user_id,
                    "resource": resource,
                    "global_requests_per_minute": self._count_requests(self.global_requests, 60)
                }
            )
            return False, self._get_rate_limit_info(user_id, current_time)

        return True, self._get_rate_limit_info(user_id, current_time)

    def _check_limit(self, requests: deque, window_seconds: int, max_requests: int) -> bool:
        """Check if requests within window exceed limit"""
        if not requests:
            return True

        current_time = time.time()
        window_start = current_time - window_seconds

        # Count requests within window
        count = sum(1 for req_time in requests if req_time >= window_start)
        return count <= max_requests

    def _count_requests(self, requests: deque, window_seconds: int) -> int:
        """Count requests within time window"""
        if not requests:
            return 0

        current_time = time.time()
        window_start = current_time - window_seconds
        return sum(1 for req_time in requests if req_time >= window_start)

    def _get_rate_limit_info(self, user_id: str, current_time: float) -> Dict[str, int]:
        """Get current rate limit information"""
        user_minute_requests = self._count_requests(self.user_requests[user_id], 60)
        user_hour_requests = self._count_requests(self.user_requests[user_id], 3600)
        global_minute_requests = self._count_requests(self.global_requests, 60)

        # Calculate time until reset
        minute_reset = 60 - int(current_time % 60)
        hour_reset = 3600 - int(current_time % 3600)

        return {
            "requests_per_minute": user_minute_requests,
            "requests_per_hour": user_hour_requests,
            "global_requests_per_minute": global_minute_requests,
            "limit_per_minute": self.requests_per_minute,
            "limit_per_hour": self.requests_per_hour,
            "minute_reset_seconds": minute_reset,
            "hour_reset_seconds": hour_reset,
            "remaining_per_minute": max(0, self.requests_per_minute - user_minute_requests),
            "remaining_per_hour": max(0, self.requests_per_hour - user_hour_requests),
            "is_blocked": user_id in self.blocked_users,
            "blocked_until": self.blocked_users.get(user_id, datetime.utcnow()).isoformat() if user_id in self.blocked_users else None
        }

    def _start_cleanup_task(self):
        """Start background cleanup task"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_data())

    async def _cleanup_expired_data(self):
        """Cleanup expired request data"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                self._cleanup()
            except Exception as e:
                logger.error(f"Rate limiter cleanup error: {e}")

    def _cleanup(self):
        """Clean up old data"""
        current_time = time.time()
        cutoff_time = current_time - 3600  # Keep 1 hour of data

        # Clean user requests
        users_to_remove = []
        for user_id, requests in self.user_requests.items():
            # Remove old requests
            while requests and requests[0] < cutoff_time:
                requests.popleft()

            # Mark empty users for removal
            if not requests and user_id not in self.blocked_users:
                users_to_remove.append(user_id)

        for user_id in users_to_remove:
            del self.user_requests[user_id]

        # Clean global requests
        while self.global_requests and self.global_requests[0] < cutoff_time:
            self.global_requests.popleft()

        # Clean blocked users
        expired_blocks = []
        for user_id, unblock_time in self.blocked_users.items():
            if datetime.utcnow() >= unblock_time:
                expired_blocks.append(user_id)

        for user_id in expired_blocks:
            del self.blocked_users[user_id]

        if expired_blocks or users_to_remove:
            logger.info(
                "Rate limiter cleanup completed",
                extra={
                    "expired_blocks": len(expired_blocks),
                    "removed_users": len(users_to_remove),
                    "active_users": len(self.user_requests),
                    "blocked_users": len(self.blocked_users)
                }
            )

    def get_user_stats(self, user_id: str) -> Dict[str, any]:
        """Get rate limiting statistics for a user"""
        current_time = time.time()
        info = self._get_rate_limit_info(user_id, current_time)

        # Add historical data
        if user_id in self.user_requests:
            requests = list(self.user_requests[user_id])
            if requests:
                info["first_request"] = datetime.fromtimestamp(min(requests)).isoformat()
                info["last_request"] = datetime.fromtimestamp(max(requests)).isoformat()
                info["total_requests"] = len(requests)

        return info

    def get_global_stats(self) -> Dict[str, any]:
        """Get global rate limiting statistics"""
        current_time = time.time()
        global_minute_requests = self._count_requests(self.global_requests, 60)
        global_hour_requests = self._count_requests(self.global_requests, 3600)

        return {
            "global_requests_per_minute": global_minute_requests,
            "global_requests_per_hour": global_hour_requests,
            "total_active_users": len(self.user_requests),
            "total_blocked_users": len(self.blocked_users),
            "global_limit_per_minute": self.requests_per_minute * 100,
            "total_requests_in_memory": len(self.global_requests)
        }

    def reset_user_limits(self, user_id: str):
        """Reset rate limits for a specific user"""
        if user_id in self.user_requests:
            del self.user_requests[user_id]
        if user_id in self.blocked_users:
            del self.blocked_users[user_id]
        logger.info(f"Reset rate limits for user: {user_id}")

    async def close(self):
        """Cleanup rate limiter resources"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass