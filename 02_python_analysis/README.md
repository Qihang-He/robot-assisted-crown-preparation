# 02 - Python analysis

Fourteen standalone scripts that run under ordinary CPython 3.8 or later with the packages pinned
in [requirements.txt](../requirements.txt) (or the conda environment of
[environment.yml](../environment.yml)). They read the meshes and point clouds produced by the
Geomagic Wrap steps and write the tables and figures of the paper.

| Folder | Scripts | Paper output |
| --- | --- | --- |
| [01_preparation_accuracy/](01_preparation_accuracy/) | 4 | main Table 2 and its Figure 2 panels, Appendix Tables 4 and 5, the region-definition figure (Figure 1) |
| [02_crown_fit/](02_crown_fit/) | 7 | crown printing accuracy (Appendix Table 6), internal fit (Appendix Table 7 and Appendix Figure 3), marginal gap (Figure 3 panels, Appendix Tables 8, 9 and 12) |
| [03_supplementary_tables/](03_supplementary_tables/) | 1 | `Supplementary_Tables.xlsx` (Tables S1-S10 and the pairwise p-value sheets) |
| [04_validation/](04_validation/) | 2 | Appendix Section 3: Tables 11a-11c and Appendix Figure 4 (Figure S1 of the supplementary material) |

Total: **14** standalone Python scripts.

## Configuration

Each script has a `DATA_ROOT` variable at the top (the supplementary-table script uses
`ANALYSIS_DIR` and `OUTPUT_FILE`) that must be set to the local project data directory containing:

* `Region_Segmentation_Results/` - the segmented STL files and the shoulder-margin point clouds
  (output of the Geomagic Wrap steps, deposited as `02_Region_Segmentation.zip`);
* `Raw_Data/Reference/` - `IP.stl` and `DG-G1-C.stl` ... `DG-G4-C.stl` (from `01_Raw_Scans.zip`);
* `analysis_results/` - the output directory for all CSV and figure results.

The expected layout is shown in [docs/naming_conventions.md](../docs/naming_conventions.md),
section 6.

## Execution order

1. **01_preparation_accuracy** - after the step 1 segmentation is complete.
2. **02_crown_fit** - after the step 2 and step 3 segmentation is complete (the marginal gap
   analysis needs the shoulder-margin point clouds of step 3).
3. **03_supplementary_tables** - after all analysis scripts have completed; it consumes their CSVs.
4. **04_validation** - independent of the other three; it needs its own manual and automatic
   segmentation directories.

Within each folder the scripts are run in numerical order (`01_` analysis, then the visualization
scripts).

## Dependencies

Python 3.8 or later with numpy, pandas, scipy, trimesh, shapely, tqdm, matplotlib, seaborn and
openpyxl; see the repository root for the pinned versions. The Geomagic Wrap scripts do not use any
of these packages.
