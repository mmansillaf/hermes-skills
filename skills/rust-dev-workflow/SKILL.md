---
name: rust-dev-workflow
description: "Rust development: build, clippy, fmt, audit"
tags: [rust, development, testing, security]
category: development
---

## When to Use
User wants to create, build, test, or review Rust code.

## Procedure

### 1. Build & Check
```bash
cargo check --all-targets --all-features
```

### 2. Format & Lint
```bash
cargo fmt -- --check
cargo clippy --all-targets --all-features -- -D warnings
```

### 3. Testing
```bash
cargo test --all-features
cargo tarpaulin --out Html --out Stdout || true
```

### 4. Security Audit
```bash
cargo audit
cargo outdated || true
```

## Pitfalls
- Don't ignore clippy warnings in new code
- Don't commit Cargo.lock for libraries (DO for binaries)
- Don't use unwrap() in production code without justification

## Verification
- Build succeeds: cargo build exit code 0
- Clippy clean: cargo clippy exit code 0
- All tests pass: cargo test exit code 0
- No audit failures: cargo audit exit code 0
