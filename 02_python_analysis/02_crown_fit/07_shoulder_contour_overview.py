#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shoulder Contour Overview

4×8 overview of shoulder margin gap on abutment contours.
Each subplot shows a scatter heatmap of the gap (RdYlGn_r, 0–0.2 mm, 20 levels)
on the abutment shoulder contour (XY projection).
Global XY limits are unified.

Output: PNG (300 dpi) and PDF.

Copyright © 2026 Qihang He
Released under the MIT licence; see LICENSE.

Paper step: marginal gap overview along the finish line (Figure 3 contour maps).
Inputs:  Region_Segmentation_Results/shoulder-margin-point-cloud/*.asc (paired A- and C-scans)
Outputs: analysis_results/overall_visual/All_Shoulder_Contour_Gap_4x8.png (300 dpi) and .pdf
Licence: MIT (see LICENSE).
"""

import os, warnings
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from matplotlib.colors import BoundaryNorm
from matplotlib.cm import ScalarMappable

warnings.filterwarnings('ignore')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150

# ============================ Configuration ============================
DATA_ROOT = r"path/to/your/project/data"

POINT_CLOUD_DIR = os.path.join(DATA_ROOT, "Region_Segmentation_Results",
                               "shoulder-margin-point-cloud")
OUTPUT_DIR = os.path.join(DATA_ROOT, "analysis_results", "overall_visual")
os.makedirs(OUTPUT_DIR, exist_ok=True)

N_SAMPLES = 3600            # angular resolution (0.1°)
GROUPS = ['G1', 'G2', 'G3', 'G4']
N_NUMBERS = 8

# Colormap config
VMIN, VMAX = 0.0, 0.2      # Gap range in mm
N_LEVELS = 20
CMAP_NAME = 'RdYlGn_r'     # Green → Yellow → Red (no blue)
boundaries = np.linspace(VMIN, VMAX, N_LEVELS + 1)
cmap = plt.cm.get_cmap(CMAP_NAME)
norm = BoundaryNorm(boundaries, cmap.N, clip=False)


def angle_sort_and_resample(pts, center, n):
    """Sort points by angle and resample to n uniform points."""
    vec = pts - center
    angles = np.arctan2(vec[:, 1], vec[:, 0])
    sort_idx = np.argsort(angles)
    pts_sorted = pts[sort_idx]
    angles_sorted = angles[sort_idx]
    angles_unwrap = np.unwrap(angles_sorted)

    _, unique_idx = np.unique(np.round(angles_unwrap, decimals=10), return_index=True)
    angles_uniq = angles_unwrap[unique_idx]
    pts_uniq = pts_sorted[unique_idx]

    if len(angles_uniq) < 3:
        raise ValueError("Too few unique angles.")

    target = np.linspace(-np.pi, np.pi, n, endpoint=False)
    sampled = np.zeros((n, 3))
    for d in range(3):
        f = interp1d(angles_uniq, pts_uniq[:, d],
                     kind='linear', fill_value='extrapolate')
        sampled[:, d] = f(target)
    return sampled, target


def process_sample(group, num):
    """Load A and C point clouds, resample, compute gap."""
    fname_a = f"{group}-R-{num}-A-shoulder-margin-point-cloud.asc"
    fname_c = f"{group}-R-{num}-C-shoulder-margin-point-cloud.asc"
    path_a = os.path.join(POINT_CLOUD_DIR, fname_a)
    path_c = os.path.join(POINT_CLOUD_DIR, fname_c)

    if not (os.path.exists(path_a) and os.path.exists(path_c)):
        return None

    pts_a = np.loadtxt(path_a, delimiter=' ', dtype=np.float64)
    pts_c = np.loadtxt(path_c, delimiter=' ', dtype=np.float64)

    if len(pts_a) < 4 or len(pts_c) < 4:
        return None

    center = (np.mean(pts_a, axis=0) + np.mean(pts_c, axis=0)) / 2
    ra, _ = angle_sort_and_resample(pts_a, center, N_SAMPLES)
    rc, _ = angle_sort_and_resample(pts_c, center, N_SAMPLES)
    dist = np.linalg.norm(ra - rc, axis=1)

    return ra[:, :2], dist


def main():
    print("=" * 60)
    print("  4×8 Shoulder Contour Gap Heatmap (Green-Yellow-Red)")
    print("=" * 60)

    # Step 1: Process all samples
    print("[1] Processing all 32 samples...")
    all_data = {}
    for group in GROUPS:
        for num in range(1, N_NUMBERS + 1):
            result = process_sample(group, num)
            if result is not None:
                all_data[(group, num)] = result

    if not all_data:
        print("ERROR: No valid samples found.")
        return

    # Step 2: Determine global XY limits
    print("[2] Determining global XY limits...")
    all_xy = np.vstack([data[0] for data in all_data.values()])
    x_min, x_max = all_xy[:, 0].min(), all_xy[:, 0].max()
    y_min, y_max = all_xy[:, 1].min(), all_xy[:, 1].max()
    x_margin = (x_max - x_min) * 0.08
    y_margin = (y_max - y_min) * 0.08
    x_lim = (x_min - x_margin, x_max + x_margin)
    y_lim = (y_min - y_margin, y_max + y_margin)
    print(f"     X: {x_lim[0]:.2f} ~ {x_lim[1]:.2f}")
    print(f"     Y: {y_lim[0]:.2f} ~ {y_lim[1]:.2f}")

    # Step 3: Create figure
    print("[3] Rendering 4×8 figure...")
    fig, axes = plt.subplots(4, 8, figsize=(28, 14))
    fig.subplots_adjust(left=0.04, right=0.92, bottom=0.02, top=0.96,
                        wspace=0.02, hspace=0.02)

    for row, group in enumerate(GROUPS):
        for col in range(N_NUMBERS):
            num = col + 1
            ax = axes[row, col]

            if (group, num) in all_data:
                xy, gap = all_data[(group, num)]

                # Scatter heatmap with thickened markers
                ax.scatter(xy[:, 0], xy[:, 1], c=gap, cmap=cmap,
                           norm=norm, s=25, edgecolors='none',
                           alpha=1.0, rasterized=True)

                ax.set_xlim(x_lim)
                ax.set_ylim(y_lim)
                ax.set_aspect('equal')

            ax.axis('off')

    # Step 4: Row labels
    for row, group in enumerate(GROUPS):
        ax = axes[row, 0]
        ax.text(-0.06, 0.5, f'{group}-R', transform=ax.transAxes,
                fontsize=20, fontweight='bold', va='center', ha='right',
                color='black')

    # Step 5: Column labels
    for col in range(N_NUMBERS):
        ax = axes[0, col]
        ax.text(0.5, 1.06, str(col + 1), transform=ax.transAxes,
                fontsize=20, fontweight='bold', va='bottom', ha='center',
                color='black')

    # Step 6: Rectangular colorbar
    cbar_ax = fig.add_axes([0.93, 0.15, 0.015, 0.7])
    sm = ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])
    ticks = np.linspace(VMIN, VMAX, 11)
    cbar = fig.colorbar(sm, cax=cbar_ax, ticks=ticks, extend='neither')
    cbar.set_label('Gap (mm)', fontsize=20)
    cbar.ax.tick_params(labelsize=20)

    # Step 7: Save
    out_path = os.path.join(OUTPUT_DIR, 'All_Shoulder_Contour_Gap_4x8.png')
    fig.savefig(out_path, dpi=300, bbox_inches='tight')
    fig.savefig(os.path.join(OUTPUT_DIR, 'All_Shoulder_Contour_Gap_4x8.pdf'), dpi=300, bbox_inches='tight')
    print(f"[4] Saved to {out_path}")
    plt.close(fig)
    print("Done.")


if __name__ == '__main__':
    main()