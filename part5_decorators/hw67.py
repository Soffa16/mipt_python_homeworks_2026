import datetime
import functools
import json
from typing import Any, ParamSpec, Protocol, TypeVar
from urllib.request import urlopen

INVALID_CRITICAL_COUNT = "Breaker count must be positive integer!"
INVALID_RECOVERY_TIME = "Breaker recovery time must be positive integer!"
VALIDATIONS_FAILED = "Invalid decorator args."
TOO_MUCH = "Too much requests, just wait."


P = ParamSpec("P")
R_co = TypeVar("R_co", covariant=True)


class CallableWithMeta(Protocol[P, R_co]):
    __name__: str
    __module__: str

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R_co: ...


class BreakerError(Exception):
    def __init__(self, message: str, func_name: str, block_time: datetime.datetime):
        super().__init__(message)
        self.func_name = func_name
        self.block_time = block_time


class CircuitBreaker:
    def __init__(
        self,
        critical_count: int = 5,
        time_to_recover: int = 30,
        triggers_on: type[Exception] = Exception,
    ):
        errors = []
        if not isinstance(critical_count, int) or critical_count <= 0:
            errors.append(ValueError(INVALID_CRITICAL_COUNT))
        if not isinstance(time_to_recover, int) or time_to_recover <= 0:
            errors.append(ValueError(INVALID_RECOVERY_TIME))

        if errors:
            raise ExceptionGroup(VALIDATIONS_FAILED, errors)

        self.critical_count = critical_count
        self.time_to_recover = time_to_recover
        self.triggers_on = triggers_on

        self._failures = 0
        self._last_failure_time: datetime.datetime | None = None

    def __call__(self, func: CallableWithMeta[P, R_co]) -> CallableWithMeta[P, R_co]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R_co:
            now = datetime.datetime.now(datetime.UTC)
            full_name = f"{func.__module__}.{func.__name__}"

            self._maybe_raise_if_blocked(now, full_name)

            try:
                result = func(*args, **kwargs)
            except self.triggers_on as e:
                self._register_failure(now, full_name, e)
                raise
            else:
                self._register_success()
                return result

        return wrapper

    def _maybe_raise_if_blocked(self, now: datetime.datetime, full_name: str) -> None:
        if self._last_failure_time is None:
            return

        time_passed = (now - self._last_failure_time).total_seconds()
        if time_passed < self.time_to_recover:
            raise BreakerError(TOO_MUCH, full_name, self._last_failure_time)

        self._failures = 0
        self._last_failure_time = None

    def _register_success(self) -> None:
        self._failures = 0

    def _register_failure(
        self,
        now: datetime.datetime,
        full_name: str,
        error: Exception,
    ) -> None:
        self._failures += 1
        if self._failures < self.critical_count:
            return

        self._last_failure_time = now
        raise BreakerError(TOO_MUCH, full_name, self._last_failure_time) from error


circuit_breaker = CircuitBreaker(5, 30, Exception)


# @circuit_breaker
def get_comments(post_id: int) -> Any:
    """
    Получает комментарии к посту

    Args:
        post_id (int): Идентификатор поста

    Returns:
        list[dict[int | str]]: Список комментариев
    """
    response = urlopen(f"https://jsonplaceholder.typicode.com/comments?postId={post_id}")
    return json.loads(response.read())


if __name__ == "__main__":
    comments = get_comments(1)
