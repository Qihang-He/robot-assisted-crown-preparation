# 01 - preparation accuracy

## What it does in the paper

Computes the preparation accuracy of the robot-prepared abutments after the per-specimen
print-scan-registration (PSR) correction, and draws the preparation-accuracy and region-definition
figures. The signed distances themselves are produced by the Geomagic Wrap step 1 script; these
scripts turn them into the reported statistics.

| Script | Paper output |
| --- | --- |
| `01_preparation_accuracy_analysis.py` | main Table 2 (region-level preparation accuracy after PSR correction) and Appendix Table 4 (per-specimen PSR error) and Appendix Table 5 (between-specimen repeatability) |
| `02_preparation_accuracy_visualization.py` | main Figure 2 panels: PSR error per specimen, `mu_prep` and `sigma_prep` raincloud plots, and `R_pos`/`mu_pos`/`P75` grouped bar chart |
| `03_preparation_overview.py` | the 4x8 signed-distance map overview of all abutments against `IP` (Figure 2 distance maps) |
| `04_region_segmentation_visualization.py` | the region-definition figure (Figure 1): 2x2 grid of region-segmented model views |

## Inputs

* `Region_Segmentation_Results/F0-base/`, `36/`, `F1-shoulder/` ... `F6-lingual-occlusal-surface/`
  (the meshes exported from the Geomagic Wrap scene).
* `Raw_Data/Reference/IP.stl` and `Region_Segmentation_Results/36/IP-36.stl`.
* `02_preparation_accuracy_visualization.py` reads the CSVs written by script 01.

## Outputs (under `<DATA_ROOT>/analysis_results/`)

* `preparation_accuracy/PSR_summary.csv`, `region_results.csv`, `region_summary.csv`,
  `consistency_PSR.csv`
* `preparation_accuracy_visualization/PreparationAccuracy_2x2.png` and `.pdf`
* `overall_visual/All_G_R_A36_vs_IP.png` and `.pdf`
* `overall_visual/` region-segmentation views

## Runtime

* Python 3.8 or later; numpy, pandas, scipy, trimesh, matplotlib, seaborn, tqdm.
* Script 01 uses up to six worker processes; the region-wise signed-distance step takes a few
  minutes for 32 specimens on a desktop machine. The scripts cache nothing.
