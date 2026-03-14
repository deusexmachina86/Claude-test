# Swingset Project — Implementation Plan

## 1. Application Choice and Rationale

The recommended application is a **web-based swingset playground simulator** — a browser tool that lets users design a backyard swingset by selecting components (frame, swings, slide, climbing wall, etc.), configure dimensions and materials, and see a live 3D preview with a bill-of-materials cost estimate.

The application has three primary user-facing concerns:

1. **Designer** — canvas to position and configure components.
2. **Inspector** — a sidebar showing selected component properties (material, dimensions, weight capacity).
3. **BOM panel** — a real-time bill of materials listing lumber cuts, hardware, and estimated cost.

---

## 2. Technology Stack

| Layer | Choice |
|---|---|
| Language | TypeScript 5.x |
| Framework | React 18 |
| Canvas / 3D | react-three-fiber + Three.js |
| State | Zustand |
| Styling | Tailwind CSS |
| Build | Vite 5 |
| Testing | Vitest + React Testing Library |
| Linting | ESLint + eslint-config-airbnb-typescript |
| Formatting | Prettier |

No backend in Phase 1 — all state lives in memory and localStorage.

---

## 3. Project Structure

```
/home/user/Claude-test/
├── CLAUDE.md
├── plan.md
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
│   │   │   ├── SwingsetCanvas.tsx
│   │   │   ├── Frame.tsx
│   │   │   ├── Swing.tsx
│   │   │   ├── Slide.tsx
│   │   │   └── ClimbingWall.tsx
│   │   ├── inspector/
│   │   │   ├── Inspector.tsx
│   │   │   ├── DimensionInput.tsx
│   │   │   └── MaterialSelect.tsx
│   │   └── bom/
│   │       ├── BomPanel.tsx
│   │       └── BomRow.tsx
│   ├── store/
│   │   ├── designStore.ts
│   │   └── bomStore.ts
│   ├── lib/
│   │   ├── geometry.ts
│   │   ├── bom.ts
│   │   └── pricing.ts
│   ├── types/
│   │   └── swingset.ts
│   └── constants/
│       └── defaults.ts
└── tests/
    ├── lib/
    │   ├── geometry.test.ts
    │   ├── bom.test.ts
    │   └── pricing.test.ts
    └── components/
        ├── Inspector.test.tsx
        └── BomPanel.test.tsx
```

---

## 4. Core Types (`src/types/swingset.ts`)

- `ComponentKind` — `'frame' | 'swing' | 'slide' | 'climbingWall'`
- `Material` — `'pressure-treated-pine' | 'cedar' | 'galvanized-steel'`
- `SwingsetComponent` — `{ id, kind, position, dimensions, material }`
- `DesignState` — `{ components: SwingsetComponent[]; selectedId: string | null }`
- `BomItem` — `{ description, quantity, unit, unitCost, totalCost }`

---

## 5. Implementation Steps

### Phase 0 — Repository Bootstrap
1. Initialise `package.json`, install runtime and dev dependencies.
2. Create `tsconfig.json`, `vite.config.ts`, `tailwind.config.ts`, ESLint/Prettier configs.
3. Add `scripts`: `dev`, `build`, `preview`, `test`, `lint`, `format`.
4. Create `index.html` entry point.
5. Commit: `chore: bootstrap project with Vite, React, TypeScript`

### Phase 1 — Types and Core Logic
1. Write `src/types/swingset.ts` and `src/constants/defaults.ts`.
2. Write pure functions in `src/lib/`: `geometry.ts`, `pricing.ts`, `bom.ts`.
3. Write unit tests for all three `lib/` modules.
4. Commit: `feat(lib): add geometry, bom, and pricing pure functions with tests`

### Phase 2 — State Management
1. Write `src/store/designStore.ts` with Zustand + `persist` middleware.
2. Write `src/store/bomStore.ts` as a derived selector.
3. Commit: `feat(store): add design and BOM Zustand stores`

### Phase 3 — 3D Canvas
1. Write `SwingsetCanvas.tsx` with react-three-fiber `<Canvas>` and `OrbitControls`.
2. Write mesh components for each `ComponentKind`.
3. Add an "Add Component" toolbar.
4. Commit: `feat(canvas): add 3D swingset canvas`

### Phase 4 — Inspector Sidebar
1. Write `Inspector.tsx`, `DimensionInput.tsx`, `MaterialSelect.tsx`.
2. Add RTL tests for Inspector.
3. Commit: `feat(inspector): add component inspector sidebar`

### Phase 5 — Bill of Materials Panel
1. Write `BomPanel.tsx` and `BomRow.tsx` with CSV export.
2. Add RTL tests for BomPanel.
3. Commit: `feat(bom): add bill of materials panel with CSV export`

### Phase 6 — Layout Assembly
1. Write `src/App.tsx` composing all three panels.
2. Add "Reset Design" button.
3. Smoke test with `npm run dev`.
4. Commit: `feat(app): assemble full layout and add reset action`

### Phase 7 — CI Setup
1. Create `.github/workflows/ci.yml`: lint, test, build on Node 20 / ubuntu-latest.
2. Commit: `chore(ci): add GitHub Actions CI workflow`

### Phase 8 — CLAUDE.md Update
1. Update `CLAUDE.md` with actual project overview, structure, and commands.
2. Commit: `docs: update CLAUDE.md to reflect actual project structure`

---

## 6. Testing Approach

### Unit Tests (Vitest)
- `geometry.ts`: bounding box computation, overlap detection.
- `bom.ts`: correct line items for a known design.
- `pricing.ts`: correct total cost for a known BOM.

### Component Tests (Vitest + RTL)
- `Inspector`: empty state, populated state, `updateComponent` called on input change.
- `BomPanel`: correct total, CSV download triggered.

### Commands
```bash
npm test            # watch mode
npm test -- --run   # CI single pass
npm test -- --coverage
```

Target: 80% coverage on `src/lib/`.

---

## 7. Key Decisions

- **Zustand over Redux**: less boilerplate for a single-page tool; avoids premature abstraction.
- **Three.js / react-three-fiber over SVG**: 3D perspective is more intuitive for spatial layout of a physical structure.
- **No backend**: localStorage is sufficient for Phase 1; store architecture allows a REST layer to be added later without structural changes.
- **Vite over Next.js**: no SSR requirements; simpler, faster dev experience, static bundle deployable to any CDN.

---

## 8. Risk Register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Three.js learning curve slows canvas work | Medium | Use `@react-three/drei` helpers to avoid raw Three.js boilerplate |
| BOM logic becomes complex for irregular lumber cuts | Medium | Scope Phase 1 to standard-length boards |
| Mobile layout degrades with three-panel layout | Low | Tailwind responsive breakpoints; collapse panels on small screens |
| Vite build breaks on Three.js tree shaking | Low | Pin Three.js to known-good minor version; add to `optimizeDeps` if needed |
