---
name: frontend-dev-workflow
description: "React/TypeScript/Vite: type-check, lint, test, build, security"
tags: [frontend, react, typescript, vite, testing]
category: development
---

## When to Use
User wants to create, refactor, test, or review frontend code.

## Procedure

### 1. Type Checking
```bash
npx tsc --noEmit
```

### 2. Linting & Formatting
```bash
npm run lint
npm run lint:fix
npm run format || true
```

### 3. Testing
```bash
npm run test:unit || npm run test
npx playwright test || true
```

### 4. Build
```bash
npm run build
```

### 5. Security Scan
```bash
npm audit --audit-level=high
```

## Pitfalls
- Don't ignore TypeScript strict errors
- Don't use `any` without justification
- Don't skip accessibility checks (use axe-core)
- Don't commit node_modules

## Verification
- Type check passes: tsc --noEmit exit code 0
- Build succeeds: npm run build exit code 0
- Tests pass: npm run test exit code 0
- No high/critical npm audit findings
