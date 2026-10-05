# Phase 10: Human-Computer Interaction & Accessibility

## HCI Principles Applied
1. **Visibility of System Status (Nielsen #1)**: Explicit indicators for relationship validation progress, active join paths, and execution times.
2. **Recognition Over Recall (Nielsen #6)**: Visual relationship graphs and candidate suggestions with clear reasons (e.g. "Matching field name 'customer_id' and entity identifier").
3. **Error Prevention (Nielsen #5)**: Strict pre-validation of join keys before federated query execution prevents runtime join failures or Cartesian explosions.
4. **User Control & Freedom (Nielsen #3)**: Manual override controls to Approve, Reject, Disable, or Delete relationships at any time.

## Accessibility Standards (WCAG 2.1 AA)
- Semantic table elements with accessible headers and row IDs.
- High-contrast badge colors for relationship statuses (`VALIDATED`, `PROPOSED`, `DISABLED`, `REJECTED`).
- Full keyboard focus navigation for modals, dropdowns, and buttons.
