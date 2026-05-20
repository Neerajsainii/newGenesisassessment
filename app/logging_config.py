import logging
import sys


class _JobIdFallbackFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "job_id"):
            record.job_id = "-"
        return True


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(_JobIdFallbackFilter())
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s job_id=%(job_id)s %(message)s",
        handlers=[handler],
    )


class JobLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        extra = kwargs.get("extra", {})
        if "job_id" not in extra:
            extra["job_id"] = self.extra.get("job_id", "-")
        kwargs["extra"] = extra
        return msg, kwargs
