# Step 3 - marginal contour extraction

## What it does in the paper

Projects the reference curve `IP-shoulder-outline-curve` onto every A- and C-scan and writes the
resulting shoulder-margin point clouds. This is the "marginal contour extraction" of Appendix
Section 4 and the right panel of the pipeline flowchart (Appendix Figure 2).

The paired point clouds are the input of the marginal gap analysis: the crown margin contour
(C-scan) and the preparation shoulder contour (A-scan) are resampled at 0.1 degree intervals
(3600 points) about their common centroid, and the Euclidean distances between corresponding points
give the marginal gap metrics of main-text Figure 3, Appendix Table 8 (per-specimen metrics),
Appendix Table 9 (pairwise comparisons) and Appendix Table 12 (marginal gap by sector). Those
statistics are computed by `02_python_analysis/02_crown_fit/`.

## Script

**`01_shoulder_contour_point_cloud_extraction.py`** - for each target model
(`G<k>-<T>-<j>-A` and `G<k>-<T>-<j>-C`):

1. cleans the scene (keeps only the source curve and the target meshes);
2. classifies the meshes into the group `initial-data`;
3. projects `IP-shoulder-outline-curve` onto the target model;
4. extracts the shoulder-outline curve;
5. generates a dense point cloud from the curve;
6. writes the point cloud as an ASCII `.asc` file;
7. groups the curve and the point cloud.

## Inputs

* Scene objects: A-scan and C-scan models named `G<k>-<T>-<j>-A` / `G<k>-<T>-<j>-C`.
* Scene curve: `IP-shoulder-outline-curve` (drawn once on `IP`). The `36-segmentation-curve` is not
  needed here.

## Outputs

* `<model>-shoulder-margin-point-cloud.asc` in `OUTPUT_DIR` (default
  `./output/shoulder_margin_point_cloud`), ASCII XYZ in millimetres.
* The curve and the point cloud also remain grouped in the Geomagic Wrap scene.

## Runtime

* Geomagic Wrap 2021 or later with its bundled Python.
* No patch clicking in the normal path; the script processes all matching models automatically
  (`FORCE_AI_NAMES` restricts it to a list if needed).
