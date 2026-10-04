#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File: 01_reference_object_processing.py
Description:
    Part 1: Clear scene -> Create groups -> Segment IP reference model.
    After execution, the user is asked to pin necessary objects manually,
    then proceed to Part 2.

Copyright 2026 Qihang He

Paper step: Step 1 - preparation accuracy, part 1 of 2 (reference object, run once).
Inputs:  the ideal preparation model named 'IP' in the Geomagic Wrap scene
Outputs: groups IP-F0-base, IP-36 and IP-F1-shoulder ... IP-F6-lingual-occlusal-surface
         in the scene (export them with
         01_geomagic_wrap_scripts/utilities/export_results_to_stl.py)
Environment: Geomagic Wrap 2021 or later with its bundled Python; prompts the operator
         to click a small patch on each region.
Licence: MIT (see LICENSE).
"""

from __future__ import annotations
import re
import sys
import geomagic.app.v3
from geomagic.app.v3.imports import *

# ===== CONFIG =====
OVERWRITE_EXISTING = True
REF_NAME = "IP"                         # Reference model name
BASE_NAME_TEMPLATE = "{}-F0-base"
MAIN_36_TEMPLATE = "{}-36"
SUB_TEMPLATES = (
    "{}-F1-shoulder", "{}-F2-axial-wall", "{}-F3-buccal-cusp-reduction",
    "{}-F4-lingual-cusp-reduction", "{}-F5-buccal-occlusal-surface",
    "{}-F6-lingual-occlusal-surface",
)

# Naming pattern for test objects (A-scan):
# Template "L1-0-1-A" matches the actual naming convention "Gi-R-j-A", e.g.:
#   G1-R-1-A, G2-P-3-A, G4-R-2-A
#   L1 = letter + 1 digit (e.g., "G1")
#   0  = any string (e.g., "R", "P")
#   1  = digits (e.g., "1", "2", "3")
#   A  = exact match for A-scan
SPECIMEN_TEMPLATE = "L1-0-1-A"

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
        return False, '', []
    group_letter = ''
    numbers = []
    for rule, part in zip(rules, name_parts):
        if rule[0] == 'letter_number':
            m = re.match(r'^([A-Za-z])(\d+)$', part)
            if not m:
                return False, '', []
            if not group_letter:
                group_letter = m.group(1)
            numbers.append(int(m.group(2)))
        elif rule[0] == 'type':
            if rule[1] == '0':
                if not part:
                    return False, '', []
            else:
                if not part.isdigit():
                    return False, '', []
                numbers.append(int(part))
        elif rule[0] == 'exact':
            if part != rule[1]:
                return False, '', []
    return True, group_letter, numbers

_AI_RULES = _parse_template(SPECIMEN_TEMPLATE)

def _is_ai_model(name):
    match, _, _ = _match_name(name, _AI_RULES)
    return match

# ===== Utility functions =====
def _get_model(name):
    return geoapp.getModelByName(name)

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

# ===== Stage 0: Clear scene =====
def clear_scene():
    print("\nStage 0: Clearing scene")
    for m in geoapp.getModels():
        if hasattr(m, 'isGroup') and m.isGroup:
            try:
                for c in list(m.groupModels):
                    c.removeFromGroup()
            except:
                pass
    keep_ids = set()
    for m in geoapp.getModels():
        if m.type == Model.Mesh:
            name = m.name.strip()
            if name == REF_NAME or _is_ai_model(name):
                keep_ids.add(m.id)
    curve = _get_model("36-segmentation-curve")
    if curve and curve.type == Model.Curves:
        keep_ids.add(curve.id)
    for m in geoapp.getModels():
        if hasattr(m, 'isGroup') and m.isGroup:
            continue
        if m.id not in keep_ids:
            try:
                geoapp.deleteModel(m)
            except:
                pass
    print("Scene cleared.")

# ===== Stage 1: Create groups =====
def create_groups():
    print("\nStage 1: Creating groups")
    for m in geoapp.getModels():
        if hasattr(m, 'isGroup') and m.isGroup and m.name.strip() != "Global":
            try:
                for c in list(m.groupModels):
                    c.removeFromGroup()
                geoapp.deleteModel(m)
            except:
                pass
    ip = _get_model(REF_NAME)
    if not ip:
        print("Error: IP model not found. Cannot create groups.")
        sys.exit(0)
    REQUIRED_GROUPS = [
        "initial-data", "36", "F0-base",
        "F1-shoulder", "F2-axial-wall", "F3-buccal-cusp-reduction",
        "F4-lingual-cusp-reduction", "F5-buccal-occlusal-surface",
        "F6-lingual-occlusal-surface", "F0-base-for-registration",
        "IP-comparison", "36-comparison",
        "IP-F1-shoulder-comparison", "IP-F2-axial-wall-comparison",
        "IP-F3-buccal-cusp-reduction-comparison", "IP-F4-lingual-cusp-reduction-comparison",
        "IP-F5-buccal-occlusal-surface-comparison", "IP-F6-lingual-occlusal-surface-comparison",
    ]
    for gname in REQUIRED_GROUPS:
        try:
            geoapp.setActiveModel(ip)
            geo.create_group(gname)
            ip.removeFromGroup()
        except Exception as e:
            print("Failed to create group {}: {}".format(gname, e))
            sys.exit(0)
    print("All groups created.")

# ===== Stage 2: Segment IP =====
def segment_IP():
    print("\nStage 2: IP surface region segmentation")
    target = _get_model(REF_NAME)
    if not target or target.type != Model.Mesh:
        print("IP does not exist or wrong type. Exiting.")
        sys.exit(0)

    base_name = BASE_NAME_TEMPLATE.format(REF_NAME)
    _delete_if_exists(base_name)
    _activate_hide_others(target)
    _pick_and_create("Please click a small patch on the base region of [{}].".format(REF_NAME), base_name)

    main_name = MAIN_36_TEMPLATE.format(REF_NAME)
    _delete_if_exists(main_name)
    _activate_hide_others(target)
    _pick_and_create("Please click a small patch on the BASE region to invert and get {}.".format(main_name), main_name, reverse=True)

    for sub_tmpl in SUB_TEMPLATES:
        sub_name = sub_tmpl.format(REF_NAME)
        _delete_if_exists(sub_name)
        _activate_hide_others(target)
        _pick_and_create("Please click a small patch on [{}] region.".format(sub_name), sub_name)

    geo.clear_all()
    print("IP segmentation done.")

# ===== Main =====
def main():
    print("=" * 50)
    print("  Part 1: Preprocessing and IP segmentation")
    print("=" * 50)
    clear_scene()
    create_groups()
    segment_IP()
    print("\nPlease manually pin required objects (e.g., IP-F0-base, IP-36), then run Part 2.")
    try:
        guiQI.messageBox(
            "IP region segmentation completed.\nPin the necessary objects in the Model Manager, then click OK.",
            "Information"
        )
    except:
        input("Press Enter after pinning objects...")
    print("\nPart 1 finished. Run Part 2 now.")

if __name__ == "__main__":
    main()