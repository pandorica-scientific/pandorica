#!/usr/bin/env python3
# PANDORICA — analytical tools for electron microscopy
# Copyright (c) 2026 Robert Kiewisz
#
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# See LICENSE for details.

"""Keep the README citation version (and CITATION.cff) in step with the single source of truth.

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
    2  could not run: a source file was missing or had an unexpected shape

The non-zero "I had to fix something" exit is what makes the pre-commit hook
fail the commit, so a stale README cannot slip through. Re-stage the README
and commit again.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import NoReturn

REPO_ROOT = Path(__file__).resolve().parent.parent
VERSION_FILE = REPO_ROOT / "pandorica" / "_version.py"
README_FILE = REPO_ROOT / "README.md"
CFF_FILE = REPO_ROOT / "CITATION.cff"
# The top-level ``version:`` key of CITATION.cff (not indented, so nested reference versions are left alone).
CFF_RE = re.compile(r"^(version:\s*)\S+\s*$", re.MULTILINE)

# Matches the BibTeX-style field, e.g. ``  version = {1.5.0},``. Capturing the
# prefix and suffix lets us swap only the value while preserving spacing.
CITATION_RE = re.compile(r"(version\s*=\s*\{)[^}]*(\})")


def fail(message: str) -> NoReturn:
    """Report a setup problem on stderr and exit with code 2.

    Distinct from the "stale README" exit code 1 so a caller (or CI) can tell a
    real error apart from a README that merely needs syncing.
    """
    print(message, file=sys.stderr)
    sys.exit(2)


def read_source_version() -> str:
    """Pull the version string out of ``_version.py`` without importing it.

    Importing the package would drag in heavy runtime dependencies, so we read
    the assignment directly.
    """
    text = VERSION_FILE.read_text(encoding="utf-8")
    match = re.search(r"""^version\s*=\s*["']([^"']+)["']""", text, re.MULTILINE)
    if not match:
        fail(f"error: could not find a version assignment in {VERSION_FILE}")
    return match.group(1)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync the README citation version from pandorica/_version.py.",
        epilog=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="report drift without rewriting the README",
    )
    args = parser.parse_args()

    version = read_source_version()
    readme = README_FILE.read_text(encoding="utf-8")

    # Expect exactly one citation field. Zero means the README format drifted;
    # more than one means a second BibTeX block crept in (e.g. a courtesy
    # citation), and a blanket rewrite would stamp pandorica's version onto it.
    matches = CITATION_RE.findall(readme)
    if len(matches) != 1:
        fail(
            f"error: expected exactly one `version = {{...}}` citation field in "
            f"{README_FILE}, found {len(matches)}"
        )

    # Use a function replacement so ``version`` is inserted literally; a string
    # template would let backslashes or ``\g<...>`` in the value be reinterpreted
    # as regex backreferences.
    updated = CITATION_RE.sub(lambda m: m.group(1) + version + m.group(2), readme)
    stale = {}
    if updated != readme:
        stale[README_FILE] = updated
    if CFF_FILE.exists():
        cff = CFF_FILE.read_text(encoding="utf-8")
        if len(CFF_RE.findall(cff)) != 1:
            fail(f"error: expected exactly one top-level `version:` key in {CFF_FILE}")
        cff_updated = CFF_RE.sub(lambda m: m.group(1) + version, cff)
        if cff_updated != cff:
            stale[CFF_FILE] = cff_updated

    names = ", ".join(f.name for f in stale)
    if not stale:
        print(f"Citation version already {version} everywhere; nothing to do.")
        return 0

    if args.check:
        print(
            f"Citation version is stale in {names} (source is {version}). "
            "Run `python scripts/sync_version.py` to fix."
        )
        return 1

    for path, text in stale.items():
        path.write_text(text, encoding="utf-8")
    print(f"Updated the citation version to {version} in {names}. Re-stage and commit again.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
