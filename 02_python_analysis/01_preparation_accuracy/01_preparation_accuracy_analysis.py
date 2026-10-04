#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Preparation Accuracy Analysis

Compute robot preparation accuracy after per‑specimen PSR (base region)
correction. For each specimen, signed distances are computed between the
robot‑prepared abutment and the ideal preparation (IP) across seven
anatomical regions.

Indicators:
    μ_prep, σ_prep, R_pos (positive ratio), μ_pos (positive mean),
    and P75 (75th percentile)

Output: CSV files under analysis_results/preparation_accuracy/

Copyright © 2026 Qihang He
Released under the MIT licence; see LICENSE.

Paper step: main-text preparation accuracy (per-specimen PSR correction).
Inputs:  Region_Segmentation_Results/{F0-base,36,F1-shoulder ... F6-lingual-occlusal-surface}/*.stl
Outputs: analysis_results/preparation_accuracy/PSR_summary.csv, region_results.csv,
         region_summary.csv, consistency_PSR.csv
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
# Set DATA_ROOT to the top‑level project directory containing:
#   Region_Segmentation_Results/  (segmented STL files)
#   Raw_Data/                    (reference files)
#   analysis_results/            (output directory)
DATA_ROOT = r"path/to/your/project/data"

STL_ROOT = os.path.join(DATA_ROOT, "Region_Segmentation_Results")
RAW_DATA_DIR = os.path.join(DATA_ROOT, "Raw_Data")
REFERENCE_DIR = os.path.join(RAW_DATA_DIR, "Reference")
REF_IP = os.path.join(REFERENCE_DIR, "IP.stl")

OUTPUT_DIR = os.path.join(DATA_ROOT, "analysis_results", "preparation_accuracy")
os.makedirs(OUTPUT_DIR, exist_ok=True)

TOL_BASE = 0.1
TOL_REGION = 1.0
WORKERS = min(6, cpu_count())

REGIONS = ['36', 'F1-shoulder', 'F2-axial-wall', 'F3-buccal-cusp-reduction',
           'F4-lingual-cusp-reduction', 'F5-buccal-occlusal-surface', 'F6-lingual-occlusal-surface']
RSHORT = {'36':'36', 'F1-shoulder':'F1', 'F2-axial-wall':'F2',
          'F3-buccal-cusp-reduction':'F3', 'F4-lingual-cusp-reduction':'F4',
          'F5-buccal-occlusal-surface':'F5', 'F6-lingual-occlusal-surface':'F6'}

BASE_FOLDER = 'F0-base'
BASE_PATTERN = re.compile(r'^(G\d+-R-\d+)-A-F0-base\.stl$')

# ============================ Utilities ============================
def _load_mesh(folder, fname):
    p = os.path.join(STL_ROOT, folder, fname)
    return trimesh.load(p) if os.path.exists(p) else None

def _signed_dist(verts, mesh):
    closest, dist, tid = trimesh.proximity.closest_point(mesh, verts)
    n = mesh.face_normals[tid]
    dot = np.einsum('ij,ij->i', verts - closest, n)
    return np.sign(dot) * dist

def _stats(signed, thresh):
    valid = np.abs(signed) <= thresh
    sv = signed[valid]
    nv = int(valid.sum())
    if nv == 0:
        return {'n': 0, 'mean': 0., 'std': 0., 'posr': 0., 'pos_mean': 0., 'p75': 0.}
    pos = sv[sv > 0]
    pos_mean = float(np.mean(pos)) if len(pos) > 0 else 0.0
    p75 = float(np.percentile(sv, 75))
    return {
        'n': nv,
        'mean': float(np.mean(sv)),
        'std': float(np.std(sv, ddof=1)),
        'posr': float(len(pos) / nv),
        'pos_mean': pos_mean,
        'p75': p75
    }

# ============================ Workers ============================
def _process_psr(sid, base_file):
    base_mesh = _load_mesh(BASE_FOLDER, base_file)
    if base_mesh is None:
        return None
    ip = trimesh.load(REF_IP)
    sd = _signed_dist(base_mesh.vertices, ip)
    s = _stats(sd, TOL_BASE)
    return (sid, s['mean'], s['std'])

def _process_region(sid, pm, ps):
    recs = []
    for reg in REGIONS:
        ref = _load_mesh(reg, f'IP-{reg}.stl')
        tar = _load_mesh(reg, f'{sid}-A-{reg}.stl')
        if ref is None or tar is None:
            continue
        sd = _signed_dist(tar.vertices, ref)
        corr = sd - pm
        s = _stats(corr, TOL_REGION)
        obs_s = _stats(sd, TOL_REGION)
        recs.append({
            'SampleID': sid,
            'Group': re.match(r'(G\d+)', sid).group(1),
            'Region': reg,
            'RegionShort': RSHORT[reg],
            'n_valid': s['n'],
            'μ_obs (mm)': obs_s['mean'],
            'σ_obs (mm)': obs_s['std'],
            'μ_prep (mm)': s['mean'],
            'σ_prep (mm)': s['std'],
            'PSR μ (mm)': pm,
            'PSR σ (mm)': ps,
            'R_pos (%)': s['posr'] * 100,
            'μ_pos (μm)': s['pos_mean'] * 1000,
            'P75 (μm)': s['p75'] * 1000
        })
    return recs

# =============================== Main ===============================
def main():
    print("=" * 60)
    print("  Preparation Accuracy – Full Computation")
    print("  Output:", OUTPUT_DIR)
    print("=" * 60)
    t0 = time.time()

    # 1. Collect sample IDs from base files
    base_path = os.path.join(STL_ROOT, BASE_FOLDER)
    base_files = {}
    for f in os.listdir(base_path):
        m = BASE_PATTERN.match(f)
        if m:
            sid = m.group(1)
            base_files[sid] = f
    sample_ids = sorted(base_files.keys(),
                        key=lambda s: (int(re.search(r'G(\d+)', s).group(1)),
                                       int(re.search(r'R-(\d+)', s).group(1))))
    print(f"[1] Found {len(sample_ids)} R‑group samples.")

    # 2. PSR computation
    print(f"[2] Computing PSR errors ({WORKERS} workers)...")
    psr_dict = {}
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        fs = {pool.submit(_process_psr, sid, base_files[sid]): sid for sid in sample_ids}
        for f in tqdm(as_completed(fs), total=len(fs), desc="PSR"):
            res = f.result()
            if res is not None:
                psr_dict[res[0]] = {'mean': res[1], 'std': res[2]}
    print(f"    Completed {len(psr_dict)} samples.")

    pd.DataFrame([{'Sample': k, 'PSR μ (mm)': v['mean'], 'PSR σ (mm)': v['std']}
                  for k, v in psr_dict.items()]).to_csv(
        os.path.join(OUTPUT_DIR, 'PSR_summary.csv'), index=False)

    # 3. Region analysis
    print(f"[3] Processing regions ({WORKERS} workers)...")
    all_recs = []
    tasks = [(sid, psr_dict[sid]['mean'], psr_dict[sid]['std'])
             for sid in sample_ids if sid in psr_dict]
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        fs = {pool.submit(_process_region, sid, pm, ps): sid for sid, pm, ps in tasks}
        for f in tqdm(as_completed(fs), total=len(fs), desc="Regions"):
            recs = f.result()
            if recs:
                all_recs.extend(recs)

    if not all_recs:
        print("ERROR: No results."); return

    df = pd.DataFrame(all_recs).sort_values(['SampleID', 'Region']).reset_index(drop=True)
    df.to_csv(os.path.join(OUTPUT_DIR, 'region_results.csv'), index=False)
    print(f"    Saved {len(df)} rows.")

    # 4. Summary
    summary_rows = []
    for reg in REGIONS:
        sub = df[df['Region'] == reg]
        if sub.empty:
            continue
        v = sub['μ_prep (mm)'].values
        summary_rows.append({
            'Region': reg,
            'RegionShort': RSHORT[reg],
            'N': len(v),
            'μ_prep (mm)': f"{np.mean(v):.4f} ± {np.std(v, ddof=1):.4f}",
            'σ_prep (mm)': f"{sub['σ_prep (mm)'].mean():.4f}",
            'R_pos (%)': f"{sub['R_pos (%)'].mean():.1f}",
            'μ_pos (μm)': f"{sub['μ_pos (μm)'].mean():.1f}",
            'P75 (μm)': f"{sub['P75 (μm)'].mean():.1f}"
        })
    df_sum = pd.DataFrame(summary_rows)
    df_sum.to_csv(os.path.join(OUTPUT_DIR, 'region_summary.csv'), index=False)
    print(df_sum.to_string(index=False))

    # 5. Consistency
    cons = [{'Region': RSHORT[reg],
             'BetweenSample_SD_of_μ_prep (mm)': df[df['Region'] == reg]['μ_prep (mm)'].std(ddof=1)}
            for reg in REGIONS if not df[df['Region'] == reg].empty]
    pd.DataFrame(cons).to_csv(os.path.join(OUTPUT_DIR, 'consistency_PSR.csv'), index=False)

    print(f"\n[4] Total time: {time.time() - t0:.1f} s")
    print("Done.")

if __name__ == '__main__':
    main()