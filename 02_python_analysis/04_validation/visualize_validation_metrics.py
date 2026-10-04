#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File: visualize_validation_metrics.py
Description:
    Generate publication-ready figures and an Excel summary table for validation
    metrics. Boxplots for Dice, Chamfer distance, Hausdorff 95% and area absolute
    difference, grouped by region and comparison type.
    Subplots labelled (a)-(d), x-axis shows region short names (36, F1-F6).

Copyright 2026 Qihang He

Paper step: Appendix Section 3 - validation figures and summary table (Figure S1).
Inputs:  intra_operator_final.csv, inter_operator_final.csv, manual_vs_auto_final.csv,
         overall_comparison_final.csv in OUTPUT_DIR
Outputs: figures/Validation_Metrics_Boxplot.png and .pdf (600 dpi),
         validation_summary.xlsx
Licence: MIT (see LICENSE).
"""

import os, warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter

warnings.filterwarnings('ignore')

# ========== CONFIGURATION ==========
# Path to the directory containing the validation CSV files
# (intra_operator_final.csv, inter_operator_final.csv, manual_vs_auto_final.csv).
# Adjust this to match your project environment.
OUTPUT_DIR = r"./output/validation_results"
FIGURE_DIR = os.path.join(OUTPUT_DIR, 'figures')
os.makedirs(FIGURE_DIR, exist_ok=True)

REGIONS = [
    "F0-base", "36",
    "F1-shoulder", "F2-axial-wall",
    "F3-buccal-cusp-reduction", "F4-lingual-cusp-reduction",
    "F5-buccal-occlusal-surface", "F6-lingual-occlusal-surface"
]
# Short names for x-axis labels
REGION_SHORT = {
    "F0-base": "F0",
    "36": "36",
    "F1-shoulder": "F1",
    "F2-axial-wall": "F2",
    "F3-buccal-cusp-reduction": "F3",
    "F4-lingual-cusp-reduction": "F4",
    "F5-buccal-occlusal-surface": "F5",
    "F6-lingual-occlusal-surface": "F6"
}

METRICS = ['dice', 'mean_distance', 'hausdorff95', 'area_abs_diff']
METRIC_LABELS = {
    'dice': 'Dice coefficient',
    'mean_distance': 'Chamfer distance (mm)',
    'hausdorff95': 'Hausdorff 95% (mm)',
    'area_abs_diff': '|Area difference| (mm\u00b2)'
}

COMPARISONS = ['intra_operator', 'inter_operator', 'manual_vs_auto']
COMP_LABELS = {
    'intra_operator': 'Intra-operator',
    'inter_operator': 'Inter-operator',
    'manual_vs_auto': 'Manual vs Auto'
}
COMP_COLORS = {
    'intra_operator': '#4477AA',
    'inter_operator': '#CC6677',
    'manual_vs_auto': '#44AA66'
}
# ====================================

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
    'axes.unicode_minus': False,
    'figure.dpi': 150,
    'savefig.dpi': 600,
    'savefig.bbox': 'tight',
    'axes.spines.top': False,
    'axes.spines.right': False,
})

def add_label(ax, label):
    """Add sub-panel label (a, b, c, d) at top-left corner."""
    ax.text(0.03, 0.97, label, transform=ax.transAxes, fontsize=14,
            fontweight='bold', va='top', ha='left',
            bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                      edgecolor='none', alpha=0.9))

def load_all_data():
    frames = []
    for comp in COMPARISONS:
        fpath = os.path.join(OUTPUT_DIR, f'{comp}_final.csv')
        if not os.path.exists(fpath):
            print(f"Warning: {fpath} not found.")
            continue
        df = pd.read_csv(fpath)
        if df.empty:
            continue
        df['comparison'] = comp
        frames.append(df)
    if not frames:
        raise FileNotFoundError("No comparison CSV files found.")
    combined = pd.concat(frames, ignore_index=True)
    # Map region names to short names
    combined['region_short'] = combined['region'].map(REGION_SHORT)
    # Ensure proper ordering
    short_order = [REGION_SHORT[r] for r in REGIONS]
    combined['region_short'] = pd.Categorical(combined['region_short'],
                                              categories=short_order,
                                              ordered=True)
    combined['comparison'] = pd.Categorical(combined['comparison'],
                                            categories=COMPARISONS,
                                            ordered=True)
    return combined

def plot_metrics_boxplot(combined):
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    axes = axes.flatten()
    for idx, metric in enumerate(METRICS):
        ax = axes[idx]
        data_plot = combined[['region_short', 'comparison', metric]].dropna()
        # Use region_short for x
        sns.boxplot(data=data_plot, x='region_short', y=metric,
                    hue='comparison', hue_order=COMPARISONS,
                    palette=COMP_COLORS, ax=ax,
                    width=0.7, linewidth=0.8, fliersize=2)
        # Add mean diamond markers
        for icomp, comp in enumerate(COMPARISONS):
            sub = data_plot[data_plot['comparison'] == comp]
            short_order = [REGION_SHORT[r] for r in REGIONS]
            for ireg, reg_short in enumerate(short_order):
                vals = sub[sub['region_short'] == reg_short][metric].values
                if len(vals) > 0:
                    mean_val = np.mean(vals)
                    n_cats = len(COMPARISONS)
                    width_box = 0.7
                    offset = (icomp - (n_cats - 1) / 2) * width_box / n_cats
                    ax.scatter(ireg + offset, mean_val, marker='D', s=25,
                               color='white', edgecolors=COMP_COLORS[comp],
                               linewidth=1.2, zorder=10)
        ax.set_xlabel('Region')
        ax.set_ylabel(METRIC_LABELS[metric])
        ax.legend_.remove()
        # Add sub-panel label (a, b, c, d)
        add_label(ax, chr(ord('a') + idx))
    # Shared legend at bottom
    handles = [plt.Line2D([0], [0], color=COMP_COLORS[comp], linewidth=2,
                          label=COMP_LABELS[comp]) for comp in COMPARISONS]
    fig.legend(handles=handles, loc='lower center', ncol=3, fontsize=12,
               frameon=True, facecolor='white', edgecolor='gray', framealpha=0.9,
               bbox_to_anchor=(0.5, -0.03))
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    fig.savefig(os.path.join(FIGURE_DIR, 'Validation_Metrics_Boxplot.png'), dpi=600)
    fig.savefig(os.path.join(FIGURE_DIR, 'Validation_Metrics_Boxplot.pdf'))
    plt.close(fig)
    print("Boxplot figure saved.")

def generate_excel_summary(combined):
    excel_path = os.path.join(OUTPUT_DIR, 'validation_summary.xlsx')
    writer = pd.ExcelWriter(excel_path, engine='openpyxl')
    # Sheet 1: per-pair data
    combined_sorted = combined.sort_values(['comparison', 'region_short', 'model_id'])
    combined_sorted.to_excel(writer, sheet_name='PerPair', index=False)
    # Sheet 2: summary statistics (using region_short for consistency)
    summary_rows = []
    short_order = [REGION_SHORT[r] for r in REGIONS]
    for comp in COMPARISONS:
        sub = combined_sorted[combined_sorted['comparison'] == comp]
        for reg_short in short_order:
            reg_sub = sub[sub['region_short'] == reg_short]
            if reg_sub.empty:
                continue
            row = {'Comparison': COMP_LABELS[comp], 'Region': reg_short}
            for metric in METRICS:
                vals = reg_sub[metric].values
                if len(vals) > 0:
                    row[f'{metric}_mean'] = np.mean(vals)
                    row[f'{metric}_sd'] = np.std(vals, ddof=1)
                    row[f'{metric}_median'] = np.median(vals)
                else:
                    row[f'{metric}_mean'] = np.nan
                    row[f'{metric}_sd'] = np.nan
                    row[f'{metric}_median'] = np.nan
            summary_rows.append(row)
    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_excel(writer, sheet_name='Summary', index=False)
    # Formatting
    for sheet_name in ['PerPair', 'Summary']:
        ws = writer.sheets[sheet_name]
        for cell in ws[1]:
            cell.font = Font(bold=True)
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = min(max_len + 2, 50)
    writer.close()
    print(f"Excel summary saved to {excel_path}")

def main():
    print("Loading data...")
    combined = load_all_data()
    print(f"Total pairs: {len(combined)}")
    plot_metrics_boxplot(combined)
    generate_excel_summary(combined)
    print("All done.")

if __name__ == "__main__":
    main()