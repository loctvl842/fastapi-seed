from typing import Any, List


def nth(arr: List[Any], n: int, default: Any = None) -> any:
    """
    Get the nth element from an array, if it exists, otherwise return the default value.
    """
    try:
        return arr[n]
    except IndexError:
        return default
