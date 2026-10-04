#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Preparation Accuracy Visualization

Produce a 2×2 composite figure:
(a) PSR error (μ_base ± σ_base) per sample (dot + errorbar)
(b) μ_prep raincloud plot with significance stars
(c) σ_prep raincloud plot
(d) R_pos (positive ratio), μ_pos, P75 as grouped bar chart.

All metrics follow the paper notation.
Output: 600 dpi PNG + PDF.

Copyright © 2026 Qihang He
Released under the MIT licence; see LICENSE.

Paper step: main-text preparation accuracy (Figure 2 panels).
Inputs:  analysis_results/preparation_accuracy/PSR_summary.csv, region_results.csv
Outputs: analysis_results/preparation_accuracy_visualization/PreparationAccuracy_2x2.png/.pdf
Licence: MIT (see LICENSE).
"""

import os, warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

warnings.filterwarnings('ignore')

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
    'axes.unicode_minus': False,
    'figure.dpi': 200,
    'savefig.dpi': 600,
    'savefig.bbox': 'tight',
    'axes.spines.top': False,
    'axes.spines.right': False,
})
sns.set_style("whitegrid", {'axes.grid': True, 'grid.linestyle': '--', 'grid.alpha': 0.15})

# ============================ Configuration ============================
DATA_ROOT = r"path/to/your/project/data"

INPUT_DIR = os.path.join(DATA_ROOT, "analysis_results", "preparation_accuracy")
OUTPUT_DIR = os.path.join(DATA_ROOT, "analysis_results", "preparation_accuracy_visualization")
os.makedirs(OUTPUT_DIR, exist_ok=True)

REGIONS = ['36', 'F1-shoulder', 'F2-axial-wall', 'F3-buccal-cusp-reduction',
           'F4-lingual-cusp-reduction', 'F5-buccal-occlusal-surface', 'F6-lingual-occlusal-surface']
RSHORT = {'36':'36', 'F1-shoulder':'F1', 'F2-axial-wall':'F2',
          'F3-buccal-cusp-reduction':'F3', 'F4-lingual-cusp-reduction':'F4',
          'F5-buccal-occlusal-surface':'F5', 'F6-lingual-occlusal-surface':'F6'}
SHORT_ORDER = [RSHORT[r] for r in REGIONS]

COLOR_PSR      = '#4477AA'
COLOR_PREP     = '#CC6677'
COLOR_PREP_LIGHT = '#E8B5B5'
COLOR_STD      = '#44AA66'
COLOR_STD_LIGHT  = '#B5D8B5'
COLOR_DOT      = '#555555'
COLOR_POS_RATIO = '#4477AA'
COLOR_POS_MEAN  = '#DDCC77'
COLOR_P75       = '#AA3377'

# Load data
df_psr = pd.read_csv(os.path.join(INPUT_DIR, 'PSR_summary.csv'))
df = pd.read_csv(os.path.join(INPUT_DIR, 'region_results.csv'))
df['Region'] = pd.Categorical(df['Region'], categories=REGIONS, ordered=True)

# Statistics for one‑sample t‑test
df_stats = []
for reg in REGIONS:
    sub = df[df['Region'] == reg]
    if sub.empty:
        continue
    v = sub['μ_prep (mm)'].values
    if len(v) >= 2:
        t, p = stats.ttest_1samp(v, 0)
        star = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else 'ns'
    else:
        star = ''
    df_stats.append({'RegionShort': RSHORT[reg], 'significance': star})

def add_label(ax, label):
    ax.text(0.03, 0.96, label, transform=ax.transAxes, fontsize=12,
            fontweight='bold', va='top', ha='left',
            bbox=dict(boxstyle='round,pad=0.15', facecolor='white', edgecolor='none', alpha=0.8))

def draw_raincloud(ax, data, x_col, y_col, order, color, color_light, stars=False):
    sns.violinplot(data=data, x=x_col, y=y_col, order=order,
                   color=color_light, alpha=0.65, inner=None,
                   bw_adjust=1.8, cut=0, width=0.65,
                   linewidth=0.8, edgecolor=color, ax=ax)
    sns.stripplot(data=data, x=x_col, y=y_col, order=order,
                  color=COLOR_DOT, alpha=0.35, size=3.5,
                  jitter=0.15, linewidth=0.3, ax=ax)
    sns.boxplot(data=data, x=x_col, y=y_col, order=order,
                width=0.12,
                boxprops={'facecolor': 'none', 'edgecolor': color, 'linewidth': 1.2},
                whiskerprops={'color': color, 'linewidth': 0.8},
                capprops={'color': color, 'linewidth': 0.8},
                medianprops={'color': color, 'linewidth': 2.0, 'solid_capstyle': 'butt'},
                flierprops={'markersize': 3, 'marker': 'o', 'alpha': 0.3}, ax=ax)
    for i, reg in enumerate(order):
        full_reg = [k for k, v in RSHORT.items() if v == reg][0]
        vals = data[data['Region'] == full_reg][y_col].values
        if len(vals):
            ax.scatter(i, np.mean(vals), marker='D', s=35, color='white',
                       edgecolors=color, linewidth=1.2, zorder=6)
    if stars:
        all_vals = data[y_col].values
        y_range = np.ptp(all_vals)
        offset = max(0.003, 0.018 * y_range)
        for i, row in enumerate(df_stats):
            if row['significance'] not in ('', 'ns'):
                vals = data[data['Region'] == REGIONS[i]][y_col].values
                if len(vals) > 0:
                    ax.text(i, np.max(vals) + offset, row['significance'],
                            ha='center', va='bottom', fontsize=10.5,
                            fontweight='bold', color=color)

# Create figure
fig = plt.figure(figsize=(17, 13))

# (a) PSR
ax = fig.add_subplot(2, 2, 1)
dfp = df_psr.sort_values('Sample')
x = np.arange(len(dfp))
ax.errorbar(x, dfp['PSR μ (mm)'], yerr=dfp['PSR σ (mm)'],
            fmt='o', color=COLOR_PSR, capsize=3, capthick=1,
            markersize=5, markerfacecolor=COLOR_PSR,
            markeredgecolor='white', markeredgewidth=0.5,
            linewidth=1, alpha=0.8, zorder=3)
mean_mu = dfp['PSR μ (mm)'].mean()
sd_mu = dfp['PSR μ (mm)'].std(ddof=1)
ax.text(0.97, 0.97,
        rf'$\mu_{{base}}$ = {mean_mu:.4f} ± {sd_mu:.4f} mm',
        transform=ax.transAxes, ha='right', fontsize=8.5,
        bbox=dict(facecolor='white', alpha=0.75, edgecolor='none', pad=3))
ax.set_xticks(x); ax.set_xticklabels(dfp['Sample'], fontsize=7, rotation=45, ha='right')
ax.set_ylabel(r'$\mu_{base} \pm \sigma_{base}$ (mm)', fontsize=10)
ax.axhline(0, color='gray', ls='--', lw=0.6, alpha=0.5)
ax.axhline(mean_mu, color=COLOR_PSR, ls='--', lw=0.8, alpha=0.7)
add_label(ax, 'a')

# (b) μ_prep
ax = fig.add_subplot(2, 2, 2)
df_b = df[['Region', 'μ_prep (mm)']].copy()
df_b['RegionShort'] = df_b['Region'].map(RSHORT)
draw_raincloud(ax, df_b, 'RegionShort', 'μ_prep (mm)', SHORT_ORDER,
               COLOR_PREP, COLOR_PREP_LIGHT, stars=True)
ax.set_ylabel(r'$\mu_{prep}$ (mm)', fontsize=10)
ax.axhline(0, color='gray', ls='--', lw=0.6, alpha=0.5)
add_label(ax, 'b')

# (c) σ_prep
ax = fig.add_subplot(2, 2, 3)
df_c = df[['Region', 'σ_prep (mm)']].copy()
df_c['RegionShort'] = df_c['Region'].map(RSHORT)
draw_raincloud(ax, df_c, 'RegionShort', 'σ_prep (mm)', SHORT_ORDER,
               COLOR_STD, COLOR_STD_LIGHT, stars=False)
ax.set_ylabel(r'$\sigma_{prep}$ (mm)', fontsize=10)
add_label(ax, 'c')

# (d) R_pos, μ_pos, P75
ax = fig.add_subplot(2, 2, 4)
x_pos = np.arange(len(SHORT_ORDER))
w = 0.18
ratio_mean = [df[df['Region']==r]['R_pos (%)'].mean() for r in REGIONS]
ratio_std = [df[df['Region']==r]['R_pos (%)'].std(ddof=1) for r in REGIONS]
ax.bar(x_pos - w, ratio_mean, w, yerr=ratio_std, capsize=2,
       color=COLOR_POS_RATIO, alpha=0.55, edgecolor='white', linewidth=0.3,
       label=r'$R_{pos}$ (%)')
ax.set_ylabel(r'$R_{pos}$ (%)', fontsize=10, color=COLOR_POS_RATIO)
ax.tick_params(axis='y', labelcolor=COLOR_POS_RATIO)
ax.set_ylim(0, 100)

ax2 = ax.twinx()
pos_mean_um = [df[df['Region']==r]['μ_pos (μm)'].mean() for r in REGIONS]
pos_mean_std_um = [df[df['Region']==r]['μ_pos (μm)'].std(ddof=1) for r in REGIONS]
p75_um = [df[df['Region']==r]['P75 (μm)'].mean() for r in REGIONS]
p75_std_um = [df[df['Region']==r]['P75 (μm)'].std(ddof=1) for r in REGIONS]
ax2.bar(x_pos, pos_mean_um, w, yerr=pos_mean_std_um, capsize=2,
        color=COLOR_POS_MEAN, alpha=0.55, edgecolor='white', linewidth=0.3,
        label=r'$\mu_{pos}$ (μm)')
ax2.bar(x_pos + w, p75_um, w, yerr=p75_std_um, capsize=2,
        color=COLOR_P75, alpha=0.55, edgecolor='white', linewidth=0.3,
        label=r'$P_{75}$ (μm)')

all_right = np.concatenate([np.array(pos_mean_um)-np.array(pos_mean_std_um),
                            np.array(pos_mean_um)+np.array(pos_mean_std_um),
                            np.array(p75_um)-np.array(p75_std_um),
                            np.array(p75_um)+np.array(p75_std_um)])
ax2.set_ylim(min(0, np.min(all_right)*1.15), max(0, np.max(all_right)*1.25))
ax2.set_ylabel(r'$\mu_{pos}$ / $P_{75}$ (μm)', fontsize=10, color='#666666')

ax.set_xticks(x_pos); ax.set_xticklabels(SHORT_ORDER)
ax.set_xlim(-0.8, len(SHORT_ORDER)-0.2)
h1, l1 = ax.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1+h2, [r'$R_{pos}$ (%)', r'$\mu_{pos}$ (μm)', r'$P_{75}$ (μm)'],
          loc='upper left', bbox_to_anchor=(0.78, 0.97), fontsize=8,
          frameon=True, facecolor='white', edgecolor='#cccccc', framealpha=0.9)
add_label(ax, 'd')

fig.tight_layout(pad=0.5)
fig.savefig(os.path.join(OUTPUT_DIR, 'PreparationAccuracy_2x2.png'), dpi=600)
fig.savefig(os.path.join(OUTPUT_DIR, 'PreparationAccuracy_2x2.pdf'), dpi=600)
plt.close(fig)
print("Figures saved.")