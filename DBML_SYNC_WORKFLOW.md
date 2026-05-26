# DBML Synchronization Workflow

## Overview

This document describes how the database schema stays synchronized between three locations:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  SQLite DB    │ ──► │  db.dbml     │ ──► │ dbdiagram.io │
│  (live)       │     │  (GitHub)    │     │  (visual)    │
└──────────────┘     └──────────────┘     └──────────────┘
```

---

## Flow

```
Developer changes schema
        │
        ▼
SQLite database updated (kali_notes.db)
        │
        ├── (manual) npm run dbml:generate
        │         or
        ├── (auto)   pre-commit hook (on git commit)
        │
        ▼
db.dbml regenerated with current schema
        │
        ▼
Commit + Push to GitHub
        │
        ▼
Copy db.dbml contents → dbdiagram.io → visual ERD updated
```

---

## Prerequisites

- Python 3.12+
- Node.js (for npm scripts — optional, Python works directly)
- VS Code with **Noise DBML** or **dbdiagram** extension

---

## Commands

### Generate DBML from the live database

```bash
# Using npm (recommended)
npm run dbml:generate

# Using Python directly
python3 scripts/sqlite2dbml.py backend/db/kali_notes.db -o db.dbml
```

### Generate from a custom database path

```bash
python3 scripts/sqlite2dbml.py /path/to/custom.db -o db.dbml
```

### Validate database connectivity

```bash
npm run dbml:validate
```

### Auto-watch for changes (requires fswatch)

```bash
npm run dbml:watch
```

---

## Git Hook (Automatic)

The pre-commit hook at `.githooks/pre-commit` automatically regenerates `db.dbml` whenever `kali_notes.db` is staged for commit.

**Install the hook:**

```bash
git config core.hooksPath .githooks
```

**How it works:**
1. Detects if `backend/db/kali_notes.db` is in the staged files
2. Runs `sqlite2dbml.py` to regenerate `db.dbml`
3. Stages the updated `db.dbml`
4. Commit proceeds as normal

---

## Syncing with dbdiagram.io

1. Open [dbdiagram.io](https://dbdiagram.io) in your browser
2. Sign in to your account
3. Open your project diagram
4. Replace the entire content of the code panel with the contents of `db.dbml`
5. The visual ERD updates instantly

For a faster workflow using the **VS Code dbdiagram extension**:
1. Install `dbdiagram` extension from the marketplace
2. Open `db.dbml`
3. Log in: `Cmd+Shift+P` → `Login with dbdiagram`
4. The ERD renders directly in VS Code — no copy/paste needed

---

## Generated File: `db.dbml`

- **Auto-generated** — do not edit manually
- **Version-controlled** in GitHub
- Contains: 12 tables, columns, types, PKs, indexes, FK relationships
- Includes logical relationships from the SwiftData model

```dbml
// Notes.ai — Database Schema (auto-generated)
// Source: kali_notes.db
// Generated: 2026-05-26 ...
```

---

## CI/CD Integration

### GitHub Actions (recommended)

```yaml
# .github/workflows/schema-check.yml
name: Schema Check
on:
  push:
    paths:
      - "backend/db/kali_notes.db"
jobs:
  generate-dbml:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Regenerate db.dbml
        run: python3 scripts/sqlite2dbml.py backend/db/kali_notes.db -o db.dbml
      - name: Check for diff
        run: |
          if ! git diff --exit-code db.dbml; then
            echo "❌ db.dbml is out of sync. Run 'npm run dbml:generate' and commit."
            exit 1
          fi
```

### GitLab CI

```yaml
schema-check:
  script:
    - python3 scripts/sqlite2dbml.py backend/db/kali_notes.db -o db.dbml
    - diff db.dbml db.dbml || (echo "Out of sync!" && exit 1)
```

---

## Multi-Developer Collaboration

| Practice | Why |
|----------|-----|
| **Never edit `db.dbml` manually** | It's auto-generated; manual edits get overwritten |
| **Regenerate before committing schema changes** | Ensures `db.dbml` reflects the actual DB |
| **Run `npm run dbml:generate` after pulling** | Syncs local `db.dbml` with any schema changes from teammates |
| **Commit `db.dbml` alongside schema migrations** | Keeps the historical record aligned with the schema at each commit |
| **Review `db.dbml` diff in PRs** | Catches unintended schema changes during code review |

---

## Best Practices

1. **Regenerate frequently** — every time the schema changes
2. **Keep the database file in `.gitignore`** if it contains real data; commit only the `db.dbml`
3. **Use the pre-commit hook** to avoid forgetting
4. **Tag commits** that include schema changes for easier tracking
5. **Document schema migrations** in commit messages referencing the affected tables
