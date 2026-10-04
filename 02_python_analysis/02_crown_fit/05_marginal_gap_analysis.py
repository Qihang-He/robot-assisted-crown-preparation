#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Marginal Gap Analysis

Compute marginal gap from shoulder margin point clouds (A and C).
Angle‑based resampling (3600 points per contour) yields:
    μ_marginal, σ_marginal, P75, and IoU_XY.
Per‑sample detail plots are saved.

Output: CSV of results, group‑wise summary, and per‑sample detail plots.

Copyright © 2026 Qihang He
Released under the MIT licence; see LICENSE.

Paper step: marginal gap from the shoulder-margin point clouds.
Inputs:  Region_Segmentation_Results/shoulder-margin-point-cloud/*.asc (A- and C-scans)
Outputs: analysis_results/marginal_gap/marginal_gap_results.csv, group_summary.csv
         and per-specimen detail plots
Licence: MIT (see LICENSE).
"""

import os, re, warnings, time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from mpl_toolkits.mplot3d import Axes3D
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm

warnings.filterwarnings('ignore')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150

# ============================ Configuration ============================
DATA_ROOT = r"path/to/your/project/data"

STL_ROOT = os.path.join(DATA_ROOT, "Region_Segmentation_Results")
INPUT_DIR = os.path.join(STL_ROOT, "shoulder-margin-point-cloud")
OUTPUT_DIR = os.path.join(DATA_ROOT, "analysis_results", "marginal_gap")
os.makedirs(OUTPUT_DIR, exist_ok=True)

N_SAMPLES = 3600
WORKERS = min(os.cpu_count(), 8)
PATTERN = re.compile(r'^(G\d+)-R-(\d+)-(A|C)-shoulder-margin-point-cloud\.asc$')


def parse(fname):
    m = PATTERN.match(fname)
    if m: return m.group(1), 'R', int(m.group(2)), m.group(3)
    return None


def resample(pts, center, n):
    vec = pts - center
    ang = np.arctan2(vec[:,1], vec[:,0])
    idx = np.argsort(ang)
    pts_s = pts[idx]; ang_s = ang[idx]
    ang_u = np.unwrap(ang_s)
    _, uidx = np.unique(np.round(ang_u, decimals=10), return_index=True)
    ang_u = ang_u[uidx]; pts_u = pts_s[uidx]
    if len(ang_u) < 3: raise ValueError
    target = np.linspace(-np.pi, np.pi, n, endpoint=False)
    samp = np.zeros((n,3))
    for d in range(3):
        f = interp1d(ang_u, pts_u[:,d], kind='linear', fill_value='extrapolate')
        samp[:,d] = f(target)
    return samp, target


def gap_stats(pa, pc):
    d = np.linalg.norm(pa-pc, axis=1)
    if len(d)==0: return None, None
    return {'μ_marginal (mm)': float(np.mean(d)),
            'σ_marginal (mm)': float(np.std(d)),
            'P75 (mm)': float(np.percentile(d, 75))}, d


def iou_xy(pa, pc):
    try:
        from shapely.geometry import Polygon
        pa_p = Polygon(pa[:,:2]); pc_p = Polygon(pc[:,:2])
        if not pa_p.is_valid or not pc_p.is_valid: return np.nan
        inter = pa_p.intersection(pc_p).area; union = pa_p.union(pc_p).area
        return inter/union if union>0 else np.nan
    except: return np.nan


def plot_detail(dist, ang, pa, pc, name, out_dir, iou=None):
    fig = plt.figure(figsize=(15,10))
    title = f'Marginal Gap: {name}' + (f'   IoU={iou:.4f}' if iou is not None and not np.isnan(iou) else '')
    fig.suptitle(title, fontsize=14)
    ax = fig.add_subplot(2,3,1, projection='3d')
    ax.plot(pa[:,0],pa[:,1],pa[:,2],'b-',lw=1.5,label='Abutment')
    ax.plot(pc[:,0],pc[:,1],pc[:,2],'r--',lw=1.5,label='Crown'); ax.legend(); ax.set_title('3D Overlay')
    ax = fig.add_subplot(2,3,2)
    ax.plot(pa[:,0],pa[:,1],'b-',lw=1.5,label='Abutment')
    ax.plot(pc[:,0],pc[:,1],'r--',lw=1.5,label='Crown'); ax.set_aspect('equal'); ax.set_title('XY Projection'); ax.legend()
    ax = fig.add_subplot(2,3,3)
    ax.plot(ang, dist, 'g-', lw=1.5)
    ax.axhline(np.mean(dist), color='gray', ls='--', label=f'Mean={np.mean(dist):.4f}')
    ax.legend(); ax.set_title('Gap vs Angle')
    ax = fig.add_subplot(2,3,4)
    sc = ax.scatter(pa[:,0], pa[:,1], c=dist, cmap='jet', s=15); ax.set_aspect('equal'); ax.set_title('Gap Heatmap (Abutment)')
    plt.colorbar(sc, ax=ax, label='Gap (mm)')
    ax = fig.add_subplot(2,3,5)
    sd = np.sort(dist); cum = np.arange(1,len(sd)+1)/len(sd)
    ax.plot(sd, cum, 'b-', lw=1.5)
    p75 = np.percentile(dist,75); ax.axvline(p75, color='purple', ls=':', label=f'P75={p75:.4f}')
    ax.set_title('CDF'); ax.legend()
    ax = fig.add_subplot(2,3,6, projection='polar')
    ax.plot(ang, dist, 'b-', lw=1.5); ax.set_title('Polar Gap')
    plt.tight_layout()
    fig.savefig(os.path.join(out_dir, f'{name}_detail.png'), dpi=200); plt.close(fig)
    # 3D strip
    fig = plt.figure(figsize=(8,5))
    ax = fig.add_subplot(111, projection='3d')
    max_d = max(dist) if len(dist)>0 else 1
    for i in range(len(pa)-1):
        ax.plot(pa[i:i+2,0], pa[i:i+2,1], pa[i:i+2,2], color=plt.cm.jet(dist[i]/max_d), lw=2)
    norm = plt.Normalize(vmin=0, vmax=max_d)
    sm = plt.cm.ScalarMappable(norm=norm, cmap='jet'); sm.set_array([])
    plt.colorbar(sm, ax=ax, label='Gap (mm)')
    ax.set_title(f'3D Colour Strip: {name}'); ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
    fig.tight_layout(); fig.savefig(os.path.join(out_dir, f'{name}_3Dstrip.png'), dpi=200); plt.close(fig)


def process_one(key, files):
    group, _, num = key
    try:
        pa = np.loadtxt(files['A'], delimiter=' ', dtype=np.float64)
        pc = np.loadtxt(files['C'], delimiter=' ', dtype=np.float64)
    except: return None
    if len(pa)<4 or len(pc)<4: return None
    center = (np.mean(pa,axis=0) + np.mean(pc,axis=0))/2
    try:
        ra, ang = resample(pa, center, N_SAMPLES)
        rc, _ = resample(pc, center, N_SAMPLES)
    except: return None
    s, d = gap_stats(ra, rc)
    if s is None: return None
    iou = iou_xy(ra, rc)
    name = f"{group}-R-{num}"
    sample_dir = os.path.join(OUTPUT_DIR, 'per_sample_plots', f"{group}_R_{num}")
    os.makedirs(sample_dir, exist_ok=True)
    plot_detail(d, ang, ra, rc, name, sample_dir, iou)
    return {'Group': group, 'Number': num,
            'μ_marginal (mm)': s['μ_marginal (mm)'],
            'σ_marginal (mm)': s['σ_marginal (mm)'],
            'P75 (mm)': s['P75 (mm)'],
            'IoU_XY': iou}


def main():
    print("="*60); print("  Marginal Gap – Parallel"); print("="*60); t0=time.time()
    files = os.listdir(INPUT_DIR)
    finfo = {}
    for f in files:
        if not f.endswith('.asc'): continue
        p = parse(f)
        if p is None: continue
        g, _, n, t = p; key = (g,_,n)
        finfo.setdefault(key, {})[t] = os.path.join(INPUT_DIR, f)
    keys = [k for k,v in finfo.items() if 'A' in v and 'C' in v]
    print(f"[1] {len(keys)} samples.")
    res = []
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        fs = {pool.submit(process_one, k, finfo[k]): k for k in keys}
        for f in tqdm(as_completed(fs), total=len(fs), desc="Samples"):
            r = f.result()
            if r: res.append(r)
    if not res: print("No results."); return
    df = pd.DataFrame(res).sort_values(['Group','Number']).reset_index(drop=True)
    df.to_csv(os.path.join(OUTPUT_DIR, 'marginal_gap_results.csv'), index=False, float_format='%.6f')
    summary = df.groupby('Group').agg(N=('μ_marginal (mm)','count'),
                                      Mean=('μ_marginal (mm)','mean'),
                                      SD=('μ_marginal (mm)','std'),
                                      Median=('μ_marginal (mm)','median'),
                                      P75_mean=('P75 (mm)','mean'),
                                      Mean_IoU=('IoU_XY','mean')).round(4)
    summary.to_csv(os.path.join(OUTPUT_DIR, 'group_summary.csv'))
    print(summary)
    print(f"Time: {time.time()-t0:.1f}s")


if __name__ == '__main__':
    main()