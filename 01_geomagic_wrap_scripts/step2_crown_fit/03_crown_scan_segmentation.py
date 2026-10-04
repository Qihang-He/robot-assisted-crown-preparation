#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File: 03_crown_scan_segmentation.py
Description:
    Part 2: Register I (C-scan) to K (S-scan), project curve, segment
    registration patch, fine registration, full segmentation of I with
    normal flipping, and grouping.

Copyright 2026 Qihang He

Paper step: Step 2 - crown fit analysis, crown scans (C-scans).
Inputs:  C-scan models named Gi-R-j-C and the registered S-scans from script 02,
         the curve '36-segmentation-curve'
Outputs: C-scan registered to the seated assembly, segmented groups
         ({name}-36, {name}-F0-outer-surface, {name}-F1-shoulder ...) with flipped normals,
         and registration matrices (.tfm) in TRANSFORM_DIR
Environment: Geomagic Wrap 2021 or later with its bundled Python; interactive registration
         and region picking.
Licence: MIT (see LICENSE).
"""

from __future__ import annotations
import re
import os
import sys
import geomagic.app.v3
from geomagic.app.v3.imports import *

OVERWRITE_EXISTING = True
K_PATTERN = r'^G(\d+)-[PR]-(\d+)-S$'   # e.g., G1-R-1-S
I_PATTERN = r'^G(\d+)-[PR]-(\d+)-C$'   # e.g., G1-R-1-C
CURVE_NAME = "36-segmentation-curve"
REG_CURVE_NAME = "36-segmentation-curve"

# --- Path configuration ---
# Directory where registration transformation matrices (.tfm) are saved.
# Adjust this to match your project environment.
TRANSFORM_DIR = r"./output/registration_matrices"

BASE_NAME_TEMPLATE = "{}-F0-outer-surface"
MAIN_36_TEMPLATE = "{}-36"
SUB_TEMPLATES = (
    "{}-F1-shoulder", "{}-F2-axial-wall", "{}-F3-buccal-cusp-reduction",
    "{}-F4-lingual-cusp-reduction", "{}-F5-buccal-occlusal-surface",
    "{}-F6-lingual-occlusal-surface",
)
REG_SUFFIX = "-for-registration"

FORCE_I_NAMES = []   # if non-empty, only these I names are processed
USE_INCREMENTAL = 1   # 1 = skip if already segmented, 0 = always process

def _get_model(name):
    name_clean = name.strip()
    m = geoapp.getModelByName(name_clean)
    if m is not None:
        return m
    for model in geoapp.getModels():
        if model.name.strip() == name_clean:
            return model
    return None

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

def _has_segmentation(name):
    if _get_model(BASE_NAME_TEMPLATE.format(name)) is not None:
        return True
    if _get_model(MAIN_36_TEMPLATE.format(name)) is not None:
        return True
    for sub_tmpl in SUB_TEMPLATES:
        if _get_model(sub_tmpl.format(name)) is not None:
            return True
    return False

def get_k_i_pairs():
    pairs = []
    for m in geoapp.getModels():
        if m.type != Model.Mesh:
            continue
        name = m.name.strip()
        match = re.match(K_PATTERN, name)
        if not match:
            continue
        i = int(match.group(1))
        middle = name.split('-')[1]
        j = int(match.group(2))
        i_name = "G{}-{}-{}-C".format(i, middle, j)
        if _get_model(i_name) is not None:
            pairs.append((name, i_name, i, j))
    pairs.sort(key=lambda x: (x[2], x[3]))
    return [(k, i) for (k, i, _, _) in pairs]

def _i_name_to_k_name(i_name):
    match = re.match(I_PATTERN, i_name)
    if not match:
        return None
    i = match.group(1)
    middle = i_name.split('-')[1]
    j = match.group(2)
    return "G{}-{}-{}-S".format(i, middle, j)

def segment_I_full(i_name):
    print("\n  --- Full segmentation of {} ---".format(i_name))
    target = _get_model(i_name)
    if not target or target.type != Model.Mesh:
        print("    {} not found. Skipping.".format(i_name))
        return
    curve = _get_model(CURVE_NAME)
    if not curve:
        print("    Curve not found.")
        return
    # base outer surface (no flip)
    base_name = BASE_NAME_TEMPLATE.format(i_name)
    _delete_if_exists(base_name)
    if not project_curve_to_boundary(i_name, CURVE_NAME):
        print("    Curve projection failed.")
        return
    _activate_hide_others(target)
    _pick_and_create("Please click a small patch on the outer base of [{}].".format(i_name), base_name)
    # 36 (invert)
    main_name = MAIN_36_TEMPLATE.format(i_name)
    _delete_if_exists(main_name)
    if not project_curve_to_boundary(i_name, CURVE_NAME):
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
        sub_name = sub_tmpl.format(i_name)
        _delete_if_exists(sub_name)
        if not project_curve_to_boundary(i_name, CURVE_NAME):
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
    print("  Segmentation of {} done.".format(i_name))

def group_models(k_name, i_name):
    k = _get_model(k_name)
    if k:
        add_to_group(k, "initial-data")
    ii = _get_model(i_name)
    if ii:
        add_to_group(ii, "initial-data")
    main_name = MAIN_36_TEMPLATE.format(i_name)
    obj = _get_model(main_name)
    if obj:
        add_to_group(obj, "36")
    base_name = BASE_NAME_TEMPLATE.format(i_name)
    obj = _get_model(base_name)
    if obj:
        add_to_group(obj, "F0-outer-surface")
    for sub_tmpl in SUB_TEMPLATES:
        sub_name = sub_tmpl.format(i_name)
        obj = _get_model(sub_name)
        if obj:
            short = sub_tmpl.split('}')[1].lstrip('-')
            add_to_group(obj, short)
    reg_part_name = "{}-F0-outer-surface{}".format(i_name, REG_SUFFIX)
    obj = _get_model(reg_part_name)
    if obj:
        add_to_group(obj, "F0-outer-surface-for-registration")

def main():
    print("=" * 50)
    print("  Part 2: I (C-scan) registration and segmentation with fine registration")
    print("=" * 50)
    if FORCE_I_NAMES:
        pairs = []
        for i_name in FORCE_I_NAMES:
            k_name = _i_name_to_k_name(i_name)
            if k_name and _get_model(i_name) and _get_model(k_name):
                pairs.append((k_name, i_name))
        if not pairs:
            print("No valid forced I names.")
            sys.exit(0)
    else:
        pairs = get_k_i_pairs()
        if not pairs:
            print("No K-I pairs found.")
            sys.exit(0)
    os.makedirs(TRANSFORM_DIR, exist_ok=True)
    for k_name, i_name in pairs:
        print("\n  Processing K={} <-> I={}".format(k_name, i_name))
        if not FORCE_I_NAMES and USE_INCREMENTAL and _has_segmentation(i_name):
            print("  Incremental: {} already segmented, skipping.".format(i_name))
            continue
        k = _get_model(k_name)
        i = _get_model(i_name)
        if k is None or i is None:
            print("  Missing model, skipping.")
            continue
        # Manual registration
        geo.clear_all()
        geoapp.setActiveModels([k, i])
        try:
            print("  Please manually register I to K.")
            geo.manual_registration()
            print("  Manual registration done.")
        except Exception as e:
            print("  Manual registration failed: {}. Exiting.".format(e))
            sys.exit(0)
        # Global registration
        geoapp.setActiveModels([k, i])
        try:
            geo.global_registration(0, 100, 2000, False, 20, False, True, False)
            print("  Global registration done.")
        except Exception as e:
            print("  Global registration error: {}".format(e))
        # Project curve for fine registration
        if not project_curve_to_boundary(i_name, REG_CURVE_NAME):
            print("  Curve projection failed.")
            continue
        reg_part_name = "{}-F0-outer-surface{}".format(i_name, REG_SUFFIX)
        _delete_if_exists(reg_part_name)
        _activate_hide_others(i)
        _pick_and_create(
            "Please click a small patch on the outer base of [{}] for registration.".format(i_name),
            reg_part_name)
        # Fine registration using the registration patch
        print("  Fine registration...")
        reg_part = _get_model(reg_part_name)
        if reg_part:
            geo.clear_all()
            geoapp.setActiveModels([k, reg_part])
            try:
                geo.global_registration(0, 100, 2000, False, 20, False, True, False)
                print("  Fine registration done.")
            except Exception as e:
                print("  Fine registration failed: {}".format(e))
                continue
            tfm_path = os.path.join(TRANSFORM_DIR, "{}.tfm".format(reg_part_name))
            geoapp.setActiveModel(reg_part)
            try:
                geo.save_track_xform(tfm_path)
            except Exception as e:
                print("  Save matrix failed: {}".format(e))
            geoapp.setActiveModel(i)
            try:
                geo.load_track_xform(tfm_path)
                print("  Transform applied to {}".format(i_name))
            except Exception as e:
                print("  Load matrix failed: {}".format(e))
        else:
            print("  Registration patch not found.")
            continue
        # Full segmentation
        segment_I_full(i_name)
        # Grouping
        print("  Grouping...")
        group_models(k_name, i_name)
        try:
            geo.remove_all_boundaries()
        except:
            pass
        geo.clear_all()
    print("\nAll processing done.")

if __name__ == "__main__":
    main()