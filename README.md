<div align="center">
  <img src="https://img.shields.io/badge/python-3.12%2B-blue" alt="Python">
  <img src="https://img.shields.io/badge/framework-Flask-red" alt="Flask">
  <img src="https://img.shields.io/badge/database-SQLite-orange" alt="SQLite">
  <br/><br/>
  <h1>⚙️ Notes.ai — Backend</h1>
  <p><strong>Two-server Python architecture · Snapshot sync relay · Read-only data API</strong></p>
</div>

---

## 📋 Table of Contents

- [Architecture Overview](#-architecture-overview)
- [Server Components](#-server-components)
- [API Reference](#-api-reference)
- [Database Schema](#-database-schema)
- [Data Flow](#-data-flow)
- [Deployment](#-deployment)

---

## 🏛️ Architecture Overview

The backend consists of **two independent Python servers** sharing a single SQLite database. The Flask API provides read-only data access for the web frontend, while the Relay Server handles snapshot ingestion from the iOS app and user authentication.

```mermaid
C4Container
  title Backend Architecture — Notes.ai

  System_Boundary(backend, "Backend") {
    Container(flask, "Flask API", "Python / Flask", "Read-only REST API")
    Container(relay, "Relay Server", "Python / http.server", "Sync relay + auth")
    ContainerDb(snapshot, "Snapshot Store", "SQLite", "iPad snapshot (.store) read-only")
    ContainerDb(main_db, "Main Database", "SQLite", "Notes_ai.db — 12 tables")
    Container(scripts, "DB Scripts", "Python", "init, add_user, migrate")
  }

  Rel(flask, snapshot, "Read (:mode=ro)", "GET /api/* endpoints")
  Rel(relay, main_db, "Read/Write", "Snapshot merge + auth queries")
  Rel(flask, main_db, "Read", "User authentication")

  UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

---

## 🖥️ Server Components

### Flask API Server (`app.py`)

| Attribute | Value |
|-----------|-------|
| **Framework** | Flask (Python) |
| **Mode** | Read-only data access |
| **Database Access** | Snapshot `.store` (read-only `:mode=ro`) + `Notes_ai.db` (users) |

Serves as the data gateway for the web frontend and iOS app. All write operations are handled indirectly through the snapshot sync pipeline.

### Relay Server (`relay.py`)

| Attribute | Value |
|-----------|-------|
| **Framework** | `http.server.BaseHTTPRequestHandler` |
| **Mode** | Read-write, sync ingestion |
| **Database Access** | `Notes_ai.db` (full read/write) |

Acts as the write endpoint for the iOS app — receives snapshot uploads, merges data into the main database, and handles authentication.

---

## 🔌 API Reference

### Flask API Endpoints

| Method | Path | Description | Source |
|--------|------|-------------|--------|
| `GET` | `/api/workspaces` | List all workspaces | `ZWORKSPACE` |
| `GET` | `/api/workspaces/<id>/notebooks` | List notebooks in workspace | `ZNOTEBOOK` |
| `GET` | `/api/notebooks/<id>/pages` | List pages in notebook | `ZPAGE` |
| `POST` | `/upload` | Receive `.store` snapshot | — |
| `POST` | `/api/auth/login` | Authenticate user | `users` |
| `GET` | `/api/logs` | Recent traffic log | In-memory ring buffer |
| `GET` | `/private` | Serve private web interface | — |

### Relay Server Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/sync/list` | List available snapshots |
| `GET` | `/api/cloud/workspaces` | Cloud workspace listing |
| `GET` | `/api/sync/download` | Download snapshot file |
| `GET` | `/api/cloud/download` | Download cloud snapshot |
| `GET` | `/api/cloud/metadata` | Health check |
| `POST` | `/api/auth/login` | Authenticate user |
| `POST` | `/api/auth/signup` | Register new user |
| `POST` | `/*` (catch-all) | Save uploaded file, trigger merge |
| `DELETE` | `/api/sync/delete` | Remove snapshot |
| `DELETE` | `/api/cloud/delete` | Remove cloud snapshot |

---

## 🗄️ Database Schema

```mermaid
erDiagram
  ZWORKSPACE ||--o{ ZNOTEBOOK : contains
  ZNOTEBOOK ||--o{ ZPAGE : contains
  ZPAGE ||--o{ ZNOTETEXT : has
  ZPAGE ||--o{ ZNOTEIMAGE : has
  ZPAGE ||--o{ ZAUDIOOBJECT : has
  ZPAGE ||--o{ ZSHAPEOBJECT : has
  ZPAGE ||--o{ ZTABLEOBJECT : has
  ZPAGE ||--o{ ZBROWSEROBJECT : has
  ZPAGE ||--o{ ZAICHATSESSION : has
  ZAICHATSESSION ||--o{ ZAICHATMESSAGE : contains

  ZWORKSPACE {
    int Z_PK "Primary key"
    string ZNAME "Workspace name"
    string ZACCENTCOLOR "UI accent color"
    string ZSERVERID "Server sync ID"
    string ZSYNCSTATUS "Sync state"
    date ZCREATIONDATE "Created timestamp"
    date ZUPDATEDAT "Updated timestamp"
  }

  ZPAGE {
    int Z_PK "Primary key"
    string ZTITLE "Page title"
    string ZCONTENT "Text content"
    blob ZDRAWINGDATA "PencilKit canvas data"
    string ZOCRTEXT "OCR recognized text"
    string ZBACKGROUNDCOLORHEX "Canvas background"
  }

  ZAICHATMESSAGE {
    int Z_PK "Primary key"
    string ZROLE "user / assistant"
    string ZCONTENT "Message body"
    date ZTIMESTAMP "Sent time"
  }
```

### Database Files

| File | Path | Purpose |
|------|------|---------|
| `Notes_ai.db` | `backend/db/` | **Primary database** — 12 tables, all production data |
| `iPad_snapshot.store` | `Sharing/` | Latest iOS snapshot (read-only for Flask API) |

### Utility Scripts

| Script | Path | Purpose |
|--------|------|---------|
| `init_users_db.py` | `backend/db/` | Create `users` table, seed demo user |
| `add_user.py` | `backend/db/` | CLI tool to add/update user accounts |
| `migrate_db.py` | `backend/db/` | Apply schema migrations |

---

## 🔄 Data Flow

```mermaid
sequenceDiagram
    participant iPad as iOS App
    participant Relay as Relay Server
    participant Flask as Flask API
    participant DB as Notes_ai.db

    Note over iPad,DB: Write Path — Snapshot Sync
    iPad->>Relay: POST /upload (.store + .wal + .shm)
    Relay->>Relay: Auto-merge WAL files
    Relay->>DB: merge_snapshot_into_main_db()
    DB->>DB: CREATE IF NOT EXISTS + DELETE + INSERT
    Relay-->>iPad: 200 OK

    Note over iPad,DB: Read Path — Data Access
    Flask->>DB: SELECT * FROM ZWORKSPACE
    DB-->>Flask: rows
    Flask-->>Client: JSON response
```

---

## 🚀 Deployment

```bash
# Start Flask API
python3 backend/app.py

# Start Relay Server
python3 backend/relay.py
```

---

<div align="center">
  <sub>Backend architecture · Notes.ai</sub>
</div>
