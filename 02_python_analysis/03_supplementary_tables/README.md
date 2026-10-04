# 03 - supplementary tables

## What it does in the paper

Compiles the CSV results of `01_preparation_accuracy/` and `02_crown_fit/` into a single formatted
Excel workbook, `Supplementary_Tables.xlsx`, with one worksheet per supplementary table
(Tables S1-S10) plus the pairwise p-value sheets. This workbook is the deposited item
`03_Analysis_Results/supplementary_tables/` of the companion dataset.

## Script

**`01_generate_supplementary_tables.py`** - reads the analysis CSVs and writes the workbook with
bold headers, fixed column widths and a descriptive title and note per worksheet. The table
definitions (`TABLE_DEFS`) at the top of the script list each worksheet, its source file and the
manuscript or appendix item it supports.

## Inputs

* `ANALYSIS_DIR`, the `analysis_results/` directory produced by the other analysis scripts:
  `preparation_accuracy/*.csv`, `crown_accuracy/*.csv`, `internal_fit/*.csv`,
  `marginal_gap/*.csv`.

## Outputs

* `OUTPUT_FILE` (default `Supplementary_Tables.xlsx`), one worksheet per table.
* The script is skipped with a warning for any source CSV that does not exist, so it can also be
  run on a partial set of results.

## Runtime

* Python 3.8 or later; pandas and openpyxl only (no trimesh, no worker processes).
* Seconds.
