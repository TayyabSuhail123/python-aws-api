import logging, sys, structlog
from config import settings

NUM_LEVEL = getattr(logging, settings.log_level.upper(), logging.INFO)

def configure_logging() -> None:
    logging.basicConfig(
        level=NUM_LEVEL,
        format="%(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(NUM_LEVEL),
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
