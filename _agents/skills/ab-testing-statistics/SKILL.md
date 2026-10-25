---
skill_name: A/B Testing & Statistics
description: Design and analyze A/B tests with sample size calculation, significance testing, and Bayesian approaches
category: Data
version: 1.0.0
---

# A/B Testing & Statistics

## Overview
A/B tests measure causal impact. Master sample sizing, statistical significance, and Bayesian methods to make data-driven decisions.

## Sample Size Calculation

### Power Analysis (Frequentist)

```python
from statsmodels.stats.power import tt_ind_solve_power

# Calculate sample size needed
# H0: Control and treatment have same mean
# H1: Treatment has 10% improvement

effect_size = 0.1 / 0.15  # Practical significance
alpha = 0.05  # Type I error (false positive)
beta = 0.2   # Type II error (false negative)
power = 1 - beta  # 0.8 (80% chance to detect true effect)

sample_size = tt_ind_solve_power(
    effect_size=effect_size,
    nobs1=None,  # Solve for sample size
    alpha=alpha,
    power=power,
    ratio=1.0,  # Equal group sizes
    alternative='two-sided'
)

print(f"Sample size needed per group: {int(sample_size)}")
# Output: ~400 per group
```

### Effect Size Estimation

```python
import numpy as np
from scipy import stats

def calculate_effect_size(control, treatment):
    """Calculate Cohen's d"""
    n1, n2 = len(control), len(treatment)
    var1, var2 = np.var(control, ddof=1), np.var(treatment, ddof=1)

    # Pooled standard deviation
    pooled_std = np.sqrt(((n1-1)*var1 + (n2-1)*var2) / (n1+n2-2))

    # Cohen's d
    d = (np.mean(treatment) - np.mean(control)) / pooled_std
    return d

control = [100, 102, 98, 101, 99]  # Control group results
treatment = [105, 107, 104, 108, 106]  # Treatment group results

d = calculate_effect_size(control, treatment)
print(f"Effect size (Cohen's d): {d:.3f}")
# d < 0.2: small effect
# d ~ 0.5: medium effect
# d > 0.8: large effect
```

## Hypothesis Testing

### Two-Sample T-Test

```python
from scipy import stats

# Independent samples
control = np.array([100, 102, 98, 101, 99, 102, 100])
treatment = np.array([105, 107, 104, 108, 106, 109, 107])

# Perform t-test
t_stat, p_value = stats.ttest_ind(control, treatment)

print(f"T-statistic: {t_stat:.3f}")
print(f"P-value: {p_value:.4f}")
print(f"Significant at α=0.05: {p_value < 0.05}")

# Calculate confidence interval
mean_diff = np.mean(treatment) - np.mean(control)
se_diff = np.sqrt(np.var(control, ddof=1)/len(control) + np.var(treatment, ddof=1)/len(treatment))
ci_lower = mean_diff - 1.96 * se_diff
ci_upper = mean_diff + 1.96 * se_diff

print(f"Mean difference: {mean_diff:.3f}")
print(f"95% CI: [{ci_lower:.3f}, {ci_upper:.3f}]")
```

### Chi-Square Test (Categorical)

```python
from scipy.stats import chi2_contingency

# Conversion rates
data = np.array([
    [100, 400],  # Control: 100 converted, 400 didn't
    [130, 370]   # Treatment: 130 converted, 370 didn't
])

chi2, p_value, dof, expected = chi2_contingency(data)

print(f"Chi-square: {chi2:.3f}")
print(f"P-value: {p_value:.4f}")
print(f"Significant: {p_value < 0.05}")

# Conversion rates
control_rate = 100 / 500
treatment_rate = 130 / 500

print(f"Control conversion: {control_rate:.1%}")
print(f"Treatment conversion: {treatment_rate:.1%}")
print(f"Relative lift: {(treatment_rate/control_rate - 1):.1%}")
```

## Bayesian A/B Testing

### Beta-Binomial Model

```python
import numpy as np
from scipy.stats import beta

# Observed data
control_conversions = 100
control_trials = 500
treatment_conversions = 130
treatment_trials = 500

# Prior: Beta(1, 1) = uniform
# Posterior = Beta(alpha + successes, beta + failures)

# Control posterior
control_alpha = 1 + control_conversions
control_beta = 1 + (control_trials - control_conversions)
control_dist = beta(control_alpha, control_beta)

# Treatment posterior
treatment_alpha = 1 + treatment_conversions
treatment_beta = 1 + (treatment_trials - treatment_conversions)
treatment_dist = beta(treatment_alpha, treatment_beta)

# Sample from posteriors
control_samples = control_dist.rvs(size=10000)
treatment_samples = treatment_dist.rvs(size=10000)

# Probability treatment is better
prob_treatment_better = np.mean(treatment_samples > control_samples)

print(f"P(Treatment > Control) = {prob_treatment_better:.3f}")

# Expected loss (regret)
expected_loss = np.mean(np.maximum(control_samples - treatment_samples, 0))
print(f"Expected loss if choose treatment: {expected_loss:.4f}")
```

### Sequential Testing

```python
class SequentialTest:
    def __init__(self, alpha=0.05, beta_error=0.2):
        self.alpha = alpha
        self.beta = beta_error
        self.power = 1 - beta_error

    def log_odds_threshold(self):
        """Sequential probability ratio test threshold"""
        return np.log((1 - self.beta) / self.alpha)

    def update(self, control_conv, control_total, treatment_conv, treatment_total):
        """Calculate log odds ratio"""
        # Likelihood ratio
        lr = (treatment_conv / (treatment_total - treatment_conv)) / (control_conv / (control_total - control_conv))
        log_odds = np.log(lr)

        return log_odds

    def decision(self, log_odds):
        """Make decision based on log odds"""
        threshold = self.log_odds_threshold()

        if log_odds > threshold:
            return "Stop - Treatment wins"
        elif log_odds < -threshold:
            return "Stop - Control wins"
        else:
            return "Continue - Need more samples"

# Example
tester = SequentialTest()
log_odds = tester.update(100, 500, 130, 500)
decision = tester.decision(log_odds)
print(f"Log odds ratio: {log_odds:.3f}")
print(f"Decision: {decision}")
```

## Multiple Testing Correction

### Bonferroni Correction

```python
from scipy.stats import ttest_ind
import pandas as pd

# Testing multiple metrics
metrics = {
    'conversion': (control_conv, treatment_conv),
    'aov': (control_aov, treatment_aov),
    'retention': (control_retention, treatment_retention)
}

alpha = 0.05
adjusted_alpha = alpha / len(metrics)  # Bonferroni

results = []
for metric_name, (control, treatment) in metrics.items():
    t_stat, p_value = ttest_ind(control, treatment)

    results.append({
        'metric': metric_name,
        'p_value': p_value,
        'significant': p_value < adjusted_alpha,
        'adjusted_alpha': adjusted_alpha
    })

results_df = pd.DataFrame(results)
print(results_df)
```

## Test Design Framework

```python
class ABTestFramework:
    def __init__(self, control_size, treatment_size):
        self.control_size = control_size
        self.treatment_size = treatment_size

    def validate_sample_size(self, expected_effect_size, power=0.8):
        """Check if we have enough power"""
        alpha = 0.05
        required_size = tt_ind_solve_power(
            effect_size=expected_effect_size,
            nobs1=None,
            alpha=alpha,
            power=power
        )

        actual_power = tt_ind_solve_power(
            effect_size=expected_effect_size,
            nobs1=self.control_size,
            alpha=alpha,
            power=None
        )

        return {
            'required_size': int(required_size),
            'actual_size': self.control_size,
            'actual_power': actual_power,
            'sufficient': self.control_size >= required_size
        }

    def estimate_duration(self, daily_traffic, control_pct=0.5):
        """Estimate test duration"""
        days_to_control_target = self.control_size / (daily_traffic * control_pct)
        return int(np.ceil(days_to_control_target))

# Example
test = ABTestFramework(control_size=1000, treatment_size=1000)
print(test.validate_sample_size(expected_effect_size=0.1))
print(f"Estimated duration: {test.estimate_duration(daily_traffic=500)} days")
```

## Results Reporting

```python
class ABTestReport:
    def __init__(self, control_conversions, control_total,
                 treatment_conversions, treatment_total):
        self.cc = control_conversions
        self.ct = control_total
        self.tc = treatment_conversions
        self.tt = treatment_total

    def generate_report(self):
        control_rate = self.cc / self.ct
        treatment_rate = self.tc / self.tt

        _, p_value = stats.chi2_contingency(np.array([
            [self.cc, self.ct - self.cc],
            [self.tc, self.tt - self.tc]
        ]))[:2]

        lift = (treatment_rate / control_rate) - 1

        return {
            'control_rate': f"{control_rate:.2%}",
            'treatment_rate': f"{treatment_rate:.2%}",
            'absolute_lift': f"{treatment_rate - control_rate:.2%}",
            'relative_lift': f"{lift:.2%}",
            'p_value': f"{p_value:.4f}",
            'significant_at_0_05': p_value < 0.05,
            'recommendation': 'Launch' if p_value < 0.05 else 'Continue testing'
        }

# Report
report = ABTestReport(100, 500, 130, 500)
for key, value in report.generate_report().items():
    print(f"{key}: {value}")
```

## Production Checklist

- [ ] Calculate required sample size before launching
- [ ] Define success metric and significance level upfront
- [ ] Use appropriate statistical test (t-test, chi-square, etc.)
- [ ] Check for multiple testing issues
- [ ] Monitor for early stopping conditions
- [ ] Document test assumptions and limitations
- [ ] Check for statistical power (aim for 80%+)
- [ ] Report confidence intervals, not just p-values
- [ ] Validate results aren't due to data quality issues
- [ ] Account for seasonality and external factors
- [ ] Use Bayesian methods for sequential testing
- [ ] Report practical significance, not just statistical
