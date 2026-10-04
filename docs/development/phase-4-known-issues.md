# Phase 4 Known Issues & Observations

## 1. Known Issues
- **None**: All 77 automated backend tests, TypeScript type checks, ESLint rules, and Next.js production builds pass with 0 errors and 0 warnings.

## 2. Technical Observations
- In DuckDB 1.5+, `CORR(col1, col2)` performs vectorized Pearson correlation in $\approx 1\text{ms}$.
- Spearman rank correlation via SQL `RANK() OVER (ORDER BY col)` provides exact rank correlation without requiring external SciPy dependencies in runtime pipelines.
