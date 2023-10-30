"""
:magic:
"""
from typing import Any, Optional


def nested_get(d: dict[Any, Any], *args) -> Optional[Any]:
    tmp = d
    result = None
    for arg in args:
        result = tmp.get(arg)
        if result is None:
            return None

        tmp = result

    return result
