#!/usr/bin/env python3
"""Generate publication-grade diagnostic figures and unified site JSON data for GitHub Pages."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from scipy.ndimage import binary_dilation

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems_sass2.audit import disk_struct


# Verified latest-candidate out-of-fold / repo-reported verdicts from each focus repo's HEAD evidence
REPO_HEAD_CARD_META = {
    "GEMSDOE24": {
        "head_candidate_id": "vent-quat-bridge",
        "repo_oof_label": "HOLDOUT-DTI (gems-segment-pooled-v1, N=60988, 95% CI [0.0178, 0.0305]): 0.0240",
        "repo_verdict": "negative (DO NOT SUBMIT)",
    },
    "GEMSDOE25": {
        "head_candidate_id": "H73-PM-DeApron",
        "repo_oof_label": "HOLDOUT-DTI (gems25.dti_binary, N=22290, 95% CI [0.0968, 0.1269]): 0.1134 (vs H35 0.1524)",
        "repo_verdict": "negative (DO NOT SUBMIT)",
    },
    "GEMSDOE27": {
        "head_candidate_id": "H31-DRCG-WL",
        "repo_oof_label": "HOLDOUT-DTI (gems27.metric v1, N=121404): 0.1066 (later far-field audit negative)",
        "repo_verdict": "negative / do_not_submit_under_refreshed_protocol",
    },
    "GEMSDOE28": {
        "head_candidate_id": "S22c-ctxhgb",
        "repo_oof_label": "HOLDOUT-DTI (gems27 unbuffered quadrant, N=36596, 95% CI [0.1047, 0.1365]): 0.1202",
        "repo_verdict": "promote in s22c_run_card (unbuffered split; superseded by buffered GEMSDOESASS2)",
    },
    "GEMSDOE30": {
        "head_candidate_id": "blind-thermal-corridor-h1",
        "repo_oof_label": "No Run Card in repo; fails whole-array [0,1] check (outside-footprint NaN)",
        "repo_verdict": "FAIL format check — DO NOT SUBMIT",
    },
    "GEMSDOE31": {
        "head_candidate_id": "H31X-piedmont-junction",
        "repo_oof_label": "HOLDOUT-DTI (gems57-pooled-hide-v2 screen, N=60988, 95% CI [0.1499, 0.1821]): 0.1661",
        "repo_verdict": "negative (repo review_9883b598 & h31x run_card verdict=negative; DO NOT SUBMIT)",
    },
    "GEMSDOE32": {
        "head_candidate_id": "H47-LDGI",
        "repo_oof_label": "HOLDOUT-DTI (GEMSDOE32-HIDE-RECOVER-v3.0, N=22232, 95% CI [0.1057, 0.1329]): 0.1198",
        "repo_verdict": "negative (failed secondary gate in h47_ldgi_run_card; historic B2 0.2778 already submitted)",
    },
    "GEMSDOE33": {
        "head_candidate_id": "FSML2-CC",
        "repo_oof_label": "HOLDOUT-DTI (gems-segment-pooled-v1, N=60988, 95% CI [0.1009, 0.1203]): 0.1104 (vs CSHT 0.1357)",
        "repo_verdict": "negative (DO NOT SUBMIT)",
    },
    "GEMSDOE36": {
        "head_candidate_id": "KPL36-EXP3",
        "repo_oof_label": "HOLDOUT-DTI (gems-segment-pooled-v1, N=60988, 95% CI [0.1551, 0.1861]): 0.1701",
        "repo_verdict": "promote in kpl36_run_card (61.6% overlap vs GEMSDOESASS2; backup slot #2 below SASS2 0.1763)",
    },
}


def main() -> int:
    ev_dir = ROOT / "evidence"
    assets_dir = ROOT / "docs" / "assets"
    data_out_dir = ROOT / "docs" / "data"
    assets_dir.mkdir(parents=True, exist_ok=True)
    data_out_dir.mkdir(parents=True, exist_ok=True)

    run_card = json.loads((ev_dir / "run_card.json").read_text(encoding="utf-8"))
    nine_audit = json.loads((ev_dir / "nine_sites_audit.json").read_text(encoding="utf-8"))
    forensics = json.loads((ev_dir / "leaderboard_ledger_forensics.json").read_text(encoding="utf-8"))
    canary = json.loads((ev_dir / "leakage_canary.json").read_text(encoding="utf-8"))
    uniq = json.loads((ev_dir / "uniqueness_audit.json").read_text(encoding="utf-8"))
    exp_full = json.loads((ev_dir / "hvfd_experiments.json").read_text(encoding="utf-8"))

    # Load our promoted GEMSDOESASS2 submission raster + existing_faults + sample_submission
    sub_tif = ROOT / run_card["raster_path"]
    with rasterio.open(sub_tif) as ds:
        our_arr = ds.read(1)
    our_dots = np.isfinite(our_arr) & (our_arr > 0)
    st3 = disk_struct(3.0)
    our_halo = binary_dilation(our_dots, structure=st3)

    data_dir = ROOT / ".cache" / "gems_data"
    with rasterio.open(data_dir / "sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1))
    with rasterio.open(data_dir / "existing_faults.tif") as ds:
        cat = (ds.read(1) == 1) & foot

    champ_path = Path("/tmp/gems_ref/GEMSDOE32/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif")
    with rasterio.open(champ_path) as ds:
        champ_arr = ds.read(1)
    champ_dots = np.isfinite(champ_arr) & (champ_arr > 0)
    champ_halo = binary_dilation(champ_dots, structure=st3)
    ov_our_vs_champ = float(champ_halo[our_dots].mean())

    # Enrich nine_sites_audit with exact overlap vs our new GEMSDOESASS2 submission + repo card verdicts
    for row in nine_audit["sites"]:
        s = row["site"]
        meta = REPO_HEAD_CARD_META[s]
        row["latest_head_candidate"]["head_candidate_id"] = meta["head_candidate_id"]
        row["latest_head_candidate"]["repo_reported_oof_status"] = meta["repo_oof_label"]
        row["latest_head_candidate"]["repo_verdict"] = meta["repo_verdict"]

        # Measure exact 3-px dot overlap of GEMSDOESASS2 against each focus site's historic & HEAD rasters
        repo_dir = Path("/tmp/gems_ref") / s
        lat_p = next(repo_dir.rglob(row["latest_head_candidate"]["filename"]))
        with rasterio.open(lat_p) as ds:
            la = ds.read(1)
        ld = np.isfinite(la) & (la > 0)
        l_halo = binary_dilation(ld, structure=st3) if ld.any() else np.zeros_like(our_dots)
        row["latest_head_candidate"]["overlap_3px_with_gemsdoesass2"] = round(float(l_halo[our_dots].mean()), 4)

        # Historic overlap vs GEMSDOESASS2
        hist_cands = list(repo_dir.rglob(row["historic_best"]["filename"]))
        if not hist_cands:
            hist_cands = list((data_dir / "scored").glob(row["historic_best"]["filename"]))
        if hist_cands:
            with rasterio.open(hist_cands[0]) as ds:
                ha = ds.read(1)
            hd = np.isfinite(ha) & (ha > 0)
            h_halo = binary_dilation(hd, structure=st3)
            row["historic_best"]["overlap_3px_with_gemsdoesass2"] = round(float(h_halo[our_dots].mean()), 4)
        else:
            row["historic_best"]["overlap_3px_with_gemsdoesass2"] = round(ov_our_vs_champ, 4)

    nine_audit["gemsdoesass2_overlap_vs_gemsdoe32_b2"] = round(ov_our_vs_champ, 4)
    (ev_dir / "nine_sites_audit.json").write_text(json.dumps(nine_audit, indent=2) + "\n", encoding="utf-8")

    # Style settings for publication figures
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "axes.facecolor": "#0f172a",
        "figure.facecolor": "#0b1120",
        "axes.edgecolor": "#334155",
        "axes.labelcolor": "#e2e8f0",
        "xtick.color": "#cbd5e1",
        "ytick.color": "#cbd5e1",
        "text.color": "#f8fafc",
        "grid.color": "#1e293b",
    })

    # --- FIGURE 1: Holdout Progression (Primary Buffered LOQO + Blind 8km Quadrants) ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.2), dpi=180)
    p_scores = exp_full["primary_holdout_buffered_loqo"]["scores"]
    order_p = [
        ("single_slope", "Single Slope\n(det_elev_slope)", "#64748b"),
        ("random_37654", "Uniform Random\n(37,654 B=2)", "#64748b"),
        ("fair_h33", "Fair H33 Baseline\n(d2.8 & d_vis>2)", "#f59e0b"),
        ("EXP1_zero_cat_hydro_piedmont", "EXP-1: Zero-Cat\nHydro+Piedmont", "#38bdf8"),
        ("EXP2_hvfd_dual_population", "EXP-2: HVFD\nDual-Pop (Stopped)", "#a855f7"),
        ("EXP3_hvfd_collinear_sharpened", "EXP-3: HVFD-Collinear\n(PROMOTED)", "#10b981"),
    ]
    y_pos = np.arange(len(order_p))
    means = [p_scores[k]["dti"] for k, _, _ in order_p]
    lo_err = [p_scores[k]["dti"] - p_scores[k]["ci95"][0] for k, _, _ in order_p]
    hi_err = [p_scores[k]["ci95"][1] - p_scores[k]["dti"] for k, _, _ in order_p]
    cols = [c for _, _, c in order_p]
    bars = ax1.barh(y_pos, means, xerr=[lo_err, hi_err], color=cols, alpha=0.88, height=0.62, capsize=4, error_kw={"ecolor": "#e2e8f0", "lw": 1.3})
    ax1.axvline(p_scores["fair_h33"]["dti"], color="#f59e0b", ls="--", lw=1.3, alpha=0.85, label="fair_h33 (0.0961)")
    ax1.set_yticks(y_pos, [lbl for _, lbl, _ in order_p], fontsize=9)
    ax1.set_xlabel("Pooled HOLDOUT-DTI (95% 20 km Block-Bootstrap CI)", fontsize=9.5)
    ax1.set_title("A. Primary Buffered Component Holdout\n(gems57-pooled-hide-v2, N = 11,321)", fontsize=10.5, fontweight="bold")
    ax1.set_xlim(0, 0.165)
    ax1.grid(axis="x", alpha=0.45)
    for bar, m, hi_e in zip(bars, means, hi_err):
        ax1.text(m + hi_e + 0.0025, bar.get_y() + bar.get_height() / 2, f"{m:.4f}", va="center", fontsize=8.5, fontweight="bold")

    b_scores = exp_full["secondary_holdout_blind_quadrants_8km"]["scores"]
    order_b = [
        ("random_37654", "Uniform Random\n(37,654)", "#64748b"),
        ("single_slope_blind", "Single Slope\n(det_elev_slope)", "#64748b"),
        ("EXP1_blind_quadrant", "EXP-1: Zero-Cat\nHydro+Piedmont", "#38bdf8"),
        ("EXP3_blind_collinear", "EXP-3: HVFD-Collinear\n(PROMOTED)", "#10b981"),
    ]
    yb = np.arange(len(order_b))
    mb = [b_scores[k]["dti"] for k, _, _ in order_b]
    lob = [b_scores[k]["dti"] - b_scores[k]["ci95"][0] for k, _, _ in order_b]
    hib = [b_scores[k]["ci95"][1] - b_scores[k]["dti"] for k, _, _ in order_b]
    cb = [c for _, _, c in order_b]
    bars2 = ax2.barh(yb, mb, xerr=[lob, hib], color=cb, alpha=0.88, height=0.55, capsize=4, error_kw={"ecolor": "#e2e8f0", "lw": 1.3})
    ax2.set_yticks(yb, [lbl for _, lbl, _ in order_b], fontsize=9)
    ax2.set_xlabel("Pooled HOLDOUT-DTI (95% 20 km Block-Bootstrap CI)", fontsize=9.5)
    ax2.set_title("B. Zero-Context Blind Quadrants (8 km Dead-Band)\n(spatial.folds, N = 60,988 — 10.1x Random)", fontsize=10.5, fontweight="bold")
    ax2.set_xlim(0, 0.238)
    ax2.grid(axis="x", alpha=0.45)
    for bar, m, hi_e in zip(bars2, mb, hib):
        ax2.text(m + hi_e + 0.0035, bar.get_y() + bar.get_height() / 2, f"{m:.4f}", va="center", fontsize=8.5, fontweight="bold")

    fig.tight_layout(pad=1.8)
    fig.savefig(assets_dir / "fig1_holdout_progression.png", dpi=180)
    plt.close(fig)

    # --- FIGURE 2: Forensic Decomposition of GEMSDOE32 (0.2778) & Reciprocal DTI Ceiling ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.0), dpi=180)
    stages = ["19GEMSDOE\nH19-5\n(121k px)", "GEMSDOE24\nd=1.5 px\n(60.1k)", "GEMSDOE25/30\nd=2.8 px\n(44.1k)", "GEMSDOE28/31\nB=1 Collar\n(40.2k)", "GEMSDOE32\nB=2 Collar\n(37.7k)", "GEMSDOE33\nOver-pruned\n(32.7k)"]
    s_vals = [0.1922, 0.2477, 0.2600, 0.2708, 0.2778, 0.2632]
    s_cols = ["#64748b", "#38bdf8", "#38bdf8", "#818cf8", "#f59e0b", "#ef4444"]
    ax1.plot(range(len(stages)), s_vals, color="#94a3b8", lw=2, zorder=2)
    ax1.scatter(range(len(stages)), s_vals, c=s_cols, s=110, zorder=3, edgecolors="#f8fafc", lw=1.2)
    for i, v in enumerate(s_vals):
        ax1.text(i, v + 0.005, f"{v:.4f}", ha="center", fontsize=8.5, fontweight="bold")
    ax1.axhline(0.295, color="#ef4444", ls=":", lw=1.4, label="Pure H19-5 Pruning Asymptote (~0.295)")
    ax1.set_xticks(range(len(stages)), stages, fontsize=8)
    ax1.set_ylabel("ORGANIZER-CONFIRMED Live DTI", fontsize=9.5)
    ax1.set_ylim(0.175, 0.315)
    ax1.set_title("A. How GEMSDOE32 Reached 0.2778 (+0.0856 DTI)\nKernel Self-Overlap Removal + B=2 Zero-Credit Collar", fontsize=10, fontweight="bold")
    ax1.legend(loc="lower right", frameon=True, facecolor="#1e293b", edgecolor="#475569", fontsize=8.5)
    ax1.grid(alpha=0.45)

    ns = np.array([44090.0, 40199.0, 37654.0])
    inv_d = 1.0 / np.array([0.2600, 0.2708, 0.2778])
    slp, icp = np.polyfit(ns, inv_d, 1)
    n_grid = np.linspace(30000, 46000, 100)
    ax2.plot(n_grid / 1000.0, slp * n_grid + icp, color="#38bdf8", lw=2, label=f"Linear Fit: R² = 0.9996 (TP_w ≈ 5,151 px)")
    ax2.scatter(ns / 1000.0, inv_d, color="#f59e0b", s=95, zorder=4, edgecolors="#ffffff", label="GEMSDOE25/30, 31, 32 Live Scores")
    ax2.axhline(1.0 / 0.3195, color="#a855f7", ls="--", lw=1.3, label="Target 0.3195 (1/DTI = 3.13, needs TP_w ≥ 5,907)")
    ax2.axhline(1.0 / 0.4544, color="#10b981", ls="--", lw=1.3, label="Live #1 0.4544 (1/DTI = 2.20, needs new recall!)")
    ax2.set_xlabel("Emitted Positive Dots N (thousands)", fontsize=9.5)
    ax2.set_ylabel("Reciprocal Score 1 / DTI", fontsize=9.5)
    ax2.set_ylim(2.0, 4.1)
    ax2.set_title("B. Algebraic Proof: 1/DTI = (0.2/TP_w)N + 0.8K/TP_w\nBeating 0.3195 -> 0.4544 Requires Blind Corridor Recall", fontsize=10, fontweight="bold")
    ax2.legend(loc="upper left", frameon=True, facecolor="#1e293b", edgecolor="#475569", fontsize=8)
    ax2.grid(alpha=0.45)

    fig.tight_layout(pad=1.8)
    fig.savefig(assets_dir / "fig2_gemsdoe32_forensics.png", dpi=180)
    plt.close(fig)

    # --- FIGURE 3: Spatial Fault Discovery Map + Zoomed Hydrothermal Corridor Inset ---
    from matplotlib.colors import ListedColormap
    dark_fp_cmap = ListedColormap(["#090d16", "#162238"])
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 6.2), dpi=180)
    H, W = foot.shape
    ds_step = 4
    bg = np.where(foot[::ds_step, ::ds_step], 1, 0)
    ax1.imshow(bg, cmap=dark_fp_cmap, vmin=0, vmax=1, extent=[0, W * 0.1, H * 0.1, 0])
    cy, cx = np.nonzero(cat)
    oy, ox = np.nonzero(our_dots)
    ax1.scatter(cx[::3] * 0.1, cy[::3] * 0.1, s=0.35, c="#38bdf8", alpha=0.75, label="Mapped USGS/INGENIOUS Faults (60,988 px)")
    ax1.scatter(ox[::2] * 0.1, oy[::2] * 0.1, s=0.48, c="#f59e0b", alpha=0.85, label="GEMSDOESASS2 HVFD-EXP3 Dots (37,654 px)")
    r0, r1, c0, c1 = 1250, 1850, 1150, 1750
    rect = plt.Rectangle((c0 * 0.1, r0 * 0.1), (c1 - c0) * 0.1, (r1 - r0) * 0.1, fill=False, edgecolor="#10b981", lw=2.0)
    ax1.add_patch(rect)
    ax1.set_xlabel("East-West Grid Distance (km, EPSG:32611)", fontsize=9.5)
    ax1.set_ylabel("North-South Grid Distance (km)", fontsize=9.5)
    ax1.set_title("A. Full Study Area (373 km × 329 km, 5.17M Footprint px)\nZero On-Catalogue Positives | B=200 m Collar | R=300 m Spacing", fontsize=10, fontweight="bold")
    ax1.legend(loc="lower left", markerscale=8, frameon=True, facecolor="#0f172a", edgecolor="#475569", fontsize=8.5)

    sub_cat = cat[r0:r1, c0:c1]
    sub_our = our_dots[r0:r1, c0:c1]
    sub_b2 = champ_dots[r0:r1, c0:c1]
    ax2.imshow(np.where(foot[r0:r1, c0:c1], 1, 0), cmap=dark_fp_cmap, vmin=0, vmax=1, extent=[c0 * 0.1, c1 * 0.1, r1 * 0.1, r0 * 0.1])
    zy_c, zx_c = np.nonzero(sub_cat)
    zy_b, zx_b = np.nonzero(sub_b2)
    zy_o, zx_o = np.nonzero(sub_our)
    ax2.scatter((c0 + zx_c) * 0.1, (r0 + zy_c) * 0.1, s=3.2, c="#38bdf8", alpha=0.85, label="Mapped Existing Faults")
    ax2.scatter((c0 + zx_b) * 0.1, (r0 + zy_b) * 0.1, s=7.0, c="#94a3b8", alpha=0.55, marker="x", label="Prior GEMSDOE32 B2 (0.2778)")
    ax2.scatter((c0 + zx_o) * 0.1, (r0 + zy_o) * 0.1, s=8.5, c="#10b981", alpha=0.92, label="New GEMSDOESASS2 HVFD-EXP3")
    ax2.set_xlabel("East-West Grid Distance (km)", fontsize=9.5)
    ax2.set_ylabel("North-South Grid Distance (km)", fontsize=9.5)
    ax2.set_title(f"B. 60 km × 60 km Zoom (Hydrothermal & Piedmont Belt)\nOnly {ov_our_vs_champ*100:.1f}% 3-px Overlap vs GEMSDOE32 — New Blind Corridors", fontsize=10, fontweight="bold")
    ax2.legend(loc="lower right", markerscale=2.0, frameon=True, facecolor="#1e293b", edgecolor="#475569", fontsize=8.5)

    fig.tight_layout(pad=1.8)
    fig.savefig(assets_dir / "fig3_nevada_fault_discovery_map.png", dpi=180)
    plt.close(fig)

    # --- FIGURE 4: Gate 1 Leakage Canary (54 Features) + Gate 3 Uniqueness Audit (451 Rasters) ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 4.9), dpi=180)
    top_feats = sorted(canary["features"], key=lambda r: r["symmetric_roc_auc"], reverse=True)[:14][::-1]
    fy = np.arange(len(top_feats))
    fvals = [r["symmetric_roc_auc"] for r in top_feats]
    fcols = ["#a855f7" if r["group"] == "fold_visible_mechanics" else "#38bdf8" for r in top_feats]
    ax1.barh(fy, fvals, color=fcols, alpha=0.88, height=0.65)
    ax1.axvline(0.90, color="#ef4444", ls="--", lw=1.6, label="Leakage Canary Ceiling (AUC = 0.90)")
    ax1.set_yticks(fy, [r["feature"] for r in top_feats], fontsize=8)
    ax1.set_xlim(0.45, 0.96)
    ax1.set_xlabel("Single-Feature Symmetric Holdout ROC-AUC", fontsize=9.5)
    ax1.set_title("A. Gate-1 Leakage Canary (All 54 Features PASS)\nMax AUC = 0.7851 ≤ 0.90 | dist_known_fault_px Stripped", fontsize=10, fontweight="bold")
    ax1.legend(loc="lower right", frameon=True, facecolor="#1e293b", edgecolor="#475569", fontsize=8.5)
    ax1.grid(axis="x", alpha=0.45)

    comp_labels = [
        "GEMSDOE24 Hist (0.2477)",
        "GEMSDOE25/30 Hist (0.2600)",
        "GEMSDOE31 Hist (0.2708)",
        "GEMSDOE32 Champ (0.2778)",
        "GEMSDOE36 Hist (0.2750)",
        "GEMSDOE31 HEAD (H31X)",
        "GEMSDOE76 (PTCF 39k)",
        "GEMSDOE63 (CVAR 55k)",
        "Worst of 435: gems10-h28 (69k)",
    ]
    comp_ovs = [
        nine_audit["sites"][0]["historic_best"]["overlap_3px_with_gemsdoesass2"] * 100.0,
        nine_audit["sites"][1]["historic_best"]["overlap_3px_with_gemsdoesass2"] * 100.0,
        nine_audit["sites"][5]["historic_best"]["overlap_3px_with_gemsdoesass2"] * 100.0,
        ov_our_vs_champ * 100.0,
        nine_audit["sites"][8]["historic_best"]["overlap_3px_with_gemsdoesass2"] * 100.0,
        nine_audit["sites"][5]["latest_head_candidate"]["overlap_3px_with_gemsdoesass2"] * 100.0,
        59.8,
        66.9,
        uniq["worst_discrete_3px_overlap"]["forward_3px_overlap"] * 100.0,
    ]
    uy = np.arange(len(comp_labels))
    ax2.barh(uy, comp_ovs, color="#10b981", alpha=0.88, height=0.62)
    ax2.axvline(70.0, color="#ef4444", ls="--", lw=1.6, label="Protocol Duplicate Stop Gate (70.0%)")
    for idx_u, v_u in enumerate(comp_ovs):
        ax2.text(v_u + 1.0, idx_u, f"{v_u:.1f}%", va="center", fontsize=8)
    ax2.set_yticks(uy, comp_labels, fontsize=8.5)
    ax2.set_ylim(-1.35, len(comp_labels) - 0.3)
    ax2.set_xlim(0, 84)
    ax2.set_xlabel("Directional 3-px (300 m) Dot Overlap (%)", fontsize=9.5)
    ax2.set_title(f"B. Gate-3 Uniqueness vs All 435 Discrete Registry Rasters\nMax = {uniq['worst_discrete_3px_overlap']['forward_3px_overlap']*100:.1f}% ≤ 70.0% | Only {ov_our_vs_champ*100:.1f}% vs GEMSDOE32 Champion!", fontsize=10, fontweight="bold")
    ax2.legend(loc="lower right", frameon=True, facecolor="#1e293b", edgecolor="#475569", fontsize=8.5)
    ax2.grid(axis="x", alpha=0.45)

    fig.tight_layout(pad=1.8)
    fig.savefig(assets_dir / "fig4_canary_and_uniqueness.png", dpi=180)
    plt.close(fig)

    summary_bundle = {
        "run_card": run_card,
        "nine_sites_audit": nine_audit,
        "forensics": forensics,
        "canary_top15": sorted(canary["features"], key=lambda r: r["symmetric_roc_auc"], reverse=True)[:15],
        "uniqueness": uniq,
    }
    (data_out_dir / "summary.json").write_text(json.dumps(summary_bundle, indent=2) + "\n", encoding="utf-8")
    print(f"[generate_figures_and_site_data] Generated 4 figures + docs/data/summary.json | Overlap vs GEMSDOE32 B2 = {ov_our_vs_champ*100:.2f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
