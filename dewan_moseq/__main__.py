import logging
import logging.config
from pathlib import Path
from dewan_moseq import load
PATH = "../test_data/results.h5"

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": "DEBUG",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": "../log.log",
            "formatter": "standard",
            "level": "DEBUG",
        },
    },
    "root": {  # Catch-all for everything
        "handlers": ["console", "file"],
        "level": "DEBUG",
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

def main():
    try:
        all_data = load.readh5(Path(PATH))
    except FileNotFoundError:
        logger.error("File [%s] not found", PATH)
        return -1

    all_data = load.relabel_data_dict(all_data)
    print(all_data)

if __name__ == "__main__":
    main()