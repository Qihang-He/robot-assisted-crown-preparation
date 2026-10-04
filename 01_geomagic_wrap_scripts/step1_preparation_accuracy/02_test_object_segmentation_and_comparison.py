#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File: 02_test_object_segmentation_and_comparison.py
Description:
    Part 2: Enhanced registration -> Full region segmentation of A-scans
           -> 3D comparison against IP -> Grouping.

Copyright 2026 Qihang He

Paper step: Step 1 - preparation accuracy, part 2 of 2 (A-scan segmentation and comparison).
Inputs:  the IP model segmented by script 01, A-scan models named Gi-R-j-A (e.g. G1-R-1-A),
         the curve '36-segmentation-curve'
Outputs: segmented A-scan groups ({name}-F0-base, {name}-36, {name}-F1-shoulder ...),
         3D comparison results grouped per specimen, and registration matrices (.tfm)
         in TRANSFORM_DIR
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

# ===== CONFIG =====
OVERWRITE_EXISTING = True
PROJECT_OFFSET = 0.0
CURVE_NAME_SUFFIX = "-segmentation-curve"
SUB_SHORT_NAMES = [
    "F1-shoulder", "F2-axial-wall", "F3-buccal-cusp-reduction",
    "F4-lingual-cusp-reduction", "F5-buccal-occlusal-surface",
    "F6-lingual-occlusal-surface"
]
REF_NAME = "IP"
BASE_NAME_TEMPLATE = "{}-F0-base"
MAIN_36_TEMPLATE = "{}-36"
SUB_TEMPLATES = (
    "{}-F1-shoulder", "{}-F2-axial-wall", "{}-F3-buccal-cusp-reduction",
    "{}-F4-lingual-cusp-reduction", "{}-F5-buccal-occlusal-surface",
    "{}-F6-lingual-occlusal-surface",
)
FIXED_PARAMS = [0, 4, 2, 0.00055, 4, 1, 15, 0.0002, 5e-05, -5e-05, -0.0002, 45]
TAIL_PARAMS = [0, 0, u'', 0, 3]
BASE_REF_NAME = "{}-F0-base".format(REF_NAME)

# --- Path configuration ---
# Directory where registration transformation matrices (.tfm) are saved.
# Adjust this to match your project environment.
TRANSFORM_DIR = r"./output/registration_matrices"

# Naming pattern for test objects (A-scan):
# Template "L1-0-1-A" matches the actual naming convention "Gi-R-j-A", e.g.:
#   G1-R-1-A, G2-P-3-A, G4-R-2-A
#   L1 = letter + 1 digit (e.g., "G1")
#   0  = any string (e.g., "R", "P")
#   1  = digits (e.g., "1", "2", "3")
#   A  = exact match for A-scan
SPECIMEN_TEMPLATE = "L1-0-1-A"

MANUAL_GROUPS = {"G": []}   # empty list means process all G-prefix models
FORCE_AI_NAMES = []          # if non-empty, only these names are processed

_ACTIVE_AI_NAMES = None
_SEGMENTED_AI_NAMES = None

# ===== Specimen name matching =====
def _parse_template(template):
    parts = template.split('-')
    rules = []
    for p in parts:
        if p.startswith('L') and len(p) > 1 and p[1:].isdigit():
            rules.append(('letter_number',))
        elif p in ("0", "1"):
            rules.append(('type', p))
        else:
            rules.append(('exact', p))
    return rules

def _match_name(name, rules):
    name_parts = name.strip().split('-')
    if len(name_parts) != len(rules):
        return False, []
    numbers = []
    for rule, part in zip(rules, name_parts):
        if rule[0] == 'letter_number':
            m = re.match(r'^([A-Za-z])(\d+)$', part)
            if not m:
                return False, []
            numbers.append(int(m.group(2)))
        elif rule[0] == 'type':
            if rule[1] == '0':
                if not part:
                    return False, []
            else:
                if not part.isdigit():
                    return False, []
                numbers.append(int(part))
        elif rule[0] == 'exact':
            if part != rule[1]:
                return False, []
    return True, numbers

_AI_RULES = _parse_template(SPECIMEN_TEMPLATE)

def _is_ai_model(name):
    match, _ = _match_name(name, _AI_RULES)
    return match

def _get_model_number(name):
    match, numbers = _match_name(name, _AI_RULES)
    if not match or not numbers:
        return None
    first_field = name.split('-')[0]
    m = re.match(r'^([A-Za-z])(\d+)$', first_field)
    if m:
        return m.group(1), numbers[0]
    return None, numbers[0]

def _has_segmentation(name):
    if _get_model(BASE_NAME_TEMPLATE.format(name)) is not None:
        return True
    if _get_model(MAIN_36_TEMPLATE.format(name)) is not None:
        return True
    for sub_tmpl in SUB_TEMPLATES:
        if _get_model(sub_tmpl.format(name)) is not None:
            return True
    return False

def _get_model(name):
    name_clean = name.strip()
    m = geoapp.getModelByName(name_clean)
    if m is not None:
        return m
    for model in geoapp.getModels():
        if model.name.strip() == name_clean:
            return model
    return None

def _get_active_ai_names():
    global _ACTIVE_AI_NAMES
    if _ACTIVE_AI_NAMES is not None:
        return _ACTIVE_AI_NAMES
    if FORCE_AI_NAMES:
        selected = []
        for name in FORCE_AI_NAMES:
            if _get_model(name):
                selected.append(name)
            else:
                print("  Warning: forced model {} not found, skipping.".format(name))
        _ACTIVE_AI_NAMES = selected
        return selected
    # incremental mode
    all_matches = []
    seen = set()
    for m in geoapp.getModels():
        if m.type == Model.Mesh and not (hasattr(m, 'isGroup') and m.isGroup):
            name = m.name.strip()
            if name in seen:
                continue
            seen.add(name)
            info = _get_model_number(name)
            if info is None:
                continue
            letter, num = info
            all_matches.append((name, letter, num))
    all_matches.sort(key=lambda x: (x[1], x[2]))
    selected = []
    for name, letter, num in all_matches:
        if letter not in MANUAL_GROUPS:
            continue
        spec = MANUAL_GROUPS[letter]
        if not spec:
            if not _has_segmentation(name):
                selected.append(name)
            else:
                print("  Skipping {} (already segmented, incremental mode).".format(name))
        else:
            in_spec = False
            for item in spec:
                if isinstance(item, int):
                    if num == item:
                        in_spec = True
                        break
                elif isinstance(item, tuple) and len(item) == 2:
                    if item[0] <= num <= item[1]:
                        in_spec = True
                        break
            if in_spec:
                selected.append(name)
    _ACTIVE_AI_NAMES = selected
    return selected

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

def get_all_non_group_objects():
    return [m for m in geoapp.getModels() if not (hasattr(m, 'isGroup') and m.isGroup) and (m.type == Model.Mesh or m.type == 0)]

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

def _find_curve(target_name):
    if _is_ai_model(target_name):
        c = _get_model("36-segmentation-curve")
        if c and c.type == Model.Curves:
            return c
    c = _get_model(target_name + CURVE_NAME_SUFFIX)
    if c and c.type == Model.Curves:
        return c
    for m in geoapp.getModels():
        if m.type == Model.Curves:
            return m
    return None

def project_curve_to_boundary(target_name, curve_name, offset=PROJECT_OFFSET):
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

def _delete_old_comparisons(ai_name):
    patterns = [ai_name, "{}-36".format(ai_name)]
    for short in SUB_SHORT_NAMES:
        patterns.append("{}-{}".format(ai_name, short))
    for name in patterns:
        obj = _get_model(name)
        if obj and obj.type != Model.Mesh:
            try:
                geoapp.deleteModel(obj)
                print("    Deleted old comparison: {}".format(name))
            except:
                pass

# ===== Stage 3: Enhanced registration =====
def enhanced_registration():
    print("\nStage 3: Enhanced registration")
    base = _get_model(BASE_REF_NAME)
    if not base:
        print("Reference base {} not found. Exiting.".format(BASE_REF_NAME))
        sys.exit(0)
    ai_names = _get_active_ai_names()
    if not ai_names:
        print("No models to process. Exiting.")
        sys.exit(0)
    print("  Manual registration of all A-scans with {} ...".format(BASE_REF_NAME))
    for ai_name in ai_names:
        ai = _get_model(ai_name)
        if ai is None:
            print("    Warning: model {} not found. Skipping.".format(ai_name))
            continue
        try:
            ai.pinned = False
        except:
            pass
        geo.clear_all()
        geoapp.setActiveModels([base, ai])
        try:
            print("    Please manually register {}. Click OK when done.".format(ai_name))
            geo.manual_registration()
        except Exception as e:
            print("    Manual registration failed for {}: {}. Exiting.".format(ai_name, e))
            sys.exit(0)
        print("    Manual registration of {} done.".format(ai_name))
    print("  Global registration...")
    all_models = [base] + [_get_model(n) for n in ai_names if _get_model(n) is not None]
    if len(all_models) >= 2:
        geoapp.setActiveModels(all_models)
        try:
            geo.global_registration(0, 100, 2000, False, 20, False, True, False)
            print("  Global registration done.")
        except Exception as e:
            print("  Global registration error (caught): {}".format(e))
    else:
        print("  Skipping global registration (need at least 2 models).")
    print("  Reorienting all A-scans...")
    for name in ai_names:
        m = _get_model(name)
        if m:
            geoapp.setActiveModel(m)
            try:
                geo.reorient_model()
            except Exception as e:
                print("    Reorient {} failed: {}".format(name, e))
    os.makedirs(TRANSFORM_DIR, exist_ok=True)
    for ai_name in ai_names:
        print("\n  Partial segmentation for {}".format(ai_name))
        target = _get_model(ai_name)
        if not target:
            print("    Model {} does not exist. Skipping.".format(ai_name))
            continue
        curve = _find_curve(ai_name)
        if not curve or not project_curve_to_boundary(ai_name, curve.name):
            print("    Curve processing failed. Skipping.")
            continue
        part_name = "{}-F0-base-for-registration".format(ai_name)
        _delete_if_exists(part_name)
        _activate_hide_others(target)
        _pick_and_create(
            "Please click a small patch on the base of [{}] to create {}.".format(ai_name, part_name),
            part_name
        )
        _activate_hide_others(target)
        try:
            geo.remove_all_boundaries()
        except:
            pass
    for ai_name in ai_names:
        part_name = "{}-F0-base-for-registration".format(ai_name)
        part_model = _get_model(part_name)
        if not part_model:
            continue
        try:
            part_model.pinned = False
        except:
            pass
        geo.clear_all()
        geoapp.setActiveModels([base, part_model])
        try:
            geo.global_registration(0, 100, 2000, False, 20, False, True, False)
        except Exception as e:
            print("    Fine registration failed: {}. Skipping.".format(e))
            continue
        tfm_path = os.path.join(TRANSFORM_DIR, "{}.tfm".format(part_name))
        geoapp.setActiveModel(part_model)
        try:
            geo.save_track_xform(tfm_path)
        except Exception as e:
            print("    Save matrix failed: {}".format(e))
            continue
        original = _get_model(ai_name)
        if original:
            geoapp.setActiveModel(original)
            try:
                geo.load_track_xform(tfm_path)
            except:
                pass
        print("    Fine registration for {} done.".format(ai_name))
    print("Enhanced registration completed.")

# ===== Stage 4: Full region segmentation of A-scans =====
def segment_Ai_full():
    global _SEGMENTED_AI_NAMES
    print("\nStage 4: Full region segmentation of A-scans")
    ai_names = _get_active_ai_names()
    _SEGMENTED_AI_NAMES = []
    for ai_name in ai_names:
        if FORCE_AI_NAMES:
            _delete_old_comparisons(ai_name)
        target = _get_model(ai_name)
        if not target or target.type != Model.Mesh:
            print("    Model {} does not exist or wrong type. Skipping.".format(ai_name))
            continue
        curve = _find_curve(ai_name)
        if not curve or not project_curve_to_boundary(ai_name, curve.name):
            print("    Curve processing failed for {}. Skipping.".format(ai_name))
            continue
        info = _get_model_number(ai_name)
        if info:
            letter = info[0]
            spec = MANUAL_GROUPS.get(letter, None)
            if spec is not None and spec and not FORCE_AI_NAMES:
                _delete_old_comparisons(ai_name)
        base_name = BASE_NAME_TEMPLATE.format(ai_name)
        _delete_if_exists(base_name)
        _activate_hide_others(target)
        _pick_and_create("Please click a small patch on the base of [{}].".format(ai_name), base_name)
        main_name = MAIN_36_TEMPLATE.format(ai_name)
        _delete_if_exists(main_name)
        _activate_hide_others(target)
        _pick_and_create(
            "Please click a small patch on the BASE region to invert and get {}.".format(main_name),
            main_name, reverse=True)
        for sub_tmpl in SUB_TEMPLATES:
            sub_name = sub_tmpl.format(ai_name)
            _delete_if_exists(sub_name)
            _activate_hide_others(target)
            _pick_and_create("Please click a small patch on [{}] region.".format(sub_name), sub_name)
        try:
            geo.remove_all_boundaries()
        except:
            pass
        geo.clear_all()
        print("  {} segmentation done.".format(ai_name))
        _SEGMENTED_AI_NAMES.append(ai_name)

# ===== Stage 5: 3D comparison =====
def compare_pair(ref_name, test_name, debug=False):
    if not _get_model(ref_name):
        return
    if not _get_model(test_name):
        return
    all_objs = get_all_non_group_objects()
    remaining = [m for m in all_objs if m.name.strip() != ref_name]
    index = next((i for i, m in enumerate(remaining) if m.name.strip() == test_name), None)
    if index is None:
        return
    geoapp.setActiveModel(_get_model(ref_name))
    params = FIXED_PARAMS + [index] + TAIL_PARAMS
    try:
        geo.compare_3d(*params)
    except Exception as e:
        if debug:
            print("  [DEBUG] 3D comparison failed: {}".format(e))

def comparison_3d():
    print("\nStage 5: 3D comparison")
    ai_names = _SEGMENTED_AI_NAMES
    if not ai_names:
        print("  No models to compare.")
        return
    for ai in ai_names:
        compare_pair(REF_NAME, ai, debug=True)
    ref_36 = "{}-36".format(REF_NAME)
    if _get_model(ref_36):
        for ai in ai_names:
            compare_pair(ref_36, "{}-36".format(ai), debug=True)
    for short in SUB_SHORT_NAMES:
        ref_sub = "{}-{}".format(REF_NAME, short)
        if _get_model(ref_sub):
            for ai in ai_names:
                compare_pair(ref_sub, "{}-{}".format(ai, short), debug=True)
    print("3D comparison done.")

# ===== Stage 6: Grouping =====
def grouping():
    print("\nStage 6: Grouping")
    ai_names = _SEGMENTED_AI_NAMES
    if not ai_names:
        return
    models = geoapp.getModels()
    all_bases = [REF_NAME] + ai_names
    meshes = [m for m in models if m.type == Model.Mesh and not (hasattr(m, 'isGroup') and m.isGroup)]
    for m in meshes:
        name = m.name.strip()
        if name in all_bases:
            add_to_group(m, "initial-data")
        elif name.endswith("-36") and name[:-3] in all_bases:
            add_to_group(m, "36")
        elif name.endswith("-F0-base") and name[:-len("-F0-base")] in all_bases:
            add_to_group(m, "F0-base")
        elif name.endswith("-F0-base-for-registration") and name[:-len("-F0-base-for-registration")] in all_bases:
            add_to_group(m, "F0-base-for-registration")
        else:
            for short in SUB_SHORT_NAMES:
                suffix = "-" + short
                if name.endswith(suffix) and name[:-len(suffix)] in all_bases:
                    add_to_group(m, short)
                    break
    others = [m for m in models if m.type != Model.Mesh and not (hasattr(m, 'isGroup') and m.isGroup)]
    for m in others:
        name = m.name.strip()
        if name in ("Global", "36-segmentation-curve"):
            continue
        if name.endswith("-36"):
            base = name[:-3]
            if base in ai_names:
                add_to_group(m, "36-comparison")
        elif any(name.endswith("-{}".format(short)) for short in SUB_SHORT_NAMES):
            for short in SUB_SHORT_NAMES:
                if name.endswith("-{}".format(short)):
                    base = name[:-len(short)-1]
                    if base in ai_names:
                        add_to_group(m, "{}-{}-comparison".format(REF_NAME, short))
                    break
        elif _is_ai_model(name) and name in ai_names:
            add_to_group(m, "{}-comparison".format(REF_NAME))
    print("Grouping done.")

# ===== Main =====
def main():
    print("=" * 50)
    print("  Part 2: Registration -> Segmentation -> 3D Comparison -> Grouping")
    print("=" * 50)
    enhanced_registration()
    segment_Ai_full()
    comparison_3d()
    grouping()
    print("\nAll done!")

if __name__ == "__main__":
    main()