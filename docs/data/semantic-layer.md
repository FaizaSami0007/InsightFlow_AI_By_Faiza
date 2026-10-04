# Semantic Layer

## Why it exists

Raw column names are not sufficient for reliable business analytics.

## Concepts

### Dimension
A categorical/grouping concept such as region, product, or customer segment.

### Measure
A numerical quantity such as revenue, units, cost, or margin.

### Metric
A named business calculation such as gross margin percentage.

### Time dimension
A normalized date/time concept used for trends and comparisons.

## MVP semantic inference

Infer candidates from:
- column type
- name patterns
- value distribution
- units
- date characteristics

Require confirmation when ambiguity is material.

## Future semantic registry

Allow users/admins to define canonical metrics, formulas, units, currency, aggregation rules, and descriptions.
