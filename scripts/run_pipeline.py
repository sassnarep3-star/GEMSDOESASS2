#!/usr/bin/env python3
"""GEMSDOESASS2 end-to-end pipeline (LANE: SCU (scarp-corridor-UTh); strike-resonance ablated after EXP3 negative).

Steps: build SRAC surface -> leakage canary -> dotted emission + B=2 prune
-> write submission (zeros + nan) -> strict validator -> hide-and-recover
holdout (candidate rebuilt from visible faults only, per fold) -> champion
comparison on the same instrument -> uniqueness audit vs the 9-site
registry -> run card + audit JSON.  Fully automated, fail-closed.
"""
import datetime
import json
import os
import subprocess
import sys

import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter, label

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "src"))

from gems.emission import catalogue_prune, greedy_dots
from gems.features import EB, EXT, LB, LIDAR, build_surface
from gems.holdout import EVALUATOR_VERSION, component_folds, run_holdout
from gems.io_grid import REGISTRY_CACHE, load_bridge, read_band, write_submission
from gems.metric import dti_binary
from gems.uniqueness import audit_against_registry

N_DOTS = 37000
SEP_PX = 2
PRUNE_PX = 2.0
STAMP = "20261027T120000Z"
SLUG = f"gemsdoesass2-scu1-scarpcorridor-uth-{N_DOTS}-{STAMP}"
OUT = os.path.join(REPO, "docs", "downloads")


def canary(footprint, cat_mask, surface):
    """Single-feature AUC vs catalogue positives (leakage canary <= 0.90)."""
    from numpy.random import default_rng
    rng = default_rng(3)
    feats = {
        "step_max": read_band(LIDAR, LB["step_max"]).astype(np.float32),
        "ex_max": read_band(LIDAR, LB["ex_max"]).astype(np.float32),
        "lapneg_max": read_band(LIDAR, LB["lapneg_max"]).astype(np.float32),
        "coh100": read_band(LIDAR, LB["coh100"]).astype(np.float32),
        "UTh": read_band(EXT, EB["UTh"]).astype(np.float32),
        "TMI_up150": read_band(EXT, EB["TMI_up150"]).astype(np.float32),
        "SCU_surface": surface,
    }
    pos_r, pos_c = np.where(cat_mask & footprint)
    bg_r, bg_c = np.where(footprint & ~cat_mask)
    pick_p = rng.choice(len(pos_r), size=min(20000, len(pos_r)), replace=False)
    pick_b = rng.choice(len(bg_r), size=100000, replace=False)
    out = {}
    for name, f in feats.items():
        xp = f[pos_r[pick_p], pos_c[pick_p]]
        xb = f[bg_r[pick_b], bg_c[pick_b]]
        # rank AUC
        allv = np.concatenate([xp, xb])
        ranks = allv.argsort().argsort().astype(np.float64)
        rp = ranks[:len(xp)]
        auc = (rp.sum() - len(xp) * (len(xp) - 1) / 2) / (len(xp) * len(xb))
        out[name] = round(float(auc), 4)
    out["max_auc"] = max(out.values())
    out["pass_leq_0.90"] = out["max_auc"] <= 0.90
    return out


def make_dots_from(cat_like, footprint):
    surf = build_surface(cat_like, footprint, prune_px=PRUNE_PX)
    d = distance_transform_edt(~cat_like)
    allowed = footprint & (d > PRUNE_PX)
    dots = greedy_dots(surf, allowed, N_DOTS, SEP_PX)
    return catalogue_prune(dots, cat_like, PRUNE_PX), surf


def main():
    cat, footprint = load_bridge()
    print("[1/7] building SCU surface from full catalogue ...")
    dots, surface = make_dots_from(cat, footprint)
    n_dots = int(dots.sum())
    print(f"      dots placed: {n_dots}")

    print("[2/7] leakage canary ...")
    can = canary(footprint, cat, surface)
    print(f"      max single-feature AUC = {can['max_auc']} (pass={can['pass_leq_0.90']})")

    print("[3/7] writing submission rasters ...")
    os.makedirs(OUT, exist_ok=True)
    arr = dots.astype(np.float32)
    info_zeros = write_submission(arr, os.path.join(OUT, f"{SLUG}-zeros.tif"),
                                  "zeros", footprint)
    a_nan = arr.copy()
    info_nan = write_submission(a_nan, os.path.join(OUT, f"{SLUG}-nan.tif"),
                                "nan", footprint)
    digest8 = info_zeros["sha256"][:8]
    print(f"      sha256[:8] = {digest8}")

    print("[4/7] strict validation ...")
    val = subprocess.run([sys.executable, os.path.join(HERE, "check_submission.py"),
                          info_zeros["tif"]], capture_output=True, text=True)
    val_json = json.loads(val.stdout)
    assert val_json["ALL_CHECKS_PASSED"], val_json
    print("      ALL CHECKS PASSED")

    print("[5/7] hide-and-recover holdout (visible-only rebuild per fold) ...")
    hold_ours = run_holdout(lambda vis: make_dots_from(vis, footprint)[0],
                            cat, footprint)
    print(f"      ours   HOLDOUT-DTI = {hold_ours['mean_dti']:.5f} "
          f"CI {hold_ours['ci95']}")

    champ_path = os.path.join(
        REGISTRY_CACHE,
        "GEMSDOE32/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif")
    champ = np.nan_to_num(read_band(champ_path), nan=0.0) > 0.5
    hold_champ = run_holdout(lambda vis: champ, cat, footprint)
    print(f"      champ  HOLDOUT-DTI = {hold_champ['mean_dti']:.5f} "
          f"CI {hold_champ['ci95']}  (as-submitted arm; full-catalogue leak in its favor)")
    # as-submitted arm for ours too (same leakage conditions as champion)
    hold_ours_as = run_holdout(lambda vis: dots, cat, footprint)
    print(f"      ours(as-submitted) = {hold_ours_as['mean_dti']:.5f} "
          f"CI {hold_ours_as['ci95']}")

    ratio = hold_ours_as["mean_dti"] / max(hold_champ["mean_dti"], 1e-9)
    est = 0.2778 * ratio
    est_lo = 0.2778 * (hold_ours_as["ci95"][0] / max(hold_champ["ci95"][1], 1e-9))
    est_hi = 0.2778 * (hold_ours_as["ci95"][1] / max(hold_champ["ci95"][0], 1e-9))

    print("[6/7] uniqueness audit vs 9-site registry ...")
    man = json.load(open(os.path.join(REPO, "registry", "registry_manifest.json")))
    registry = [dict(name=f"{r['site']}:{r['name']}",
                     path=os.path.join(REGISTRY_CACHE, r["path"]),
                     owner_reported_score=r["owner_reported_score"])
                for r in man["rasters"]]
    uni = audit_against_registry(info_zeros["tif"], dots, surface, footprint, registry)
    print(f"      unique vs all registry rasters: {uni['all_pass']}; "
          f"worst overlap {uni['worst_overlap']['dot_overlap_3px']} "
          f"({uni['worst_overlap']['name']})")

    print("[7/7] run card ...")
    beats_champ = hold_ours_as["mean_dti"] > hold_champ["mean_dti"]
    verdict = "promote" if (uni["all_pass"] and can["pass_leq_0.90"]
                            and val_json["ALL_CHECKS_PASSED"] and beats_champ) \
        else ("candidate-unique-validated" if (uni["all_pass"] and can["pass_leq_0.90"]
                                               and val_json["ALL_CHECKS_PASSED"])
              else "negative")
    note = (f"SASS2 SCU scarp-corridor-UTh {n_dots}d B2 sep2 | "
            f"HOLDOUT {hold_ours_as['mean_dti']:.4f} vs champ "
            f"{hold_champ['mean_dti']:.4f} | {digest8}")[:140]
    card = {
        "hypothesis": "SCU: lidar scarp evidence (step/slope-excess/crest-convexity) in the 200m-3km catalogue flank corridor, corroborated by GeoDAWN U/Th, marks unmapped fault strands; strike-resonance sub-hypothesis tested NEGATIVE (EXP3) and removed",
        "mechanism": "Basin-and-Range normal faults grow clustered sub-parallel strand arrays; young scarps preserve 2-10 m wavelength topographic steps; hydrothermal fluids moving on faults deposit U relative to Th",
        "non_fault_mimic": "late-Pleistocene Lake Lahontan shoreline benches locally parallel to range fronts (partially suppressed by UTh + corridor gating, not eliminated)",
        "holdout_dti": {
            "label": "HOLDOUT-DTI",
            "evaluator": EVALUATOR_VERSION,
            "ours_visible_only": hold_ours,
            "ours_as_submitted": hold_ours_as,
            "champion_0.2778_as_submitted": hold_champ,
        },
        "estimated_live_score": {
            "label": "ESTIMATE (holdout-ratio x 0.2778 OWNER-REPORTED champion). NOT a score.",
            "point": round(est, 4), "range": [round(est_lo, 4), round(est_hi, 4)],
        },
        "leakage_canary": can,
        "uniqueness": uni,
        "raster_sha256": info_zeros["sha256"],
        "validator": val_json,
        "submission_name": f"GEMSDOESASS2-SCU1-{digest8.upper()}",
        "submission_note_140": note,
        "n_dots": n_dots,
        "params": dict(n_dots_target=N_DOTS, sep_px=SEP_PX, prune_px=PRUNE_PX),
        "verdict": verdict,
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "files": {"zeros": info_zeros, "nan": info_nan},
    }
    with open(os.path.join(REPO, "evidence", "run_card.json"), "w") as f:
        json.dump(card, f, indent=2)
    with open(os.path.join(OUT, f"{SLUG}-audit.json"), "w") as f:
        json.dump(card, f, indent=2)
    print(json.dumps({k: card[k] for k in
                      ["submission_name", "estimated_live_score", "verdict",
                       "submission_note_140"]}, indent=2))


if __name__ == "__main__":
    main()
