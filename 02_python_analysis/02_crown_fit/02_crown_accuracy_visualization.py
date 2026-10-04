#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Crown Accuracy Visualization

Violin plot with individual points, box, mean±SD, and significance brackets
for μ_crown and σ_crown across groups G1–G4.

Output: PNG (600 dpi) and PDF.

Copyright © 2026 Qihang He
Released under the MIT licence; see LICENSE.

Paper step: crown printing accuracy (group figure).
Inputs:  analysis_results/crown_accuracy/crown_accuracy.csv, crown_group_summary.csv
Outputs: analysis_results/crown_accuracy_visualization/ PNG (600 dpi) and PDF
Licence: MIT (see LICENSE).
"""

import os, warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from itertools import combinations

warnings.filterwarnings('ignore')

plt.rcParams.update({'font.family': 'sans-serif', 'font.sans-serif': ['Arial', 'Helvetica'],
                     'axes.unicode_minus': False, 'figure.dpi': 150, 'savefig.dpi': 600,
                     'savefig.bbox': 'tight', 'axes.spines.top': False, 'axes.spines.right': False})

# ============================ Configuration ============================
DATA_ROOT = r"path/to/your/project/data"

INPUT_FILE = os.path.join(DATA_ROOT, "analysis_results", "crown_accuracy", "crown_accuracy.csv")
OUTPUT_DIR = os.path.join(DATA_ROOT, "analysis_results", "crown_accuracy_visualization")
os.makedirs(OUTPUT_DIR, exist_ok=True)

df = pd.read_csv(INPUT_FILE)
df['μ_crown (μm)'] = df['μ_crown (mm)'] * 1000
df['σ_crown (μm)'] = df['σ_crown (mm)'] * 1000
GROUPS = ['G1','G2','G3','G4']
COLORS = ['#a6cee3','#4e79a7','#1b3d6b','#0a1a33']
MARKERS = ['o','s','D','^']


def add_label(ax, label):
    ax.text(0.02, 0.97, label, transform=ax.transAxes, fontsize=10, fontweight='bold',
            va='top', ha='left', bbox=dict(boxstyle='round,pad=0.08', facecolor='white', edgecolor='none', alpha=0.85))


def draw_brackets(ax, x_pos, group_data, y_base, step=0.5, arm=0.15):
    pairs = list(combinations(range(4),2))
    p_vals = []
    valid = []
    for i,j in pairs:
        if len(group_data[i])>0 and len(group_data[j])>0:
            _, p = stats.mannwhitneyu(group_data[i], group_data[j], alternative='two-sided')
            p_vals.append(p); valid.append((i,j))
    if not valid: return None
    corr = np.minimum(np.array(p_vals)*len(valid), 1.0)
    sig_idx = [k for k in range(len(valid)) if corr[k] < 0.05]
    if not sig_idx: return None
    intervals = []
    offsets = np.linspace(-0.08, 0.08, 4)
    for k in sig_idx:
        i,j = valid[k]; x1 = x_pos[i]+offsets[i]-0.01; x2 = x_pos[j]+offsets[j]+0.01
        intervals.append((x1, x2, corr[k], i, j))
    intervals.sort(key=lambda e: (-(e[1]-e[0]), e[0]))
    layers = []
    for x1, x2, p, i, j in intervals:
        placed = False
        for li, layer in enumerate(layers):
            if not any(not (x2 <= lx1 or x1 >= lx2) for lx1,lx2 in layer):
                layer.append((x1,x2)); placed = True; break
        if not placed:
            layers.append([(x1,x2)])
    for li, layer in enumerate(layers):
        for (x1,x2,p,_,_) in [it for it in intervals if any(abs(it[0]-lx1)<1e-3 for lx1,lx2 in layer)]:
            y = y_base + li*step
            star = '***' if p<0.001 else '**' if p<0.01 else '*'
            ax.plot([x1,x1,x2,x2],[y-arm, y, y, y-arm], color='#C44E52', lw=0.9, clip_on=False)
            ax.text((x1+x2)/2, y+0.02, star, ha='center', va='bottom', fontsize=8, fontweight='bold', color='#C44E52')
    return y_base + len(layers)*step


fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9,5))
for ax, col, ylabel in [(ax1, 'μ_crown (μm)', r'$\mu_{\mathrm{crown}}$ (μm)'),
                         (ax2, 'σ_crown (μm)', r'$\sigma_{\mathrm{crown}}$ (μm)')]:
    group_data = [df[df['Group']==g][col].values for g in GROUPS]
    parts = ax.violinplot(group_data, positions=range(4), showmeans=False, showmedians=False,
                          bw_method=0.3, widths=0.50)
    for i, pc in enumerate(parts['bodies']):
        pc.set_facecolor(COLORS[i]); pc.set_edgecolor(COLORS[i]); pc.set_alpha(0.25)
    for i, data in enumerate(group_data):
        if len(data)<4: continue
        q1, med, q3 = np.percentile(data, [25,50,75])
        iqr = q3-q1
        ax.plot([i-0.14, i+0.14], [med, med], color=COLORS[i], lw=1.2, zorder=4)
        ax.plot([i-0.07, i+0.07], [q1, q1], color=COLORS[i], lw=0.5, zorder=4)
        ax.plot([i-0.07, i+0.07], [q3, q3], color=COLORS[i], lw=0.5, zorder=4)
        lower = max(np.min(data), q1-1.5*iqr); upper = min(np.max(data), q3+1.5*iqr)
        ax.plot([i,i], [lower, q1], color=COLORS[i], lw=0.4, zorder=4)
        ax.plot([i,i], [q3, upper], color=COLORS[i], lw=0.4, zorder=4)
        jitter = np.random.uniform(-0.08, 0.08, len(data))
        ax.scatter(np.full(len(data), i)+jitter, data, color=COLORS[i], alpha=0.65, s=20, edgecolors='none', zorder=5)
        m, s = np.mean(data), np.std(data, ddof=1)
        ax.errorbar(i, m, yerr=s, fmt=MARKERS[i], color=COLORS[i], markersize=7,
                    markerfacecolor=COLORS[i], markeredgecolor='white', markeredgewidth=0.6,
                    capsize=2.5, capthick=0.8, elinewidth=0.8, zorder=6)
    vmin, vmax = np.min(np.concatenate(group_data)), np.max(np.concatenate(group_data))
    y_base = vmax + (vmax-vmin)*0.1
    bracket_info = draw_brackets(ax, range(4), group_data, y_base, step=0.5*(vmax-vmin)/max(vmax-vmin,0.5))
    top = bracket_info + 0.2*(vmax-vmin) if bracket_info else vmax + 0.15*(vmax-vmin)
    ax.set_ylim(vmin - 0.08*(vmax-vmin), top)
    ax.set_xticks(range(4)); ax.set_xticklabels(GROUPS, fontsize=8)
    ax.set_ylabel(ylabel, fontsize=9)
    add_label(ax, 'ab'[ax.get_subplotspec().colspan.start])
fig.tight_layout()
fig.savefig(os.path.join(OUTPUT_DIR, 'CrownAccuracy_violin.png'), dpi=600)
fig.savefig(os.path.join(OUTPUT_DIR, 'CrownAccuracy_violin.pdf'))
plt.close(fig)
print("Done.")