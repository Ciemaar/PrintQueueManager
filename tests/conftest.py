import platform

if platform.system() == "Windows":
    import multiprocessing

    original_get_context = multiprocessing.get_context

    def dummy_get_context(method=None):
        """Mock out the fork context to run locally on windows."""
        if method == "fork":
            return original_get_context()
        return original_get_context(method)

    multiprocessing.get_context = dummy_get_context
