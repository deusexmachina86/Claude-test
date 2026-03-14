# Baby Cradle Project — Implementation Plan

## 1. Application Choice and Rationale

The recommended application is a **web-based baby cradle designer and configurator** — a browser tool that lets users design a custom baby cradle by selecting styles (traditional rocker, convertible crib, bassinet), configuring dimensions and materials, and viewing a live 3D preview with a bill of materials and safety checklist.

The application has four primary user-facing concerns:

1. **Designer** — 3D canvas to configure and preview the cradle.
2. **Inspector** — sidebar for component properties (material, dimensions, finish).
3. **Safety Checklist** — real-time panel validating compliance with CPSC/ASTM safety standards (slat spacing, mattress fit, weight limits).
4. **BOM Panel** — bill of materials with lumber cuts, hardware, and cost estimate; CSV export.

---

## 2. Technology Stack

| Layer | Choice |
|---|---|
| Language | TypeScript 5.x |
| Framework | React 18 |
| Canvas / 3D | react-three-fiber + Three.js |
| State | Zustand (+ localStorage persist) |
| Styling | Tailwind CSS |
| Build | Vite 5 |
| Testing | Vitest + React Testing Library |
| Linting | ESLint + eslint-config-airbnb-typescript |
| Formatting | Prettier |

No backend in Phase 1.

---

## 3. Project Structure

```
/home/user/Claude-test/
├── CLAUDE.md
├── plan.md                        # Swingset plan (previous)
├── plan-cradle.md                 # This document
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.ts
├── .eslintrc.cjs
├── .prettierrc
├── index.html
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── components/
│   │   ├── canvas/
│   │   │   ├── CradleCanvas.tsx   # react-three-fiber scene root
│   │   │   ├── Frame.tsx          # Side rails and end panels
│   │   │   ├── Slats.tsx          # Vertical slats
│   │   │   ├── Mattress.tsx       # Mattress platform mesh
│   │   │   └── Rocker.tsx         # Rocker base (optional)
│   │   ├── inspector/
│   │   │   ├── Inspector.tsx
│   │   │   ├── DimensionInput.tsx
│   │   │   ├── MaterialSelect.tsx
│   │   │   └── StyleSelect.tsx    # Rocker / Stationary / Convertible
│   │   ├── safety/
│   │   │   ├── SafetyPanel.tsx    # Checklist panel
│   │   │   └── SafetyRule.tsx     # Single rule with pass/fail indicator
│   │   └── bom/
│   │       ├── BomPanel.tsx
│   │       └── BomRow.tsx
│   ├── store/
│   │   ├── designStore.ts
│   │   └── bomStore.ts
│   ├── lib/
│   │   ├── geometry.ts            # Bounding boxes, fit checks
│   │   ├── safety.ts              # CPSC/ASTM rule evaluations (pure functions)
│   │   ├── bom.ts                 # BOM computation from design state
│   │   └── pricing.ts             # Material unit costs
│   ├── types/
│   │   └── cradle.ts              # Core type contracts
│   └── constants/
│       └── defaults.ts            # Default dimensions, safety thresholds
└── tests/
    ├── lib/
    │   ├── geometry.test.ts
    │   ├── safety.test.ts
    │   ├── bom.test.ts
    │   └── pricing.test.ts
    └── components/
        ├── Inspector.test.tsx
        ├── SafetyPanel.test.tsx
        └── BomPanel.test.tsx
```

---

## 4. Core Types (`src/types/cradle.ts`)

- `CradleStyle` — `'rocker' | 'stationary' | 'convertible'`
- `Material` — `'maple' | 'cherry' | 'pine' | 'birch-plywood'`
- `Finish` — `'natural-oil' | 'non-toxic-paint' | 'beeswax'`
- `CradleDesign` — `{ id, style, dimensions, material, finish, slatCount }`
- `SafetyResult` — `{ rule: string; passed: boolean; detail: string }`
- `BomItem` — `{ description, quantity, unit, unitCost, totalCost }`

---

## 5. Safety Rules (`src/lib/safety.ts`)

All rules are pure functions that take a `CradleDesign` and return a `SafetyResult`.

| Rule | Standard | Threshold |
|---|---|---|
| Slat spacing | CPSC 16 CFR 1219 | ≤ 2⅜ in (60 mm) |
| Interior length | ASTM F2194 | 900–1000 mm |
| Interior width | ASTM F2194 | 380–580 mm |
| Mattress gap (sides) | CPSC | ≤ 25 mm on each side |
| Mattress gap (ends) | CPSC | ≤ 25 mm on each end |
| Side rail height | ASTM F2194 | ≥ 150 mm above mattress |
| Weight capacity label | CPSC | Must be specified |

These rules have no side effects and are fully unit-testable.

---

## 6. Implementation Steps

### Phase 0 — Repository Bootstrap
1. Initialise `package.json`, install runtime and dev dependencies.
2. Create `tsconfig.json`, `vite.config.ts`, `tailwind.config.ts`, ESLint/Prettier configs.
3. Add npm scripts: `dev`, `build`, `preview`, `test`, `lint`, `format`.
4. Create `index.html` entry point with `<div id="root">`.
5. Commit: `chore: bootstrap project with Vite, React, TypeScript`

### Phase 1 — Types and Core Logic
1. Write `src/types/cradle.ts` and `src/constants/defaults.ts`.
2. Write pure functions in `src/lib/`: `geometry.ts`, `safety.ts`, `bom.ts`, `pricing.ts`.
3. Write unit tests for all four `lib/` modules (target: 80% coverage on `src/lib/`).
4. Commit: `feat(lib): add geometry, safety, bom, and pricing pure functions with tests`

### Phase 2 — State Management
1. Write `src/store/designStore.ts` with Zustand + `persist` middleware.
   - Actions: `updateStyle`, `updateDimensions`, `updateMaterial`, `updateFinish`, `updateSlatCount`, `reset`.
2. Write `src/store/bomStore.ts` as a derived selector calling `computeBom`.
3. Commit: `feat(store): add cradle design and BOM Zustand stores`

### Phase 3 — 3D Canvas
1. Write `CradleCanvas.tsx` with react-three-fiber `<Canvas>`, `OrbitControls`, and ground plane.
2. Write mesh components: `Frame.tsx` (side rails + end panels), `Slats.tsx` (array of vertical slats computed from `slatCount` and spacing), `Mattress.tsx`, `Rocker.tsx` (conditionally rendered).
3. Animate the rocker with a gentle sinusoidal tilt when `style === 'rocker'` using `useFrame`.
4. Commit: `feat(canvas): add 3D cradle canvas with rocker animation`

### Phase 4 — Inspector Sidebar
1. Write `Inspector.tsx`, `DimensionInput.tsx`, `MaterialSelect.tsx`, `StyleSelect.tsx`.
2. All inputs call design store actions on change.
3. Add RTL tests for Inspector covering each control.
4. Commit: `feat(inspector): add cradle inspector sidebar`

### Phase 5 — Safety Checklist Panel
1. Write `SafetyPanel.tsx` that reads `designStore` state, runs all safety rules, and renders `SafetyRule` rows.
2. Write `SafetyRule.tsx` — a row with a green check / red X icon, rule name, and detail message.
3. Display a summary badge: "All checks passed" (green) or "N issues found" (red).
4. Add RTL tests for `SafetyPanel` covering pass and fail states.
5. Commit: `feat(safety): add real-time safety checklist panel`

### Phase 6 — Bill of Materials Panel
1. Write `BomPanel.tsx` with total cost summary and `BomRow` for each line item.
2. Add "Download CSV" button.
3. Add RTL tests.
4. Commit: `feat(bom): add bill of materials panel with CSV export`

### Phase 7 — Layout Assembly
1. Write `App.tsx`: toolbar at top, canvas centre, inspector right, safety + BOM panels in a tabbed bottom drawer.
2. Add "Reset Design" button.
3. Smoke test with `npm run dev`.
4. Commit: `feat(app): assemble full cradle designer layout`

### Phase 8 — CI and Docs
1. Create `.github/workflows/ci.yml`: lint, test, build on Node 20 / ubuntu-latest.
2. Update `CLAUDE.md` with project overview, structure, and commands.
3. Commit: `chore(ci): add CI workflow` and `docs: update CLAUDE.md`

---

## 7. Testing Approach

### Unit Tests (Vitest)
- `geometry.ts`: mattress fit gap calculations.
- `safety.ts`: each rule returns `passed: true` for compliant inputs and `passed: false` with a descriptive detail for non-compliant inputs.
- `bom.ts`: correct lumber list for a known design.
- `pricing.ts`: correct total for a known BOM.

### Component Tests (Vitest + RTL)
- `Inspector`: each control renders and calls the correct store action.
- `SafetyPanel`: shows green summary when all rules pass; shows red badge and failing rule details when a rule fails.
- `BomPanel`: correct total; CSV download triggered.

### Commands
```bash
npm test            # watch mode
npm test -- --run   # CI single pass
npm test -- --coverage
```

---

## 8. Key Decisions

- **Safety panel added vs. swingset plan**: baby furniture has well-defined regulatory standards (CPSC, ASTM F2194); modelling these as pure, testable functions adds genuine value and differentiates this tool.
- **Rocker animation**: a gentle `useFrame` sinusoidal tilt makes the 3D preview more engaging and immediately communicates the rocker style to users. It is toggled off for stationary/convertible styles.
- **`slatCount` as a first-class design parameter**: slat spacing is a critical safety dimension, so it is derived from interior width and slat count rather than entered directly, preventing users from inadvertently setting unsafe spacing.
- **Tabbed bottom drawer**: BOM and Safety panels share the bottom area via tabs, keeping the layout clean on smaller screens without losing either panel.

---

## 9. Risk Register

| Risk | Likelihood | Mitigation |
|---|---|---|
| ASTM F2194 threshold values need verification | Medium | Hardcode known values from public CPSC/ASTM summaries; note in code that a legal review is needed before production use |
| Rocker animation performance on low-end devices | Low | Use `requestAnimationFrame` budget in `useFrame`; disable animation via a user toggle |
| Slat mesh count causes render slowdown (many slats) | Low | Merge slat geometries with `InstancedMesh` if slat count exceeds 20 |
| Mobile layout degrades with complex panel arrangement | Low | Tailwind responsive breakpoints; stack panels vertically on small screens |
