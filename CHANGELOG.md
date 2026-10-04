# Changelog

All notable changes to this repository are documented in this file.

## v1.0.0 - 2026-10-04

First public release, accompanying the manuscript submission *"Accuracy of robotic full-crown
preparation and preoperative crown fit"* (submitted to the *Journal of Dental Research*).

* The repository layout is organised by runtime: `01_geomagic_wrap_scripts/` holds the seven
  Geomagic Wrap 2021 scripts in the three processing steps of Appendix Section 4 plus the STL
  export utility, and `02_python_analysis/` holds the fourteen standalone CPython scripts.
* `02_python_analysis/` covers preparation accuracy (main Table 2, Appendix Tables 4 and 5),
  crown fit (Appendix Tables 6-9 and 12, Appendix Figure 3, Figure 3), the supplementary table
  workbook and the segmentation validation of Appendix Section 3 (Appendix Tables 11a-11c,
  Appendix Figure 4).
* `docs/` documents the end-to-end workflow, the specimen, region and scene-object naming
  conventions, and the companion figshare data deposit.
* Every script carries a module docstring stating the paper output, the expected inputs, the
  written outputs and the runtime.
* `requirements.txt` and `environment.yml` pin the dependencies of the standalone scripts; the
  Geomagic Wrap scripts need none of them.
* Licence: MIT. Citation metadata: `CITATION.cff`.
