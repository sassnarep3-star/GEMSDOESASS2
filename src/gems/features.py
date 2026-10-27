"""LANE: SCU — Scarp-Corridor-UTh dotted emission (this repo lane; strike-resonance tested and dropped as negative, see evidence/experiments.json).

Hypothesis (pre-registered in evidence/run_card.json):
Unmapped normal-fault strands in the Basin-and-Range footprint sit in the
200 m - 3 km flank corridor of the mapped USGS/INGENIOUS catalogue (fault
systems cluster into sub-parallel strand arrays), carry lidar-scale scarp
evidence (step/slope-excess/crest-convexity at 2-10 m wavelengths), and are
corroborated by a GeoDAWN radiometric U/Th fluid-pathway anomaly.
Sub-hypothesis TESTED AND NEGATIVE (EXP3, evidence/experiments.json):
weighting scarps by strike-resonance with the local catalogue grain
cos^2(theta_lidar - theta_catalogue) *reduced* hide-and-recover HOLDOUT-DTI
at every dot budget in every fold, so the shipped surface keeps the
orientation term neutral (use_resonance=False).

Layers: lidar_scarp_features_u8.tif (step_max, ex_max, lapneg_max, coh100,
strike, valid) + geodawn_extensions_u8.tif (UTh, TMI_up150) from the
GEMSDOE24 cache (GeoDAWN DOI 10.5066/P93LGLVQ).

Difference vs registry lanes: no registry site conditions scarp evidence on
the *catalogue strike-resonance field* cos^2(theta_lidar - theta_catalogue).
Tip/step-over, topo-gap, Euler, PINN, phase-congruency, poisson/dotted-
lattice resampling lanes all key on position or isotropic intensity, not on
orientation agreement between lidar scarps and the visible catalogue.
"""
from __future__ import annotations

import os

import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter

from .io_grid import REGISTRY_CACHE, read_band

LIDAR = os.path.join(REGISTRY_CACHE, "GEMSDOE24/data/external/lidar_scarp_features_u8.tif")
EXT = os.path.join(REGISTRY_CACHE, "GEMSDOE24/data/external/geodawn_extensions_u8.tif")

# lidar band order (from lidar_scarp_features.json):
LB = {n: i + 1 for i, n in enumerate(
    ["ex_max", "ex_mean", "step_max", "lapneg_max", "lappos_max",
     "downface_max", "upface_max", "cross_max", "relief", "coh100",
     "strike", "valid"])}
EB = {n: i + 1 for i, n in enumerate(["ThK", "UK", "UTh", "TMI_up150"])}


def _nrm(u8: np.ndarray) -> np.ndarray:
    return u8.astype(np.float32) / 255.0


def catalogue_strike_field(cat_mask: np.ndarray, sigma: float = 8.0):
    """Local catalogue orientation via smoothed structure tensor.

    Returns (theta_deg in [0,180), validity weight in [0,1]).
    Derived ONLY from the mask passed in — the holdout recomputes this from
    visible faults alone (no leakage of withheld segments).
    """
    f = gaussian_filter(cat_mask.astype(np.float32), 3.0)
    gy, gx = np.gradient(f)
    jxx = gaussian_filter(gx * gx, sigma)
    jyy = gaussian_filter(gy * gy, sigma)
    jxy = gaussian_filter(gx * gy, sigma)
    # orientation of the *line* (perpendicular to gradient eigenvector)
    theta_grad = 0.5 * np.arctan2(2 * jxy, jxx - jyy)
    theta_line = (np.degrees(theta_grad) + 90.0) % 180.0
    energy = np.sqrt((jxx - jyy) ** 2 + 4 * jxy ** 2)
    e95 = np.percentile(energy, 99)
    validity = np.clip(energy / max(e95, 1e-12), 0, 1).astype(np.float32)
    return theta_line.astype(np.float32), validity


def build_surface(cat_mask: np.ndarray, footprint: np.ndarray,
                  prune_px: float = 2.0, corridor_px: float = 30.0,
                  use_resonance: bool = False) -> np.ndarray:
    """SRAC surface in [0,1] on the full grid (0 outside footprint)."""
    step = _nrm(read_band(LIDAR, LB["step_max"]))
    exm = _nrm(read_band(LIDAR, LB["ex_max"]))
    lapn = _nrm(read_band(LIDAR, LB["lapneg_max"]))
    coh = _nrm(read_band(LIDAR, LB["coh100"]))
    strike_u8 = read_band(LIDAR, LB["strike"])
    valid = read_band(LIDAR, LB["valid"]) > 0

    uth = _nrm(read_band(EXT, EB["UTh"]))
    tmi = read_band(EXT, EB["TMI_up150"]).astype(np.float32)

    scarp = (0.5 * step + 0.3 * exm + 0.2 * lapn) * (0.35 + 0.65 * coh)

    if use_resonance:
        theta_cat, w_cat = catalogue_strike_field(cat_mask)
        theta_lidar = strike_u8.astype(np.float32) / 255.0 * 180.0
        dth = np.deg2rad(theta_lidar - theta_cat)
        resonance = np.cos(dth) ** 2  # 1 parallel, 0 perpendicular
        # weakly defined catalogue orientation falls back to neutral
        reso_w = w_cat * resonance + (1 - w_cat) * 0.5
    else:
        # EXP3 ablation won on HOLDOUT-DTI (evidence/experiments.json):
        # strike-resonance is a tested-and-NEGATIVE sub-hypothesis.
        reso_w = np.full(cat_mask.shape, 0.5, np.float32)

    dcat = distance_transform_edt(~cat_mask)
    corridor = np.clip((dcat - prune_px) / 1.0, 0, 1) * \
        np.clip((corridor_px + 10.0 - dcat) / 10.0, 0, 1)

    bonus = 1.0 + 0.30 * uth

    surf = scarp * (0.30 + 0.70 * reso_w) * corridor * bonus  # reso_w neutral 0.5 unless use_resonance

    # non-lidar areas: magnetic-edge fallback (TMI upward-continued gradient)
    gy, gx = np.gradient(gaussian_filter(tmi, 2.0))
    gmag = np.hypot(gx, gy)
    g99 = np.percentile(gmag[footprint], 99)
    mag_edge = np.clip(gmag / max(g99, 1e-9), 0, 1)
    fallback = 0.25 * mag_edge * (0.30 + 0.70 * reso_w) * corridor * bonus
    surf = np.where(valid, surf, fallback).astype(np.float32)

    surf[~footprint] = 0.0
    m = surf.max()
    if m > 0:
        surf /= m
    return surf
