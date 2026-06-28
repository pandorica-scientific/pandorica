#!/usr/bin/env python3
#######################################################################
#  Serial Stitcher - An Automatic tool for tomograms stitching        #
#                                                                     #
#  https://github.com/RRobert92                                       #
#                                                                     #
#  Robert Kiewisz                                                     #
#  PolyForm Noncommercial License 1.0.0 - see LICENSE                 #
#######################################################################
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Robert Kiewisz
"""Keep the README citation version in step with the single source of truth.

The version lives in ``pandorica/_version.py``. The README citation block
hard-codes it as ``version = {X}`` because GitHub renders the README as static
text and cannot fetch anything at view time. This script reads the real
version and rewrites the README so the two can never drift.

Usage
-----
    python scripts/sync_version.py          # rewrite README if it is stale
    python scripts/sync_version.py --check  # report drift, change nothing

Exit codes
----------
    0  README already matched the source version (nothing to do)
    1  README was stale; it has now been rewritten (or, with --check, would be)

The non-zero "I had to fix something" exit is what makes the pre-commit hook
fail the commit, so a stale README cannot slip through. Re-stage the README
and commit again.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VERSION_FILE = REPO_ROOT / "pandorica" / "_version.py"
README_FILE = REPO_ROOT / "README.md"

# Matches the BibTeX-style field, e.g. ``  version = {1.5.0},``. Capturing the
# prefix and suffix lets us swap only the value while preserving spacing.
CITATION_RE = re.compile(r"(version\s*=\s*\{)[^}]*(\})")


def read_source_version() -> str:
    """Pull the version string out of ``_version.py`` without importing it.

    Importing the package would drag in heavy runtime dependencies, so we read
    the assignment directly.
    """
    text = VERSION_FILE.read_text(encoding="utf-8")
    match = re.search(r"""^version\s*=\s*["']([^"']+)["']""", text, re.MULTILINE)
    if not match:
        sys.exit(f"error: could not find a version assignment in {VERSION_FILE}")
    return match.group(1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="report drift without rewriting the README",
    )
    args = parser.parse_args()

    version = read_source_version()
    readme = README_FILE.read_text(encoding="utf-8")

    matches = CITATION_RE.findall(readme)
    if not matches:
        sys.exit(
            f"error: no `version = {{...}}` citation field found in {README_FILE}"
        )

    updated = CITATION_RE.sub(rf"\g<1>{version}\g<2>", readme)
    if updated == readme:
        print(f"README citation version already {version}; nothing to do.")
        return 0

    if args.check:
        print(
            f"README citation version is stale (source is {version}). "
            "Run `python scripts/sync_version.py` to fix."
        )
        return 1

    README_FILE.write_text(updated, encoding="utf-8")
    print(
        f"Updated README citation version to {version}. "
        "Re-stage README.md and commit again."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
