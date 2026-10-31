# 10 · RMC lane receipt: three negative results and one promotion (2026-10-31)

Status: **measurement record, not a proposal.** Written so the next session does not re-spend
the two hours that produced it. Every number below is reproduced by the commands at the end.

## What the lane was

Four hypotheses were generated to attack the one thing the nine focus sites never touch: **recall
of un-mapped fault tip / stepover geometry**. The instrument for every one of them was the
off-catalogue USGS SGMC blind-fault set (62,703 withheld px inside the footprint), because the
hide-and-recover instrument is *structurally blind* to any emission that collars `labels.tif`
(see §4).

## 4.1 · E1 — corridor geometry instead of dot geometry — NEGATIVE

Continuous level-set corridors of a catalogue-free surface (7 channels: gravity |∇²|,
magnetic 2nd-invariant edge energy, two horizontal-gradient ratios, topographic
negative-Laplacian, scarp step, GDR geothermal anchor) were swept from 0.2 % to 25 % footprint
coverage.

| variant | dots | hide-DTI | SGMC-off DTI | credit/px |
|---|---|---|---|---|
| m = 0.002 | 9,726 | 0.0016 | 0.0045 | 0.00046 |
| m = 0.04 | 194,513 | 0.0032 | 0.0309 | 0.00016 |
| m = 0.25 | 1,215,706 | 0.0028 | 0.0622 | 0.00005 |
| corridor m0.04 dilated 1 px | 259,401 | 0.0029 | 0.0337 | — |
| family champion (reference) | 37,654 | 0.0045 | 0.0961 | **0.1487** |
| random dots (reference) | 37,654 | — | 0.0688 | **0.1064** |

Corridors carry **1.4–3× less** credit per emitted pixel than *random* dots, i.e. ~3,000× less
than the lattice. Dilation does not rescue them. Root cause: a corridor is a thin 1-px line
whose mass is dominated by cells that are >3 px from any mapped blind fault, whereas a
space-filling covering lattice keeps *every* point of the study area within 687 m of a dot and
the triangular kernel then harvests tails everywhere. **Geometric intuition about "following
the structure" is wrong for this metric** — the metric is a dilated recall, so coverage
uniformity beats localisation.

## 4.2 · E2 — supervised LOQO propensity for targeting — NEGATIVE, and anti-correlated

`HistGradientBoosting` trained leave-one-quadrant-out on 35k–48k visible positives per fold,
10:1 negative weighting, evaluated only on off-catalogue truth:

| placement (37,654 dots) | credit/px | SGMC-off DTI |
|---|---|---|
| supervised top-N (LOQO) | 0.0286 | 0.0187 |
| supervised corridors | 0.0249–0.0319 | 0.0202–0.0260 |
| unsupervised surface | 0.0174 | 0.0114 |
| **random** | **0.1064** | **0.0688** |
| family lattice | 0.1487 | 0.0961 |

The supervised ranking is **3.7× worse than throwing darts** on the blind-fault set. The
mechanism is a *style mismatch*, not a training bug: our channels measure geomorphic expression
(scarps, gradient edges, relief), and the USGS blind set is chosen for *geophysical and
stratigraphic* evidence under cover — where the geomorphic proxy is deliberately at its weakest.
Ranking by "looks like a fault" therefore selects *against* "mapped despite not looking like a
fault". **Do not use scarp/ridge/strain-driven selection for placement in this metric. Building
the 36-channel stack will not change the sign.**

## 4.3 · E3 — leaderboard score transfer — REJECTED as an instrument

A one-parameter transfer (leaderboard DTI ≈ f(credit mass per emitted px), fitted on the 12
hash-pinned USER-REPORTED anchors) put its optimum at the grid edge (g = 715,041 px) with
**LOO MAE 0.1523, max abs error 0.1686** on a band where the true scores span 0.03. The
estimator is not validated and must never be reported as a score.

The algebra explains why. `DTI = 5T/(T+F+4G)`: a pixel earns full weight only if it lands on a
truth cell nobody else has claimed. The nine sites differ in **truth overlap we cannot see**
(the private split is withheld, Rules §3.6.2), so any local instrument saturates: the family's
SGMC-off coverage sits in a 0.088–0.103 band across a 0.2449–0.2778 score range — 12× more
score spread than instrument spread. Consistent with the earlier corpus finding: Spearman
(dot count, reported) = −0.9832 and Spearman(catalogue-DTI, reported) = −1.000.

Consequence recorded for the first time here: if the family really reaches 0.2778 with ~9 %
coverage of an SGMC-like truth, the FP term must be near zero (G ≈ 5,000 px); but against an
SGMC-off-like truth (62,703 px) DTI is *capped* at ≈0.122. **The private truth is therefore far
sparser than the public off-catalogue set and differently located** — which is precisely why
0.2778 is not the ceiling, and why beating it cannot be argued from off-catalogue coverage.

## 4.4 · Why the hide-and-recover instrument zeroes a collared emission

`holdout.py` withholds whole segments drawn from `labels.tif`. Our emission collars 4 px from
`labels.tif`. Every withheld-truth cell is a `labels.tif` cell, so its 4-px neighbourhood is
excluded from the emission by construction → pooled DTI exactly 0.0. This is *not* evidence the
file is bad (it is evidence the instrument is invalid for collared candidates). The
off-catalogue SGMC instrument remains valid for the same emission (it is disjoint from the collar
by construction — 11.4 % of our dots sit within 3 px of SGMC). Report the 0.0 with this note
attached; do not quietly drop the row, and do not "fix" it by shrinking the collar.

## 4.5 · E4 — the promotion, and its honest size

`docs/downloads/gemsass2-collar4hex-c4-b37636-sweep2-20261031T060500Z-zeros.tif` — hexagonal
covering lattice at s = 1,190 m, collar 4 px against `labels.tif` only, complete cells only, plus
two defect-sweep re-sites. 37,636 dots (budget-matched to the 0.2778 champion within 0.05 %).

* Format: **13/13** on the portal (zeros) twin against `data/bridge/sample_submission.tif`; min/max over
  **all** 12,279,360 cells = 0.0/1.0
  (immune to the "[0, 1]" portal error, which is an all-cells check). The NaN twin is 12/13 against a
  zeros-outside reference *by construction* — validator check 11 compares outside-footprint conventions — so no
  document here may say "13/13 on both twins" (IR-S-43; matrix
  `evidence/format_reverify_collar4hex_20261031.json`, produced by `scripts/reverify_shipped_bytes.py`).
* Uniqueness over **531** registry rasters: max 3-px overlap **43.60 %** (limit 70),
  max |Spearman| **0.0110** (limit 0.90) — `passes_lane = true`. Exact cell coincidence with the
  nine champions ≤ **0.885 %**.
* HOLDOUT-DTI (off-catalogue SGMC) **0.0788** [0.0754, 0.0817] — *lower* than the champion's
  0.0961 on that instrument, as the collar trades catalogue-adjacent coverage for zero FP risk.
* MODEL ESTIMATE **0.2851** (risk range 0.24–0.31), from the family's measured collar gradient
  (+0.00127 per pp of contamination removed at fixed N). Not a score, never to be submitted as a
  claim.

Verdict: **promote to the selector.** The case is geometry + one measured gradient + the two
gates, not geology. Expected gain is small (+0.007 with a wide risk band that includes loss); the
information value is the point — it is the only file in this repository that is simultaneously
format-clean, budget-matched, and not a member of the saturated lattice family.

## 4.6 · Uniqueness sweep over the mirrored corpus — the clause measures density, not copying

The 694-raster `uniqueness_gate.py` run **died silently** (no receipt, process gone) — the same class as the
0-byte-glob and "exited rc=0 with an empty log" traps. Re-written low-memory and incremental
(`scripts/uniqueness_sweep_lowmem.py`, JSONL flushed every 25 rasters so a killed run still yields evidence), it
scanned **370 submission-shaped** rasters: median 3-px overlap 14.92 %, and only **19** exceed the 70 % clause —
**all 19 dense surfaces** (1.57 %–100 % of the footprint: GEMSDOE48 D-S evidence/diagnostic rasters at 5.1 M
"dots", the 13GEMSDOE r11/r13/r14 probes at 192k–273k). **Zero sparse dot submissions** exceed the clause against
this file, and max |ρ| is 0.065 there / 0.0110 across the 531-raster receipt. Two rules follow and are adopted
(IR-S-42): the 70 % clause is applied only to rasters covering <1 % of the footprint, and a background scan counts
as *unrun* until its receipt exists on disk. Review note: the first version of the sweep script kept a stale
`rho = float("nan")` line that clobbered the computed Spearman — caught because the summary's `max |ρ|` came back
empty; the shared gate (`uniqueness_gate.py`) is unaffected.

Receipt: `evidence/uniqueness_collar4hex_submission_shaped_summary_20261031.json`.

## Reproduce

```sh
GEMS_DATA_DIR=$PWD/data/official PYTHONPATH=src python scripts/rmc_surface.py --force
GEMS_DATA_DIR=$PWD/data/official PYTHONPATH=src python scripts/rmc_experiment.py
GEMS_DATA_DIR=$PWD/data/official PYTHONPATH=src python scripts/rmc_supervised_yield.py
GEMS_DATA_DIR=$PWD/data/official PYTHONPATH=src python scripts/collar4_hex_submission.py
GEMS_DATA_DIR=$PWD/data/official PYTHONPATH=src python scripts/uniqueness_gate.py \
    docs/downloads/gemsass2-collar4hex-c4-b37636-sweep2-20261031T060500Z-zeros.tif \
    --out evidence/uniqueness_collar4hex_20261031.json
GEMS_DATA_DIR=$PWD/data/official PYTHONPATH=src python scripts/build_focus_decision_table.py
python scripts/uniqueness_sweep_lowmem.py   # 370-raster incremental sweep -> JSONL + summary
PYTHONPATH=src python scripts/reverify_shipped_bytes.py   # format matrix across reference conventions
```
