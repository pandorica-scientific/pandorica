# PANDORICA — analytical tools for electron microscopy
# Copyright (c) 2026 Robert Kiewisz
#
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# See LICENSE for details.

"""
Constellation (local shape-context) descriptors for boundary endpoints.

The endpoint matcher's distance + tangent cost describes each microtubule by a
single point and a short arrow. In a DENSE PARALLEL bundle that fingerprint is
nearly identical for an MT and its neighbour, so the assignment can't tell them
apart and produces swaps. This module adds a richer, per-MT fingerprint: the
*pattern* of where its neighbours sit — a 2-D log-polar histogram (a
shape-context, Belongie et al. 2002) of the in-plane offsets to its k nearest
boundary endpoints.

Two MTs match well on this term only when their whole local neighbourhood
*arrangement* agrees, which a lone parallel neighbour does not reproduce. The
arrangement is largely preserved across the cut (the bundle travels together),
so it is a strong cross-section disambiguator that needs no neighbour
correspondence (the histogram abstracts that away) and no ground truth.

Frame: descriptors are built in the **coarse-aligned (absolute) frame**. The
coarse pose already removes gross rotation (residual a few degrees), so an
absolute-frame histogram is coherent between the two faces; the rare
large-residual-rotation interface is handled upstream by the rotation rescue.
Births/deaths perturb a few histogram bins, not the whole descriptor, so the
term degrades gracefully rather than failing.
"""

import numpy as np
from scipy.spatial import cKDTree


def _xy(endpoints):
    return np.array([e["pos"][:2] for e in endpoints], dtype=float)


def shape_context_descriptors(
    endpoints,
    rho: float,
    k: int = 10,
    n_r: int = 4,
    n_theta: int = 8,
    r_inner_rho: float = 0.125,
    r_max_rho: float = 6.0,
):
    """
    Per-endpoint log-polar shape-context histogram of its in-plane neighbours.

    :param endpoints: list of ``{id, pos, dir}`` (one boundary face).
    :param rho: median NN endpoint spacing (the length unit; ports across voxel sizes).
    :param k: number of nearest neighbours to bin.
    :param n_r / n_theta: radial (log-spaced) and angular bin counts → descriptor
        length ``n_r * n_theta``.
    :param r_inner_rho / r_max_rho: inner / outer radius of the log-radial bins, in ρ.
    :return: ``[n, n_r*n_theta]`` row-normalised (sum-1) descriptors; all-zero rows
        for endpoints with no neighbour in range (treated as uninformative downstream).
    """
    n = len(endpoints)
    dim = n_r * n_theta
    out = np.zeros((n, dim), dtype=float)
    if n < 3:
        return out
    xy = _xy(endpoints)
    tree = cKDTree(xy)
    r_max = r_max_rho * rho
    r_edges = np.geomspace(r_inner_rho * rho, r_max, n_r + 1)
    kq = min(k + 1, n)
    dists, idx = tree.query(xy, k=kq)
    for i in range(n):
        for j, d in zip(idx[i, 1:], dists[i, 1:]):  # skip self (col 0)
            if d <= 0.0 or d > r_max:
                continue
            rb = int(np.searchsorted(r_edges, d, side="right") - 1)
            if rb < 0 or rb >= n_r:
                continue
            v = xy[j] - xy[i]
            theta = np.arctan2(v[1], v[0]) + np.pi  # [0, 2π)
            tb = int(theta / (2.0 * np.pi) * n_theta) % n_theta
            out[i, rb * n_theta + tb] += 1.0
        s = out[i].sum()
        if s > 0.0:
            out[i] /= s
    return out


def descriptor_cost(a: np.ndarray, b: np.ndarray, eps: float = 1e-6) -> float:
    """
    Symmetric χ² distance between two normalised shape-context histograms, in [0, 1].

    0 = identical neighbourhood arrangement, 1 = disjoint. Returns ``0.5`` (neutral)
    when either descriptor is empty (an endpoint with no neighbours in range), so the
    term neither rewards nor penalises an uninformative pair.
    """
    sa, sb = a.sum(), b.sum()
    if sa <= 0.0 or sb <= 0.0:
        return 0.5
    num = (a - b) ** 2
    den = a + b + eps
    return 0.5 * float(np.sum(num / den))
