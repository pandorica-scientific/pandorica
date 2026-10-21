# PANDORICA — analytical tools for electron microscopy
# Copyright (c) 2026 Robert Kiewisz
#
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# See LICENSE for details.

import os

from pandorica._version import version

# Temporal fallback for mps devices
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

__version__ = version
