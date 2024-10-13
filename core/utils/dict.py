from typing import Any, Optional


def dict_deep_extend(*dicts):
    """
    Merge an arbitrary number of dictionaries deeply.
    """

    def merge_2_dicts(a, b):
        if isinstance(a, dict) and isinstance(b, dict):
            result = {**b}
            for key, value in a.items():
                if key not in result:
                    result[key] = value
                else:
                    result[key] = merge_2_dicts(value, result[key])
            return result
        else:
            return a if b is None else b

    merged = {}
    for d in dicts:
        if not isinstance(d, dict):
            raise TypeError("All arguments must be dictionaries")
        merged = merge_2_dicts(merged, d)
    return merged


def dig(dict_: dict[str, Any], path: str, default: Optional[Any] = None) -> Any:
    keys = path.split(".")
    value = dict_
    for key in keys:
        try:
            value = value[key]
        except KeyError:
            return default
    return value


def plant(dict_: dict[str, Any], path: str, value: Any):
    keys = path.split(".")
    current = dict_
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    current[keys[-1]] = value
