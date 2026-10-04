# Step 1 - preparation accuracy

## What it does in the paper

Region segmentation of the ideal preparation (`IP`) and of every robot-prepared abutment scan
(A-scan), followed by point-to-triangle signed-distance comparison of each A-scan region against
the corresponding `IP` region. This is the "preparation accuracy analysis" of Appendix Section 4
and the left panel of the pipeline flowchart (Appendix Figure 2).

The scene groups and the signed distances produced here are the input of the main-text preparation
accuracy analysis (main Table 2) and of Appendix Tables 4 and 5 (per-specimen PSR error and
between-specimen repeatability), which are computed by `02_python_analysis/01_preparation_accuracy/`.

## Scripts

1. **`01_reference_object_processing.py`** - run once. Clears the scene, creates all required
   groups and interactively segments the `IP` model into seven regions.
2. **`02_test_object_segmentation_and_comparison.py`** - for every A-scan: manual registration to
   `IP-F0-base`, global and fine registration, interactive region segmentation, 3D comparison
   against the corresponding `IP` region, and automatic grouping of the results.

## Inputs

* Scene objects: the ideal preparation named `IP`; the A-scans named `G<k>-<T>-<j>-A`
  (e.g. `G1-R-1-A`).
* Scene curves: `36-segmentation-curve`.
* Script 01 must have been run and its region objects pinned before script 02 runs.

## Outputs

* Region groups in the scene: `<model>-F0-base`, `<model>-36` and
  `<model>-F1-shoulder` ... `<model>-F6-lingual-occlusal-surface`, plus the 3D comparison results
  grouped per specimen.
* Registration transformation matrices (`.tfm`) in `TRANSFORM_DIR` (default
  `./output/registration_matrices`).
* STL files only after the export utility is run:
  `01_geomagic_wrap_scripts/utilities/export_results_to_stl.py`.

## Runtime

* Geomagic Wrap 2021 or later with its bundled Python.
* Interactive: prompts for a patch click on each region and for confirmation of the manual
  registration.
