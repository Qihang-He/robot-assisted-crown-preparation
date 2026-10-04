#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Marginal Gap Visualization

2×2 composite figure for μ_marginal, σ_marginal, P75, IoU_XY.
Bar + scatter + error bars + significance brackets.
600 dpi output.

Copyright © 2026 Qihang He
Released under the MIT licence; see LICENSE.

Paper step: marginal gap (Figure 3 panels).
Inputs:  analysis_results/marginal_gap/marginal_gap_results.csv
Outputs: analysis_results/marginal_gap_visualization/MarginalGap_Composite.png/.pdf
         and pairwise_pvalues_<metric>.csv
Licence: MIT (see LICENSE).
"""

import os, warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from itertools import combinations

warnings.filterwarnings('ignore')
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','Helvetica'],
                     'axes.unicode_minus':False,'figure.dpi':150,'savefig.dpi':600,
                     'savefig.bbox':'tight','axes.spines.top':False,'axes.spines.right':False})

# ============================ Configuration ============================
DATA_ROOT = r"path/to/your/project/data"

INPUT_DIR = os.path.join(DATA_ROOT, "analysis_results", "marginal_gap")
OUTPUT_DIR = os.path.join(DATA_ROOT, "analysis_results", "marginal_gap_visualization")
os.makedirs(OUTPUT_DIR, exist_ok=True)

GROUPS = ['G1','G2','G3','G4']; COLORS = ['#a6cee3','#4e79a7','#1b3d6b','#0a1a33']
METRICS = ['μ_marginal (mm)','σ_marginal (mm)','P75 (mm)','IoU_XY']
LABELS = [r'$\mu_{\mathrm{marginal}}$ (mm)', r'$\sigma_{\mathrm{marginal}}$ (mm)',
          r'$P_{75}$ (mm)', r'$IoU_{XY}$']

df = pd.read_csv(os.path.join(INPUT_DIR, 'marginal_gap_results.csv'))


def pairwise(df, metric):
    gd = [df[df['Group']==g][metric].values for g in GROUPS]
    _, pkw = stats.kruskal(*gd)
    pairs = list(combinations(range(4),2))
    raw = [stats.mannwhitneyu(gd[i], gd[j], alternative='two-sided')[1] for i,j in pairs]
    corr = np.minimum(np.array(raw)*len(pairs),1.0)
    pmat = pd.DataFrame(np.ones((4,4)), index=GROUPS, columns=GROUPS)
    for (i,j), p in zip(pairs, corr): pmat.iloc[i,j]=p; pmat.iloc[j,i]=p
    return pmat, pkw


# Main composite figure
fig, axes = plt.subplots(2,2,figsize=(10,8)); axes_flat = axes.flatten()
x = np.arange(4)
for ax, metric, label in zip(axes_flat, METRICS, LABELS):
    gd = [df[df['Group']==g][metric].values for g in GROUPS]
    means = [np.mean(d) for d in gd]; stds = [np.std(d,ddof=1) for d in gd]
    ax.bar(x, means, yerr=stds, capsize=4, color=[COLORS[i] for i in range(4)], alpha=0.75, edgecolor='white', width=0.6)
    for i, d in enumerate(gd):
        j = np.random.uniform(-0.15,0.15,size=len(d))
        ax.scatter(np.full(len(d),i)+j, d, color=COLORS[i], alpha=0.3, s=15, edgecolors='none', zorder=5)
    pmat, pkw = pairwise(df, metric)
    if pkw < 0.05:
        sig = [(i,j) for i in range(4) for j in range(i+1,4) if pmat.iloc[i,j]<0.05]
        if sig:
            ymax = max(means)+max(stds); ymin = min(means)-max(stds); yr = max(ymax-ymin,0.001)
            by = ymax + 0.05*yr; st = 0.06*yr
            for k,(i,j) in enumerate(sig):
                yl = by + k*st
                ax.plot([x[i],x[i],x[j],x[j]],[yl-st*0.15, yl, yl, yl-st*0.15], color='#C44E52', lw=1.2, clip_on=False)
                ax.text((x[i]+x[j])/2, yl+st*0.1, '*', ha='center', va='bottom', fontsize=11, color='#C44E52', fontweight='bold')
            ax.set_ylim(ymin-0.1*yr, by+len(sig)*st+0.1*yr)
    else:
        ymin = min(means)-max(stds); ymax = max(means)+max(stds)
        ax.set_ylim(ymin-0.2*(ymax-ymin), ymax+0.2*(ymax-ymin))
    ax.set_xticks(x); ax.set_xticklabels(GROUPS); ax.set_ylabel(label); ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.text(0.03,0.96, chr(97+list(axes_flat).index(ax)), transform=ax.transAxes, fontsize=12, fontweight='bold', va='top', ha='left',
            bbox=dict(boxstyle='round,pad=0.1', facecolor='white', edgecolor='none', alpha=0.8))
plt.tight_layout()
fig.savefig(os.path.join(OUTPUT_DIR, 'MarginalGap_Composite.png'), dpi=600)
fig.savefig(os.path.join(OUTPUT_DIR, 'MarginalGap_Composite.pdf'))
plt.close(fig)
print("Composite figure saved.")

# Save pairwise p‑values
for metric in METRICS:
    pmat, _ = pairwise(df, metric)
    pmat.to_csv(os.path.join(OUTPUT_DIR, f'pairwise_pvalues_{metric}.csv'))
print("Pairwise p‑values saved.")