import asyncio
from typing import Any, Callable, TypeVar

T = TypeVar("T")


async def attempt(fn: Callable[..., T], *args, **kwargs) -> T | Exception:
    """
    Attempt to run a function and return the result or an exception

    Args:
        fn (Callable): Function to run

    Returns:
        Result of the function or an exception

    Examples:
        >>> import asyncio
        >>> result = asyncio.run(attempt(lambda x: 10 / x, 2))
        >>> assert result == 5
    """

    try:
        if asyncio.iscoroutinefunction(fn):
            return await fn(*args, **kwargs)
        return fn(*args, **kwargs)
    except Exception as e:
        return e


def is_error(e: Any):
    """
    Check if the given object is an instance of Exception or its subclasses

    Args:
        e (Any): Object to check

    Returns:
        bool: True if the object is an instance of Exception or its subclasses, False otherwise
    """
    exception_types = [Exception, ValueError, TypeError]  # Add more as needed

    # Check if the object is an instance of any of the specified exception types
    return any(isinstance(e, exc_type) for exc_type in exception_types)
