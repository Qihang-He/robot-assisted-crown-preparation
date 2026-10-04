# 01 - Geomagic Wrap scripts

Seven scripts that run inside **Geomagic Wrap 2021 or later** (3D Systems, USA) with the Python
environment bundled with the application. They import `geomagic.app.v3`, drive the Geomagic Wrap
scene and prompt the operator to click a small patch on the target region, so they are interactive
and cannot be run end to end unattended. No third-party package is needed: of this repository only
the standard library and `geomagic.app.v3` are used.

These scripts correspond to the "three processing steps" of Appendix Section 4: preparation
accuracy analysis, crown fit analysis and marginal contour extraction, plus one utility that
exports the scene to STL. The end-to-end position of each step is shown in the pipeline flowchart,
Appendix Figure 2; the data flow is described in [docs/workflow.md](../docs/workflow.md).

## Contents

| Folder | Scripts | Purpose |
| --- | --- | --- |
| [step1_preparation_accuracy/](step1_preparation_accuracy/) | 2 | region segmentation of `IP` and of every A-scan, registration, signed-distance comparison |
| [step2_crown_fit/](step2_crown_fit/) | 3 | region segmentation of the design crowns, registration of the S-scans to the abutment frame, segmentation of the C-scans |
| [step3_marginal_contour/](step3_marginal_contour/) | 1 | shoulder-margin point clouds for every A- and C-scan |
| [utilities/](utilities/) | 1 | batch export of every region group to STL |

Total: **7** Geomagic Wrap scripts. Appendix Section 4 states "eight"; the repository contains
seven, and the discrepancy is recorded rather than repaired by editing the appendix (see the
[root README](../README.md)).

## Shared conventions

* Each script has a `CONFIG` block at the top of the file with input and output paths and an
  `OVERWRITE_EXISTING` (or `USE_INCREMENTAL`) switch.
* The scripts write into `./output/...` by default; change `TRANSFORM_DIR`, `OUTPUT_DIR` or
  `BASE_DIR` to match your environment.
* Object names in the Geomagic Wrap scene must follow
  [docs/naming_conventions.md](../docs/naming_conventions.md), section 4.
* Run the step 1 and step 2 scripts in the order of their `01_`, `02_`, `03_` prefixes, in one
  Geomagic Wrap session, and export with the utility at the end.

## Environment

* Geomagic Wrap 2021 or later, installed with its Python scripting support (bundled Python 3.6+).
* The standalone packages of `requirements.txt` are **not** used by these scripts.
