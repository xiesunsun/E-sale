import time
from threading import Lock


class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: float = 5.0,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self.failure_count = 0
        self.state = "CLOSED"
        self.opened_at: float | None = None

        self._lock = Lock()

    def allow_request(self) -> bool:
        with self._lock:
            if self.state == "CLOSED":
                return True

            if self.state == "OPEN":
                elapsed = time.monotonic() - self.opened_at

                if elapsed >= self.recovery_timeout:
                    self.state = "HALF_OPEN"
                    return True

                return False

            # HALF_OPEN 时已经有一个探测请求了
            return False

    def record_success(self):
        with self._lock:
            self.failure_count = 0
            self.state = "CLOSED"
            self.opened_at = None

    def record_failure(self):
        with self._lock:
            self.failure_count += 1

            if (
                self.state == "HALF_OPEN"
                or self.failure_count >= self.failure_threshold
            ):
                self.state = "OPEN"
                self.opened_at = time.monotonic()

    def snapshot(self):
        with self._lock:
            return {
                "state": self.state,
                "failure_count": self.failure_count,
            }
