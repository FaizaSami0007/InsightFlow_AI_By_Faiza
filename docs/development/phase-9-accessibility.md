# Phase 9: Accessibility & Human-Computer Interaction (HCI)

## 1. Compliance Standards

Phase 9 export and sharing features comply with WCAG 2.1 AA and Shneiderman's 8 Golden Rules:

- **Visibility of System Status:** Clear progression indicators during export ("Preparing PDF report...", "Rendering high-resolution snapshot...", "Export ready.").
- **User Control & Freedom:** 1-click modal dismissal via ESC key or backdrop click; cancellation without leaving dirty background jobs.
- **Error Prevention:** Clear warning callouts when generating public share links informing the user about link visibility.
- **Recognition over Recall:** Visual format selector cards with icons, descriptions, and active state rings; automatic copy feedback ("Link copied.").
- **Accessibility:**
  - Keyboard navigation for all modals, inputs, and format toggles.
  - Visible focus rings with high-contrast teal highlights (`focus-visible:ring-2 focus-visible:ring-teal`).
  - Semantic ARIA roles (`role="dialog"`, `aria-modal="true"`, `aria-labelledby`).
  - Tabular fallbacks and textual labels accompanying all chart representations in PDF exports.
