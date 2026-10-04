#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File: 01_shoulder_contour_point_cloud_extraction.py
Description:
    Extract shoulder contour curves from A- and C-scans and generate
    point clouds (.asc). Uses the reference curve IP-shoulder-outline-curve.

Copyright 2026 Qihang He

Paper step: Step 3 - marginal contour extraction (input for the marginal gap analysis).
Inputs:  A-scan and C-scan models named Gi-R-j-A / Gi-R-j-C and the reference curve
         'IP-shoulder-outline-curve'
Outputs: shoulder-outline curves and dense point clouds written as ASCII .asc files
         ('{name}-shoulder-margin-point-cloud.asc') in OUTPUT_DIR
Environment: Geomagic Wrap 2021 or later with its bundled Python.
Licence: MIT (see LICENSE).
"""

from __future__ import annotations
import re
import os
import sys
import geomagic.app.v3
from geomagic.app.v3.imports import *

SOURCE_CURVE_NAME = "IP-shoulder-outline-curve"

# --- Path configuration ---
# Output directory for point cloud (.asc) files.
# Adjust this to match your project environment.
OUTPUT_DIR = r"./output/shoulder_margin_point_cloud"

CURVE_SUFFIX = "-shoulder-outline-curve"
POINT_SUFFIX = "-shoulder-margin-point-cloud"
FORCE_AI_NAMES = []   # empty = auto process all matching A and C models

# Naming convention: Gi-R-j-A (A-scan) or Gi-R-j-C (C-scan)
# e.g., G1-R-1-A, G2-P-3-C, G4-R-2-C
def _is_target_model(name):
    parts = name.split('-')
    if len(parts) != 4:
        return False
    if not re.match(r'^[A-Za-z]\d+$', parts[0]):
        return False
    if parts[1] not in ('R', 'P'):
        return False
    if not parts[2].isdigit():
        return False
    if parts[3] not in ('A', 'C'):
        return False
    return True

def _get_model(name):
    name_clean = name.strip()
    m = geoapp.getModelByName(name_clean)
    if m is not None:
        return m
    for model in geoapp.getModels():
        if model.name.strip() == name_clean:
            return model
    return None

def get_pure_mesh_list():
    return [m for m in geoapp.getModels() if m.type == Model.Mesh and not (hasattr(m, 'isGroup') and m.isGroup)]

def get_curve_list():
    all_models = geoapp.getModels()
    curves = [m for m in all_models if m.type == Model.Curves]
    curves.sort(key=lambda m: all_models.index(m))
    return curves

def _activate_hide_others(name_or_model):
    if isinstance(name_or_model, str):
        m = _get_model(name_or_model)
        if m is None:
            raise RuntimeError("Model not found: {}".format(name_or_model))
    else:
        m = name_or_model
    geoapp.setActiveModel(m)
    geo.hide_inactive_objects()
    return m

def _delete_if_exists(name):
    m = _get_model(name)
    if m:
        try:
            geoapp.deleteModel(m)
        except:
            pass

def find_group(name):
    target = name.strip()
    for m in geoapp.getModels():
        if hasattr(m, 'isGroup') and m.isGroup and m.name.strip() == target:
            return m
    return None

def add_to_group(model, group_name):
    g = find_group(group_name)
    if g:
        try:
            model.addToGroup(g)
        except:
            pass

def ensure_groups():
    required_groups = ["initial-data", "shoulder-outline-curve", "shoulder-margin-point-cloud"]
    any_mesh = None
    for m in geoapp.getModels():
        if m.type == Model.Mesh and not (hasattr(m, 'isGroup') and m.isGroup):
            any_mesh = m
            break
    if not any_mesh:
        print("Warning: no mesh to create groups.")
        return
    for gname in required_groups:
        if find_group(gname) is None:
            try:
                geoapp.setActiveModel(any_mesh)
                geo.create_group(gname)
                any_mesh.removeFromGroup()
                print("Created group: {}".format(gname))
            except Exception as e:
                print("Failed to create group {}: {}".format(gname, e))

def clean_scene():
    keep_names = {SOURCE_CURVE_NAME}
    for m in geoapp.getModels():
        if m.type == Model.Mesh and not (hasattr(m, 'isGroup') and m.isGroup):
            if _is_target_model(m.name.strip()):
                keep_names.add(m.name.strip())
    deleted = 0
    for m in list(geoapp.getModels()):
        if hasattr(m, 'isGroup') and m.isGroup:
            continue
        if m.name.strip() not in keep_names:
            try:
                geoapp.deleteModel(m)
                deleted += 1
            except:
                pass
    print("Cleaned: deleted {} objects.".format(deleted))

def classify_meshes():
    group_name = "initial-data"
    count = 0
    for m in geoapp.getModels():
        if m.type == Model.Mesh and not (hasattr(m, 'isGroup') and m.isGroup):
            if _is_target_model(m.name.strip()):
                add_to_group(m, group_name)
                count += 1
    print("Classified {} meshes into '{}'.".format(count, group_name))

def get_target_names():
    if FORCE_AI_NAMES:
        selected = [n for n in FORCE_AI_NAMES if _get_model(n) is not None]
        return selected
    selected = []
    seen = set()
    for m in geoapp.getModels():
        if m.type == Model.Mesh and not (hasattr(m, 'isGroup') and m.isGroup):
            name = m.name.strip()
            if name in seen:
                continue
            seen.add(name)
            if _is_target_model(name):
                selected.append(name)
    selected.sort()
    return selected

def process_target(target_name):
    print("\n" + "=" * 50)
    print("Processing: {}".format(target_name))
    print("=" * 50)
    target = _get_model(target_name)
    if not target or target.type != Model.Mesh:
        print("  Invalid target.")
        return False
    source_curve = _get_model(SOURCE_CURVE_NAME)
    if not source_curve or source_curve.type != Model.Curves:
        print("  Source curve not found.")
        return False
    mesh_list = get_pure_mesh_list()
    target_idx = next((i for i, m in enumerate(mesh_list) if m.id == target.id), None)
    if target_idx is None:
        print("  Cannot get index.")
        return False
    # Activate source curve and project to target
    _activate_hide_others(source_curve)
    try:
        geo.copy_curve_to_object(target_idx, 0, 0, 0.000235571)
    except Exception as e:
        print("  Projection failed: {}".format(e))
        return False
    # Extract curve
    curve_name = "{}{}".format(target_name, CURVE_SUFFIX)
    _delete_if_exists(curve_name)
    try:
        geo.features_to_curves(1, 51, 5e-06, 6, 3.87919e-05, 0, curve_name)
        print("  Curve: {}".format(curve_name))
    except Exception as e:
        print("  Curve extraction failed: {}".format(e))
        return False
    new_curve = _get_model(curve_name)
    if not new_curve:
        return False
    _activate_hide_others(new_curve)
    # Create point cloud
    point_name = "{}{}".format(target_name, POINT_SUFFIX)
    _delete_if_exists(point_name)
    try:
        geo.create_points(point_name, 0, 3.75908e-05, 1, 100000)
        print("  Point cloud: {}".format(point_name))
    except Exception as e:
        print("  Point cloud creation failed: {}".format(e))
        return False
    try:
        geo.hide_inactive_objects()
    except:
        pass
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    save_filename = "{}{}.asc".format(target_name, POINT_SUFFIX)
    save_path = os.path.join(OUTPUT_DIR, save_filename)
    try:
        geo.saveas(save_path, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, -1, 0, 1, 0)
        print("  Saved: {}".format(save_path))
    except Exception as e:
        print("  Save failed: {}".format(e))
        return False
    point_obj = _get_model(point_name)
    if new_curve:
        add_to_group(new_curve, "shoulder-outline-curve")
    if point_obj:
        add_to_group(point_obj, "shoulder-margin-point-cloud")
    print("  Done with {}.".format(target_name))
    return True

def main():
    print("=" * 60)
    print("  Shoulder Contour Extraction and Point Cloud Generation")
    print("=" * 60)
    clean_scene()
    ensure_groups()
    classify_meshes()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    targets = get_target_names()
    if not targets:
        print("No target models found.")
        sys.exit(0)
    print("Found {} targets.".format(len(targets)))
    success = fail = 0
    for t in targets:
        if process_target(t):
            success += 1
        else:
            fail += 1
    print("\nTotal: success={}, fail={}".format(success, fail))
    print("Output: {}".format(OUTPUT_DIR))

if __name__ == "__main__":
    main()