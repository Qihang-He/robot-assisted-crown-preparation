#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Region Segmentation Visualization

Plot a 2×2 grid of region‑segmented models:
(a) IP 3D view (elev=25, azim=-60)
(b) IP top view (elev=90, azim=270)
(c) G1-R-1-C 3D view (elev=25, azim=60)
(d) G1-R-1-C bottom view (elev=-90, azim=90)

Regions are colored with a soft palette; F0 is semi‑transparent.
All axes are hidden. A shared legend is placed at the bottom.
Output: PNG (300 dpi) and PDF.

Copyright © 2026 Qihang He
Released under the MIT licence; see LICENSE.

Paper step: region definition figure (Figure 1 panels).
Inputs:  Region_Segmentation_Results/{36,F0-outer-surface,F1-shoulder ... F6-lingual-occlusal-surface}/
Outputs: analysis_results/overall_visual/ region-segmentation views (300 dpi PNG and PDF)
Licence: MIT (see LICENSE).
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import trimesh

# ========================= Configuration =========================
DATA_ROOT = r"path/to/your/project/data"

SEG_RESULT_DIR = os.path.join(DATA_ROOT, "Region_Segmentation_Results")
OUTPUT_DIR     = os.path.join(DATA_ROOT, "analysis_results", "overall_visual")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Color scheme (soft academic palette, base semi-transparent)
REGIONS = [
    ("F0", "#C0C0C0", "F0",           0.25),
    ("F1", "#D05A6E", "F1",           0.85),
    ("F2", "#6A8DBA", "F2",           0.85),
    ("F3", "#78B86E", "F3",           0.85),
    ("F4", "#E6B800", "F4",           0.85),
    ("F5", "#E07B39", "F5",           0.85),
    ("F6", "#A074C4", "F6",           0.85),
]

IP_SUFFIX_MAP = {
    "F0": "base", "F1": "shoulder", "F2": "axial-wall",
    "F3": "buccal-cusp-reduction", "F4": "lingual-cusp-reduction",
    "F5": "buccal-occlusal-surface", "F6": "lingual-occlusal-surface"
}

CROWN_SUFFIX_MAP = {
    "F0": "outer-surface", "F1": "shoulder", "F2": "axial-wall",
    "F3": "buccal-cusp-reduction", "F4": "lingual-cusp-reduction",
    "F5": "buccal-occlusal-surface", "F6": "lingual-occlusal-surface"
}


def load_stl_region(model_name, region_abbr, region_suffix):
    """Load a region STL file given model name and region abbreviation."""
    folder_name = f"{region_abbr}-{region_suffix}"
    file_name   = f"{model_name}-{folder_name}.stl"
    file_path   = os.path.join(SEG_RESULT_DIR, folder_name, file_name)
    if not os.path.exists(file_path):
        print(f"  [WARN] File not found: {file_path}")
        return None
    return trimesh.load(file_path)


def build_collection(mesh, color, alpha):
    """Create a Poly3DCollection from a mesh with specified color and alpha."""
    if mesh is None:
        return None
    faces = mesh.faces
    verts = mesh.vertices
    poly = Poly3DCollection(verts[faces],
                            facecolors=color,
                            edgecolors=None,
                            alpha=alpha,
                            antialiased=True)
    return poly


def plot_subplot(ax, model_name, suffix_map, view_elev, view_azim, scale=0.75):
    """
    Plot a single subplot with all regions.
    Returns the list of legend handles for shared legend.
    """
    legend_elements_returned = []

    for reg_abbr, color, label, alpha in REGIONS:
        suffix = suffix_map[reg_abbr]
        mesh = load_stl_region(model_name, reg_abbr, suffix)
        if mesh is None:
            continue
        poly = build_collection(mesh, color, alpha)
        if poly is not None:
            ax.add_collection3d(poly)
            if not any(le.get_label() == label for le in legend_elements_returned):
                legend_elements_returned.append(
                    plt.Rectangle((0,0),1,1, fc=color, ec='none',
                                  alpha=alpha, label=label)
                )

    # Set axes limits based on all loaded meshes
    all_pts = []
    for reg_abbr, _, _, _ in REGIONS:
        suffix = suffix_map[reg_abbr]
        mesh = load_stl_region(model_name, reg_abbr, suffix)
        if mesh is not None:
            all_pts.append(mesh.vertices)
    if all_pts:
        all_pts = np.vstack(all_pts)
        x_min, x_max = np.min(all_pts[:,0]), np.max(all_pts[:,0])
        y_min, y_max = np.min(all_pts[:,1]), np.max(all_pts[:,1])
        z_min, z_max = np.min(all_pts[:,2]), np.max(all_pts[:,2])
        max_range = max(x_max-x_min, y_max-y_min, z_max-z_min) / 2
        x_mid = (x_min + x_max) / 2
        y_mid = (y_min + y_max) / 2
        z_mid = (z_min + z_max) / 2
        ax.set_xlim(x_mid - max_range * scale, x_mid + max_range * scale)
        ax.set_ylim(y_mid - max_range * scale, y_mid + max_range * scale)
        ax.set_zlim(z_mid - max_range * scale, z_mid + max_range * scale)

    ax.view_init(elev=view_elev, azim=view_azim)
    ax.set_axis_off()
    return legend_elements_returned


def main():
    # Create 2×2 grid
    fig, axes = plt.subplots(2, 2, figsize=(14, 12),
                             subplot_kw={'projection': '3d'})

    all_legend_handles = []

    # Subplot a: IP 3D
    handles = plot_subplot(axes[0,0], "IP", IP_SUFFIX_MAP, 25, -60, scale=0.65)
    if not all_legend_handles:
        all_legend_handles = handles

    # Subplot b: IP top view
    plot_subplot(axes[0,1], "IP", IP_SUFFIX_MAP, 90, 270, scale=0.65)

    # Subplot c: G1-R-1-C 3D
    plot_subplot(axes[1,0], "G1-R-1-C", CROWN_SUFFIX_MAP, 25, 60, scale=0.8)

    # Subplot d: G1-R-1-C bottom view
    plot_subplot(axes[1,1], "G1-R-1-C", CROWN_SUFFIX_MAP, -90, 90, scale=0.8)

    # Labels a, b, c, d
    for idx, ax in enumerate(axes.ravel()):
        ax.text2D(0.05, 0.95, chr(ord('a') + idx),
                  transform=ax.transAxes,
                  fontsize=14, fontweight='bold',
                  va='top', ha='left')

    # Shared legend at bottom
    fig.legend(handles=all_legend_handles, loc='lower center',
               ncol=7, fontsize=10, framealpha=0.9,
               bbox_to_anchor=(0.5, -0.02))

    plt.subplots_adjust(left=0.05, right=0.95, bottom=0.1, top=0.92,
                        wspace=0.05, hspace=0.1)

    # Save PNG and PDF
    png_path = os.path.join(OUTPUT_DIR, "region_segmentation_2x2.png")
    pdf_path = os.path.join(OUTPUT_DIR, "region_segmentation_2x2.pdf")
    fig.savefig(png_path, dpi=300, bbox_inches='tight')
    fig.savefig(pdf_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {png_path}")
    print(f"Saved: {pdf_path}")


if __name__ == "__main__":
    main()