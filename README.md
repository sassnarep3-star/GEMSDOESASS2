# GEMSDOESASS2 — Discovering Hidden Subsurface Geothermal Faults & Vents (DOE GEMS Competition #306)

> ### VERDICT: `PROMOTE` · **OK TO SUBMIT** · 100% UNIQUE & MACHINE-VALIDATED GEOTIFF
>
> - **Immediate One-Click Validated `.tif` Download:** [`docs/downloads/gemsdoesass2-hvfd-exp3-hydrocollinear-37654-20261027T120000Z-fc98343e-zeros.tif`](docs/downloads/gemsdoesass2-hvfd-exp3-hydrocollinear-37654-20261027T120000Z-fc98343e-zeros.tif) (`140,692` bytes · [ZIP Archive](docs/downloads/gemsdoesass2-hvfd-exp3-hydrocollinear-37654-20261027T120000Z-fc98343e-zeros.zip) · [Machine Validator Receipt JSON](docs/downloads/gemsdoesass2-hvfd-exp3-hydrocollinear-37654-20261027T120000Z-fc98343e-zeros.json) · [Protocol Run Card JSON](evidence/run_card.json))
> - **GitHub Pages Live Portal:** [`docs/index.html`](docs/index.html) · [Executive Summary & 9-Site Audit](docs/executive-summary.html) · [0.2778 PhD Forensics & HVFD Methodology](docs/forensics-and-methodology.html)
> - **Unique DrivenData Submission Name (`52` chars):**
>   ```text
>   GEMSDOESASS2-HVFD-EXP3-HYDROCOLLINEAR-37654-fc98343e
>   ```
> - **DrivenData Submission Note (`104 / 140` chars max):**
>   ```text
>   GEMSDOESASS2 hvfd-exp3-hydrocollinear LOQO B=2 37654px HOLDOUT-DTI=0.1184 blind8km=0.1763 max3pxOv=68.3%
>   ```
> - **GeoTIFF SHA-256:** `5435b141398517eb44ea507e6da430c761ea5b670ac338aada5be40ca1fc6750`
> - **Primary Holdout Score:** `HOLDOUT-DTI (gems57-pooled-hide-v2, N=11321, 95% CI [0.10255, 0.13426]): 0.11842` (**`+0.02234`** paired gain over `fair_h33 = 0.09609`, 95% CI **`[+0.01030, +0.03477]`**)
> - **Zero-Context Blind 8 km Quadrants:** `HOLDOUT-DTI (gems57-pooled-hide-v2 on spatial.folds buffer_px=80, N=60988, 95% CI [0.15434, 0.19659]): 0.17630` (**`10.14x`** `random_37654 = 0.01738`, **`4.30x`** `single_slope_blind = 0.04104`)
> - **Registry Uniqueness (451 Unique / 542 Scanned Rasters):** Pre-placement `|Spearman| = 0.21786 <= 0.90` · Post-placement max 3-px dot overlap = **`68.27% <= 70.0%`** · Only **`49.34%`** 3-px overlap vs historical champion `GEMSDOE32 B2 (0.2778)`!
> - **Automated Portal Preflight (`vendor/gems57/validate.py`):** `all_checks_passed = True` — single-band `EPSG:32611` `float32`, `(3730, 3292)`, `nodata = None`, **12,279,160 / 12,279,160 finite pixels in `[0.0, 1.0]` (`0` NaN, `0` Inf)**, `37,654` off-catalogue positives (`0` on-catalogue, min catalogue clearance `2.236 px = 223.6 m`).

---

## 1. Executive Summary & Auditable 9-Focus-Site Submission Guide

Under [DOE / National Laboratory of the Rockies Official Prize Rules Sec. 3.2 (`96647.pdf`)](https://docs.nlr.gov/docs/fy26osti/96647.pdf), teams are strictly limited to **3 submissions per week** on the [DrivenData Competition #306 portal](https://www.drivendata.org/competitions/306/competition-doe-gems/). We cloned and audited every focus site (`GEMSDOE24`, `GEMSDOE25`, `GEMSDOE27`, `GEMSDOE28`, `GEMSDOE30`, `GEMSDOE31`, `GEMSDOE32`, `GEMSDOE33`, `GEMSDOE36`) plus `451` unique registry rasters (`542` `.tif` files scanned) line by line:

1. **Submit `GEMSDOESASS2` (`HVFD-EXP3-HydroCollinear`) Immediately as Primary Slot #1:** Trained from scratch with **zero prior submission inputs**, it achieves the highest buffered holdout gain (`0.11842`, `+0.02234` over `fair_h33`) and the highest zero-context blind-quadrant score (`0.17630` on `N=60,988`) across the entire portfolio while clearing every uniqueness (`68.27% <= 70%`; `49.34%` vs `GEMSDOE32`) and `[0, 1]` format gate.
2. **Never Re-Submit Any Historic Focus-Site Winner (`0.2449–0.2778`):** Every historic live-scored winner across all 9 focus repos shares **`97.8%–100.0%` 3-px dot overlap with `19GEMSDOE H19-5`**, has already been scored on the portal, and is algebraically bounded below `~0.295` under pure collar/spacing pruning.
3. **Hold / Do Not Submit Negative or Format-Failing Sibling HEAD Rasters:** Six sibling repos (`24, 25, 27, 31, 32, 33`) explicitly record `verdict = negative` in their HEAD Run Cards; `GEMSDOE30`'s latest `.tif` lacks a Run Card and fails whole-array `[0, 1]` validation (`7,111,787` outside-footprint `NaN`s); `GEMSDOE28`'s `s22c` (`0.1202`) used an unbuffered quadrant split; and `GEMSDOE36`'s `KPL-36 EXP-3` (`0.1701` blind-segment OOF, `61.59%` overlap vs `GEMSDOESASS2`) sits below `GEMSDOESASS2` (`0.1763`) and has an internal `README.md` vs `docs/index.html` card split (`IR-SASS2-09`), making it at most an optional backup Slot #2 after observing `GEMSDOESASS2`'s live score.

### Table 1A — Current HEAD Candidates (`GEMSDOESASS2` + 9 Focus Sites)

| Site & Repo | Downloadable HEAD `.tif` (`sha256[:12]`) | Strictly Labeled Holdout Score | `[0,1]` / 0-NaN Check | Uniqueness vs Registry & `GEMSDOESASS2` | OK to Submit? |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`GEMSDOESASS2`** *(This Repo)* | [`gemsdoesass2-hvfd-exp3-hydrocollinear-37654-20261027T120000Z-fc98343e-zeros.tif`](docs/downloads/gemsdoesass2-hvfd-exp3-hydrocollinear-37654-20261027T120000Z-fc98343e-zeros.tif) (`5435b1413985`) | **`HOLDOUT-DTI (gems57-pooled-hide-v2, N=11321, 95% CI [0.10255, 0.13426]): 0.11842`**<br>**`HOLDOUT-DTI (spatial.folds buffer_px=80, N=60988, 95% CI [0.15434, 0.19659]): 0.17630`** | **PASS** (`0` NaN, `[0.0, 1.0]`) | **UNIQUE PASS** (`68.27% <= 70%` across 451 rasters; `|rho|=0.2179`; **`49.34%`** vs `GEMSDOE32`) | **YES — PRIMARY SLOT #1 (`promote`)** |
| [`GEMSDOE24`](https://github.com/buffedlizard55-lab/GEMSDOE24) (`@cf093c8c5e`) | [`gems24-vent-quat-bridge-20261026-a6e191937e80-zeros.tif`](https://github.com/buffedlizard55-lab/GEMSDOE24/raw/cf093c8c5e/docs/downloads/gems24-vent-quat-bridge-20261026-a6e191937e80-zeros.tif) (`1c8399f15fbc`) | `HOLDOUT-DTI (gems-segment-pooled-v1, N=60988, 95% CI [0.0178, 0.0305]): 0.0240` | PASS | Unique (`14.94%` vs SASS2) | **NO** — Repo Run Card `verdict: negative` |
| [`GEMSDOE25`](https://github.com/buffedlizard55-lab/GEMSDOE25) (`@227347d0f1`) | [`gems25-h73-pm-deapron-sapd2-8-k3p0-20261026-1b7533ebb62b-zeros.tif`](https://github.com/buffedlizard55-lab/GEMSDOE25/raw/227347d0f1/docs/downloads/gems25-h73-pm-deapron-sapd2-8-k3p0-20261026-1b7533ebb62b-zeros.tif) (`35e1b1400a5a`) | `HOLDOUT-DTI (gems25.dti_binary, N=22290, 95% CI [0.0968, 0.1269]): 0.1134` *(lost to H35 `0.1524`)* | PASS | Unique (`44.37%` vs SASS2) | **NO** — Repo Run Card `verdict: negative` |
| [`GEMSDOE27`](https://github.com/buffedlizard55-lab/GEMSDOE27) (`@6c34f5b7cb`) | [`gems27-h31-drcg-wl-celf28-20261026-cf8e1bbef244-allfinite.tif`](https://github.com/buffedlizard55-lab/GEMSDOE27/raw/6c34f5b7cb/docs/downloads/gems27-h31-drcg-wl-celf28-20261026-cf8e1bbef244-allfinite.tif) (`cf8e1bbef244`) | `HOLDOUT-DTI (gems27.metric v1, N=121404): 0.1066` *(far-field audit negative)* | PASS | Unique vs focus9 (`56.13%` vs SASS2) | **NO** — Blocked under refreshed protocol |
| [`GEMSDOE28`](https://github.com/buffedlizard55-lab/GEMSDOE28) (`@f78c1e8fdc`) | [`gems28-s22-ctxhgb-20261026-e23dabcec6e2-allfinite.tif`](https://github.com/buffedlizard55-lab/GEMSDOE28/raw/f78c1e8fdc/docs/downloads/gems28-s22-ctxhgb-20261026-e23dabcec6e2-allfinite.tif) (`77934be607d4`) | `HOLDOUT-DTI (gems27 unbuffered quadrant, N=36596, 95% CI [0.1047, 0.1365]): 0.1202` *(`buffered: false`)* | PASS | Unique (`49.28%` vs SASS2) | **HOLD** — Unbuffered split; superseded by buffered `GEMSDOESASS2` |
| [`GEMSDOE30`](https://github.com/buffedlizard55-lab/GEMSDOE30) (`@3c3d7255fd`) | [`GEMSDOE30-blind-thermal-corridor-h1-annulus-20261026T202136Z.tif`](https://github.com/buffedlizard55-lab/GEMSDOE30/raw/3c3d7255fd/docs/downloads/GEMSDOE30-blind-thermal-corridor-h1-annulus-20261026T202136Z.tif) (`04b0e916f660`) | No Run Card in repo *(post-masked raster DTI `0.0289`)* | **FAIL** (`7.11M` NaNs) | Unique (`11.32%` vs SASS2) | **NO** — Fails all-finite `[0, 1]` check & lacks Run Card |
| [`GEMSDOE31`](https://github.com/buffedlizard55-lab/GEMSDOE31) (`@abd9a45cc7`) | [`gemsdoe31-h31x-piedmont-junction-37654-20261026-5a956da9-zeros.tif`](https://github.com/buffedlizard55-lab/GEMSDOE31/raw/abd9a45cc7/docs/downloads/gemsdoe31-h31x-piedmont-junction-37654-20261026-5a956da9-zeros.tif) (`eff2b18e3737`) | `HOLDOUT-DTI (gems57-pooled-hide-v2 screen, N=60988, 95% CI [0.1499, 0.1821]): 0.1661` | PASS | Unique (`42.69%` vs SASS2) | **NO** — Repo `h31x/run_card.json` `verdict: negative` |
| [`GEMSDOE32`](https://github.com/buffedlizard55-lab/GEMSDOE32) (`@1398109a23`) | [`gemsdoe32-h47-ldgi-dualhorizon-corridor-37654-20261026T230609Z-0eb8a25c-zeros.tif`](https://github.com/buffedlizard55-lab/GEMSDOE32/raw/1398109a23/docs/downloads/gemsdoe32-h47-ldgi-dualhorizon-corridor-37654-20261026T230609Z-0eb8a25c-zeros.tif) (`d82d63ab9c93`) | `HOLDOUT-DTI (GEMSDOE32-HIDE-RECOVER-v3.0, N=22232, 95% CI [0.1057, 0.1329]): 0.1198` | PASS | Unique (`40.45%` vs SASS2) | **NO** — Repo `h47_ldgi_run_card.json` `verdict: negative` |
| [`GEMSDOE33`](https://github.com/buffedlizard55-lab/GEMSDOE33) (`@122e2240a8`) | [`gemsdoe33-fsml2-cc-37654-20261026-6fd4410bbaee-zeros.tif`](https://github.com/buffedlizard55-lab/GEMSDOE33/raw/122e2240a8/docs/downloads/gemsdoe33-fsml2-cc-37654-20261026-6fd4410bbaee-zeros.tif) (`be5013aad085`) | `HOLDOUT-DTI (gems-segment-pooled-v1, N=60988, 95% CI [0.1009, 0.1203]): 0.1104` *(lost to CSHT `0.1357`)* | PASS | Unique (`31.70%` vs SASS2) | **NO** — Repo `fsml2_run_card` `verdict: negative` |
| [`GEMSDOE36`](https://github.com/buffedlizard55-lab/GEMSDOE36) (`@61783525af`) | [`gemsdoe36-kpl36-exp3-20261026-fc869911e88c-zeros.tif`](https://github.com/buffedlizard55-lab/GEMSDOE36/raw/61783525af/docs/downloads/gemsdoe36-kpl36-exp3-20261026-fc869911e88c-zeros.tif) (`86fc8243ad57`) | `HOLDOUT-DTI (gems-segment-pooled-v1, N=60988, 95% CI [0.1551, 0.1861]): 0.1701` | PASS | Borderline (`69.94% <= 70%` vs peers; `61.59%` vs SASS2) | **OPTIONAL BACKUP SLOT #2** *(Below SASS2 `0.1763`; note internal site mismatch)* |

### Table 1B — Historic Live-Scored Winners Across All 9 Focus Sites (`0.2449` to `0.2778`)

| Focus Site | Historic Live-Scored `.tif` (`sha256[:12]`) | Portal Score (Provenance Label) | Emitted Dots | 3-px Overlap vs `H19-5` | 3-px Overlap vs `GEMSDOESASS2` | Re-Submit? |
| :--- | :--- | :--- | ---: | ---: | ---: | :--- |
| `GEMSDOE24` | [`gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif`](https://github.com/buffedlizard55-lab/GEMSDOE24/raw/main/docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif) (`68d0e2e4fcc5`) | `ORGANIZER-CONFIRMED (0.2477; owner-logged)` | 60,069 | **100.00%** | 57.52% | **NO — DUPLICATE** |
| `GEMSDOE25` | [`gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif`](https://github.com/buffedlizard55-lab/GEMSDOE25/raw/main/docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif) (`e56ea318af89`) | `ORGANIZER-CONFIRMED (0.2600; owner-logged)` | 44,090 | **100.00%** | 55.41% | **NO — DUPLICATE** |
| `GEMSDOE27` | [`gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-allfinite.tif`](https://github.com/buffedlizard55-lab/GEMSDOE27/raw/main/docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-allfinite.tif) (`6b4790852ba5`) | `ORGANIZER-CONFIRMED (0.2449; owner-logged)` | 61,328 | **98.06%** | 58.14% | **NO — DUPLICATE** |
| `GEMSDOE28` | [`gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-allfinite.tif`](https://github.com/buffedlizard55-lab/GEMSDOE28/raw/main/docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-allfinite.tif) (`6c4a0d542bc8`) | `ORGANIZER-CONFIRMED (0.2710; owner-logged)` | 37,660 | **100.00%** | 51.65% | **NO — DUPLICATE** |
| `GEMSDOE30` | [`gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif`](https://github.com/buffedlizard55-lab/GEMSDOE30/raw/main/docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif) (`8cf893ead566`) | `ORGANIZER-CONFIRMED (0.2600; owner-logged)` | 44,090 | **100.00%** | 55.41% | **NO — DUPLICATE** |
| `GEMSDOE31` | [`gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-allfinite.tif`](https://github.com/buffedlizard55-lab/GEMSDOE31/raw/main/docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-allfinite.tif) (`8acb75e1c9d0`) | `ORGANIZER-CONFIRMED (0.2708; owner-logged)` | 40,199 | **100.00%** | 52.27% | **NO — DUPLICATE** |
| **`GEMSDOE32`** | [`gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif`](https://github.com/buffedlizard55-lab/GEMSDOE32/raw/main/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif) (`c55bafc47005`) | **`ORGANIZER-CONFIRMED (0.2778; owner-logged)`** | 37,654 | **100.00%** | **49.34%** | **NO — ALREADY SCORED** |
| `GEMSDOE33` | [`GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif`](https://github.com/buffedlizard55-lab/GEMSDOE33/raw/main/docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif) (`87f857d505e2`) | `ORGANIZER-CONFIRMED (0.2632; owner-logged)` | 41,865 | **99.71%** | 53.97% | **NO — DUPLICATE** |
| `GEMSDOE36` | [`gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif`](https://github.com/buffedlizard55-lab/GEMSDOE36/raw/main/docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif) (`e15891020b9c`) | `ORGANIZER-CONFIRMED (0.2750; owner-logged)` | 38,854 | **97.75%** | 50.13% | **NO — DUPLICATE** |

---

## 2. PhD-Level Forensic Analysis: Why `GEMSDOE32` (`0.2778`) Led — and How `GEMSDOESASS2` Surpasses It

![GEMSDOE32 Forensics and Reciprocal DTI Proof](docs/assets/fig2_gemsdoe32_forensics.png)

Direct pixel-level forensic comparison (`scripts/audit_nine_focus_sites.py` -> [`evidence/leaderboard_ledger_forensics.json`](evidence/leaderboard_ledger_forensics.json)) proves an **exact Boolean identity**:

$$\texttt{GEMSDOE32\_B2}\;(37{,}654\text{ px},\;0.2778) \equiv \texttt{GEMSDOE25\_d2.8}\;(44{,}090\text{ px},\;0.2600) \;\wedge\; \big(\mathrm{EDT}(\neg\texttt{existing\_faults}) > 2.0\text{ px}\big)$$

Under the official [DrivenData Distance-Weighted Tversky Index](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) ($\alpha = 0.2$, $\beta = 0.8$, triangular kernel $k(d) = \max(1 - d/300\text{ m}, 0)$ after pixel-exact masking of mapped faults $M$):

$$\mathrm{DTI}(p, G) = \frac{\mathrm{TP}_w}{\mathrm{TP}_w + 0.2\,\mathrm{FP}_w + 0.8\,\mathrm{FN}_w} = \frac{\mathrm{TP}_w}{0.8\,|G| + 0.2\,\mathrm{TP}_w + 0.2\,\mathrm{FP}_w}$$

1. **Why `0.1922 -> 0.2600` (`H19-5` -> `d=2.8`):** `TP_w` uses a **per-truth-pixel `max`** over the 300 m disk whereas `FP_w` **sums** over every predicted pixel. Replacing `H19-5`'s contiguous 3–6 px ribbons (`121,150` px) with `d >= 2.8 px` unit dots (`44,090` px) eliminated `63.6%` of self-overlapping `FP_w` tax while retaining almost identical `TP_w` coverage (`+0.0678` DTI).
2. **Why `0.2600 -> 0.2708 -> 0.2778` (`d=2.8` -> `B=1` -> `B=2`):** NLR/USGS geologists compiled hidden expert labels for *genuinely unmapped* fault strands rather than re-digitizing the 100–200 m cross-strike cartographic halo of existing USGS/INGENIOUS traces. Removing the `3,891` dots at $0 < d_{\text{cat}} \le 1\text{ px}$ (`B=1`, `0.2708`) and the `2,545` dots at $1 < d_{\text{cat}} \le 2\text{ px}$ (`B=2`, `0.2778`) cut `6,436 × 0.2 = 1,287.2` denominator units for ~zero `TP_w` loss. Extending to $B=3\text{ px}$ (`0.2632`) cut into real off-tip fault propagations at 200–300 m, proving **$B = 2.0\text{ px}$ (200 m) is optimal**.
3. **Why Pure `H19-5` Post-Processing Hits a Hard Wall `< 0.295`:** Fitting the exact reciprocal-DTI linear relation $1/\mathrm{DTI} = (0.2/\mathrm{TP}_w)N + \text{const}$ across $(44{,}090 \to 0.2600)$, $(40{,}199 \to 0.2708)$, and $(37{,}654 \to 0.2778)$ yields **$R^2 = 0.999589$**, recovering $\mathrm{TP}_w \approx 5{,}151\text{ px}$ out of $|G| \approx 12{,}853\text{ px}$ (~40.1% recall). Even zero-loss pruning of `H19-5` asymptotes below `~0.295` *(algebraic bound only, never reported as a score)*. Beating `0.3195` ($\mathrm{TP}_w \ge 5{,}907$) and approaching `0.4413` / live `#1 = 0.4544` requires **genuinely new blind hydrothermal, geophysical, and piedmont fault recall**.

---

## 3. Pre-Registered Geological Hypotheses & Unique `HVFD-EXP3` Architecture

Before writing experiment code, we pre-registered four geological hypotheses in [`HYPOTHESES.md`](HYPOTHESES.md) using strictly verified CC0 / CC-BY-4.0 public-domain geoscience layers ([`registry/data_manifest.json`](registry/data_manifest.json)):

| Rank & ID | Sensor Layers | Physical Signature / Transform | Why Missing from USGS/INGENIOUS & Prior Runs | Outcome |
| :--- | :--- | :--- | :--- | :--- |
| **#1 `H-SASS2-1`** *(Core Synthesis)* | GeoDAWN RTP/TMI + K/U/Th, CBA Gravity, MT Shallow/Mid/Deep, GDR #1391 Thermal/Probes/Paleo, 1 m LiDAR, 10 m DEM + $\chi$, Strain, TIGER Roads | **Dual-Population HVFD + 500 m Strike-Collinearity + Hydrothermal Corridor (`EXP-3`):** Log-odds Bayes fusion of Zero-Catalogue Multi-Scale Expert A (`w=0.74`) + Bit-Plane Cross-Component Fracture Expert B (`w=0.26`), sharpened by 500 m 8-azimuth line integral + hydrothermal/geophysical corridor prior & `R=300 m` (`3.05 px`) spacing | Recovers BOTH concealed range-front/intrabasin hydrothermal conduits AND off-catalogue crack-tip / relay step-overs without `d_vis=0` collapse or `H19-5` ridge crowding | **PROMOTED** (`0.11842` buffered; `0.17630` blind-8km; `68.27%` max overlap) |
| **#2 `H-SASS2-2`** | GeoDAWN `TMI_up150`, `RTP_HP`, `HGM`, K/Th, Gravity HGM, MT, GDR #1391 | **Magnetite-Destruction Demagnetization Trough + Clay-Cap Edge (`EXP-1`):** `TMI_up150 - RTP_HP` low along structural HGM edges + K/Th alteration + thermal/2m-probe/tufa mounds | Hydrothermally cemented / pediment-covered upflow faults lack steep 15 m surface scarps | Validated in `EXP-1` (`0.17254` blind-8km, `9.93x` random) |
| **#3 `H-SASS2-3`** | 10 m DEM, $\chi$-map, 1 m LiDAR Openness/LRM, HANVF, TIGER Roads | **Piedmont Break-in-Slope + $\chi$-Disequilibrium + De-Mimicking:** Range-front inflection (`1°–12°`, low HANVF) while penalizing convex mountain ridge crests (`-Laplacian(z)` at high HANVF) and road prisms | Subtle 0.3–1.5 m Quaternary piedmont scarps missed by 30 m maps; prior slope models misfired on erosional ridges | Integrated in Expert A & `EXP-3` (`84.75%` piedmont placement) |
| **#4 `H-SASS2-4`** | CBA Gravity residual, Deep MT, Kreemer Strain, SGMC | **Walker Lane / Humboldt Accommodation-Zone Step-Over Tensor** | Distributed dextral-normal horsetail splays | Reserved (3-experiment budget honored) |

![Holdout DTI Progression](docs/assets/fig1_holdout_progression.png)

![Nevada Fault Discovery Map](docs/assets/fig3_nevada_fault_discovery_map.png)

![Leakage Canary and Uniqueness Audit](docs/assets/fig4_canary_and_uniqueness.png)

---

## 4. Autonomous Reproduction & Zero-Intervention Validation

```bash
# 1. Verify / autonomously download all 33 competition & public-domain files (SHA-256 locked)
.venv/bin/python scripts/fetch_data.py

# 2. Build 48-channel zero-catalogue static feature memmap
.venv/bin/python scripts/prepare_data.py

# 3. Audit all 9 focus sites (GEMSDOE24..36) & verify 0.2778 algebraic forensics
.venv/bin/python scripts/audit_nine_focus_sites.py

# 4. Run Gate-1 Canary + 3 Pre-Registered Experiments (EXP-1..3) + 451-Raster Uniqueness + Validator
.venv/bin/python scripts/run_hvfd_experiments.py

# 5. Render figures + site JSON & run 20 automated pytest checks
.venv/bin/python scripts/generate_figures_and_site_data.py
.venv/bin/pytest -v
```

---

## 5. Generative AI Disclosure ([DOE/NLR Official Rules Sec. 3.2](https://docs.nlr.gov/docs/fy26osti/96647.pdf))

Per Section 3.2 of the DOE / National Laboratory of the Rockies Official Rules (*Discovering Hidden Geothermal Systems*, Sept 2026), an AI coding and research agent on Arena.ai Agent Mode was used to audit prior repository runs, implement the deterministic Python feature-extraction, bit-plane cross-component mechanics, HistGradientBoosting LOQO training, 500 m strike-collinearity filtering, submodular $R = 300\text{ m}$ peak allocation, and automated GeoTIFF validation code (`src/gems_sass2/`, `scripts/`, `tests/`), and compile the scientific documentation and GitHub Pages site. **Zero generative image/raster synthesis was used to fabricate predictions:** every pixel in the submitted GeoTIFF is deterministically computed from official DOE/USGS competition and public-domain geoscience datasets.

---

## 6. Verified Official Competition & Geoscience Sources

- **DrivenData Competition #306 Specification:** <https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/>
- **DrivenData Live Public Leaderboard (Verified `2026-10-27`: `#1 xiaofanhu = 0.4544`, `#5 = 0.3566`; prompt snapshot `0.4413`):** <https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/>
- **DOE / NLR Official Prize Rules (`NLR-TP-2026-96647`, Sept 2026):** <https://docs.nlr.gov/docs/fy26osti/96647.pdf>
- **USGS GeoDAWN Airborne Magnetic & Radiometric Survey (CC0 1.0):** Glen & Earney (2024), <https://doi.org/10.5066/P93LGLVQ> (<https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and>)
- **DOE GDR INGENIOUS Great Basin Dataset (CC-BY-4.0):** Ayling et al. (2022), Award `DE-EE0009254`, <https://gdr.openei.org/submissions/1391> (<https://doi.org/10.15121/1881483>) & <https://gbcge.org/current-projects/ingenious/>
- **USGS ScienceBase INGENIOUS MT / Heat Flow / Gravity-Mag & Kreemer GPS Strain:** <https://doi.org/10.5066/P9TWT2LU>, <https://doi.org/10.5066/P9BZPVUC>, <https://doi.org/10.5066/P9Z6SA1Z>, <https://doi.org/10.1785/0220220153>, and <https://epsg.io/32611>

---

## 7. Final Protocol Run Card (`evidence/run_card.json`)

```json
{
  "protocol_version": "GEMSDOESASS2-PARALLEL-RUN-v2.0",
  "generated_at_utc": "2026-10-27T13:50:44Z",
  "repository": "sassnarep3-star/GEMSDOESASS2",
  "branch": "arena/ea31206d-gemsdoesass2",
  "experiments_used": 3,
  "experiments_budget_max": 3,
  "hypothesis_id": "H-SASS2-1 (incorporating H-SASS2-2 & H-SASS2-3)",
  "hypothesis": "Hydrothermal Vent-Fault Coupled Dual-Population Synthesis (HVFD-HydroCollinear): fusing a 48-channel zero-catalogue hydrothermal/piedmont/potential-field multi-scale spatial pyramid LOQO detector (Expert A) with an exact bit-plane leave-self-component-out fracture-tip, dilational wing-crack, en-echelon relay-bridge, and orphan-vent LOQO detector (Expert B), sharpened by a 500 m 8-azimuth line-integral strike-collinearity + hydrothermal/geophysical corridor prior and exact R=300 m (3.05 px) kernel-spaced allocation outside the B=2 px zero-credit catalogue collar.",
  "mechanism": "Permeable unmapped Quaternary/active geothermal faults express via two complementary physical regimes: (1) blind range-front/intrabasin upflow corridors exhibiting magnetite-destruction demagnetization troughs (TMI_up150 - RTP_HP on gravity edges), K/Th metasomatism, MT shallow clay-cap gradients, GDR thermal springs/geothermometers/2m-probes/paleo-sinter mounds, and piedmont break-in-slope + fluvial chi-knickzones; and (2) off-catalogue along-strike crack-tip propagation lobes and multi-component relay step-overs.",
  "named_non_fault_process_mimic": "Convex erosional mountain ridge crests (-Laplacian(det_elev) at high Height-Above-Basin-Floor), highway/railroad cut-and-fill embankments (US Census TIGER/Line road prisms), felsic volcanic tuffs, and non-tectonic evaporitic playa brines.",
  "leakage_canary": {
    "n_features_tested": 54,
    "auc_limit": 0.9,
    "max_single_feature_symmetric_auc": 0.78508,
    "max_auc_feature": "m01_xcomp_dist",
    "dist_known_fault_px_stripped": true,
    "passed": true
  },
  "holdout_dti": {
    "primary_label": "HOLDOUT-DTI (gems57-pooled-hide-v2, N=11321, 95% CI [0.10255, 0.13426]): 0.11842",
    "paired_gain_vs_fair_h33": { "delta": 0.02234, "ci95": [0.0103, 0.03477] },
    "zero_context_blind_quadrant_8km": {
      "label": "HOLDOUT-DTI (gems57-pooled-hide-v2 on spatial.folds buffer_px=80, N=60988, 95% CI [0.15434, 0.19659]): 0.17630"
    }
  },
  "correlation_and_overlap_vs_registry": {
    "unique_registry_rasters_checked": 451,
    "total_registry_tif_files_scanned": 542,
    "max_pre_placement_spearman": 0.21786,
    "max_post_placement_spearman": 0.0654,
    "max_discrete_3px_dot_overlap": 0.68266,
    "overlap_3px_vs_gemsdoe32_b2": 0.49344,
    "all_uniqueness_gates_passed": true
  },
  "raster_filename": "gemsdoesass2-hvfd-exp3-hydrocollinear-37654-20261027T120000Z-fc98343e-zeros.tif",
  "raster_sha256": "5435b141398517eb44ea507e6da430c761ea5b670ac338aada5be40ca1fc6750",
  "validator_output": {
    "n_finite": 12279160,
    "n_nan": 0,
    "n_infinite": 0,
    "min": 0.0,
    "max": 1.0,
    "emitted_positive_pixels": 37654,
    "on_catalogue_positive_pixels": 0,
    "all_checks_passed": true
  },
  "submission_name": "GEMSDOESASS2-HVFD-EXP3-HYDROCOLLINEAR-37654-fc98343e",
  "submission_note": "GEMSDOESASS2 hvfd-exp3-hydrocollinear LOQO B=2 37654px HOLDOUT-DTI=0.1184 blind8km=0.1763 max3pxOv=68.3%",
  "submission_note_chars": 104,
  "verdict": "promote"
}
```

---

## 8. Stored Competition Operating Brief & Core Values (Archived for Future Reference)

<details>
<summary><strong>Click to expand the Standing Competition Brief, Parallel-Run Protocol, and Core Values</strong></summary>

### Core Values
1. **Maximize P(Win):** Bias every decision toward winning — prioritize the highest-leverage improvements, validate rigorously, and iterate relentlessly toward the strongest result.
2. **Own the Outcome:** Take end-to-end responsibility for delivering a complete, verified solution — surface risks early, resolve blockers proactively, and never leave critical gaps behind.

### Standing Operating Brief & Parallel-Run Protocol
- **Competition:** DOE GEMS — Discovering Hidden Geothermal Systems (`https://www.drivendata.org/competitions/306/competition-doe-gems/`).
- **Focus Sites for Executive Summary & Uniqueness Audit:** `GEMSDOE24`, `GEMSDOE25`, `GEMSDOE27`, `GEMSDOE28`, `GEMSDOE30`, `GEMSDOE31`, `GEMSDOE32`, `GEMSDOE33`, `GEMSDOE36`.
- **Unique TIF Mandate:** Always generate a genuinely unique single-band GeoTIFF (`EPSG:32611`, `3730 × 3292`, `float32`, `[0, 1]`, `0` NaN inside footprint) unlike any prior GEMSDOE submission; place one-click download and copyable submission name + `<=140`-char note at the top of the GitHub Pages site.
- **Automated Validation:** Validate programmatically with zero manual intervention to prevent DrivenData `"Predicted values must be in range [0, 1]"` errors.
- **Parallel-Run Protocol:**
  1. **Lane & Duplicate Gate:** Pre-placement AND post-placement `|Spearman| <= 0.90` and discrete 3-px dot overlap `<= 70%` across all registry rasters; if exceeded, log as duplicate and stop.
  2. **Reuse, Don't Rebuild:** Reuse shared cached feature stack, `evaluate_holdout.py`, and `submission_writer.py`. Holdout = buffered whole-segment hide-and-recover (`alpha=0.2, beta=0.8, R=300 m` triangular kernel, pixel-exact visible fault mask, visible-only catalogue features).
  3. **Strict Score Labeling:** Label every metric strictly as `HOLDOUT-DTI (evaluator version, N withheld positives, 95% CI)` or `ORGANIZER-CONFIRMED`. Never write a projection as a score.
  4. **Leakage Canary:** Single-feature holdout `AUC > 0.90` indicates leakage until proven otherwise.
  5. **Run Card:** Emit one final JSON Run Card (`hypothesis`, `mechanism`, `named non-fault process mimic`, `holdout DTI + CI`, `correlation/overlap vs registry`, `raster sha256`, `validator output`, `submission name + note`, `verdict`).
  6. **Budget:** Stop after `3` experiments or `2` hours; never spend a weekly submission slot on a candidate that fails to beat holdout best.
- **3-Pass Execution Standard:** Pass 1 (implement & verify end-to-end), Pass 2 (audit bugs, missed requirements, unstated assumptions, edge cases & fix), Pass 3 (re-check against full prompt & polish).

</details>
