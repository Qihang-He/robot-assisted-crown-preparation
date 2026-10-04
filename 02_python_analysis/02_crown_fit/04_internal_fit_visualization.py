#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Internal Fit Visualization

2×1 strip plot with mean±SD for μ_gap and σ_gap per region.
Significance brackets drawn among groups (Bonferroni‑corrected MWU).

Output: PNG (300 dpi) and PDF.

Copyright © 2026 Qihang He
Released under the MIT licence; see LICENSE.

Paper step: internal fit (region-wise group figure).
Inputs:  analysis_results/internal_fit/gap_results.csv
Outputs: analysis_results/internal_fit_visualization/ PNG (300 dpi) and PDF
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
                     'axes.unicode_minus': False, 'figure.dpi': 150, 'savefig.dpi': 300,
                     'savefig.bbox': 'tight', 'axes.spines.top': False, 'axes.spines.right': False})

# ============================ Configuration ============================
DATA_ROOT = r"path/to/your/project/data"

INPUT_DIR = os.path.join(DATA_ROOT, "analysis_results", "internal_fit")
OUTPUT_DIR = os.path.join(DATA_ROOT, "analysis_results", "internal_fit_visualization")
os.makedirs(OUTPUT_DIR, exist_ok=True)

REGIONS = ['36', 'F1-shoulder', 'F2-axial-wall', 'F3-buccal-cusp-reduction',
           'F4-lingual-cusp-reduction', 'F5-buccal-occlusal-surface', 'F6-lingual-occlusal-surface']
RSHORT = {'36':'36', 'F1-shoulder':'F1', 'F2-axial-wall':'F2',
          'F3-buccal-cusp-reduction':'F3', 'F4-lingual-cusp-reduction':'F4',
          'F5-buccal-occlusal-surface':'F5', 'F6-lingual-occlusal-surface':'F6'}
GROUPS = ['G1','G2','G3','G4']
COLORS = ['#a6cee3','#4e79a7','#1b3d6b','#0a1a33']
MARKERS = ['o','s','D','^']

df = pd.read_csv(os.path.join(INPUT_DIR, 'gap_results.csv'))
df['Region'] = pd.Categorical(df['Region'], categories=REGIONS, ordered=True)
df['Group'] = pd.Categorical(df['Group'], categories=GROUPS, ordered=True)


def add_label(ax, label):
    ax.text(0.015, 0.97, label, transform=ax.transAxes, fontsize=12,
            fontweight='bold', va='top', ha='left',
            bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                      edgecolor='none', alpha=0.85))


def pairwise_pvals(df, metric, region):
    sub = df[df['Region']==region]
    g = [sub[sub['Group']==g][metric].values for g in GROUPS]
    _, p_kw = stats.kruskal(*g)
    pairs = list(combinations(range(4),2))
    raw, valid = [], []
    for i,j in pairs:
        if len(g[i])>0 and len(g[j])>0:
            _, p = stats.mannwhitneyu(g[i], g[j], alternative='two-sided')
            raw.append(p); valid.append((i,j))
    if valid:
        corr = np.minimum(np.array(raw)*len(valid), 1.0)
    else: corr = np.array([])
    return p_kw, valid, corr


def draw_brackets(ax, centers, ri, valid, corr, y_base, bl=0.004, step=0.028):
    offsets = np.linspace(-0.3,0.3,4)
    for k, ((i,j), p) in enumerate(zip(valid, corr)):
        if p>=0.05: continue
        star = '***' if p<0.001 else '**' if p<0.01 else '*'
        y = y_base + k*step
        x1 = centers[ri] + offsets[i]; x2 = centers[ri] + offsets[j]
        ax.plot([x1,x1,x2,x2], [y-bl, y, y, y-bl], color='#C44E52', lw=0.9, clip_on=False)
        ax.text((x1+x2)/2, y-0.003, star, ha='center', va='bottom', fontsize=8,
                fontweight='bold', color='#C44E52')


fig, (ax1, ax2) = plt.subplots(2,1,figsize=(12,10))
n_reg = len(REGIONS); spacing = 1.5
centers = np.arange(n_reg)*spacing
offsets = np.linspace(-0.3,0.3,4)
bl = 0.004; step = 0.028

for idx, (ax, metric, ylabel) in enumerate([
        (ax1, 'μ_gap (mm)', r'$\mu_{\mathrm{gap}}$ (mm)'),
        (ax2, 'σ_gap (mm)', r'$\sigma_{\mathrm{gap}}$ (mm)')]):

    all_v = df[metric].values; vmin, vmax = np.min(all_v), np.max(all_v); vr = max(vmax-vmin,0.001)
    max_sig = 0
    for ri in range(n_reg):
        _, vp, pc = pairwise_pvals(df, metric, REGIONS[ri])
        if any(p<0.05 for p in pc): max_sig = max(max_sig, sum(p<0.05 for p in pc))
    y_base = vmax + max(0.002, 0.008*vr)
    if max_sig > 0: top = y_base + max_sig*step + bl + 0.005
    else: top = vmax + 0.03*vr + 0.005
    ax.set_ylim(vmin-0.08*vr, top)

    for ri, reg in enumerate(REGIONS):
        sub = df[df['Region']==reg]; xc = centers[ri]
        for gi, g in enumerate(GROUPS):
            data = sub[sub['Group']==g][metric].values
            if len(data)==0: continue
            xp = xc + offsets[gi]
            jitter = np.random.uniform(-0.08,0.08,len(data))
            ax.scatter(np.full(len(data), xp)+jitter, data, color=COLORS[gi],
                       alpha=0.45, s=12, marker=MARKERS[gi], zorder=3)
            m, s_ = np.mean(data), np.std(data, ddof=1)
            ax.errorbar(xp, m, yerr=s_, fmt=MARKERS[gi], color=COLORS[gi],
                        capsize=2.5, capthick=1.2, markersize=7,
                        markerfacecolor=COLORS[gi], markeredgecolor='white',
                        markeredgewidth=0.8, lw=1.5, zorder=5)
        p_kw, vp, pc = pairwise_pvals(df, metric, reg)
        if p_kw < 0.05 and any(p<0.05 for p in pc):
            draw_brackets(ax, centers, ri, vp, pc, y_base, bl, step)

    ax.set_xticks(centers); ax.set_xticklabels([RSHORT[r] for r in REGIONS])
    ax.set_ylabel(ylabel)
    if vmin<0<vmax: ax.axhline(0, color='gray', ls='--', lw=0.5, alpha=0.5)
    add_label(ax, chr(ord('a') + idx))

# Legend
handles = [plt.Line2D([0],[0], marker=MARKERS[i], color='w',
                      markerfacecolor=COLORS[i], markersize=8,
                      markeredgecolor='white', markeredgewidth=0.5,
                      label=GROUPS[i]) for i in range(4)]
fig.legend(handles=handles, loc='lower center', ncol=4, fontsize=9,
           frameon=True, facecolor='white', edgecolor='#cccccc', framealpha=0.9,
           bbox_to_anchor=(0.5,-0.02))
plt.tight_layout(); fig.subplots_adjust(bottom=0.08)

fig.savefig(os.path.join(OUTPUT_DIR, 'InternalFit_stripplot.png'), dpi=300)
fig.savefig(os.path.join(OUTPUT_DIR, 'InternalFit_stripplot.pdf'))
plt.close(fig); print("PNG and PDF saved.")