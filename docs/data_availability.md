# Data availability

## Code (this repository)

This repository contains the analysis code only. Cite the article together with release `v1.0.0`
of this repository; the machine-readable metadata are in [CITATION.cff](../CITATION.cff).

## Data deposit

The raw scans and the derived result tables are deposited separately at figshare:

> **https://doi.org/10.6084/m9.figshare.34067511**

The deposit is organised as four archives, one per numbered item, plus a deposit README, a file
manifest, a complete file inventory and SHA-256 checksums:

| Item | Contents | Files |
| --- | --- | --- |
| `01_Raw_Scans.zip` | raw optical scans: `Main_Specimens/G1..G4/` (32 specimens x A/C/S = 96 files; the first three specimens of each group are the 12 pilot specimens) and `Reference_Models/` (`IP.stl`, `DG-G1-C.stl` ... `DG-G4-C.stl`) | 101 STL |
| `02_Region_Segmentation.zip` | region-segmented meshes and shoulder-margin point clouds, one directory per region (`36/`, `F0-base/`, `F1-shoulder/` ... `F6-lingual-occlusal-surface/`, `shoulder-margin-point-cloud/`) | 580 |
| `03_Analysis_Results.zip` | the derived CSVs: `preparation_accuracy/`, `crown_accuracy/`, `internal_fit/`, `marginal_gap/`, `supplementary_tables/` | 11 CSV |
| `04_Supplementary_Materials.zip` | supplementary document and table, the validation figure and the delivered validation scripts and result tables | 14 |

The deposit README documents the file naming, the units and the sign conventions, the software used
and the provenance of every archive. The specimen, region and scene-object names match the
conventions used by the scripts in this repository; see
[naming_conventions.md](naming_conventions.md).

## Reproducing the deposited tables

1. Download and unpack `02_Region_Segmentation.zip` and `01_Raw_Scans.zip`.
2. Assemble a working directory with `Region_Segmentation_Results/` (from
   `02_Region_Segmentation.zip`) and `Raw_Data/Reference/` (the five reference models of
   `01_Raw_Scans.zip`); the layout is given in [naming_conventions.md](naming_conventions.md),
   section 6.
3. Set `DATA_ROOT` at the top of each analysis script to that working directory.
4. Run the scripts in the order given in the [root README](../README.md). The CSVs written under
   `analysis_results/` reproduce the deposit item `03_Analysis_Results.zip`.

The Geomagic Wrap scripts in `01_geomagic_wrap_scripts/` regenerate the segmentation products of
`02_Region_Segmentation.zip` from the scanner output; they need Geomagic Wrap 2021 or later and its
bundled Python.

## Known limitation: the `initial-data` group

Two analysis scripts read the complete, unsegmented crown mesh from
`Region_Segmentation_Results/initial-data/`:

* `02_python_analysis/02_crown_fit/01_crown_accuracy_analysis.py` (crown printing accuracy);
* `02_python_analysis/02_crown_fit/03_internal_fit_analysis.py` (internal fit).

That group is deliberately not part of the deposit, because it duplicates the C-scan STL files of
`01_Raw_Scans.zip`. Before running those two scripts, export the complete crown meshes into
`Region_Segmentation_Results/initial-data/` with
`01_geomagic_wrap_scripts/utilities/export_results_to_stl.py`, or copy the `*-C.stl` files of
`01_Raw_Scans/` there. All other analyses run directly on the deposited folders.

## Reported but not deposited

* The manually delineated region meshes used for the segmentation validation (Appendix Section 3)
  are not part of the deposit; only the resulting metric tables are. The validation scripts read
  them from `MANUAL_ROOT`/`AUTO_ROOT` and are documented in
  `02_python_analysis/04_validation/README.md`.
* The cad/cam files of the ideal preparation and the design crowns are part of the printed-model
  workflow and are not deposited; the exported reference models `IP.stl` and `DG-G<k>-C.stl` are.
