import config


class PresentationLogger:
    """Lightweight output control for presentation generation."""

    def __init__(
        self,
        verbose=None,
        printer=print,
    ):
        self._verbose = verbose
        self._printer = printer

    @property
    def verbose(self):
        if self._verbose is not None:
            return bool(self._verbose)

        return bool(
            config.PRESENTATION_VERBOSE_LOGGING
        )

    def detail(self, message=""):
        if self.verbose:
            self._printer(message)

    def info(self, message=""):
        self._printer(message)

    def warning(self, message):
        self._printer(f"WARNING: {message}")

    def error(self, message):
        self._printer(f"ERROR: {message}")


presentation_logger = PresentationLogger()
