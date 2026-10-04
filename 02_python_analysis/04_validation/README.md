# 04 - validation of the semi-automated region segmentation

## What it does in the paper

Reproduces Appendix Section 3. Four geometric metrics - the Dice coefficient (scaled by 2, so that
2 indicates perfect coincidence, computed from point-to-triangle distances at a 0.05 mm threshold),
the Chamfer distance, the Hausdorff 95% distance and the absolute area difference - are computed
between pairs of manually or automatically segmented region meshes of twelve A-scans
(`G<k>-R-1` to `G<k>-R-3`, k = 1-4) for three comparisons:

* **intra-operator**: Operator A, round 1 vs round 2 (O1-1 vs O1-2);
* **inter-operator**: Operator A vs Operator B (O1-1 vs O2-1);
* **manual versus automatic**: Operator A round 1 vs the projection pipeline (O1-1 vs Auto).

The results are Appendix Tables 11a-11c and Appendix Figure 4 (also referred to as Figure S1 of the
supplementary material). No hypothesis test is applied; the aim is geometric equivalence.

## Scripts

1. **`compute_validation_metrics.py`** - builds the manual and automatic index from the two
   directory trees, computes the four metrics for every pair in parallel, and writes the CSV files.
2. **`visualize_validation_metrics.py`** - writes the boxplot figure (panels a-d, one box per region
   and comparison) and the Excel summary table from those CSVs.

## Inputs

* `MANUAL_ROOT` - manual segmentation STL files, one subdirectory per region, named
  `O<operator>-<round>-<specimen>-<region>.stl` (e.g. `O1-1-G1-R-1-A-F0-base.stl`).
* `AUTO_ROOT` - automatic segmentation STL files, one subdirectory per region, named
  `<specimen>-<region>.stl` (e.g. `G1-R-1-A-F0-base.stl`).
* `visualize_validation_metrics.py` reads the CSVs written by the compute script.

Both patterns are implemented as the regexes `MANUAL_PATTERN` and `AUTO_PATTERN` at the top of
`compute_validation_metrics.py`; the defaults are `./data/manual_segmentation` and
`./data/auto_segmentation`.

## Outputs (under `OUTPUT_DIR`, default `./output/validation_results`)

* `intra_operator_final.csv`, `inter_operator_final.csv`, `manual_vs_auto_final.csv`,
  `overall_comparison_final.csv`
* `figures/Validation_Metrics_Boxplot.png` and `.pdf` (600 dpi)
* `validation_summary.xlsx`

## Runtime

* Python 3.8 or later; numpy, pandas, trimesh, tqdm, matplotlib, seaborn, openpyxl.
* The compute script samples 5000 points per mesh and uses up to six worker processes; minutes for
  12 specimens x 8 regions x 3 comparisons.

## Notes

* The manually delineated operator meshes are **not** part of the data deposit; only the resulting
  metric tables are. The automatic region meshes can be re-created with the Geomagic Wrap step 1
  script or taken from `02_Region_Segmentation.zip`.
* The licence of this repository (MIT) applies to these scripts as well; see the root
  [LICENSE](../../LICENSE).
