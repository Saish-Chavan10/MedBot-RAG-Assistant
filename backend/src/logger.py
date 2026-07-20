import logging 
import sys
from pathlib import Path

try:
    import colorlog
    HAS_COLOR= True
except ImportError:
    HAS_COLOR = False

try:
    from config import LOG_LEVEL, LOG_DIR
except Exception:
    LOG_LEVEL = "INFO"
    LOG_DIR = Path("logs")
    LOG_DIR.mkdir(exist_ok=True)


def get_logger(name:str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    
    level = getattr(logging, LOG_LEVEL.upper(),logging.info)
    logger.setLevel(level)

    if HAS_COLOR:
        fmt = colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s | %(levelname)-8s%(reset)s | %(name)-25s | %(message)s",
            datefmt="%H:%M:%S",

            log_colors={
                "DEBUG":"cyan",
                "INFO":"green",
                "WARNING":"yellow",
                "ERROR":"red",
                "CRITIAL":"bold_red",
            }
        )
    else:
        fmt = logging.Formatter(
            "%(log_color)s%(asctime)s | %(levelname)-8s%(reset)s | %(name)-25s | %(message)s",
            datefmt="%H:%M:%S",
        )

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    fh = logging.FileHandler(LOG_DIR/ "medbot.log", encoding="utf-8")
    fh.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)-25s | %(message)s"
    ))
    logger.addHandler(fh)

    return logger