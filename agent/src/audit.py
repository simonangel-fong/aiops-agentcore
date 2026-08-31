"""Record each tool call."""

import functools
import json
import logging
import time

logger = logging.getLogger("agent.audit")


def _summarise(result):
    """Describe the result without dumping it -- logs and runbook passages are
    untrusted text and do not belong verbatim in the audit trail."""
    if isinstance(result, dict):
        return {
            "keys": sorted(result)[:8],
            "available": result.get("available", True),
            "bytes": len(json.dumps(result, default=str)),
        }
    return {"type": type(result).__name__, "bytes": len(str(result))}


def audited(func):
    """Log one line before and after each tool call."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        started = time.monotonic()
        logger.info(
            "tool_call %s",
            json.dumps({"tool": func.__name__, "args": kwargs or list(args)}, default=str),
        )
        try:
            result = func(*args, **kwargs)
        except Exception as exc:
            logger.info(
                "tool_result %s",
                json.dumps(
                    {
                        "tool": func.__name__,
                        "ok": False,
                        "error": str(exc)[:200],
                        "ms": round((time.monotonic() - started) * 1000),
                    }
                ),
            )
            raise

        logger.info(
            "tool_result %s",
            json.dumps(
                {
                    "tool": func.__name__,
                    "ok": True,
                    "ms": round((time.monotonic() - started) * 1000),
                    **_summarise(result),
                },
                default=str,
            ),
        )
        return result

    return wrapper
