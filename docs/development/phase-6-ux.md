# Phase 6: Conversational UX & HCI Architecture

## 1. UX Design Philosophy

The Conversational Analytical Workspace in InsightFlow AI applies Nielsen's 10 Usability Heuristics and Shneiderman's 8 Golden Rules to enterprise data intelligence:

1. **Visibility of System Status**:
   - Live animated indicators during plan generation and tool execution (`Executing analytical plan and grounding response via DuckDB engine...`).
   - Clear badge indicators showing active dataset and pinned version.
2. **Match Between System & Real World**:
   - Plain conversational language ("What region generated the most revenue?").
   - Display formatting (commas, percentages, currency where semantics dictate) without altering exact backend numbers.
3. **User Control & Freedom**:
   - Instant "New Analysis Session" creation without page reloads.
   - Delete session with explicit confirmation modal.
4. **Consistency & Standards**:
   - Soft enterprise color palette (Ink `#172033`, Slate `#536176`, Cloud `#F7F9FC`, Teal `#0F766E`).
   - Shared component patterns with dataset detail tabs.
5. **Error Prevention & Recovery**:
   - Ambiguity dialogs with human-friendly guidance instead of raw HTTP 422 errors.
   - One-click "Retry" button on transient network issues.
6. **Recognition Over Recall**:
   - Dataset-aware Starter Question chips for new sessions.
   - 2–4 Dynamic Suggested Follow-up Question chips after analytical answers.

---

## 2. Evidence & Provenance Panel

Each assistant answer is paired with an expandable analytical evidence card detailing:
- Dataset Name and Version Number
- Deterministic Tool Operations Executed
- Analytical IDs & Safe Parameters
- Data Quality & Missingness Disclaimers
