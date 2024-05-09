"""
:magic:
"""

import fnmatch
import os
from collections import deque
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Optional

from tqdm import tqdm


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


def parse_repository_name(repository_name: str) -> tuple[str, str]:
    if ":" in repository_name:
        split = repository_name.split(":")
        return split[0], split[1]

    return repository_name, "latest"


@contextmanager
def progress_bar(
    desc: Optional[str] = None,
    bar_format: Optional[str] = None,
    update_tick: int = 0.3,
    position: int = 1,
    total: Optional[int] = None,
) -> tqdm:
    bar = tqdm(
        desc=desc,
        total=total,
        bar_format=bar_format,
        position=position,
        mininterval=update_tick,
    )
    try:
        yield bar
    finally:
        # last update to get 100%
        bar.update(1)
        bar.close()
