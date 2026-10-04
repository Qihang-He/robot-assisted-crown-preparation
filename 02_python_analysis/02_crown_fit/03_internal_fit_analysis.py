#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Internal Fit Analysis

Compute internal fit (gap) between crown (C) and abutment (A) for each region.
Signed distance from C to A after alignment.

Output: per‑sample μ_gap and σ_gap (CSV), and group‑wise summary.

Copyright © 2026 Qihang He
Released under the MIT licence; see LICENSE.

Paper step: internal fit (gap between crown and abutment).
Inputs:  Region_Segmentation_Results/{36,F1-shoulder ... F6-lingual-occlusal-surface}/ (C- and A-scans)
Outputs: analysis_results/internal_fit/gap_results.csv, gap_group_summary.csv
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
OUTPUT_DIR = os.path.join(DATA_ROOT, "analysis_results", "internal_fit")
os.makedirs(OUTPUT_DIR, exist_ok=True)

THRESHOLD = 1.0
WORKERS = min(6, cpu_count())

REGIONS = ['36', 'F1-shoulder', 'F2-axial-wall', 'F3-buccal-cusp-reduction',
           'F4-lingual-cusp-reduction', 'F5-buccal-occlusal-surface', 'F6-lingual-occlusal-surface']
RSHORT = {'36':'36', 'F1-shoulder':'F1', 'F2-axial-wall':'F2',
          'F3-buccal-cusp-reduction':'F3', 'F4-lingual-cusp-reduction':'F4',
          'F5-buccal-occlusal-surface':'F5', 'F6-lingual-occlusal-surface':'F6'}


def load_mesh(folder, fname):
    p = os.path.join(STL_ROOT, folder, fname)
    return trimesh.load(p) if os.path.exists(p) else None


def signed_dist(verts, ref):
    closest, dist, tid = trimesh.proximity.closest_point(ref, verts)
    n = ref.face_normals[tid]
    return np.sign(np.einsum('ij,ij->i', verts - closest, n)) * dist


def stats(sd, thresh):
    valid = np.abs(sd) <= thresh
    sv = sd[valid]
    if len(sv) == 0:
        return None
    return {'n': len(sv), 'μ_gap (mm)': float(np.mean(sv)), 'σ_gap (mm)': float(np.std(sv, ddof=1))}


def process(sid, group):
    recs = []
    for reg in REGIONS:
        a = load_mesh(reg, f'{sid}-A-{reg}.stl')
        c = load_mesh(reg, f'{sid}-C-{reg}.stl')
        if a is None or c is None: continue
        sd = signed_dist(c.vertices, a)
        s = stats(sd, THRESHOLD)
        if s is None: continue
        recs.append({'SampleID': sid, 'Group': group, 'Region': reg,
                     'RegionShort': RSHORT[reg], 'n_valid': s['n'],
                     'μ_gap (mm)': s['μ_gap (mm)'], 'σ_gap (mm)': s['σ_gap (mm)']})
    return recs


def main():
    print("="*60)
    print("  Internal Fit (A vs C) – Parallel")
    print("="*60)
    t0 = time.time()
    folder36 = os.path.join(STL_ROOT, '36')
    pat = re.compile(r'^(G\d+-R-\d+)-A-36\.stl$')
    sids = sorted(set(re.match(pat, f).group(1) for f in os.listdir(folder36) if re.match(pat, f)))
    print(f"[1] {len(sids)} samples.")
    all_recs = []
    tasks = [(s, re.match(r'(G\d+)', s).group(1)) for s in sids]
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        fs = {pool.submit(process, s, g): s for s,g in tasks}
        for f in tqdm(as_completed(fs), total=len(fs), desc="Gap"):
            recs = f.result()
            if recs: all_recs.extend(recs)
    if not all_recs: print("No results."); return
    df = pd.DataFrame(all_recs).sort_values(['SampleID','Region']).reset_index(drop=True)
    df.to_csv(os.path.join(OUTPUT_DIR, 'gap_results.csv'), index=False)
    summary = df.groupby(['Group','RegionShort'])[['μ_gap (mm)','σ_gap (mm)']].agg(['mean','std','count'])
    summary.columns = ['_'.join(c).strip() for c in summary.columns]
    summary.to_csv(os.path.join(OUTPUT_DIR, 'gap_group_summary.csv'))
    print(summary)
    print(f"Time: {time.time()-t0:.1f}s")


if __name__ == '__main__':
    main()