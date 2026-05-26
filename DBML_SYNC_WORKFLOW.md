# DBML Synchronization Workflow

## Overview

Fully automated pipeline: **SQLite DB → `db.dbml` → dbdiagram.io (visual ERD)**.

```
┌──────────────┐     ┌──────────────┐     ┌─────────────────────┐
│  SQLite DB    │ ──► │  db.dbml     │ ──► │ dbdiagram.io API    │
│  (live)       │     │  (GitHub)    │     │  (auto on push)     │
└──────────────┘     └──────────────┘     └─────────────────────┘
       ▲                      │                      │
       │                      ▼                      ▼
   Developer              Git commit             Always synced
   changes schema      + GitHub push            visual ERD
```

---

## Setup (One-Time)

### 1. Get a dbdiagram.io API token

1. Sign up for a [dbdiagram.io](https://dbdiagram.io) account (API requires a paid plan)
2. Go to **Settings → API Tokens** and generate a token
3. Copy the token

### 2. Find your diagram ID

1. Open your diagram in dbdiagram.io
2. The URL looks like: `https://dbdiagram.io/d/YourDiagramName-664d69b5f994a43a6264b553`
3. The last segment (`664d69b5f994a43a6264b553`) is your diagram ID

### 3. Configure secrets

**For GitHub Actions (auto-sync on push):**

Add secrets to your repo: **Settings → Secrets and variables → Actions**

| Secret | Value |
|--------|-------|
| `DBDIAGRAM_API_TOKEN` | Your API token |
| `DBDIAGRAM_DIAGRAM_ID` | Your diagram ID (e.g. `664d69b5f994a43a6264b553`) |

**For local use:**

```bash
export DBDIAGRAM_API_TOKEN="your-token"
export DBDIAGRAM_DIAGRAM_ID="your-diagram-id"
```

---

## Flow (Automatic)

```
Developer changes schema
        │
        ▼
SQLite database updated (kali_notes.db)
        │
        ├── (manual) npm run dbml:generate
        │         or
        ├── (auto)   .githooks/pre-commit (on git commit)
        │
        ▼
db.dbml regenerated with current schema
        │
        ▼
git push origin main
        │
        ▼
GitHub Actions (sync-dbdiagram.yml)
        │
        ├── Regenerates db.dbml (double-check)
        ├── Pushes content to dbdiagram.io API
        │
        ▼
dbdiagram.io visual ERD updated  ← always up to date
```

---

## Prerequisites

- Python 3.12+
- Node.js (for npm scripts — optional, Python works directly)
- VS Code with **Noise DBML** or **dbdiagram** extension
- dbdiagram.io account (paid plan for API access)

---

## Commands

### Generate DBML from the live database

```bash
# Using npm (recommended)
npm run dbml:generate

# Using Python directly
python3 scripts/sqlite2dbml.py backend/db/kali_notes.db -o db.dbml
```

### Push to dbdiagram.io (manual one-shot)

```bash
npm run dbml:push
```

Requires environment variables `DBDIAGRAM_API_TOKEN` and `DBDIAGRAM_DIAGRAM_ID`.

### Pull latest database from source repo

```bash
npm run dbml:pull
```

Fetches `kali_notes.db` from `kali0/backend`.

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

## Manual Sync (No API)

If you don't have a paid dbdiagram.io plan, you can still sync manually:

### Option A: Copy/paste

1. Open [dbdiagram.io](https://dbdiagram.io) in your browser
2. Sign in to your account
3. Open your project diagram
4. Replace the entire content of the code panel with `db.dbml`
5. The visual ERD updates instantly

### Option B: VS Code extension

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

### GitHub Actions — Auto-sync dbdiagram.io

```yaml
# .github/workflows/sync-dbdiagram.yml
name: Sync dbdiagram.io
on:
  push:
    branches: [main]
    paths:
      - "db.dbml"
      - "scripts/sqlite2dbml.py"
      - "backend/db/kali_notes.db"
  workflow_dispatch:

jobs:
  push-to-dbdiagram:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Push to dbdiagram.io
        env:
          DBDIAGRAM_API_TOKEN: ${{ secrets.DBDIAGRAM_API_TOKEN }}
          DBDIAGRAM_DIAGRAM_ID: ${{ secrets.DBDIAGRAM_DIAGRAM_ID }}
        run: |
          if [ -z "$DBDIAGRAM_API_TOKEN" ] || [ -z "$DBDIAGRAM_DIAGRAM_ID" ]; then
            echo "⚠️  Skipping — secrets not configured"
            exit 0
          fi
          JSON=$(cat db.dbml | jq -Rs '{name: "Notes.ai Schema", content: .}')
          curl -s -X PUT "https://api.dbdiagram.io/v1/diagrams/${DBDIAGRAM_DIAGRAM_ID}" \
            -H "dbdiagram-access-token: ${DBDIAGRAM_API_TOKEN}" \
            -H "Content-Type: application/json" \
            -d "${JSON}"
```

### GitHub Actions — Schema validation only

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
