#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File: compute_validation_metrics.py
Description:
    Compute segmentation consistency metrics (Dice, Chamfer distance,
    Hausdorff 95%, area absolute difference) for three comparisons:
      - intra_operator (O1-1 vs O1-2)
      - inter_operator (O1-1 vs O2-1)
      - manual_vs_auto   (O1-1 vs Auto)
    Parallel processing with progress bar.

Copyright 2026 Qihang He

Paper step: Appendix Section 3 - validation of the semi-automated region segmentation.
Inputs:  MANUAL_ROOT (O<operator>-<round>-<specimen>-<region>.stl) and
         AUTO_ROOT (<specimen>-<region>.stl) segmentation directories
Outputs: intra_operator_final.csv, inter_operator_final.csv, manual_vs_auto_final.csv,
         overall_comparison_final.csv in OUTPUT_DIR
Licence: MIT (see LICENSE).
"""

import os, re, glob, warnings, time
import numpy as np
import pandas as pd
import trimesh
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count

warnings.filterwarnings('ignore')

# ========== CONFIGURATION ==========
# Paths to the manual and automatic segmentation STL directories.
# Each subdirectory corresponds to a region (F0-base, 36, F1-shoulder, etc.).
MANUAL_ROOT = r"./data/manual_segmentation"
AUTO_ROOT   = r"./data/auto_segmentation"

# Output directory for comparison results (CSV files).
OUTPUT_DIR  = r"./output/validation_results"

REGIONS = [
    "F0-base", "36",
    "F1-shoulder", "F2-axial-wall",
    "F3-buccal-cusp-reduction", "F4-lingual-cusp-reduction",
    "F5-buccal-occlusal-surface", "F6-lingual-occlusal-surface"
]

DICE_THRESHOLD = 0.05   # mm
N_SAMPLE_POINTS = 5000
WORKERS = min(6, cpu_count())
# ====================================

MANUAL_PATTERN = re.compile(
    r'^O(\d+)-(\d+)-((?:G[1-4]-R-[1-3]-A))-(' + '|'.join(REGIONS) + r')\.stl$'
)
AUTO_PATTERN = re.compile(
    r'^((?:G[1-4]-R-[1-3]-A))-(' + '|'.join(REGIONS) + r')\.stl$'
)

def build_manual_index(root):
    idx = {}
    for reg in REGIONS:
        folder = os.path.join(root, reg)
        if not os.path.isdir(folder): continue
        for f in glob.glob(os.path.join(folder, "*.stl")):
            basename = os.path.basename(f)
            m = MANUAL_PATTERN.match(basename)
            if m:
                op, rep, mid, reg_name = int(m.group(1)), int(m.group(2)), m.group(3), m.group(4)
                idx[(op, rep, mid, reg_name)] = f
    return idx

def build_auto_index(root):
    idx = {}
    for reg in REGIONS:
        folder = os.path.join(root, reg)
        if not os.path.isdir(folder): continue
        for f in glob.glob(os.path.join(folder, "*.stl")):
            basename = os.path.basename(f)
            m = AUTO_PATTERN.match(basename)
            if m:
                mid, reg_name = m.group(1), m.group(2)
                idx[(mid, reg_name)] = f
    return idx

def load_mesh(path):
    try:
        mesh = trimesh.load(path)
        if not isinstance(mesh, trimesh.Trimesh):
            mesh = mesh.to_mesh() if hasattr(mesh, 'to_mesh') else None
        if mesh is None: return None
        nondeg = mesh.nondegenerate_faces()
        if not np.all(nondeg):
            mesh.update_faces(nondeg)
            mesh.remove_unreferenced_vertices()
        return mesh
    except Exception as e:
        warnings.warn(f"Failed to load {path}: {e}")
        return None

def compute_surface_distances(mesh_a, mesh_b, n_samples=N_SAMPLE_POINTS):
    n_a = min(n_samples, len(mesh_a.vertices))
    n_b = min(n_samples, len(mesh_b.vertices))
    pts_a = mesh_a.sample(n_a) if n_a > 0 else mesh_a.vertices.copy()
    pts_b = mesh_b.sample(n_b) if n_b > 0 else mesh_b.vertices.copy()
    if pts_a.shape[0] == 0 or pts_b.shape[0] == 0:
        return np.nan, np.nan
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        _, dist_a_to_b, _ = trimesh.proximity.closest_point(mesh_b, pts_a)
        _, dist_b_to_a, _ = trimesh.proximity.closest_point(mesh_a, pts_b)
    dist_a_to_b = np.nan_to_num(dist_a_to_b, nan=1e6, posinf=1e6, neginf=1e6)
    dist_b_to_a = np.nan_to_num(dist_b_to_a, nan=1e6, posinf=1e6, neginf=1e6)
    all_dists = np.concatenate([dist_a_to_b, dist_b_to_a])
    mean_dist = float(np.mean(all_dists))
    hausdorff95 = float(np.percentile(all_dists, 95))
    return mean_dist, hausdorff95

def compute_dice(mesh_a, mesh_b, threshold=DICE_THRESHOLD, n_samples=N_SAMPLE_POINTS):
    n_a = min(n_samples, len(mesh_a.vertices))
    n_b = min(n_samples, len(mesh_b.vertices))
    pts_a = mesh_a.sample(n_a) if n_a > 0 else mesh_a.vertices.copy()
    pts_b = mesh_b.sample(n_b) if n_b > 0 else mesh_b.vertices.copy()
    if pts_a.shape[0] == 0 or pts_b.shape[0] == 0:
        return np.nan
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        _, dist_a_to_b, _ = trimesh.proximity.closest_point(mesh_b, pts_a)
        _, dist_b_to_a, _ = trimesh.proximity.closest_point(mesh_a, pts_b)
    dist_a_to_b = np.nan_to_num(dist_a_to_b, nan=1e6, posinf=1e6, neginf=1e6)
    dist_b_to_a = np.nan_to_num(dist_b_to_a, nan=1e6, posinf=1e6, neginf=1e6)
    overlap_a = np.sum(dist_a_to_b <= threshold)
    overlap_b = np.sum(dist_b_to_a <= threshold)
    dice = (overlap_a + overlap_b) / (n_a + n_b) * 2.0
    return dice

def compute_one_pair(args):
    """args: (path1, path2, model_id, region)"""
    path1, path2, mid, reg = args
    mesh1 = load_mesh(path1)
    mesh2 = load_mesh(path2)
    if mesh1 is None or mesh2 is None:
        return None
    area1 = mesh1.area
    area2 = mesh2.area
    area_abs_diff = abs(area1 - area2)
    mean_dist, hausdorff95 = compute_surface_distances(mesh1, mesh2)
    dice = compute_dice(mesh1, mesh2)
    return {
        'model_id': mid,
        'region': reg,
        'area1': area1,
        'area2': area2,
        'area_diff': area1 - area2,
        'area_abs_diff': area_abs_diff,
        'mean_distance': mean_dist,
        'hausdorff95': hausdorff95,
        'dice': dice,
        'vertex_count1': len(mesh1.vertices),
        'vertex_count2': len(mesh2.vertices),
    }

def process_comparison_parallel(comparison_name, pairs, output_dir):
    if not pairs:
        print(f"  {comparison_name}: no pairs to process.")
        return pd.DataFrame()

    args_list = [(pa, pb, mid, reg) for mid, reg, pa, pb in pairs]
    results = []
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(compute_one_pair, args): args for args in args_list}
        for future in tqdm(as_completed(futures), total=len(futures),
                           desc=f"{comparison_name}", unit="pair"):
            res = future.result()
            if res is not None:
                results.append(res)
    df = pd.DataFrame(results)
    out_path = os.path.join(output_dir, f'{comparison_name}_final.csv')
    if not df.empty:
        df['comparison'] = comparison_name
    df.to_csv(out_path, index=False)
    print(f"  {comparison_name}: {len(df)} pairs saved -> {out_path}")
    return df

def main():
    print("=" * 60)
    print("  Validation Metrics - Parallel Computation")
    print("=" * 60)
    t0 = time.time()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    manual_idx = build_manual_index(MANUAL_ROOT)
    auto_idx = build_auto_index(AUTO_ROOT)
    print(f"Manual entries: {len(manual_idx)}")
    print(f"Auto entries:   {len(auto_idx)}")

    # Prepare pairs for each comparison
    intra_pairs, inter_pairs, auto_pairs = [], [], []
    for (op, rep, mid, reg), path1 in manual_idx.items():
        if op == 1 and rep == 1:
            # Intra operator
            key2 = (1, 2, mid, reg)
            if key2 in manual_idx:
                intra_pairs.append((mid, reg, path1, manual_idx[key2]))
            # Inter operator
            key3 = (2, 1, mid, reg)
            if key3 in manual_idx:
                inter_pairs.append((mid, reg, path1, manual_idx[key3]))
            # Manual vs Auto
            auto_key = (mid, reg)
            if auto_key in auto_idx:
                auto_pairs.append((mid, reg, path1, auto_idx[auto_key]))

    # Process in parallel for each comparison (sequential among comparisons)
    all_dfs = []
    for comp_name, pairs in [('intra_operator', intra_pairs),
                             ('inter_operator', inter_pairs),
                             ('manual_vs_auto', auto_pairs)]:
        df = process_comparison_parallel(comp_name, pairs, OUTPUT_DIR)
        if not df.empty:
            all_dfs.append(df)

    # Overall summary
    if all_dfs:
        overall = pd.concat(all_dfs, ignore_index=True)
        overall.to_csv(os.path.join(OUTPUT_DIR, 'overall_comparison_final.csv'), index=False)
        print("Overall summary saved.")
    else:
        print("No data for overall summary.")

    print(f"Total time: {time.time() - t0:.1f} s")
    print("Done.")

if __name__ == '__main__':
    main()