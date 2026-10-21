# PANDORICA — analytical tools for electron microscopy
# Copyright (c) 2026 Robert Kiewisz
#
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# See LICENSE for details.

"""
File-format I/O for pandorica.

Format-level readers and writers shared across the project, kept apart from
domain-specific data models (the stitcher's :class:`pandorica.stitch.dataset
.Dataset`, etc.). Sub-modules:

* :mod:`pandorica.io.amira` — AmiraMesh ``.am`` image lattices and spatial
  graphs (ASCII + binary, read + write), plus folder-discovery helpers for
  Amira datasets.

Import the specific reader/writer you need rather than star-importing, to
keep the package's import-time cost bounded:

    from pandorica.io.amira import read_amira_volume, write_spatial_graph
"""
