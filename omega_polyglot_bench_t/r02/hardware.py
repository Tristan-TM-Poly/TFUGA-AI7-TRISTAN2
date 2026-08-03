"""Conservative local hardware fingerprinting without privileged probes."""
from __future__ import annotations

from hashlib import sha256
import json
import os
import platform
import sys

from .model import HardwareProfile


def fingerprint() -> HardwareProfile:
    raw = {
        "system": platform.system() or "unknown",
        "machine": platform.machine() or "unknown",
        "processor": platform.processor() or "unknown",
        "python": platform.python_version(),
        "cpu_count": os.cpu_count() or 1,
        "byteorder": sys.byteorder,
    }
    profile_id = "hw_" + sha256(json.dumps(raw, sort_keys=True).encode()).hexdigest()[:20]
    return HardwareProfile(profile_id=profile_id, features=(), **raw)
