"""
:magic:
"""
import fnmatch
import os
from collections import deque
from pathlib import Path
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


def find_first_occurrence_of_file(
    path: Path, pattern: str, max_depth: int = 4
) -> Optional[Path]:
    resolved_path_str = str(path.resolve())
    queue = deque([(resolved_path_str, 0)])
    while queue:
        curr_dir, curr_depth = queue.popleft()
        if curr_depth > max_depth:
            continue

        # Path has walk method in 3.12
        for root, dirs, files in os.walk(curr_dir):
            matches = fnmatch.filter(files, pattern)
            if matches:
                return matches[0]

            for subdir in dirs:
                queue.append((os.path.join(root, subdir), curr_depth + 1))

    return None
