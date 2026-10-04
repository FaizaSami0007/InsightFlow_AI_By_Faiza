# HCI + Soft UI Design System

## Design objective

Make analytics understandable, controllable, efficient, and calm. The UI should reduce cognitive load rather than decorate it.

## HCI checklist

### Visibility of status
Processing states show progress, stage, and expected next action.

### Match to real world
Use familiar terms such as Dataset, Filter, Revenue, Region, Date Range, Dashboard.

### User control
Every destructive action is reversible where feasible. AI changes use versioning rather than destructive mutation.

### Consistency
Same interaction patterns for filters, menus, forms, errors, and confirmation.

### Error prevention
Validate before execution; preview destructive operations; constrain AI tools.

### Recognition over recall
Expose current dataset, active filters, selected metric, and current dashboard state.

### Flexibility
Keyboard shortcuts and power-user interactions exist without making the default UI complex.

### Minimalism
Remove decorative elements that do not support interpretation or action.

### Error recovery
Errors explain what happened, what was affected, and what the user can do next.

### Help
Contextual help appears at the point of need.

## Soft UI

Use subtle surfaces and depth:

- white surfaces on cloud background
- 1px borders
- restrained shadow
- 10–14px radii
- no heavy skeuomorphism
- no low-contrast text
- clear focus ring

## Color tokens

| Token | Value | Use |
|---|---|---|
| ink | #172033 | primary text |
| slate | #536176 | secondary text |
| cloud | #F7F9FC | page background |
| surface | #FFFFFF | panels |
| teal | #0F766E | primary action |
| teal-soft | #E6F4F1 | selected state |
| blue | #2563EB | informational interaction |
| amber | #B45309 | warning |
| danger | #B42318 | destructive/error |
| border | #E3E8EF | boundaries |

## Layout

Use an 8px spacing system and a predictable 12-column content grid. Data-heavy screens favor density with whitespace between conceptual groups, not excessive whitespace inside tables.

## Navigation

Primary navigation should remain stable. Do not hide critical navigation behind hover-only interactions.

## Accessibility

- keyboard operability
- visible focus
- semantic HTML
- form labels
- descriptive errors
- sufficient contrast
- reduced-motion support
- chart summaries/accessible alternatives
- screen-reader names for icon buttons

## Responsive behavior

Mobile should not simply shrink desktop. Reflow data tables, convert multi-column dashboards into a prioritized stack, and preserve essential controls.
