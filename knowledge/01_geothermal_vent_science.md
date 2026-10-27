# Geothermal Vent Science for Blind Fault Discovery — Audited Sources

## Why blind faults vent heat
- Great Basin extension creates high heat flow (80–100 mW/m² vs 60 continental mean). Faults act as conduits when permeability is breached: dilation + clay-cap breaching allows hydrothermal fluids to advect heat to <2 m depth, creating subtle 1–5°C anomalies in 2 m temperature probe surveys (INGENIOUS GDR 1391, 544 probes). These halos are ~2–5 km wide, far larger than the 100 m pixel, so kriging is effective.
- Sources: GDR 1391 DOI 10.15121/1881483 (CC-BY-4.0) <https://gdr.openei.org/submissions/1391> ; GBCGE INGENIOUS <https://gbcge.org/current-projects/ingenious/> ; SGMC DS1052 <https://doi.org/10.3133/ds1052> (Horton et al. 2017).

## Radiometric hydrothermal alteration signature
- Hydrothermal leaching depletes K in the top 0.5–1 m (gamma rays sample this depth), enriches Th/K. GeoDAWN airborne radiometric K, Th, U, TC maps (USGS ScienceBase 657e1d85d34e23d3533209f7, DOI 10.5066/P93LGLVQ, CC-BY) show this as low-K, high-ThK, high-UK. Our TTC uses K-depletion = 1−K_norm and ThK = Th/K (both Sobel gradient for lateral edge).
- Verified in ` /tmp/GEMSDOE24/data/external/geodawn_rad.json` and `geodawn_extensions.json` (quantised 1–255 per-channel 1st–99th pct). Nodata =0.

## Magnetic tilt derivative (RTP→TDR)
- Reduced-to-pole (RTP) corrects latitude skew; tilt derivative TDR = atan(VG/HG) crosses zero at magnetic contacts. A 100 m fault with susceptibility contrast produces a zero-contour + sign flip. This is a physical edge, not a scarp, so it persists under cover. GeoDAWN TMI, RTP, HG, VG bands (same DOI) provide HG/VG. Our TTC requires TDR zero within 200 m of a lidar step.
- Reference: USGS GeoDAWN acquisition report `GeoDAWN_NV_WestCentral_Geophysical_2020_D21_Report.pdf` (GDR external audit_sources).

## LiDAR micro-scarp at 2 m → 100 m
- 1 m 3DEP DEM tiles (716, USGS 3DEP <https://www.usgs.gov/3d-elevation-program> via <https://apps.nationalmap.gov/downloader/>) aggregated to 100 m via `lidar_scarp_features_u8.tif` (12 bands: ex_max, step_max, lapneg_max, relief, coh100, etc. — see `lidar_scarp_features.json`). `ex_max` = max slope excess over 30 m regional slope; `step_max` = 10 m minus 50 m slope. These fire on 10–50 m fault scarps but also on paleo-shorelines; triple-AND suppresses the latter.
- Verified via `lidar_scarp_features.json` workflow run <https://github.com/buffedlizard55-lab/7GEMSDOE/actions/runs/36266555805>.

## Geodetic strain (dilatation)
- INGENIOUS geodesy (Nevada Geodetic Lab) provides dilatation/shear at 100 m (bands 4,7,8 of training_features: geod_2ndinv, geod_shearrate, geod_dilaterate). Dilatation >p90 marks actively extending jogs where relay ramps / step-overs will host hidden faults (our Rank #2 hypothesis). Free, official, in training_features.tif (sha 4371c82e).

## USGS faults catalogue and its gaps
- Quaternary Faults v1/v2 (GDR: faults_quaternary_...zip 5.76/5.85 MB) and SGMC state maps (DS1052) together show 60,988 catalogue pixels in footprint (prepared_manifest.json). Yet 2020 M6.5 Monte Cristo Range rupture was on largely unmapped Candelaria faults: Koehler et al. 2021 SRL 92(2A) 823 <https://doi.org/10.1785/0220200371> + Liu et al. BSSA 111(6) <https://doi.org/10.1785/0120200327> + NBMG map <http://www.nbmg.unr.edu/Geohazards/Earthquakes/MonteCristoRangeEQData.html> prove unmapped faults rupture. Our B=2 buffer acknowledges this catalog incompleteness.

## Competition specifics
- Metric: distance-weighted Tversky DTI α=0.2 β=0.8 R=300 m triangular k(d)=max(1−d/R,0) — see <https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric> and Wikipedia Tversky <https://en.wikipedia.org/wiki/Tversky_index>.
- Format: EPSG:32611 (WGS84 / UTM 11N) <https://epsg.io/32611>, 100 m, 3730×3292, transform [100,0,243350,0,-100,4508550] matching sample_submission.tif sha 2176d08e... (verified via rasterio in GEMSDOE32 prepared_manifest.json).
- Training features 19 bands: mag_anom, rtp, tmi_hg, geod_2ndinv, iso_grav_anom_slope, tc, geod_shearrate, geod_dilaterate, tmi_vg, deq_n100a15, etc. (reference solution notebook <https://github.com/drivendataorg/gems-prize-reference-solution>).
