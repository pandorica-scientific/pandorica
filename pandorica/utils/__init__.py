# PANDORICA — analytical tools for electron microscopy
# Copyright (c) 2026 Robert Kiewisz
#
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# See LICENSE for details.

"""
General utilities shared across pandorica.

These helpers don't belong to any single domain (the stitcher, napari plugin,
or future tools); they're pure numerical / point-cloud / geometry primitives
that any pandorica module can call without circular-import worries. Sub-
modules:

* :mod:`pandorica.utils.pointcloud` — point-cloud helpers, currently
  :func:`pc_median_dist` (the ρ-scale unit the stitcher uses for portability
  across pixel sizes).

Import the specific helper you need:

    from pandorica.utils.pointcloud import pc_median_dist
"""
