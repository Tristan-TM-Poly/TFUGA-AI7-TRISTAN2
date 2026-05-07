from __future__ import annotations

import argparse
import asyncio
import hashlib
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class GHFMConfig:
    root: Path
    merkle_log: Path
    interaction_file: Path
    stase_threshold_seconds: int = 3600
    raman_interval_seconds: float = 10.0
    merkle_interval_seconds: float = 15.0
    ms33_interval_seconds: float = 5.0
    max_cycles: int | None = None

    @classmethod
    def from_root(cls, root: Path, max_cycles: int | None = None) -> "GHFMConfig":
        root = root.expanduser().resolve()
        return cls(
            root=root,
            merkle_log=root / "Yggdrasil_Merkle.log",
            interaction_file=root / "ms33_telemetry.log",
            max_cycles=max_cycles,
        )


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def compute_merkle_hash(previous_hash: str, timestamp: str, label: str) -> str:
    payload = f"{previous_hash}|{timestamp}|{label}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def append_merkle_block(log_path: Path, previous_hash: str, label: str) -> str:
    timestamp = utc_now_iso()
    new_hash = compute_merkle_hash(previous_hash, timestamp, label)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"{timestamp} | {new_hash} | {label}\n")
    return new_hash


def touch_interaction_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)


def seconds_since_interaction(path: Path) -> float | None:
    if not path.exists():
        return None
    return time.time() - path.stat().st_mtime


async def vector_raman_ingestion(config: GHFMConfig, stop: asyncio.Event) -> None:
    cycle = 0
    while not stop.is_set():
        cycle += 1
        print("[GHFM-D1] Raman ingestion placeholder: ready for PyMC or spectral hooks.")
        if config.max_cycles is not None and cycle >= config.max_cycles:
            return
        await asyncio.sleep(config.raman_interval_seconds)


async def vector_yggdrasil_merkle(config: GHFMConfig, stop: asyncio.Event) -> None:
    previous_hash = "GENESIS_BLOCK_TFUGA"
    cycle = 0
    while not stop.is_set():
        cycle += 1
        previous_hash = await asyncio.to_thread(
            append_merkle_block,
            config.merkle_log,
            previous_hash,
            "Validated",
        )
        print(f"[GHFM-D2] Merkle block sealed -> {previous_hash[:16]}...")
        if config.max_cycles is not None and cycle >= config.max_cycles:
            return
        await asyncio.sleep(config.merkle_interval_seconds)


async def vector_ms33_stase(config: GHFMConfig, stop: asyncio.Event) -> None:
    cycle = 0
    while not stop.is_set():
        cycle += 1
        seconds = seconds_since_interaction(config.interaction_file)
        if seconds is None:
            touch_interaction_file(config.interaction_file)
            print("[GHFM-D3] MS33 telemetry initialized.")
        elif seconds > config.stase_threshold_seconds:
            print(f"[GHFM-D3] MS33 stase detected after {int(seconds)}s. Energy-saving mode advised.")
        else:
            print(f"[GHFM-D3] Node active. Last interaction: {int(seconds)}s.")
        if config.max_cycles is not None and cycle >= config.max_cycles:
            return
        await asyncio.sleep(config.ms33_interval_seconds)


async def run_ouroboros(config: GHFMConfig) -> None:
    stop = asyncio.Event()
    await asyncio.gather(
        vector_raman_ingestion(config, stop),
        vector_yggdrasil_merkle(config, stop),
        vector_ms33_stase(config, stop),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TFUGA GHFMnD async local orchestrator")
    parser.add_argument("--root", default=".", help="Working directory for local logs")
    parser.add_argument("--max-cycles", type=int, default=None, help="Finite cycles for tests or dry runs")
    parser.add_argument("--stase-threshold", type=int, default=3600)
    parser.add_argument("--raman-interval", type=float, default=10.0)
    parser.add_argument("--merkle-interval", type=float, default=15.0)
    parser.add_argument("--ms33-interval", type=float, default=5.0)
    return parser


def config_from_args(args: argparse.Namespace) -> GHFMConfig:
    root = Path(args.root).expanduser().resolve()
    return GHFMConfig(
        root=root,
        merkle_log=root / "Yggdrasil_Merkle.log",
        interaction_file=root / "ms33_telemetry.log",
        stase_threshold_seconds=args.stase_threshold,
        raman_interval_seconds=args.raman_interval,
        merkle_interval_seconds=args.merkle_interval,
        ms33_interval_seconds=args.ms33_interval,
        max_cycles=args.max_cycles,
    )


def main() -> None:
    args = build_parser().parse_args()
    config = config_from_args(args)
    print("=== TFUGA GHFMnD OUROBOROS ONLINE ===")
    try:
        asyncio.run(run_ouroboros(config))
    except KeyboardInterrupt:
        print("\n[SYSTEM] Manual interruption. Ouroboros suspended.")


if __name__ == "__main__":
    main()
