#!/usr/bin/env python3
"""Check lane uniqueness vs 40 registry rasters. Usage: python scripts/check_uniqueness.py docs/downloads/your.tif"""

# Safety stop: original research code remains below for historical review.
# See research/review-passes.md and docs/data/audit.json before any reuse.
import sys as _legacy_sys
_LEGACY_REASON = 'Withdrawn legacy uniqueness check: the partial registry and binary-dot correlation do not meet the surface and all-entry requirements.'
if __name__ == '__main__':
    print(_LEGACY_REASON + ' DO NOT SUBMIT.', file=_legacy_sys.stderr)
    raise SystemExit(2)
raise RuntimeError(_LEGACY_REASON)

import sys, pathlib, glob, numpy as np, rasterio
from scipy.ndimage import distance_transform_edt
import scipy.stats as stats

FOOTPRINT = np.load("/tmp/footprint_mask.npy")

def overlap_with_reference(candidate_path, registry_paths):
    with rasterio.open(candidate_path) as src:
        cand = src.read(1) > 0.5
        cand_ys, cand_xs = np.where(cand)
        cand_set = list(zip(cand_ys, cand_xs))
    max_overlap=0
    max_rho=0
    for rp in registry_paths:
        with rasterio.open(rp) as src:
            ref = src.read(1) > 0.5
            dist = distance_transform_edt(~ref)
            if len(cand_set)==0:
                ov=0
            else:
                ys=np.array([y for y,x in cand_set])
                xs=np.array([x for y,x in cand_set])
                within = dist[ys, xs] <=3
                ov = within.mean()*100
            max_overlap = max(max_overlap, ov)
            # spearman
            h,w=FOOTPRINT.shape
            cand_bin = np.zeros((h,w), dtype=np.uint8)
            if len(cand_set):
                cand_bin[ys, xs]=1
            # sample 20000
            rng=np.random.default_rng(0)
            idx=rng.choice(np.where(FOOTPRINT.flatten())[0], size=min(20000, FOOTPRINT.sum()), replace=False)
            a=cand_bin.flatten()[idx]
            b=ref.flatten()[idx]
            try:
                rho,_=stats.spearmanr(a,b)
                if np.isnan(rho):
                    rho=0
                rho=abs(rho)
            except:
                rho=0
            max_rho=max(max_rho, rho)
            print(f"{pathlib.Path(rp).name}: overlap {ov:.2f}% rho {rho:.4f}")
    print(f"MAX overlap {max_overlap:.2f}% rho {max_rho:.4f} -> {'PASS' if max_overlap<=70 and max_rho<=0.90 else 'FAIL'}")

if __name__=="__main__":
    if len(sys.argv)<2:
        print("usage: python scripts/check_uniqueness.py candidate.tif")
        sys.exit(1)
    candidate = sys.argv[1]
    regs = glob.glob("/tmp/GEMSDOE32/docs/downloads/*.tif")[:40]
    overlap_with_reference(candidate, regs)
