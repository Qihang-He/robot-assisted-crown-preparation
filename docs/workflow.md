# End-to-end workflow

This document describes the order in which the specimens were produced, scanned and analysed, and
which part of this repository produces which artefact. It follows the manuscript and the appendix;
no step is described here that is not implemented in the repository or documented in the companion
data deposit.

## Overview

```
  CAD/CAM design            printing                  robotic preparation
  IP, DG-G<k>-C     -->     PolyJet, VeroDentPlus --> six-axis robot, tracked handpiece
                                                              |
                                                              v
  analysis                  region segmentation       optical scanning
  02_python_analysis  <--   Geomagic Wrap        <--   A-scan / C-scan / S-scan
                            (01_geomagic_wrap_scripts)        ^
                                                              |
                                                     crown seating (2-kg load)
```

| Stage | What happens | Artefacts | Where it is implemented |
| --- | --- | --- | --- |
| 1. Design | Ideal preparation (`IP`) and the four preoperative crown designs (`DG-G1-C` ... `DG-G4-C`) are designed with identical parameters except the cement-space offset (40, 60, 80, 100 um inward from `IP`) | `IP.stl`, `DG-G<k>-C.stl` | external CAD/CAM software (Exocad); not part of this repository |
| 2. Printing | Mandibular first molar models (tooth #36 in a teeth 35-37 arch) and the crowns are printed in VeroDentPlus on a PolyJet printer; 32 specimens are randomised to the four cement-space groups | printed models and crowns | external (Stratasys J750); not part of this repository |
| 3. Robotic preparation | A six-axis industrial robot with marker-based optical tracking executes the planned paths with a cylindrical diamond bur (new bur per specimen) | prepared abutments | external; not part of this repository |
| 4. Optical scanning | The as-manufactured crowns (C-scans), the prepared abutments (A-scans) and the seated assemblies (S-scans) are digitised by a laboratory optical scanner and exported as binary STL | `G<k>-<T>-<j>-{A,C,S}.stl` | external (3Shape); scanner output is the input of the code in this repository |
| 5. Region segmentation | Anatomical boundaries are drawn once on `IP` and projected onto every model, giving the regions F0-F6 and the aggregate region `36`; registration of the seating (S) and crown (C) scans to the abutment frame | `Region_Segmentation_Results/` (deposited as `02_Region_Segmentation.zip`) | `01_geomagic_wrap_scripts/step1_preparation_accuracy/`, `.../step2_crown_fit/` |
| 6. Marginal contour | The reference curve `IP-shoulder-outline-curve` is projected onto every A- and C-scan to extract the shoulder-margin point clouds | `<model>-shoulder-margin-point-cloud.asc` | `01_geomagic_wrap_scripts/step3_marginal_contour/` |
| 7. Export | All segmented meshes are exported to STL, one directory per region group | the `02_Region_Segmentation/` layout | `01_geomagic_wrap_scripts/utilities/` |
| 8. Analysis | Per-specimen PSR correction, preparation accuracy, crown printing accuracy, internal fit, marginal gap and the supplementary table workbook | `analysis_results/` CSVs and figures (deposited as `03_Analysis_Results.zip`) | `02_python_analysis/01_preparation_accuracy/`, `.../02_crown_fit/`, `.../03_supplementary_tables/` |
| 9. Validation | Dice, Chamfer distance, Hausdorff 95% and absolute area difference between manual and automatic region segmentation (Appendix Section 3) | validation CSVs, `figures/Validation_Metrics_Boxplot.*`, `validation_summary.xlsx` | `02_python_analysis/04_validation/` |

## Stage detail

### 1. Design and printing

The ideal preparation `IP` is the planned target geometry of tooth #36. The four design crowns
`DG-G1-C` ... `DG-G4-C` differ only in the cement space (40, 60, 80 and 100 um inward from `IP`).
The printed arch carries the non-operative base (region `F0-base`) that is left untouched by the
robot and therefore serves as the print-scan-registration (PSR) reference.

### 2. Robotic preparation

Each specimen is prepared once. The bur-tooth angle differs between regions (rotation plus
translation for the shoulder and the axial wall, a fixed angle for the cusp-reduction and occlusal
surfaces), which is the mechanism discussed in the manuscript; the regional grouping is listed in
[`naming_conventions.md`](naming_conventions.md).

### 3. Scanning

* **A-scan** - the printed arch after robotic preparation.
* **C-scan** - the as-manufactured preoperative crown.
* **S-scan** - the seated assembly: the crown seated on the prepared abutment under a 2-kg static
  load.

### 4. Region segmentation and registration (Geomagic Wrap)

The segmentation curve `36-segmentation-curve` is drawn once on `IP` and projected onto every other
model, so that all specimens share the same anatomical boundaries. Run order inside Geomagic Wrap:

1. `step1_preparation_accuracy/01_reference_object_processing.py` (once) - region groups on `IP`.
2. `step1_preparation_accuracy/02_test_object_segmentation_and_comparison.py` - per A-scan:
   manual registration to `IP-F0-base`, global and fine registration, region segmentation,
   3D comparison against the corresponding `IP` region.
3. `step2_crown_fit/01_design_crown_segmentation.py` - region groups on `DG-G<k>-C`.
4. `step2_crown_fit/02_seating_scan_registration.py` - S-scan registered into the abutment frame.
5. `step2_crown_fit/03_crown_scan_segmentation.py` - C-scan registered to the S-scan, curve
   projected, fine registration on the outer-surface patch, region segmentation with flipped
   normals on the intaglio.
6. `step3_marginal_contour/01_shoulder_contour_point_cloud_extraction.py` - shoulder-margin point
   clouds for every A- and C-scan.
7. `utilities/export_results_to_stl.py` - STL export of every region group.

Steps 2, 3, 4 and 5 prompt the operator to pick a patch on the target region and to confirm the
manual registration; they are not fully automatic. Each script has a `CONFIG` block at the top.

### 5. Analysis (standalone Python)

All analysis scripts read a single `DATA_ROOT` directory and are run in the order documented in the
[root README](../README.md). The physical pipeline above ends at the point clouds and STL meshes;
everything after that is arithmetic on those files:

* PSR correction on `F0-base` -> preparation accuracy per region;
* ICP registration of the C-scan to `DG-G<k>-C` -> crown printing accuracy;
* signed distances between the C- and A-scan region meshes -> internal fit;
* angular resampling (3600 points per contour) of the paired shoulder-margin point clouds ->
  marginal gap, its per-sector breakdown and its first-order harmonic.

### 6. Validation (Appendix Section 3)

Twelve A-scans (`G<k>-R-1` to `G<k>-R-3`, k = 1-4) were segmented manually twice by Operator A and
once by Operator B. The same scans were segmented automatically by the projection pipeline above.
The four metrics are computed for three comparisons: intra-operator (O1-1 vs O1-2), inter-operator
(O1-1 vs O2-1) and manual-versus-automatic (O1-1 vs Auto). The results are Appendix Tables 11a-11c
and Appendix Figure 4 (also referred to as Figure S1 of the supplementary material).
