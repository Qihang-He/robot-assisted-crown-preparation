#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File: 02_seating_scan_registration.py
Description:
    Part 1: Manual + global registration of K (S-scan) to base L (A-F0-base).
    No fine registration. Groups K and base into 'initial-data'.

Copyright 2026 Qihang He

Paper step: Step 2 - crown fit analysis, seating scans.
Inputs:  S-scan models named Gi-R-j-S and the matching abutment bases Gi-R-j-A-F0-base
         produced by Step 1
Outputs: S-scan registered into the abutment frame and grouped as 'initial-data';
         transformation matrices (.tfm) in TRANSFORM_DIR
Environment: Geomagic Wrap 2021 or later with its bundled Python; manual + global
         registration (no fine registration).
Licence: MIT (see LICENSE).
"""

from __future__ import annotations
import re
import os
import sys
import geomagic.app.v3
from geomagic.app.v3.imports import *

OVERWRITE_EXISTING = True
BASE_PATTERN = r'^G(\d+)-[PR]-(\d+)-A-F0-base$'   # e.g., G1-R-1-A-F0-base
K_PATTERN   = r'^G(\d+)-[PR]-(\d+)-S$'            # e.g., G1-R-1-S
I_PATTERN   = r'^G(\d+)-[PR]-(\d+)-C$'            # e.g., G1-R-1-C (not used here)
REF_NAME = "M1"   # not used but kept for compatibility
CURVE_NAME = "36-segmentation-curve"
REG_CURVE_NAME = "36-segmentation-curve"

GROUP_NAMES = [
    "initial-data", "36", "F0-outer-surface",
    "F1-shoulder", "F2-axial-wall", "F3-buccal-cusp-reduction",
    "F4-lingual-cusp-reduction", "F5-buccal-occlusal-surface",
    "F6-lingual-occlusal-surface", "F0-outer-surface-for-registration",
    "F0-base-for-registration"
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
    if name == REF_NAME:
        return True
    if name in (CURVE_NAME, REG_CURVE_NAME):
        return True
    if re.match(BASE_PATTERN, name):
        return True
    if re.match(K_PATTERN, name):
        return True
    if re.match(I_PATTERN, name):
        return True
    if name.startswith(REF_NAME + '-'):
        return True
    return False

def clear_scene():
    print("\nStage 0: Clearing scene (keep only K, bases, curves)")
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
                    continue
                geoapp.setActiveModel(first_mesh)
                geo.create_group(gname)
                first_mesh.removeFromGroup()
                print("  Created group: {}".format(gname))
            except Exception as e:
                print("  Group {} creation failed: {}".format(gname, e))
        else:
            print("  Group exists: {}".format(gname))

def get_base_names():
    bases = []
    for m in geoapp.getModels():
        if m.type != Model.Mesh:
            continue
        name = m.name.strip()
        match = re.match(BASE_PATTERN, name)
        if match:
            i = int(match.group(1))
            j = int(match.group(2))
            bases.append((name, i, j))
    bases.sort(key=lambda x: (x[1], x[2]))
    return [b[0] for b in bases]

def group_initial_models(k_name, base_name):
    k = _get_model(k_name)
    if k:
        add_to_group(k, "initial-data")
    base = _get_model(base_name)
    if base:
        add_to_group(base, "initial-data")

def main():
    print("=" * 50)
    print("  Part 1: Registration of K (seating scan) to Base L (A-F0-base)")
    print("  Manual + global registration. No fine registration.")
    print("=" * 50)
    clear_scene()
    create_groups()
    base_list = get_base_names()
    if not base_list:
        print("No base models found.")
        sys.exit(0)
    for base_name in base_list:
        match = re.match(BASE_PATTERN, base_name)
        if not match:
            continue
        i, j = match.group(1), match.group(2)
        middle = base_name.split('-')[1]
        k_name = "G{}-{}-{}-S".format(i, middle, j)
        base = _get_model(base_name)
        k = _get_model(k_name)
        if base is None or k is None:
            print("  Skipping pair: base={}, k={}".format(base_name, k_name))
            continue
        print("\n  Processing {} <-> {}".format(base_name, k_name))
        try:
            base.pinned = True
            k.pinned = False
        except:
            pass
        # Manual registration
        geo.clear_all()
        geoapp.setActiveModels([base, k])
        try:
            geo.manual_registration()
            print("  Manual registration done.")
        except Exception as e:
            print("  Manual registration failed: {}".format(e))
            sys.exit(0)
        # Global registration
        geoapp.setActiveModels([base, k])
        try:
            geo.global_registration(0, 100, 2000, False, 20, False, True, False)
            print("  Global registration done.")
        except Exception as e:
            print("  Global registration error: {}".format(e))
        try:
            geoapp.setActiveModel(k)
            geo.reorient_model()
        except:
            pass
        group_initial_models(k_name, base_name)
        try:
            geo.remove_all_boundaries()
        except:
            pass
        geo.clear_all()
        print("  {} done.".format(k_name))
    print("\nAll registrations complete. Now run Part 2.")
    try:
        guiQI.messageBox("Registration done. Click OK to proceed.")
    except:
        input("Press Enter to continue...")

if __name__ == "__main__":
    main()