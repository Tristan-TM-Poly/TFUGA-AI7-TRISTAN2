"""Private worker process for :mod:`omega_ai_tristan_lab.sandbox`."""

from __future__ import annotations

import contextlib
import io
import json
import socket
import sys


def _apply_posix_limits(memory_mb: int) -> None:
    try:
        import resource
    except ImportError:
        return
    memory = int(memory_mb) * 1024 * 1024
    try:
        resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
    except (ValueError, OSError):
        pass


def _deny_network() -> None:
    def blocked(*args, **kwargs):
        raise PermissionError("Network access blocked by Tristan user-space sandbox")
    socket.create_connection = blocked
    socket.socket.connect = blocked


def main() -> int:
    request = json.load(sys.stdin)
    _apply_posix_limits(int(request.get("memory_mb", 512)))
    permissions = set(map(str, request.get("allowed_permissions", ("PURE",))))
    from .policy import PolicyContext
    from .runtime import TristanRuntime

    runtime = TristanRuntime(auto_discover=True)
    if "NETWORK_READ" not in permissions:
        _deny_network()

    stream = io.StringIO()
    with contextlib.redirect_stdout(stream):
        execution = runtime.execute_capability(
            str(request["capability"]),
            request.get("payload") or {},
            policy_context=PolicyContext.sandbox(permissions - {"PURE"}),
        )
    json.dump({"output": execution.output, "execution": execution.to_dict(), "worker_stdout": stream.getvalue()}, sys.stdout, default=str)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
