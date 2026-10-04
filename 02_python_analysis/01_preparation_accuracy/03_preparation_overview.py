#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Preparation Overview

4×8 batch comparison of robot‑prepared abutments (Gi-R-j-A-36) against
the ideal preparation (IP-36). Each subplot shows a top view (elev=90°)
of the signed distance map using jet colormap (40 levels, −0.2 to 0.2 mm).
Global coordinate limits are unified across all samples.

Output: PNG (300 dpi) and PDF.

Copyright © 2026 Qihang He
Released under the MIT licence; see LICENSE.

Paper step: preparation accuracy overview (Figure 2 distance maps).
Inputs:  Region_Segmentation_Results/36/*.stl (A-scans) and Region_Segmentation_Results/36/IP-36.stl
Outputs: analysis_results/overall_visual/All_G_R_A36_vs_IP.png (300 dpi) and .pdf
Licence: MIT (see LICENSE).
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm
from matplotlib.cm import ScalarMappable
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import trimesh

# ============================ Configuration ============================
DATA_ROOT = r"path/to/your/project/data"

STL_DIR = os.path.join(DATA_ROOT, "Region_Segmentation_Results", "36")
REF_FILE = os.path.join(STL_DIR, "IP-36.stl")
OUTPUT_DIR = os.path.join(DATA_ROOT, "analysis_results", "overall_visual")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Colormap parameters
VMIN, VMAX = -0.2, 0.2
N_LEVELS = 40
cmap = plt.cm.jet
boundaries = np.linspace(VMIN, VMAX, N_LEVELS + 1)
norm = BoundaryNorm(boundaries, cmap.N, clip=False)


def compute_face_signed_distances(mesh_ref, mesh_sample):
    """Signed distance per face using vertex average method."""
    closest, dist, tri_id = trimesh.proximity.closest_point(
        mesh_ref, mesh_sample.vertices)
    normals = mesh_ref.face_normals[tri_id]
    vec = mesh_sample.vertices - closest
    dot = np.einsum('ij,ij->i', vec, normals)
    sign = np.where(dot >= 0, 1.0, -1.0)
    vert_signed = sign * dist
    faces = mesh_sample.faces
    face_signed = np.mean(vert_signed[faces], axis=1)
    return face_signed


def main():
    print("Loading reference mesh (IP-36)...")
    ref = trimesh.load(REF_FILE)
    if isinstance(ref, trimesh.Scene):
        ref = list(ref.geometry.values())[0]

    # Enumerate all samples (G1-R-1-A-36 to G4-R-8-A-36)
    groups = [f"G{i}" for i in range(1, 5)]
    sample_paths = []
    for ri, g in enumerate(groups):
        for ci in range(1, 9):
            fname = f"{g}-R-{ci}-A-36.stl"
            fpath = os.path.join(STL_DIR, fname)
            if not os.path.exists(fpath):
                print(f"Warning: {fpath} not found, skip.")
                continue
            sample_paths.append((ri, ci - 1, fpath))

    # Pre-scan all vertices for global limits
    print("Scanning all samples for global coordinate limits...")
    all_vert_list = [ref.vertices]
    for _, _, fpath in sample_paths:
        mesh = trimesh.load(fpath)
        if isinstance(mesh, trimesh.Scene):
            mesh = list(mesh.geometry.values())[0]
        all_vert_list.append(mesh.vertices)
    all_verts = np.vstack(all_vert_list)

    global_xlim = [all_verts[:, 0].min(), all_verts[:, 0].max()]
    global_ylim = [all_verts[:, 1].min(), all_verts[:, 1].max()]
    global_zlim = [all_verts[:, 2].min(), all_verts[:, 2].max()]

    # Natural aspect ratio for top view
    x_range = global_xlim[1] - global_xlim[0]
    y_range = global_ylim[1] - global_ylim[0]
    z_range = global_zlim[1] - global_zlim[0]
    aspect_xy = [x_range, y_range, z_range * 0.3]

    # Figure sizing
    nrows, ncols = 4, 8
    fig, axes = plt.subplots(nrows, ncols, figsize=(28, 14),
                             subplot_kw={'projection': '3d'})
    fig.subplots_adjust(left=0.06, right=0.88, bottom=0.04, top=0.94,
                        wspace=0.03, hspace=0.03)

    # Render each sample
    for ri, ci, fpath in sample_paths:
        print(f"Processing {os.path.basename(fpath)} ...")
        sample = trimesh.load(fpath)
        if isinstance(sample, trimesh.Scene):
            sample = list(sample.geometry.values())[0]

        d_face = compute_face_signed_distances(ref, sample)
        ax = axes[ri, ci]

        verts = sample.vertices
        faces = sample.faces
        face_verts = verts[faces]
        coll = Poly3DCollection(face_verts,
                                facecolors=cmap(norm(d_face)),
                                edgecolors='none',
                                alpha=0.95,
                                rasterized=True)
        ax.add_collection3d(coll)

        # Unified global limits
        ax.set_xlim(global_xlim)
        ax.set_ylim(global_ylim)
        ax.set_zlim(global_zlim)

        # Top view with natural XY proportion
        ax.view_init(elev=90, azim=-90)
        ax.set_box_aspect(aspect_xy)

        # Publication style: no grid, no ticks
        ax.grid(False)
        for axis in [ax.xaxis, ax.yaxis, ax.zaxis]:
            axis.set_ticklabels([])
            axis.set_ticks([])
            axis.line.set_color('none')
            axis.pane.fill = False
            axis.pane.set_edgecolor('white')
        ax.set_facecolor('white')

    # Turn off any unused subplots
    for idx in range(len(sample_paths), nrows * ncols):
        r = idx // ncols
        c = idx % ncols
        axes[r, c].axis('off')

    # Row labels (left side): G1-R to G4-R
    row_labels = [f"G{i}-R" for i in range(1, 5)]
    for ri in range(nrows):
        ax = axes[ri, 0]
        pos = ax.get_position()
        x = pos.x0 - 0.02
        y = pos.y0 + pos.height / 2
        fig.text(x, y, row_labels[ri], va='center', ha='right',
                 fontsize=20, fontweight='bold')

    # Column labels (top): 1 to 8
    col_labels = [str(i) for i in range(1, 9)]
    for ci in range(ncols):
        ax = axes[0, ci]
        pos = ax.get_position()
        x = pos.x0 + pos.width / 2
        y = pos.y1 + 0.02
        fig.text(x, y, col_labels[ci], va='bottom', ha='center',
                 fontsize=20, fontweight='bold')

    # Shared rectangular colorbar
    cbar_ax = fig.add_axes([0.90, 0.15, 0.015, 0.7])
    sm = ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])
    cbar = fig.colorbar(sm, cax=cbar_ax,
                        ticks=np.linspace(VMIN, VMAX, 11),
                        extend='neither')
    cbar.set_label('Signed Distance (mm)', fontsize=20)
    cbar.ax.tick_params(labelsize=20, length=5, width=1.0)

    # Save
    out_path = os.path.join(OUTPUT_DIR, 'All_G_R_A36_vs_IP.png')
    fig.savefig(out_path, dpi=300, bbox_inches='tight')
    fig.savefig(os.path.join(OUTPUT_DIR, 'All_G_R_A36_vs_IP.pdf'), dpi=300, bbox_inches='tight')
    print(f"Saved to {out_path}")
    plt.close(fig)


if __name__ == '__main__':
    main()