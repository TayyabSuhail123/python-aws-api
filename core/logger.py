import logging
import structlog

# The descion to use structlog was made so that the logs can be machine readable by cloudfront or Grafana

def configure_logging(level: int = logging.INFO) -> None:
    
    logging.basicConfig(
        level=level,
        format="%(message)s",        
    )

    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(level),
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),   # adds ISO8601 timestamp
            structlog.processors.add_log_level,            # adds "level" field
            structlog.processors.JSONRenderer(),           # final JSON output
        ],
    )
