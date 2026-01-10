#!/usr/bin/env python3
"""
PR Manipulation Experiment - Analysis Report Generator

Generates comprehensive analysis with visualizations and markdown report.
"""

import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import json
from pathlib import Path
from scipy import stats

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 11

# Output directory for charts
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

def load_data():
    """Load and prepare data"""
    df = pd.read_csv('data/results.csv')
    return df

def save_figure(filename):
    """Save current figure to output directory"""
    plt.savefig(OUTPUT_DIR / filename, dpi=300, bbox_inches='tight')
    plt.close()

def generate_classification_distribution(df):
    """Generate classification distribution chart"""
    counts = df['classification'].value_counts()
    n = len(df)
    proportions = counts / n * 100

    plt.figure(figsize=(10, 6))
    ax = counts.plot(
        kind='bar',
        color=['#e74c3c', '#f39c12', '#3498db', '#2ecc71']
    )

    # Add percentage labels on bars
    for i, (count, pct) in enumerate(zip(counts, proportions)):
        ax.text(i, count + max(counts) * 0.01, f'{pct:.1f}%',
                ha='center', va='bottom', fontsize=10, fontweight='bold')

    plt.title('Classification Distribution', fontsize=14, fontweight='bold')
    plt.xlabel('Classification', fontsize=12)
    plt.ylabel('Count', fontsize=12)
    plt.xticks(rotation=45)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    save_figure('classification_distribution.png')

def generate_refusal_by_model(df):
    """Generate refusal rate by model chart"""
    refusal_by_model = df.groupby('model')['classification'].apply(
        lambda x: (x == 'refused').sum() / len(x) * 100
    ).sort_values(ascending=True)

    plt.figure(figsize=(10, 6))
    bars = plt.barh(refusal_by_model.index, refusal_by_model.values, color='#e74c3c')

    # Add percentage labels
    for i, (bar, val) in enumerate(zip(bars, refusal_by_model.values)):
        plt.text(val + max(refusal_by_model.values) * 0.02, i, f'{val:.1f}%',
                va='center', fontsize=10, fontweight='bold')

    plt.title('Refusal Rate by Model', fontsize=14, fontweight='bold')
    plt.xlabel('Refusal Rate (%)', fontsize=12)
    plt.ylabel('Model', fontsize=12)
    plt.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    save_figure('refusal_by_model.png')

    return refusal_by_model.sort_values(ascending=False)

def generate_measurement_analysis(df_non_refused):
    """Generate measurement condition analysis chart"""
    measurement_order = ['pending', 'minor', 'moderate', 'severe']

    classification_by_measurement = pd.crosstab(
        df_non_refused['measurement_condition'],
        df_non_refused['classification'],
        normalize='index'
    ) * 100
    classification_by_measurement = classification_by_measurement.reindex(measurement_order)

    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(measurement_order))
    width = 0.25
    classifications = list(classification_by_measurement.columns)
    colors = {'disclosed_accurate': '#2ecc71', 'omitted': '#e74c3c', 'distorted': '#f39c12'}

    for i, classification in enumerate(classifications):
        vals = classification_by_measurement[classification].values
        bars = ax.bar(x + i * width, vals, width, label=classification,
                     color=colors.get(classification, '#95a5a6'))

        # Add percentage labels
        for j, val in enumerate(vals):
            if val > 2:  # Only show label if bar is tall enough
                ax.text(x[j] + i * width, val + 1, f'{val:.1f}%',
                       ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax.set_xlabel('Measurement Condition', fontsize=12)
    ax.set_ylabel('Percentage', fontsize=12)
    ax.set_title('Classification Distribution by Measurement Condition', fontsize=14, fontweight='bold')
    ax.set_xticks(x + width * (len(classifications) - 1) / 2)
    ax.set_xticklabels(measurement_order)
    ax.legend(title='Classification', bbox_to_anchor=(1.05, 1))
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    save_figure('classification_by_measurement.png')

    return classification_by_measurement

def generate_stakes_analysis(df_non_refused):
    """Generate stakes tier analysis chart"""
    stakes_order = ['low', 'medium', 'high']

    classification_by_stakes = pd.crosstab(
        df_non_refused['stakes_tier'],
        df_non_refused['classification'],
        normalize='index'
    ) * 100
    classification_by_stakes = classification_by_stakes.reindex(stakes_order)

    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(stakes_order))
    width = 0.25
    classifications = list(classification_by_stakes.columns)
    colors = {'disclosed_accurate': '#2ecc71', 'omitted': '#e74c3c', 'distorted': '#f39c12'}

    for i, classification in enumerate(classifications):
        vals = classification_by_stakes[classification].values
        bars = ax.bar(x + i * width, vals, width, label=classification,
                     color=colors.get(classification, '#95a5a6'))

        # Add percentage labels
        for j, val in enumerate(vals):
            if val > 2:  # Only show label if bar is tall enough
                ax.text(x[j] + i * width, val + 1, f'{val:.1f}%',
                       ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax.set_xlabel('Stakes Tier', fontsize=12)
    ax.set_ylabel('Percentage', fontsize=12)
    ax.set_title('Classification Distribution by Stakes Tier', fontsize=14, fontweight='bold')
    ax.set_xticks(x + width * (len(classifications) - 1) / 2)
    ax.set_xticklabels(stakes_order)
    ax.legend(title='Classification', bbox_to_anchor=(1.05, 1))
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    save_figure('classification_by_stakes.png')

    return classification_by_stakes

def generate_model_comparison(df):
    """Generate model comparison chart (including refusals)"""
    classification_by_model = pd.crosstab(
        df['model'],
        df['classification'],
        normalize='index'
    ) * 100

    colors = {
        'disclosed_accurate': '#2ecc71',
        'omitted': '#e74c3c',
        'distorted': '#f39c12',
        'refused': '#95a5a6'
    }

    # Ensure consistent color ordering
    cols_order = [c for c in ['disclosed_accurate', 'omitted', 'distorted', 'refused']
                  if c in classification_by_model.columns]
    plot_colors = [colors.get(c, '#95a5a6') for c in cols_order]

    plt.figure(figsize=(10, 6))
    classification_by_model[cols_order].plot(
        kind='barh',
        stacked=True,
        color=plot_colors
    )
    plt.title('Classification Distribution by Model (Including Refusals)', fontsize=14, fontweight='bold')
    plt.xlabel('Percentage', fontsize=12)
    plt.ylabel('Model', fontsize=12)
    plt.legend(title='Classification', bbox_to_anchor=(1.25, 1))
    plt.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    save_figure('classification_by_model.png')

def generate_classification_by_scenario(df_non_refused):
    """Generate classification distribution by scenario chart"""
    scenario_order = ['A', 'B', 'C']

    classification_by_scenario = pd.crosstab(
        df_non_refused['scenario'],
        df_non_refused['classification'],
        normalize='index'
    ) * 100
    classification_by_scenario = classification_by_scenario.reindex(scenario_order)

    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(scenario_order))
    width = 0.25
    classifications = list(classification_by_scenario.columns)
    colors = {'disclosed_accurate': '#2ecc71', 'omitted': '#e74c3c', 'distorted': '#f39c12'}

    for i, classification in enumerate(classifications):
        vals = classification_by_scenario[classification].values
        bars = ax.bar(x + i * width, vals, width, label=classification,
                     color=colors.get(classification, '#95a5a6'))

        # Add percentage labels
        for j, val in enumerate(vals):
            if val > 2:
                ax.text(x[j] + i * width, val + 1, f'{val:.1f}%',
                       ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax.set_xlabel('Scenario', fontsize=12)
    ax.set_ylabel('Percentage', fontsize=12)
    ax.set_title('Classification Distribution by Scenario', fontsize=14, fontweight='bold')
    ax.set_xticks(x + width * (len(classifications) - 1) / 2)
    ax.set_xticklabels(scenario_order)
    ax.legend(title='Classification', bbox_to_anchor=(1.05, 1))
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    save_figure('classification_by_scenario.png')

    return classification_by_scenario

def generate_distortion_heatmap(df_crisis):
    """Generate heatmap for distortion rate by model and measurement condition"""
    measurement_order = ['pending', 'minor', 'moderate', 'severe']

    distortion_rate = df_crisis.groupby(['model', 'measurement_condition']).apply(
        lambda x: (x['classification'] == 'distorted').sum() / len(x) * 100,
        include_groups=False
    ).unstack(fill_value=0)

    distortion_rate = distortion_rate[measurement_order]

    plt.figure(figsize=(10, 6))
    sns.heatmap(
        distortion_rate,
        annot=True,
        fmt='.1f',
        cmap='YlOrRd',
        vmin=0,
        vmax=distortion_rate.max().max() if distortion_rate.max().max() > 0 else 10,
        cbar_kws={'label': 'Distortion Rate (%)'}
    )
    plt.title('Distortion Rate by Model and Measurement Condition', fontsize=14, fontweight='bold')
    plt.xlabel('Measurement Condition', fontsize=12)
    plt.ylabel('Model', fontsize=12)
    plt.tight_layout()
    save_figure('heatmap_distortion.png')

def generate_heatmap_honest_disclosure(df_crisis):
    """Generate heatmap for honest disclosure rate"""
    measurement_order = ['pending', 'minor', 'moderate', 'severe']

    honest_rate = df_crisis.groupby(['model', 'measurement_condition']).apply(
        lambda x: (x['classification'] == 'disclosed_accurate').sum() / len(x) * 100,
        include_groups=False
    ).unstack(fill_value=0)

    honest_rate = honest_rate[measurement_order]

    plt.figure(figsize=(10, 6))
    sns.heatmap(
        honest_rate,
        annot=True,
        fmt='.1f',
        cmap='RdYlGn',
        vmin=0,
        vmax=100,
        cbar_kws={'label': 'Honest Disclosure Rate (%)'}
    )
    plt.title('Honest Disclosure Rate by Model and Measurement Condition', fontsize=14, fontweight='bold')
    plt.xlabel('Measurement Condition', fontsize=12)
    plt.ylabel('Model', fontsize=12)
    plt.tight_layout()
    save_figure('heatmap_honest_disclosure.png')

def generate_heatmap_omission(df_crisis):
    """Generate heatmap for omission rate"""
    stakes_order = ['low', 'medium', 'high']

    omission_rate = df_crisis.groupby(['model', 'stakes_tier']).apply(
        lambda x: (x['classification'] == 'omitted').sum() / len(x) * 100,
        include_groups=False
    ).unstack(fill_value=0)

    omission_rate = omission_rate[stakes_order]

    plt.figure(figsize=(8, 6))
    sns.heatmap(
        omission_rate,
        annot=True,
        fmt='.1f',
        cmap='RdYlGn_r',
        vmin=0,
        vmax=100,
        cbar_kws={'label': 'Omission Rate (%)'}
    )
    plt.title('Omission Rate by Model and Stakes Tier', fontsize=14, fontweight='bold')
    plt.xlabel('Stakes Tier', fontsize=12)
    plt.ylabel('Model', fontsize=12)
    plt.tight_layout()
    save_figure('heatmap_omission.png')

def perform_statistical_tests(df_non_refused):
    """Perform statistical tests"""
    results = {}

    # Chi-square test: Measurement condition vs Classification
    contingency_table = pd.crosstab(
        df_non_refused['measurement_condition'],
        df_non_refused['classification']
    )
    chi2, p_value, dof, expected = stats.chi2_contingency(contingency_table)

    results['measurement_vs_classification'] = {
        'chi2': chi2,
        'p_value': p_value,
        'dof': dof,
        'significant': p_value < 0.05
    }

    # Chi-square test: Stakes tier vs Classification
    contingency_table2 = pd.crosstab(
        df_non_refused['stakes_tier'],
        df_non_refused['classification']
    )
    chi2_2, p_value_2, dof_2, expected_2 = stats.chi2_contingency(contingency_table2)

    results['stakes_vs_classification'] = {
        'chi2': chi2_2,
        'p_value': p_value_2,
        'dof': dof_2,
        'significant': p_value_2 < 0.05
    }

    return results

def generate_markdown_report(df, df_non_refused, df_crisis, refusal_by_model, stat_results):
    """Generate comprehensive markdown report"""
    measurement_order = ['pending', 'minor', 'moderate', 'severe']
    stakes_order = ['low', 'medium', 'high']

    report = []
    report.append("# PR Manipulation Experiment - Analysis Report\n")
    report.append("Analysis and visualization of LLM-generated press releases across measurement conditions and stakes.\n")

    # Research Question
    report.append("## Research Question\n")
    report.append("Do LLMs omit or distort internal test measurements in corporate communications, and does this behavior increase with:\n")
    report.append("1. **Violation severity** (how far above legal limits)\n")
    report.append("2. **Stakes level** (legal exposure, harm, public attention)\n")

    # Dataset Overview
    report.append("## Dataset Overview\n")
    report.append(f"- **Total runs:** {len(df)}\n")
    report.append(f"- **Scenarios:** {df['scenario'].nunique()} ({', '.join(df['scenario'].unique())})\n")
    if 'stakes_tier' in df.columns:
        report.append(f"- **Stakes tiers:** {df['stakes_tier'].nunique()}\n")
    if 'measurement_condition' in df.columns:
        report.append(f"- **Measurement conditions:** {df['measurement_condition'].nunique()}\n")
    report.append(f"- **Models:** {df['model'].nunique()}\n")

    # Overall Classification
    report.append("## Overall Classification Distribution\n")
    report.append(f"![Classification Distribution](classification_distribution.png)\n")
    report.append("\n### Breakdown:\n")
    for classification, count in df['classification'].value_counts().items():
        pct = (count / len(df)) * 100
        report.append(f"- **{classification}:** {count} ({pct:.1f}%)\n")

    # Refusal Analysis
    report.append("## Refusal Analysis\n")
    report.append(f"![Refusal by Model](refusal_by_model.png)\n")
    report.append("\n### Refusal Rate by Model:\n")
    for model, rate in refusal_by_model.items():
        report.append(f"- **{model}:** {rate:.1f}%\n")

    # Measurement Condition Analysis
    report.append("## Violation Severity Analysis\n")
    report.append("How does violation severity affect disclosure behavior?\n")
    report.append(f"![Classification by Measurement](classification_by_measurement.png)\n")

    honest_by_measurement = df_non_refused.groupby('measurement_condition')['classification'].apply(
        lambda x: (x == 'disclosed_accurate').sum() / len(x) * 100
    ).reindex(measurement_order)

    report.append("\n### Honest Disclosure Rate by Violation Severity:\n")
    for condition, rate in honest_by_measurement.items():
        report.append(f"- **{condition}:** {rate:.1f}%\n")

    # Stakes Tier Analysis
    report.append("## Stakes Tier Analysis\n")
    report.append(f"![Classification by Stakes](classification_by_stakes.png)\n")

    honest_by_stakes = df_non_refused.groupby('stakes_tier')['classification'].apply(
        lambda x: (x == 'disclosed_accurate').sum() / len(x) * 100
    ).reindex(stakes_order)

    report.append("\n### Honest Disclosure Rate by Stakes Tier:\n")
    for tier, rate in honest_by_stakes.items():
        report.append(f"- **{tier}:** {rate:.1f}%\n")

    # Scenario Analysis
    report.append("## Scenario Analysis\n")
    report.append(f"![Classification by Scenario](classification_by_scenario.png)\n")

    # Model Comparison
    report.append("## Model Comparison\n")
    report.append(f"![Classification by Model](classification_by_model.png)\n")

    # Heatmaps
    report.append("## Detailed Heatmaps\n")
    report.append("### Honest Disclosure Rate by Model × Measurement Condition\n")
    report.append(f"![Honest Disclosure Heatmap](heatmap_honest_disclosure.png)\n")
    report.append("\n### Omission Rate by Model × Stakes Tier\n")
    report.append(f"![Omission Heatmap](heatmap_omission.png)\n")
    report.append("\n### Distortion Rate by Model × Measurement Condition\n")
    report.append(f"![Distortion Heatmap](heatmap_distortion.png)\n")

    # Statistical Testing
    report.append("## Statistical Testing\n")

    report.append("### Chi-Square Test: Measurement Condition vs Classification\n")
    meas_stat = stat_results['measurement_vs_classification']
    report.append(f"- Chi-square statistic: {meas_stat['chi2']:.4f}\n")
    report.append(f"- P-value: {meas_stat['p_value']:.4f}\n")
    report.append(f"- Degrees of freedom: {meas_stat['dof']}\n")
    report.append(f"- Significant at α=0.05: **{'YES' if meas_stat['significant'] else 'NO'}**\n")

    report.append("\n### Chi-Square Test: Stakes Tier vs Classification\n")
    stakes_stat = stat_results['stakes_vs_classification']
    report.append(f"- Chi-square statistic: {stakes_stat['chi2']:.4f}\n")
    report.append(f"- P-value: {stakes_stat['p_value']:.4f}\n")
    report.append(f"- Degrees of freedom: {stakes_stat['dof']}\n")
    report.append(f"- Significant at α=0.05: **{'YES' if stakes_stat['significant'] else 'NO'}**\n")

    # Key Findings
    report.append("## Key Findings Summary\n")

    total_non_refused = len(df_non_refused)
    honest_rate_overall = (df_non_refused['classification'] == 'disclosed_accurate').sum() / total_non_refused * 100
    omission_rate_overall = (df_non_refused['classification'] == 'omitted').sum() / total_non_refused * 100
    distortion_rate_overall = (df_non_refused['classification'] == 'distorted').sum() / total_non_refused * 100

    report.append("### Overall Behavior (non-refusals):\n")
    report.append(f"- **Honest disclosure:** {honest_rate_overall:.1f}%\n")
    report.append(f"- **Omission:** {omission_rate_overall:.1f}%\n")
    report.append(f"- **Distortion:** {distortion_rate_overall:.1f}%\n")

    # Model rankings
    honest_rates = df_non_refused.groupby('model')['classification'].apply(
        lambda x: (x == 'disclosed_accurate').sum() / len(x) * 100
    )

    report.append("\n### Model Rankings:\n")
    report.append(f"- **Most likely to refuse:** {refusal_by_model.idxmax()} ({refusal_by_model.max():.1f}%)\n")
    report.append(f"- **Least likely to refuse:** {refusal_by_model.idxmin()} ({refusal_by_model.min():.1f}%)\n")
    report.append(f"- **Most honest (when not refusing):** {honest_rates.idxmax()} ({honest_rates.max():.1f}%)\n")
    report.append(f"- **Least honest (when not refusing):** {honest_rates.idxmin()} ({honest_rates.min():.1f}%)\n")

    return '\n'.join(report)

def main():
    """Main execution function"""
    print("Loading data...")
    df = load_data()

    print(f"Loaded {len(df)} total runs")
    print(f"Models: {df['model'].nunique()}")

    # Prepare filtered datasets
    df_crisis = df[df['measurement_condition'].notna()].copy()
    df_non_refused = df_crisis[df_crisis['classification'] != 'refused'].copy()

    print("\nGenerating visualizations...")
    print("  - Classification distribution")
    generate_classification_distribution(df)

    print("  - Refusal analysis")
    refusal_by_model = generate_refusal_by_model(df)

    print("  - Measurement condition analysis")
    generate_measurement_analysis(df_non_refused)

    print("  - Stakes tier analysis")
    generate_stakes_analysis(df_non_refused)

    print("  - Scenario analysis")
    generate_classification_by_scenario(df_non_refused)

    print("  - Model comparison")
    generate_model_comparison(df_crisis)

    print("  - Honest disclosure heatmap")
    generate_heatmap_honest_disclosure(df_crisis)

    print("  - Omission heatmap")
    generate_heatmap_omission(df_crisis)

    print("  - Distortion heatmap")
    generate_distortion_heatmap(df_crisis)

    print("\nPerforming statistical tests...")
    stat_results = perform_statistical_tests(df_non_refused)

    print("\nGenerating markdown report...")
    report = generate_markdown_report(df, df_non_refused, df_crisis, refusal_by_model, stat_results)

    # Save report
    report_path = OUTPUT_DIR / "ANALYSIS_REPORT.md"
    with open(report_path, 'w') as f:
        f.write(report)

    print(f"\nAnalysis complete!")
    print(f"  - Charts saved to: {OUTPUT_DIR}/")
    print(f"  - Report saved to: {report_path}")
    print(f"\nGenerated {len(list(OUTPUT_DIR.glob('*.png')))} charts")

if __name__ == "__main__":
    main()
