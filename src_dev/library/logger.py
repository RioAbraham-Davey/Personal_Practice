import logging


class Log:
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

    _GLOBAL = DEBUG
    _DEFAULT = WARNING

    def __init__(self, name, level=None):
        if level is None:
            level = Log._DEFAULT
        self.log = logging.getLogger(name)
        self.log.setLevel(Log._GLOBAL)
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(level)
        formatter = logging.Formatter("[%(levelname)s]:(%(name)s):%(message)s")
        stream_handler.setFormatter(formatter)
        self.log.addHandler(stream_handler)

    def get_logger(self):
        return self.log
