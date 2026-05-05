from __future__ import annotations

import logging
import sys

_LOG = "layerfield_qaoa"


def get_logger() -> logging.Logger:
    log = logging.getLogger(_LOG)
    if not log.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(message)s"))
        log.addHandler(handler)
        log.propagate = False
    log.setLevel(logging.INFO)
    return log


__all__ = ["get_logger"]
