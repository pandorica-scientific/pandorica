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

"""Tests for the constellation (shape-context) descriptor (``constellation.py``)."""

import numpy as np
import pytest

from pandorica.stitch.matching import matcher as mt
from pandorica.stitch.matching.constellation import (
    descriptor_cost,
    shape_context_descriptors,
)


def _ep(mt_id, pos):
    return {"id": mt_id, "pos": np.array(pos, dtype=float), "dir": np.array([1.0, 0, 0])}


def _constellation(center, offsets, ids_from=0):
    """A centre endpoint (index 0) plus neighbours at the given offsets."""
    eps = [_ep(ids_from, (center[0], center[1], 0.0))]
    for i, (dx, dy) in enumerate(offsets, 1):
        eps.append(_ep(ids_from + i, (center[0] + dx, center[1] + dy, 0.0)))
    return eps


def test_descriptors_row_normalised():
    eps = _constellation((0, 0), [(10, 0), (0, 10), (-10, 0), (0, -10)])
    desc = shape_context_descriptors(eps, rho=10.0)
    sums = desc.sum(axis=1)
    # Every endpoint with neighbours in range sums to 1 (histogram); none exceeds 1.
    assert np.all(sums <= 1.0 + 1e-9)
    assert sums[0] == pytest.approx(1.0)  # centre sees all four neighbours


def test_cost_identical_is_zero_disjoint_is_high():
    a = _constellation((0, 0), [(10, 0), (0, 10), (-10, 0)])
    b = _constellation((500, 500), [(10, 0), (0, 10), (-10, 0)])  # same pattern, far away
    da = shape_context_descriptors(a, rho=10.0)[0]
    db = shape_context_descriptors(b, rho=10.0)[0]
    assert descriptor_cost(da, da) == pytest.approx(0.0)
    # Translation-invariant: identical arrangement at a different location → ~0 cost.
    assert descriptor_cost(da, db) == pytest.approx(0.0, abs=1e-9)


def test_cost_separates_by_neighbourhood_pattern():
    # Same centre position, OPPOSITE neighbour arrangements → descriptors must disagree,
    # which is exactly the dense-parallel tie-break the term exists for.
    ref = _constellation((0, 0), [(10, 0), (0, 10)])          # neighbours right + up
    same = _constellation((0, 0), [(10, 0), (0, 10)])         # same pattern
    diff = _constellation((0, 0), [(-10, 0), (0, -10)])       # neighbours left + down
    d_ref = shape_context_descriptors(ref, rho=10.0)[0]
    d_same = shape_context_descriptors(same, rho=10.0)[0]
    d_diff = shape_context_descriptors(diff, rho=10.0)[0]
    assert descriptor_cost(d_ref, d_same) < descriptor_cost(d_ref, d_diff)
    assert descriptor_cost(d_ref, d_diff) > 0.5  # opposite arrangements are very different


def test_empty_descriptor_is_neutral():
    # An endpoint with no neighbour in range yields an all-zero descriptor → neutral 0.5.
    lonely = shape_context_descriptors([_ep(0, (0, 0, 0))], rho=10.0)
    assert lonely.shape[0] == 1
    assert descriptor_cost(lonely[0], lonely[0]) == pytest.approx(0.5)


def test_match_sections_runs_with_constellation_weight():
    # Integration: the weighted matcher returns a valid one-to-one assignment.
    ref = []
    k = 0
    for i in range(5):
        for j in range(5):
            ref.append(_ep(k, (i * 10.0, j * 10.0, 0.0)))
            k += 1
    mov = [_ep(e["id"], e["pos"] + np.array([1.0, 1.0, 0.0])) for e in ref]
    matches, ref_xy, mov_xy, conf, id_pairs = mt.match_sections(
        ref, mov, rho=10.0, constellation_weight=0.4
    )
    assert len(matches) > 0
    # One-to-one: no ref or mov index used twice.
    assert len({r for r, _, _ in matches}) == len(matches)
    assert len({c for _, c, _ in matches}) == len(matches)
