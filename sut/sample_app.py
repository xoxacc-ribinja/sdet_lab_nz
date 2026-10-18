#!/usr/bin/env python3
"""A small, deterministic CLI program to test as a separate process.

Modes:
  ok   - write a message to stdout and return 0
  fail - write an error to stderr and return 17
  slow - print a starting message, wait 5 seconds, then return 0
"""

import sys
import time


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in ("ok", "fail", "slow"):
        print("Usage: python3 sut/sample_app.py <ok|fail|slow>", file=sys.stderr)
        return 2

    mode = sys.argv[1]
    if mode == "ok":
        print("RESULT: OK")
        return 0
    if mode == "fail":
        print("ERROR: simulated failure", file=sys.stderr)
        return 17

    print("STARTED", flush=True)
    time.sleep(5)
    print("RESULT: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
