#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File: export_results_to_stl.py
Description:
    Export all meshes organized in groups to STL files.
    Incremental mode: skip existing files if OVERWRITE_EXISTING=0.

Copyright 2026 Qihang He

Paper step: utility for Steps 1-3 (exports the segmented meshes to STL).
Inputs:  all groups present in the Geomagic Wrap scene
Outputs: one STL per mesh under BASE_DIR/<group name>/, e.g.
         stl_export/F1-shoulder/G1-R-1-A-F1-shoulder.stl
Environment: Geomagic Wrap 2021 or later with its bundled Python.
Licence: MIT (see LICENSE).
"""

from __future__ import annotations
import os
import sys
import geomagic.app.v3
from geomagic.app.v3.imports import *

# --- Path configuration ---
# Root directory where STL files will be saved, organized by group name.
# Adjust this to match your project environment.
BASE_DIR = r"./output/stl_export"

OVERWRITE_EXISTING = 1
SAVEAS_ARGS = (3, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, -1, 0, 1, 0)

def main():
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)
    all_models = geoapp.getModels()
    groups = [m for m in all_models if hasattr(m, 'isGroup') and m.isGroup]
    if not groups:
        print("No groups found in scene.")
        sys.exit(0)
    total_exported = 0
    total_skipped = 0
    for group in groups:
        gname = group.name.strip()
        try:
            children = group.groupModels
        except:
            children = []
        meshes = [c for c in children if c.type == Model.Mesh]
        if not meshes:
            continue
        group_dir = os.path.join(BASE_DIR, gname)
        if not os.path.exists(group_dir):
            os.makedirs(group_dir)
        print("\nGroup: {} ({} meshes)".format(gname, len(meshes)))
        for mesh in meshes:
            mname = mesh.name.strip()
            if not mname:
                mname = "unnamed"
            filepath = os.path.join(group_dir, mname + ".stl")
            if os.path.isfile(filepath) and not OVERWRITE_EXISTING:
                print("  [Skip] {}".format(filepath))
                total_skipped += 1
                continue
            try:
                geoapp.setActiveModel(mesh)
                geo.hide_inactive_objects()
                geo.saveas(filepath, *SAVEAS_ARGS)
                if os.path.getsize(filepath) > 0:
                    print("  [Export] {}".format(filepath))
                    total_exported += 1
                else:
                    print("  [Warning] Empty file: {}".format(filepath))
            except Exception as e:
                print("  [Error] {}: {}".format(filepath, e))
    print("\nExport done. Exported: {}, Skipped: {}".format(total_exported, total_skipped))
    print("Output directory: {}".format(BASE_DIR))

if __name__ == "__main__":
    main()