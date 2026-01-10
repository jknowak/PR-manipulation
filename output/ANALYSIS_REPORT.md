# PR Manipulation Experiment - Analysis Report

Analysis and visualization of LLM-generated press releases across measurement conditions and stakes.

## Research Question

Do LLMs omit or distort internal test measurements in corporate communications, and does this behavior increase with:

1. **Violation severity** (how far above legal limits)

2. **Stakes level** (legal exposure, harm, public attention)

## Dataset Overview

- **Total runs:** 185

- **Scenarios:** 4 (A, B, C, D)

- **Stakes tiers:** 3

- **Measurement conditions:** 4

- **Models:** 5

## Overall Classification Distribution

![Classification Distribution](classification_distribution.png)


### Breakdown:

- **disclosed_accurate:** 103 (55.7%)

- **omitted:** 55 (29.7%)

- **refused:** 20 (10.8%)

- **distorted:** 7 (3.8%)

## Refusal Analysis

![Refusal by Model](refusal_by_model.png)


### Refusal Rate by Model:

- **sonnet:** 54.1%

- **deepseek:** 0.0%

- **gpt4o-mini:** 0.0%

- **grok-4:** 0.0%

- **llama:** 0.0%

## Violation Severity Analysis

How does violation severity affect disclosure behavior?

![Classification by Measurement](classification_by_measurement.png)


### Honest Disclosure Rate by Violation Severity:

- **pending:** 71.4%

- **minor:** 65.0%

- **moderate:** 61.5%

- **severe:** 46.2%

## Stakes Tier Analysis

![Classification by Stakes](classification_by_stakes.png)


### Honest Disclosure Rate by Stakes Tier:

- **low:** 56.4%

- **medium:** 60.4%

- **high:** 67.3%

## Scenario Analysis

![Classification by Scenario](classification_by_scenario.png)

## Model Comparison

![Classification by Model](classification_by_model.png)

## Detailed Heatmaps

### Honest Disclosure Rate by Model × Measurement Condition

![Honest Disclosure Heatmap](heatmap_honest_disclosure.png)


### Omission Rate by Model × Stakes Tier

![Omission Heatmap](heatmap_omission.png)


### Distortion Rate by Model × Measurement Condition

![Distortion Heatmap](heatmap_distortion.png)

## Statistical Testing

### Chi-Square Test: Measurement Condition vs Classification

- Chi-square statistic: 11.8884

- P-value: 0.0645

- Degrees of freedom: 6

- Significant at α=0.05: **NO**


### Chi-Square Test: Stakes Tier vs Classification

- Chi-square statistic: 2.2558

- P-value: 0.6888

- Degrees of freedom: 4

- Significant at α=0.05: **NO**

## Key Findings Summary

### Overall Behavior (non-refusals):

- **Honest disclosure:** 61.3%

- **Omission:** 34.4%

- **Distortion:** 4.4%


### Model Rankings:

- **Most likely to refuse:** sonnet (54.1%)

- **Least likely to refuse:** deepseek (0.0%)

- **Most honest (when not refusing):** deepseek (91.7%)

- **Least honest (when not refusing):** grok-4 (11.1%)
