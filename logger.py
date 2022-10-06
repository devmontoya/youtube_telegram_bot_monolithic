import logging


def logger(logger_name: str):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # File
    file_log = logging.FileHandler(f"{logger_name}.log")
    file_log.setLevel(logging.INFO)
    file_log.setFormatter(formatter)

    # Console
    console_log = logging.StreamHandler()
    console_log.setLevel(logging.DEBUG)
    console_log.setFormatter(formatter)

    logger.addHandler(file_log)
    logger.addHandler(console_log)

    return logger


log = logger("Youtube_bot")
