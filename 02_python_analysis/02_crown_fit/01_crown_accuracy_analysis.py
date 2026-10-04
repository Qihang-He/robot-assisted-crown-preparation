#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Crown Accuracy Analysis

Evaluate crown printing accuracy by ICP‑registering the actual full crown
(from initial‑data) to the design crown (DG). Signed distances computed
over all vertices after transformation.

Output: per‑sample μ_crown and σ_crown (CSV), transformation matrices,
       and group‑wise summary.

Copyright © 2026 Qihang He
Released under the MIT licence; see LICENSE.

Paper step: crown printing accuracy.
Inputs:  Region_Segmentation_Results/initial-data/*.stl (C-scans) and Raw_Data/Reference/DG-G1-C ... DG-G4-C.stl
Outputs: analysis_results/crown_accuracy/crown_accuracy.csv (per specimen + ICP matrix),
         crown_group_summary.csv
Licence: MIT (see LICENSE).
"""

import os, re, warnings, time
import numpy as np
import pandas as pd
import trimesh
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count

warnings.filterwarnings('ignore')

# ============================ Configuration ============================
DATA_ROOT = r"path/to/your/project/data"

STL_ROOT = os.path.join(DATA_ROOT, "Region_Segmentation_Results")
RAW_DATA_DIR = os.path.join(DATA_ROOT, "Raw_Data")
REF_TRI_DIR = os.path.join(RAW_DATA_DIR, "Reference")
INITIAL_DIR = os.path.join(STL_ROOT, "initial-data")
OUTPUT_DIR = os.path.join(DATA_ROOT, "analysis_results", "crown_accuracy")
os.makedirs(OUTPUT_DIR, exist_ok=True)

TOL = 0.1
WORKERS = min(6, cpu_count())
ICP_MAX_ITER = 200
ICP_THRESHOLD = 1e-6
PATTERN = re.compile(r'^(G\d+-R-\d+)-C\.stl$')


def load_mesh(path):
    return trimesh.load(path) if os.path.exists(path) else None


def signed_dist(verts, ref):
    closest, dist, tid = trimesh.proximity.closest_point(ref, verts)
    n = ref.face_normals[tid]
    dot = np.einsum('ij,ij->i', verts - closest, n)
    return np.sign(dot) * dist


def stats(sd, thresh):
    valid = np.abs(sd) <= thresh
    sv = sd[valid]
    if len(sv) == 0:
        return None
    return {'n': len(sv), 'μ_crown (mm)': float(np.mean(sv)), 'σ_crown (mm)': float(np.std(sv, ddof=1))}


def process(sid, group):
    actual = load_mesh(os.path.join(INITIAL_DIR, f'{sid}-C.stl'))
    design = load_mesh(os.path.join(REF_TRI_DIR, f'DG-{group}-C.stl'))
    if actual is None or design is None:
        return sid, None, None
    try:
        from trimesh.registration import icp
        mat, _, _ = icp(actual.vertices, design.vertices, threshold=ICP_THRESHOLD, max_iterations=ICP_MAX_ITER)
    except Exception as e:
        print(f"[ICP] {sid}: {e}"); return sid, None, None
    trans = trimesh.transform_points(actual.vertices, mat)
    sd = signed_dist(trans, design)
    s = stats(sd, TOL)
    if s is None:
        return sid, None, None
    rec = {'SampleID': sid, 'Group': group, 'n_valid': s['n'],
           'μ_crown (mm)': s['μ_crown (mm)'], 'σ_crown (mm)': s['σ_crown (mm)']}
    return sid, mat, rec


def main():
    print("="*60)
    print("  Crown Accuracy – ICP + Full Cloud")
    print("="*60)
    t0 = time.time()
    files = os.listdir(INITIAL_DIR)
    sids = sorted(set(re.match(PATTERN, f).group(1) for f in files if re.match(PATTERN, f)),
                  key=lambda s: (int(re.search(r'G(\d+)',s).group(1)), int(re.search(r'R-(\d+)',s).group(1))))
    print(f"[1] {len(sids)} samples.")
    records, transforms = [], {}
    tasks = [(s, re.match(r'(G\d+)', s).group(1)) for s in sids]
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        fs = {pool.submit(process, s, g): s for s, g in tasks}
        for f in tqdm(as_completed(fs), total=len(fs), desc="ICP"):
            sid, mat, rec = f.result()
            if mat is not None:
                transforms[sid] = mat
            if rec is not None:
                records.append(rec)
    if not records:
        print("No results."); return
    df = pd.DataFrame(records).sort_values('SampleID').reset_index(drop=True)
    df.to_csv(os.path.join(OUTPUT_DIR, 'crown_accuracy.csv'), index=False)
    # Save matrices
    mat_dir = os.path.join(OUTPUT_DIR, 'transformation_matrices')
    os.makedirs(mat_dir, exist_ok=True)
    for s, m in transforms.items():
        np.savetxt(os.path.join(mat_dir, f'{s}_ICP.txt'), m, fmt='%.8f')
    # Summary
    summary = df.groupby('Group')[['μ_crown (mm)', 'σ_crown (mm)']].agg(['mean', 'std']).round(4)
    summary.to_csv(os.path.join(OUTPUT_DIR, 'crown_group_summary.csv'))
    print(summary)
    print(f"Time: {time.time()-t0:.1f}s")


if __name__ == '__main__':
    main()