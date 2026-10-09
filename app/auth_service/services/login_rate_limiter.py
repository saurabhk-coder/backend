import threading
import time
from typing import Dict, List, Optional, Tuple


class LoginRateLimiter:
    """
    In-memory rate limiter and account lockout service for login attempts.
    Thread-safe sliding-window attempt tracker with temporary blocking.
    """

    def __init__(
        self,
        max_attempts: int = 5,
        window_seconds: int = 300,
        block_duration_seconds: int = 300,
    ):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.block_duration_seconds = block_duration_seconds
        self._attempts: Dict[str, List[float]] = {}
        self._blocked_until: Dict[str, float] = {}
        self._lock = threading.Lock()

    def _normalize_key(self, username: Optional[str]) -> str:
        return (username or "").strip().lower()

    def is_blocked(self, username: Optional[str]) -> Tuple[bool, int]:
        """
        Check whether the given user is currently blocked.
        Returns:
            (is_blocked, remaining_seconds)
        """
        key = self._normalize_key(username)
        if not key:
            return False, 0

        with self._lock:
            now = time.time()
            blocked_until = self._blocked_until.get(key)
            if blocked_until is not None:
                if now < blocked_until:
                    remaining = int(blocked_until - now) + 1
                    return True, remaining
                else:
                    # Block expired: clean up
                    del self._blocked_until[key]
                    self._attempts.pop(key, None)

            # Check if active attempts within sliding window already reached max
            attempts = self._get_active_attempts(key, now)
            if len(attempts) >= self.max_attempts:
                self._blocked_until[key] = now + self.block_duration_seconds
                return True, self.block_duration_seconds

            return False, 0

    def _get_active_attempts(self, key: str, now: float) -> List[float]:
        cutoff = now - self.window_seconds
        active = [t for t in self._attempts.get(key, []) if t > cutoff]
        self._attempts[key] = active
        return active

    def record_attempt(self, username: Optional[str]) -> Tuple[bool, int, int]:
        """
        Record a login attempt timestamp for the user.
        Returns:
            (is_blocked_now, current_attempt_count, remaining_block_seconds)
        """
        key = self._normalize_key(username)
        if not key:
            return False, 0, 0

        with self._lock:
            now = time.time()
            attempts = self._get_active_attempts(key, now)
            attempts.append(now)
            self._attempts[key] = attempts
            count = len(attempts)

            if count >= self.max_attempts:
                self._blocked_until[key] = now + self.block_duration_seconds
                return True, count, self.block_duration_seconds

            return False, count, 0

    def record_failed_attempt(self, username: Optional[str]) -> Tuple[bool, int, int]:
        """
        Record a failed login attempt for the user.
        If attempts reach max_attempts, the user is blocked for block_duration_seconds.
        """
        return self.record_attempt(username)

    def block_user(
        self, username: Optional[str], duration_seconds: Optional[int] = None
    ) -> None:
        """Manually block a user for duration_seconds."""
        key = self._normalize_key(username)
        if not key:
            return
        duration = (
            duration_seconds
            if duration_seconds is not None
            else self.block_duration_seconds
        )
        with self._lock:
            self._blocked_until[key] = time.time() + duration

    def clear(self, username: Optional[str] = None) -> None:
        """
        Reset attempts and unblock.
        If username is provided, resets only that user.
        If username is None, resets all rate limiter state.
        """
        with self._lock:
            if username is None:
                self._attempts.clear()
                self._blocked_until.clear()
            else:
                key = self._normalize_key(username)
                self._attempts.pop(key, None)
                self._blocked_until.pop(key, None)

    def get_attempts_count(self, username: Optional[str]) -> int:
        """Return the number of active attempts recorded within current window."""
        key = self._normalize_key(username)
        if not key:
            return 0
        with self._lock:
            return len(self._get_active_attempts(key, time.time()))


LOGIN_RATE_LIMITER = LoginRateLimiter(
    max_attempts=5,
    window_seconds=300,
    block_duration_seconds=300,
)
