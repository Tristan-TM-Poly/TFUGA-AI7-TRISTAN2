"""Local-first digest prototype package."""

from .demo_data import DemoDataset, generate_demo_dataset, write_demo_dataset
from .manifest import (
    ChecksumEntry,
    ReviewInfo,
    RunManifest,
    SourceInfo,
    build_manifest,
    checksum_entries,
    discover_output_files,
    sha256_file,
    write_checksum_registry,
    write_manifest,
)

__all__ = [
    "DemoDataset",
    "generate_demo_dataset",
    "write_demo_dataset",
    "ChecksumEntry",
    "ReviewInfo",
    "RunManifest",
    "SourceInfo",
    "build_manifest",
    "checksum_entries",
    "discover_output_files",
    "sha256_file",
    "write_checksum_registry",
    "write_manifest",
]
