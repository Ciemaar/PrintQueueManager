"""Patches multiprocessing get_context on Windows to prevent rq import crashes."""

import multiprocessing
import platform

if platform.system() == "Windows":
    original_get_context = multiprocessing.get_context

    def patched_get_context(method=None):
        """Mock out the fork context to run locally on windows."""
        if method == "fork":
            # On Windows, 'fork' is not available. RQ tries to get the fork context
            # during import. By returning the default context instead, we prevent
            # the ValueError from crashing the application and tests.
            # Note: The worker itself won't run properly on Windows, but the webapp
            # can still enqueue jobs to Redis.
            return original_get_context()
        return original_get_context(method)

    multiprocessing.get_context = patched_get_context
