# Naming conventions

The names used by the scripts, by the deposited data and by the manuscript are the same. This page
is the single reference for them.

## 1. Specimen identifiers

```
G<k>-<T>-<j>-<scan>
```

| Field | Values | Meaning |
| --- | --- | --- |
| `G<k>` | `G1` `G2` `G3` `G4` | cement-space group: 40, 60, 80 and 100 um (n = 8 per group) |
| `<T>` | `R` | regular specimen of the main experiment, `j` = 1-8 |
|  | `P` | pilot specimen (`j` = 1); deposited for completeness, not reported in the paper |
| `<j>` | `1`-`8` | specimen index inside the group |
| `<scan>` | `A` | abutment scan: the printed arch after robotic preparation |
|  | `C` | crown scan: the as-manufactured preoperative crown |
|  | `S` | seating scan: the crown seated on the abutment under a 2-kg static load |

Examples: `G1-R-1-A` = group 1 (40 um cement space), regular specimen 1, prepared abutment.
`G3-P-1-C` = the pilot specimen of group 3, crown scan.

A complete specimen therefore consists of the triple `G<k>-<T>-<j>-A`, `-C` and `-S`.

## 2. Reference models

| Name | Meaning |
| --- | --- |
| `IP` | ideal preparation: the planned (target) preparation geometry of tooth #36 |
| `DG-G<k>-C` | design crown: the preoperative crown design of group `k` (k = 1-4) |

## 3. Region codes

| Code | Region name used in file names | Meaning |
| --- | --- | --- |
| `F0` | `F0-base` | non-operative base of the printed arch; PSR reference |
|  | `F0-outer-surface` | outer surface of crowns and crown scans; crown registration |
| `F1` | `F1-shoulder` | shoulder |
| `F2` | `F2-axial-wall` | axial wall |
| `F3` | `F3-buccal-cusp-reduction` | buccal cusp reduction |
| `F4` | `F4-lingual-cusp-reduction` | lingual cusp reduction |
| `F5` | `F5-buccal-occlusal-surface` | buccal occlusal surface |
| `F6` | `F6-lingual-occlusal-surface` | lingual occlusal surface |
| `36` | `36` | complete operative surface (F1-F6 combined) |
|  | `shoulder-margin-point-cloud` | shoulder-margin point cloud of A- and C-scans |

Elsewhere in the repository `F0` alone means `F0-base`.

Example: `G1-R-1-A-F1-shoulder.stl` is the shoulder region of the prepared abutment of specimen
`G1-R-1`; `G1-R-1-A-shoulder-margin-point-cloud.asc` is its shoulder-margin point cloud.

## 4. Geomagic Wrap scene object names

The Geomagic Wrap scripts address models by name, so the scene must use these names.

| Scene object | Pattern | Produced by |
| --- | --- | --- |
| Ideal preparation | `IP` | imported by the operator |
| Design crowns | `DG-G<k>-C` (k = 1-4) | imported by the operator |
| A-scans | `G<k>-<T>-<j>-A` | imported by the operator |
| C-scans | `G<k>-<T>-<j>-C` | imported by the operator |
| S-scans | `G<k>-<T>-<j>-S` | imported by the operator |
| Segmentation curve | `36-segmentation-curve` | drawn once on `IP` by the operator |
| Shoulder curve | `IP-shoulder-outline-curve` | drawn once on `IP` by the operator |
| Region meshes | `<model>-F0-base`, `<model>-36`, `<model>-F1-shoulder` ... `<model>-F6-lingual-occlusal-surface` | step 1 and step 2 scripts |
| Region meshes of a crown | `<model>-F0-outer-surface`, `<model>-36`, `<model>-F1-shoulder` ... | step 2 scripts |
| Registration patches | `<model>-F0-base-for-registration`, `<model>-F0-outer-surface-for-registration` | step 2 scripts |
| Shoulder contours | `<model>-shoulder-outline-curve`, `<model>-shoulder-margin-point-cloud` | step 3 script |

Region groups used in the scene: `initial-data`, `36`, `F0-base`, `F0-outer-surface`,
`F1-shoulder`, `F2-axial-wall`, `F3-buccal-cusp-reduction`, `F4-lingual-cusp-reduction`,
`F5-buccal-occlusal-surface`, `F6-lingual-occlusal-surface` and the two registration groups above.
The export utility writes one directory per group.

## 5. Point-cloud files

```
<model>-shoulder-margin-point-cloud.asc
```

ASCII XYZ, one point per line, in millimetres. `<model>` is an A- or C-scan name.

For the marginal-gap analysis the point clouds are paired by specimen: the A-scan contour is the
preparation shoulder, the C-scan contour is the crown margin, and the two are resampled at 0.1
degree intervals (3600 points) about their common centroid. The analysis script recognises the
files through the regular expression `^(G\d+)-R-(\d+)-(A|C)-shoulder-margin-point-cloud\.asc$`.

## 6. Data directory expected by the analysis scripts

Every analysis script has a `DATA_ROOT` variable; the directory must contain:

```
<DATA_ROOT>/
├── Region_Segmentation_Results/      # = 02_Region_Segmentation.zip of the deposit
│   ├── 36/
│   ├── F0-base/
│   ├── F1-shoulder/ ... F6-lingual-occlusal-surface/
│   ├── initial-data/                 # complete C-scan meshes; see data_availability.md
│   └── shoulder-margin-point-cloud/
├── Raw_Data/
│   └── Reference/                    # IP.stl and DG-G1-C.stl ... DG-G4-C.stl
└── analysis_results/                 # created by the scripts
```

## 7. Validation file names

The validation scripts match the manual and automatic segmentation by regular expression:

| Set | Pattern | Example |
| --- | --- | --- |
| manual | `O<operator>-<round>-<specimen>-<region>.stl` | `O1-1-G1-R-1-A-F0-base.stl` |
| automatic | `<specimen>-<region>.stl` | `G1-R-1-A-F0-base.stl` |

Both are declared as `MANUAL_PATTERN` and `AUTO_PATTERN` at the top of
`02_python_analysis/04_validation/compute_validation_metrics.py`, and both sets are organised in one
subdirectory per region.

## 8. Units and signs

* Geometry (`.stl`, `.asc`): millimetres.
* Result tables: the unit is part of the column name; `(mm)` and `(um)` columns are not
  interchangeable.
* Signed point-to-triangle distances are positive when the test surface lies outside the reference
  surface, that is, **positive = under-prepared**.
* Angular quantities are referred to the buccal axis: 0 degrees buccal, +90 degrees mesial,
  180 degrees lingual, -90 degrees distal.
