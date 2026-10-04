# Feature Flags & Release Safety

Experimental features should be behind flags.

Examples:
- ai_dashboard_editing
- semantic_metric_inference
- advanced_visualizations
- external_connectors

Release sequence:

```text
Development
→ Internal validation
→ Small pilot
→ Broader rollout
→ Default
```

A flag must have an owner, purpose, default state, and removal plan.
