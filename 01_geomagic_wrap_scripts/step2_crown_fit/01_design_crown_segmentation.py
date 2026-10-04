#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File: 01_design_crown_segmentation.py
Description:
    Segment the preoperative design crowns (DG-Gi-C) using the 36-segmentation-curve.
    No registration needed. Flip normals for 36 and F1-F6 (not for base).
    Incremental mode: skip if already segmented.

Copyright 2026 Qihang He

Paper step: Step 2 - crown fit analysis, design crowns.
Inputs:  design crown models named DG-Gi-C (e.g. DG-G1-C), the curve '36-segmentation-curve'
Outputs: groups DG-Gi-C-36, DG-Gi-C-F0-outer-surface and DG-Gi-C-F1-shoulder ... F6
         (internal surfaces with flipped normals), exportable to STL
Environment: Geomagic Wrap 2021 or later with its bundled Python.
Licence: MIT (see LICENSE).
"""

from __future__ import annotations
import re
import os
import sys
import geomagic.app.v3
from geomagic.app.v3.imports import *

OVERWRITE_EXISTING = True
CROWN_PATTERN = r'^DG-G(\d+)-C$'   # e.g., DG-G1-C, DG-G2-C
CURVE_NAME = "36-segmentation-curve"

BASE_NAME_TEMPLATE = "{}-F0-outer-surface"
MAIN_36_TEMPLATE = "{}-36"
SUB_TEMPLATES = (
    "{}-F1-shoulder", "{}-F2-axial-wall", "{}-F3-buccal-cusp-reduction",
    "{}-F4-lingual-cusp-reduction", "{}-F5-buccal-occlusal-surface",
    "{}-F6-lingual-occlusal-surface",
)

GROUP_NAMES = [
    "initial-data", "36", "F0-outer-surface",
    "F1-shoulder", "F2-axial-wall", "F3-buccal-cusp-reduction",
    "F4-lingual-cusp-reduction", "F5-buccal-occlusal-surface",
    "F6-lingual-occlusal-surface", "F0-outer-surface-for-registration"
]

def _get_model(name):
    name_clean = name.strip()
    m = geoapp.getModelByName(name_clean)
    if m is not None:
        return m
    for model in geoapp.getModels():
        if model.name.strip() == name_clean:
            return model
    return None

def _model_should_keep(name):
    if name == CURVE_NAME:
        return True
    if re.match(CROWN_PATTERN, name):
        return True
    return False

def clear_scene():
    print("\nStage 0: Clearing scene (keep only design crowns and curve)")
    for m in geoapp.getModels():
        if hasattr(m, 'isGroup') and m.isGroup:
            try:
                for c in list(m.groupModels):
                    c.removeFromGroup()
                geoapp.deleteModel(m)
            except:
                pass
    for m in geoapp.getModels():
        if hasattr(m, 'isGroup') and m.isGroup:
            continue
        name = m.name.strip()
        if not _model_should_keep(name):
            try:
                geoapp.deleteModel(m)
                print("  Deleted: {}".format(name))
            except:
                pass
    print("Scene cleared.")

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
    if OVERWRITE_EXISTING:
        m = _get_model(name)
        if m:
            geoapp.deleteModel(m)

def get_pure_mesh_list():
    return [m for m in geoapp.getModels() if m.type == Model.Mesh and not (hasattr(m, 'isGroup') and m.isGroup)]

def get_curve_list():
    all_models = geoapp.getModels()
    curves = [m for m in all_models if m.type == Model.Curves]
    curves.sort(key=lambda m: all_models.index(m))
    return curves

def _pick_and_create(prompt, new_name, reverse=False):
    geo.clear_all()
    res = guiQI.pickTriangles(prompt)
    if res is None:
        print("User cancelled. Exiting.")
        sys.exit(0)
    geo.select_bounded_components()
    if reverse:
        geo.reverse_selection()
    _delete_if_exists(new_name)
    geo.selection_to_object(1, new_name)

def project_curve_to_boundary(target_name, curve_name, offset=0.0):
    target = _get_model(target_name)
    curve = _get_model(curve_name)
    if not target or target.type != Model.Mesh:
        return False
    if not curve or curve.type != Model.Curves:
        return False
    _activate_hide_others(target)
    try:
        geo.remove_all_boundaries()
    except:
        pass
    mesh_list = get_pure_mesh_list()
    target_idx = next((i for i, m in enumerate(mesh_list) if m.id == target.id), None)
    curve_list = get_curve_list()
    curve_idx = next((i for i, m in enumerate(curve_list) if m.id == curve.id), None)
    if target_idx is None or curve_idx is None:
        return False
    _activate_hide_others(curve)
    try:
        geo.copy_curve_to_object(target_idx, curve_idx, 0, offset)
    except:
        return False
    _activate_hide_others(target)
    try:
        geo.convert_to_boundaries()
    except:
        return False
    geo.clear_all()
    return True

def flip_active_normals():
    try:
        geo.flip_polygon_normals()
        print("    Normals flipped.")
    except Exception as e:
        print("    Flip normals failed: {}".format(e))

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

def create_groups():
    for gname in GROUP_NAMES:
        if find_group(gname) is None:
            try:
                first_mesh = next((m for m in geoapp.getModels() if m.type == Model.Mesh and not (hasattr(m, 'isGroup') and m.isGroup)), None)
                if first_mesh is None:
                    print("Warning: no mesh to create group.")
                    continue
                geoapp.setActiveModel(first_mesh)
                geo.create_group(gname)
                first_mesh.removeFromGroup()
                print("  Created group: {}".format(gname))
            except Exception as e:
                print("  Failed to create group {}: {}".format(gname, e))
        else:
            print("  Group already exists: {}".format(gname))

def _has_segmentation(name):
    if _get_model(BASE_NAME_TEMPLATE.format(name)) is not None:
        return True
    if _get_model(MAIN_36_TEMPLATE.format(name)) is not None:
        return True
    for sub_tmpl in SUB_TEMPLATES:
        if _get_model(sub_tmpl.format(name)) is not None:
            return True
    return False

def get_crown_names():
    names = []
    for m in geoapp.getModels():
        if m.type != Model.Mesh:
            continue
        name = m.name.strip()
        match = re.match(CROWN_PATTERN, name)
        if match:
            num = int(match.group(1))
            names.append((name, num))
    names.sort(key=lambda x: x[1])
    return [n[0] for n in names]

def segment_crown_full(crown_name):
    print("\n  --- Full segmentation of {} ---".format(crown_name))
    target = _get_model(crown_name)
    if not target or target.type != Model.Mesh:
        print("    Model {} not found. Skipping.".format(crown_name))
        return
    curve = _get_model(CURVE_NAME)
    if not curve:
        print("    Curve {} not found.".format(CURVE_NAME))
        return
    # base
    base_name = BASE_NAME_TEMPLATE.format(crown_name)
    _delete_if_exists(base_name)
    if not project_curve_to_boundary(crown_name, CURVE_NAME):
        print("    Curve projection failed.")
        return
    _activate_hide_others(target)
    _pick_and_create("Please click a small patch on the outer base of [{}].".format(crown_name), base_name)
    # 36 (invert)
    main_name = MAIN_36_TEMPLATE.format(crown_name)
    _delete_if_exists(main_name)
    if not project_curve_to_boundary(crown_name, CURVE_NAME):
        print("    Curve projection failed.")
        return
    _activate_hide_others(target)
    _pick_and_create(
        "Please click a small patch on the BASE region to invert and get {}.".format(main_name),
        main_name, reverse=True)
    print("    Flipping normals for {}...".format(main_name))
    flip_active_normals()
    # subregions
    for sub_tmpl in SUB_TEMPLATES:
        sub_name = sub_tmpl.format(crown_name)
        _delete_if_exists(sub_name)
        if not project_curve_to_boundary(crown_name, CURVE_NAME):
            print("    Curve projection failed for {}.".format(sub_name))
            continue
        _activate_hide_others(target)
        _pick_and_create("Please click a small patch on [{}] region.".format(sub_name), sub_name)
        print("    Flipping normals for {}...".format(sub_name))
        flip_active_normals()
    try:
        geo.remove_all_boundaries()
    except:
        pass
    geo.clear_all()
    print("  Segmentation of {} done.".format(crown_name))

def group_crown_models(crown_name):
    crown = _get_model(crown_name)
    if crown:
        add_to_group(crown, "initial-data")
    main_name = MAIN_36_TEMPLATE.format(crown_name)
    obj = _get_model(main_name)
    if obj:
        add_to_group(obj, "36")
    base_name = BASE_NAME_TEMPLATE.format(crown_name)
    obj = _get_model(base_name)
    if obj:
        add_to_group(obj, "F0-outer-surface")
    for sub_tmpl in SUB_TEMPLATES:
        sub_name = sub_tmpl.format(crown_name)
        obj = _get_model(sub_name)
        if obj:
            short = sub_tmpl.split('}')[1].lstrip('-')
            add_to_group(obj, short)

def main():
    print("=" * 50)
    print("  Design Crown Segmentation")
    print("  Pattern: {}".format(CROWN_PATTERN))
    print("=" * 50)
    clear_scene()
    create_groups()
    crown_names = get_crown_names()
    if not crown_names:
        print("No design crowns found.")
        sys.exit(0)
    for cn in crown_names:
        print("\n  Processing {} ...".format(cn))
        if _has_segmentation(cn):
            print("  Incremental: {} already segmented, skipping.".format(cn))
            continue
        segment_crown_full(cn)
        group_crown_models(cn)
    print("\nAll design crowns segmented.")

if __name__ == "__main__":
    main()