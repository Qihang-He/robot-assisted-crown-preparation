# Utilities - batch STL export

## What it does in the paper

Exports every region group of the Geomagic Wrap scene to individual STL files, one directory per
group. It is the utility that turns the scene produced by
[step1](../step1_preparation_accuracy/) and [step2](../step2_crown_fit/) into the
`02_Region_Segmentation/` layout of the data deposit, which is the input of the whole
`02_python_analysis/` pipeline. It produces no manuscript table or figure of its own.

## Script

**`export_results_to_stl.py`**

1. iterates over all groups in the scene;
2. for each group that contains meshes, creates a subdirectory named after the group under
   `BASE_DIR`;
3. exports each mesh as `<mesh name>.stl`;
4. skips existing files when `OVERWRITE_EXISTING = 0` (incremental mode).

## Inputs

* Any groups containing mesh objects in the Geomagic Wrap scene (created by the step 1 and step 2
  scripts).
* Curves and point clouds are not exported; the shoulder-margin point clouds are written directly
  by [step3](../step3_marginal_contour/).

## Outputs

* `BASE_DIR/<group name>/<mesh name>.stl`, for example
  `output/stl_export/F1-shoulder/G1-R-1-A-F1-shoulder.stl`.
* `BASE_DIR` defaults to `./output/stl_export`.
* The complete, unsegmented crown meshes can also be exported here as the `initial-data` group when
  the two analysis scripts that need them are to be run; see
  [docs/data_availability.md](../../docs/data_availability.md).

## Runtime

* Geomagic Wrap 2021 or later with its bundled Python.
* Non-interactive; run after any segmentation step.
