import json
import sys
from pathlib import Path

TARGET = 512


def main():
    from pypdf import PdfReader
    pdf = Path(sys.argv[1])
    actual = len(PdfReader(str(pdf)).pages)
    receipt = {"target_pages": TARGET, "actual_pages": actual, "delta": TARGET - actual, "status": "PASS" if actual == TARGET else "HOLD"}
    Path("page_count_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0 if actual == TARGET else 2


if __name__ == "__main__":
    raise SystemExit(main())
