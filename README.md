# Analysis code: Accuracy of robotic full-crown preparation and preoperative crown fit

This repository contains the analysis code of the study *"Accuracy of robotic full-crown preparation
and preoperative crown fit"* (submitted to the *Journal of Dental Research*). Thirty-two
PolyJet-printed mandibular first molar models (tooth #36) were randomised into four cement-space
groups (40, 60, 80 and 100 um; n = 8 each) and prepared by a six-axis robot with marker-based
optical tracking, after which preoperatively fabricated crowns with the matching cement space were
seated on the prepared abutments. The code segments the scanned models into seven anatomical
regions, estimates and removes the per-specimen print-scan-registration (PSR) error, and computes
the preparation accuracy, crown printing accuracy, internal fit, marginal gap and the validation of
the semi-automated region segmentation.

The numerical results and the raw scans are deposited separately at figshare
(**https://doi.org/10.6084/m9.figshare.34067511**); see *Data availability* below.

## Repository layout

The top level separates the two runtimes: `01_` scripts run inside Geomagic Wrap, `02_` scripts run
under plain CPython.

```
.
├── README.md
├── LICENSE                               MIT licence
├── CITATION.cff                          citation metadata
├── CHANGELOG.md
├── requirements.txt                      Python dependencies of 02_python_analysis/
├── environment.yml                       optional conda environment (same dependencies)
├── .gitignore
├── docs/
│   ├── workflow.md                       end-to-end pipeline, stage by stage
│   ├── naming_conventions.md             specimen, region and scene-object names
│   └── data_availability.md              the companion figshare deposit
├── 01_geomagic_wrap_scripts/             7 scripts: Geomagic Wrap 2021 + bundled Python
│   ├── step1_preparation_accuracy/       2 scripts: IP and A-scan region segmentation + comparison
│   ├── step2_crown_fit/                  3 scripts: design crowns, S-scans, C-scans
│   ├── step3_marginal_contour/           1 script:  shoulder-margin point clouds
│   └── utilities/                        1 script:  batch STL export
└── 02_python_analysis/                   14 scripts: CPython >= 3.8
    ├── 01_preparation_accuracy/          4 scripts: PSR correction, accuracy, figures
    ├── 02_crown_fit/                     7 scripts: crown accuracy, internal fit, marginal gap
    ├── 03_supplementary_tables/          1 script:  Supplementary_Tables.xlsx
    └── 04_validation/                    2 scripts: segmentation validation (Appendix Section 3)
```

Two kinds of script live here and they are **not** interchangeable:

| Kind | Location | Runtime |
| --- | --- | --- |
| Geomagic Wrap scripts (7) | `01_geomagic_wrap_scripts/` | Geomagic Wrap 2021 or later with the Python environment bundled with the application; they `import geomagic.app.v3`, drive the scene and prompt the operator, so they are interactive |
| Standalone Python scripts (14) | `02_python_analysis/` | ordinary CPython >= 3.8 with the packages in `requirements.txt` |

Note on the appendix wording: Appendix Section 4 states that the deposit comprises "eight Geomagic
Wrap Python scripts in three processing steps". The repository contains **seven** Geomagic Wrap
scripts (two in step 1, three in step 2, one in step 3, plus the optional `utilities/` export
script). The discrepancy is recorded here and in the deposit report; the appendix itself was not
edited.

## Installation

### Standalone Python scripts

```
python -m venv .venv
.venv\Scripts\activate            # Windows
pip install -r requirements.txt
```

or, with conda:

```
conda env create -f environment.yml
conda activate crown-prep-analysis
```

Python 3.8 or later is required; the deposited results were produced with Python 3.10 and
numpy 1.21+, pandas 1.3+, scipy 1.7+, trimesh 3.9+, shapely 1.8+, tqdm 4.60+, matplotlib 3.4+,
seaborn 0.11+ and openpyxl 3.0+.

### Geomagic Wrap scripts

* Geomagic Wrap 2021 or later (3D Systems, USA), installed with its Python scripting support.
* No third-party packages: the scripts use only `geomagic.app.v3` and the standard library.
* Each script has a `CONFIG` block at the top (paths, patterns, `OVERWRITE_EXISTING`). The scripts
  write into `./output/...` by default; change `TRANSFORM_DIR`, `OUTPUT_DIR` or `BASE_DIR` to match
  your environment.

## The standalone Python scripts

Point every analysis script at the same data directory by editing the `DATA_ROOT` variable at the
top of the file (the supplementary-table script uses `ANALYSIS_DIR` and `OUTPUT_FILE`); the expected
directory layout is given in [docs/naming_conventions.md](docs/naming_conventions.md), section 6.
"Inputs" below are relative to that directory; "outputs" are written under
`<DATA_ROOT>/analysis_results/`.

| # | Script | Paper output | Inputs | Outputs |
| --- | --- | --- | --- | --- |
| 1 | `02_python_analysis/01_preparation_accuracy/01_preparation_accuracy_analysis.py` | main Table 2; Appendix Tables 4 and 5 | `F0-base/`, `36/`, `F1-F6/`, `Raw_Data/Reference/IP.stl` | `preparation_accuracy/{PSR_summary,region_results,region_summary,consistency_PSR}.csv` |
| 2 | `02_python_analysis/01_preparation_accuracy/03_preparation_overview.py` | Figure 2 distance maps | `36/`, `36/IP-36.stl` | `overall_visual/All_G_R_A36_vs_IP.png`, `.pdf` |
| 3 | `02_python_analysis/01_preparation_accuracy/02_preparation_accuracy_visualization.py` | Figure 2 panels (PSR error, raincloud plots, bar chart) | the CSVs of script 1 | `preparation_accuracy_visualization/PreparationAccuracy_2x2.png`, `.pdf` |
| 4 | `02_python_analysis/01_preparation_accuracy/04_region_segmentation_visualization.py` | Figure 1 (region definition) | all region folders | `overall_visual/` region-segmentation views |
| 5 | `02_python_analysis/02_crown_fit/01_crown_accuracy_analysis.py` | Appendix Table 6 (crown printing accuracy) | `initial-data/`, `Raw_Data/Reference/DG-G*.stl` | `crown_accuracy/crown_accuracy.csv`, `crown_group_summary.csv` |
| 6 | `02_python_analysis/02_crown_fit/02_crown_accuracy_visualization.py` | figure for Appendix Table 6 | the CSVs of script 5 | `crown_accuracy_visualization/` figure |
| 7 | `02_python_analysis/02_crown_fit/03_internal_fit_analysis.py` | Appendix Table 7 (internal fit) | `36/`, `F1-F6/` (C- and A-scans), `initial-data/` | `internal_fit/gap_results.csv`, `gap_group_summary.csv` |
| 8 | `02_python_analysis/02_crown_fit/04_internal_fit_visualization.py` | Appendix Figure 3 | `internal_fit/gap_results.csv` | `internal_fit_visualization/` figure |
| 9 | `02_python_analysis/02_crown_fit/05_marginal_gap_analysis.py` | Appendix Table 8 (per-specimen marginal gap) | `shoulder-margin-point-cloud/*.asc` | `marginal_gap/marginal_gap_results.csv`, `group_summary.csv`, per-specimen plots |
| 10 | `02_python_analysis/02_crown_fit/06_marginal_gap_visualization.py` | Figure 3 panels; Appendix Table 9 | `marginal_gap/marginal_gap_results.csv` | `marginal_gap_visualization/MarginalGap_Composite.png`, `.pdf`, `pairwise_pvalues_*.csv` |
| 11 | `02_python_analysis/02_crown_fit/07_shoulder_contour_overview.py` | Figure 3 contour maps; the series behind Appendix Table 12 | `shoulder-margin-point-cloud/*.asc` | `overall_visual/All_Shoulder_Contour_Gap_4x8.png`, `.pdf` |
| 12 | `02_python_analysis/03_supplementary_tables/01_generate_supplementary_tables.py` | `Supplementary_Tables.xlsx` (Tables S1-S10 and the pairwise p-value sheets) | `ANALYSIS_DIR` (all CSVs above) | `Supplementary_Tables.xlsx` |
| 13 | `02_python_analysis/04_validation/compute_validation_metrics.py` | Appendix Tables 11a-11c | `MANUAL_ROOT`, `AUTO_ROOT` (manual and automatic region meshes) | `intra_operator_final.csv`, `inter_operator_final.csv`, `manual_vs_auto_final.csv`, `overall_comparison_final.csv` |
| 14 | `02_python_analysis/04_validation/visualize_validation_metrics.py` | Appendix Figure 4 (Figure S1 of the supplementary material) | the CSVs of script 13 | `figures/Validation_Metrics_Boxplot.png`, `.pdf`, `validation_summary.xlsx` |

Scripts 1, 5, 7, 9 and 13 use up to six worker processes and cache nothing; on a desktop machine
the region-wise signed-distance step (script 1) takes a few minutes for 32 specimens.

Scripts 5 and 7 additionally need the complete, unsegmented crown meshes in
`Region_Segmentation_Results/initial-data/`, which are not part of the data deposit; see
[docs/data_availability.md](docs/data_availability.md).

## The Geomagic Wrap workflow

Run the following in this order, in one Geomagic Wrap session, with the models and curves of
[docs/naming_conventions.md](docs/naming_conventions.md), section 4 present in the scene.

1. `01_geomagic_wrap_scripts/step1_preparation_accuracy/01_reference_object_processing.py` - clears
   the scene, creates the region groups and segments the `IP` model. Run once.
   *Expected output:* the groups `IP-F0-base`, `IP-36` and `IP-F1-shoulder` ...
   `IP-F6-lingual-occlusal-surface`.
2. `01_geomagic_wrap_scripts/step1_preparation_accuracy/02_test_object_segmentation_and_comparison.py`
   - for every A-scan: manual registration to `IP-F0-base`, global and fine registration,
   interactive region segmentation, 3D comparison against the corresponding `IP` region and
   automatic grouping of the results.
   *Expected output:* per-specimen region groups with their signed-distance comparison results and
   the `.tfm` matrices.
3. `01_geomagic_wrap_scripts/step2_crown_fit/01_design_crown_segmentation.py` - segments the four
   design crowns with `36-segmentation-curve` (normals flipped on the intaglio).
4. `01_geomagic_wrap_scripts/step2_crown_fit/02_seating_scan_registration.py` - manual plus global
   registration of each S-scan to the matching abutment base (no fine registration).
5. `01_geomagic_wrap_scripts/step2_crown_fit/03_crown_scan_segmentation.py` - registers each C-scan
   to its S-scan, projects the curve, fine-registers on the outer-surface patch and segments the
   C-scan.
6. `01_geomagic_wrap_scripts/step3_marginal_contour/01_shoulder_contour_point_cloud_extraction.py` -
   projects `IP-shoulder-outline-curve` onto every A- and C-scan and writes the shoulder-margin
   point clouds.
   *Expected output:* `<model>-shoulder-margin-point-cloud.asc` per A- and C-scan.
7. `01_geomagic_wrap_scripts/utilities/export_results_to_stl.py` - exports every group to
   `<BASE_DIR>/<group name>/<mesh name>.stl`, reproducing the layout of the deposited
   `02_Region_Segmentation/` folder.

Several steps prompt the operator to click a small patch on the target region (base, axial wall,
etc.) and to confirm the manual registration, so the workflow cannot be automated end to end. The
pipeline as a whole, including the physical stages that precede it, is described in
[docs/workflow.md](docs/workflow.md).

## The validation workflow

The validation of the semi-automated region segmentation (Appendix Section 3) is independent of the
pipeline above:

```
python 02_python_analysis/04_validation/compute_validation_metrics.py
python 02_python_analysis/04_validation/visualize_validation_metrics.py
```

* `compute_validation_metrics.py` reads the manual segmentations from `MANUAL_ROOT` (files named
  `O<operator>-<round>-<specimen>-<region>.stl`) and the automatic ones from `AUTO_ROOT` (files
  named `<specimen>-<region>.stl`) and writes the four per-pair CSVs with the Dice, Chamfer,
  Hausdorff 95% and absolute-area-difference metrics of Appendix Section 3.2.4.
* `visualize_validation_metrics.py` writes `figures/Validation_Metrics_Boxplot.png` and `.pdf`
  (Appendix Figure 4, also referred to as Figure S1) and `validation_summary.xlsx`.

## Reproducing the deposited tables

The deposited result tables are the reference output of the standalone scripts above. To recompute
them:

1. Download and unpack `01_Raw_Scans.zip` and `02_Region_Segmentation.zip` from the figshare deposit
   (see [docs/data_availability.md](docs/data_availability.md)).
2. Assemble a working directory containing `Region_Segmentation_Results/` (from
   `02_Region_Segmentation.zip`) and `Raw_Data/Reference/` (the five reference models of
   `01_Raw_Scans.zip`).
3. Set `DATA_ROOT` in every analysis script to that directory and run the scripts in the order of
   the table above (1-4, then 5-11, then 12).
4. Compare the results with `03_Analysis_Results.zip` of the deposit. A convenient single check is
   that `analysis_results/preparation_accuracy/region_summary.csv` reproduces the region-level
   preparation accuracy of main Table 2, and that the group summaries of internal fit, crown
   accuracy and marginal gap match Appendix Tables 6-8. Small differences in the last digits are
   expected from the platform-specific threading of `trimesh.proximity` and from BLAS ordering.

The deposited data use the same folder names that the scripts expect, so no renaming is needed. The
one exception is the `initial-data` group, discussed in
[docs/data_availability.md](docs/data_availability.md).

## Data availability

* Raw scans, region-segmented meshes, shoulder-margin point clouds and the derived result tables:
  figshare, **https://doi.org/10.6084/m9.figshare.34067511**; see
  [docs/data_availability.md](docs/data_availability.md) for the contents of the four archives.
* Code: this repository; cite release `v1.0.0`
  (the machine-readable metadata are in [CITATION.cff](CITATION.cff)).

## Licence

MIT licence; see [LICENSE](LICENSE). Copyright (c) 2026 Qihang He, Yuchen Liu, Jie Zhang, Shiwei
Song, Chen Liu, Shizhu Bai, Yimin Zhao.

## Citation

If you use this code, please cite the article and the archived release:

> He Q, Liu Y, Zhang J, Song S, Liu C, Bai S, Zhao Y. Accuracy of robotic full-crown preparation and
> preoperative crown fit. *Journal of Dental Research* (submitted).

Machine-readable metadata are in [CITATION.cff](CITATION.cff).

## Contact

Corresponding authors named in the manuscript appendix: Prof. Shizhu Bai and Prof. Chen Liu, State
Key Laboratory of Oral & Maxillofacial Reconstruction and Regeneration, National Clinical Research
Center for Oral Diseases, Shaanxi Key Laboratory of Stomatology, Digital Center, School of
Stomatology, The Fourth Military Medical University, No. 145 Changle West Road, Xincheng District,
Xi'an 710032, Shaanxi, PR China.

* Shizhu Bai - Baishizhu@foxmail.com
* Chen Liu - Liuchen0508@foxmail.com

