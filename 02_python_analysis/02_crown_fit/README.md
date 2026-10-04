# 02 - crown fit

## What it does in the paper

Computes the printing accuracy of the preoperative crowns, the internal fit between the crown and
the prepared abutment, and the marginal gap along the finish line (including its angular structure
and the pairwise group comparisons). Together these are the crown-fit results of the manuscript.

| Script | Paper output |
| --- | --- |
| `01_crown_accuracy_analysis.py` | crown printing accuracy per specimen and per group (Appendix Table 6) |
| `02_crown_accuracy_visualization.py` | violin plot with significance brackets for `mu_crown` and `sigma_crown` across G1-G4 (figure for Appendix Table 6) |
| `03_internal_fit_analysis.py` | internal fit `mu_gap`, `sigma_gap` per region and group (Appendix Table 7) |
| `04_internal_fit_visualization.py` | 2x1 strip plot with mean and SD for the internal fit metrics (Appendix Figure 3) |
| `05_marginal_gap_analysis.py` | marginal gap `mu`, `sigma`, `P75` and `IoU_XY` per specimen and group (Appendix Table 8); the per-sector series behind Appendix Table 12 |
| `06_marginal_gap_visualization.py` | 2x2 composite figure for the marginal gap metrics (Figure 3 panels) and the pairwise p-value tables (Appendix Table 9) |
| `07_shoulder_contour_overview.py` | 4x8 heatmap overview of the shoulder-margin gap along the finish line (Figure 3 contour maps) |

## Inputs

* `Region_Segmentation_Results/36/`, `F1-shoulder/` ... `F6-lingual-occlusal-surface/` - the C- and
  A-scan region meshes for the internal fit analysis.
* `Region_Segmentation_Results/initial-data/` - the complete crown meshes, needed by
  `01_crown_accuracy_analysis.py` and `03_internal_fit_analysis.py` only. This group is not part of
  the data deposit; see [docs/data_availability.md](../../docs/data_availability.md).
* `Raw_Data/Reference/DG-G1-C.stl` ... `DG-G4-C.stl` - the design crowns for the ICP registration of
  `01_crown_accuracy_analysis.py`.
* `Region_Segmentation_Results/shoulder-margin-point-cloud/*.asc` - the paired A- and C-scan
  shoulder-margin point clouds for the marginal gap analyses (scripts 05, 06, 07).
* The visualization scripts (02, 04, 06) read the CSVs written by the corresponding analysis
  scripts.

## Outputs (under `<DATA_ROOT>/analysis_results/`)

* `crown_accuracy/crown_accuracy.csv` (per specimen, with the ICP matrix) and
  `crown_group_summary.csv`
* `crown_accuracy_visualization/` figure (600 dpi PNG and PDF)
* `internal_fit/gap_results.csv` and `gap_group_summary.csv`
* `internal_fit_visualization/` figure (300 dpi PNG and PDF)
* `marginal_gap/marginal_gap_results.csv`, `group_summary.csv` and the per-specimen detail plots
* `marginal_gap_visualization/MarginalGap_Composite.png` and `.pdf`, plus
  `pairwise_pvalues_<metric>.csv`
* `overall_visual/All_Shoulder_Contour_Gap_4x8.png` and `.pdf`

## Runtime

* Python 3.8 or later; numpy, pandas, scipy, trimesh, shapely, matplotlib, tqdm.
* The analysis scripts (01, 03, 05) use up to six worker processes; script 05 resamples each
  contour at 3600 angular points and also writes one detail plot per specimen.
