#!/usr/bin/env python3
"""Experiments 2 & 3 (budget: 3 total, #1 was SRAC-v1 baseline).

EXP2 — dot-budget sweep: on the visible-only hide-and-recover instrument,
score dot prefixes N in {20k, 28k, 37k, 44k, 55k} of the greedy order.
EXP3 — ablation control: same sweep with strike-resonance OFF (isotropic
scarp x corridor).  If the ablation wins, the SRAC hypothesis is negative
and is reported as such.
Selection uses ONLY this instrument; SGMC stays a confirmation diagnostic.
"""
import json
import os
import sys

import numpy as np
from scipy.ndimage import distance_transform_edt

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "src"))

from gems import features
from gems.features import build_surface
from gems.holdout import component_folds
from gems.io_grid import load_bridge
from gems.metric import dti_binary

NS = [20000, 28000, 37000, 44000, 55000]
SEP = 2
PRUNE = 2.0


def greedy_order(surface, allowed, n_max, sep=SEP):
    h, w = surface.shape
    s = np.where(allowed, surface, 0.0).ravel()
    order = np.argsort(-s)
    pos = order[s[order] > 0]
    occupied = np.zeros((h, w), dtype=bool)
    coords = []
    for flat in pos:
        if len(coords) >= n_max:
            break
        r, c = divmod(int(flat), w)
        if occupied[r, c]:
            continue
        coords.append((r, c))
        occupied[max(0, r - sep):r + sep + 1, max(0, c - sep):c + sep + 1] = True
    return np.array(coords)


def surface_noreso(cat_like, footprint):
    """Ablation: monkeypatched resonance-free surface (reso weight neutral)."""
    import numpy as _np
    orig = features.catalogue_strike_field
    try:
        features.catalogue_strike_field = lambda m, sigma=8.0: (
            _np.zeros(m.shape, _np.float32), _np.zeros(m.shape, _np.float32))
        return build_surface(cat_like, footprint)
    finally:
        features.catalogue_strike_field = orig


def main():
    cat, footprint = load_bridge()
    labels, idx, fold_of = component_folds(cat)
    results = {f"{v}:{n}": [] for v in ("SRAC", "NO-RESO") for n in NS}
    for f in range(4):
        withheld = np.isin(labels, idx[fold_of == f])
        visible = cat & ~withheld
        d_vis = distance_transform_edt(~visible)
        truth = withheld & (d_vis > 5.0) & footprint
        score_mask = footprint & ~visible
        allowed = footprint & (d_vis > PRUNE)
        for variant, surf in (("SRAC", build_surface(visible, footprint)),
                              ("NO-RESO", surface_noreso(visible, footprint))):
            coords = greedy_order(surf, allowed, max(NS))
            for n in NS:
                dots = np.zeros_like(cat, dtype=bool)
                cc = coords[:n]
                dots[cc[:, 0], cc[:, 1]] = True
                res = dti_binary(dots & score_mask, truth, score_mask)
                results[f"{variant}:{n}"].append(round(res["dti"], 5))
        print(f"fold {f} done")
    summary = {k: dict(folds=v, mean=round(float(np.mean(v)), 5))
               for k, v in results.items()}
    best = max(summary, key=lambda k: summary[k]["mean"])
    out = dict(instrument="hide-and-recover visible-only, GEMSDOESASS2-HRv1",
               results=summary, best=best)
    with open(os.path.join(REPO, "evidence", "experiments.json"), "w") as fjs:
        json.dump(out, fjs, indent=2)
    for k in sorted(summary, key=lambda k: -summary[k]["mean"]):
        print(f"{summary[k]['mean']:.5f}  {k}  {summary[k]['folds']}")
    print("BEST:", best)


if __name__ == "__main__":
    main()
