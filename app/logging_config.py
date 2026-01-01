import sys
from pathlib import Path
from loguru import logger


def setup_logging(*, log_dir: str = "logs", level: str = "INFO") -> None:
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    logger.remove()  # remove default stderr handler

    # 1) Pretty console
    logger.add(
        sys.stderr,
        level=level,
        backtrace=False,
        diagnose=False,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message} | {extra}",
    )

    # 2) File sink with rotation/retention/compression
    logger.add(
        str(Path(log_dir) / "self_learning_{time:YYYYMMDD}.log"),
        level=level,
        rotation="10 MB",
        retention="14 days",
        compression="zip",
        encoding="utf-8",
    )
