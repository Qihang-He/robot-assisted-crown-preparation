# Step 2 - crown fit (preoperative crowns and seating fit)

## What it does in the paper

Region segmentation of the four preoperative design crowns (`DG-G1-C` ... `DG-G4-C`), registration
of the seating scans (S-scans) to the abutment base, and registration plus region segmentation of
the crown scans (C-scans). This is the "crown fit analysis" of Appendix Section 4 and the middle
panel of the pipeline flowchart (Appendix Figure 2).

The segmented crown and abutment region meshes produced here feed the crown printing accuracy
(Appendix Table 6), the internal fit (Appendix Table 7) and the marginal gap analyses, which are
computed by `02_python_analysis/02_crown_fit/`; the shoulder-margin point clouds needed for the
marginal gap are extracted in step 3.

## Scripts

1. **`01_design_crown_segmentation.py`** - segments `DG-G<k>-C` with `36-segmentation-curve`; the
   intaglio surfaces receive flipped normals. Incremental: an already segmented crown is skipped.
2. **`02_seating_scan_registration.py`** - manual plus global registration of each S-scan
   (`G<k>-<T>-<j>-S`) to the matching abutment base (already segmented in step 1). No fine
   registration is applied in this step.
3. **`03_crown_scan_segmentation.py`** - for each C-scan: manual and global registration to the
   S-scan, projection of the segmentation curve, extraction of the outer-surface registration
   patch, fine registration, interactive segmentation into seven regions with flipped normals on the
   intaglio (`36` and the subregions), and grouping.

## Inputs

* Scene objects: design crowns `DG-G<k>-C`; S-scans `G<k>-<T>-<j>-S`; C-scans `G<k>-<T>-<j>-C`;
  the abutment bases `G<k>-<T>-<j>-A-F0-base` produced in step 1.
* Scene curves: `36-segmentation-curve`.

## Outputs

* Region groups in the scene: `<model>-36`, `<model>-F0-outer-surface`,
  `<model>-F1-shoulder` ... `<model>-F6-lingual-occlusal-surface`, together with the group
  `initial-data` and the two registration patches
  (`<model>-F0-outer-surface-for-registration`, `<model>-F0-base-for-registration`).
  The `initial-data` group holds the complete (unsegmented) C-scan meshes that two analysis scripts
  additionally need; see [docs/data_availability.md](../../docs/data_availability.md).
* Registration transformation matrices (`.tfm`) in `TRANSFORM_DIR` (default
  `./output/registration_matrices`).
* STL files only after the export utility is run.

## Runtime

* Geomagic Wrap 2021 or later with its bundled Python.
* Interactive: patch clicks and confirmation of the manual registrations.
