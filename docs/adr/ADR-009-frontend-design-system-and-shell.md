# ADR-009: Frontend Soft UI Design System, Accessible Shell, and Centralized API Client

## Status
Accepted (Phase 1)

## Context
A professional analytics platform requires a calm, high-density, accessible UI system that avoids superficial aesthetic trends (neon gradients, excessive glassmorphism) while prioritizing scanability, keyboard accessibility, and predictable user feedback states.

## Decision
1. **Institutional Soft UI & Token System**: Built upon Next.js App Router, TypeScript, and Tailwind CSS. The color palette strictly enforces:
   - Primary Ink: `#172033`
   - Slate: `#536176`
   - Cloud: `#F7F9FC`
   - Surface: `#FFFFFF`
   - Teal (Primary Action / Analytical Accent): `#0F766E`
   - Soft Teal: `#E6F4F1`
   - Blue: `#2563EB`
   - Amber: `#B45309`
   - Danger: `#B42318`
   - Border: `#E3E8EF`
2. **Accessible Responsive AppShell**:
   - Sidebar supports 3 responsive modes: Collapsible Expanded/Compact on Desktop, Compact on Tablet, Drawer/Sheet with backdrop on Mobile.
   - Includes skip-to-content accessible link (`#main-content`) for screen readers and keyboard users.
   - All interactive controls enforce high-visibility focus rings (`ring-2 ring-teal ring-offset-2`).
3. **Reusable Design System Primitives & Global UX States**:
   - UI Primitives: `Button`, `Input`, `Select`, `Card`, `Badge`, `Tooltip`, `Dialog`, `Dropdown`, `Tabs`, `Table`, `Alert`, `Skeleton`.
   - Global UX States: `LoadingState`, `EmptyState`, `ErrorState` (with retry action), `SuccessState`, `ProcessingState` (with stage indicator and progress bar).
4. **Centralized API Client**: All HTTP traffic is channeled through `src/lib/api-client.ts`, handling timeouts, request ID injection, and normalized `ApiError` instances.
5. **State Management**: Zustand handles local UI/shell layout state (`useShellStore`), while TanStack Query manages server caching and invalidation.

## Consequences
- UI components are modular, accessible, and strictly consistent.
- The UI eliminates blank screens through standard loading and error state contracts.
- Ready for rapid vertical integration across upcoming datasets and visualization phases.
