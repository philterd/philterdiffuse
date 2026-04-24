# Privacy Budget Management

Differential privacy relies on a "privacy budget," often denoted by epsilon ($\epsilon$). Every time you query data and add noise, a portion of that budget is consumed. To prevent "privacy exhaustion"—where an attacker can reconstruct the original data by averaging multiple queries—Philter Diffuse tracks and limits the total budget spent.

## How it Works

Philter Diffuse tracks the total epsilon spent per collection (or JSON source) in a persistent metadata store.

- **MongoDB Mode**: Spent epsilon is stored in a collection named `privacy_metadata` within the target database.
- **JSON Mode**: Spent epsilon is stored in a local file named `privacy_budget.json`.

## Budget Ceiling

The `--budget-ceiling` option sets the maximum allowed cumulative epsilon for a given source.

If a new query would cause the total spent epsilon to exceed the budget ceiling:

1. The tool will notify the user with a warning.
2. It will apply "infinite noise," effectively zeroing out the results or returning non-useful data.
3. No further accurate information will be released for that specific source until the budget is reset or the ceiling is increased.

## Interpretation of Epsilon

Philter Diffuse provides a qualitative interpretation of the epsilon value to help auditors understand the level of protection:

| Epsilon Range | Protection Strength |
|---------------|---------------------|
| $\epsilon \leq 0.1$ | EXTREME |
| $0.1 < \epsilon \leq 1.0$ | HIGH |
| $1.0 < \epsilon \leq 5.0$ | MODERATE |
| $\epsilon > 5.0$ | LOW (Testing Only) |

Generally, a lower epsilon provides stronger privacy but less accuracy.
