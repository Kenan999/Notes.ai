"""
Diagrams — Mermaid diagram definitions for architecture visualization.

All diagrams use Mermaid.js syntax (v11+) and render in GitHub-Flavored
Markdown. Each function returns a string that can be embedded directly
into a .md file.
"""


def system_context_diagram() -> str:
    """System context / C4 Level-1 diagram."""
    return """

## System Context Diagram

```mermaid
C4Context
  title System Context — Notes.ai

  Person(ios_user, "iPad User", "Primary note-taker with Pencil")
  Person(web_user, "Web User", "Read-only browser access")

  System(ios, "iOS App", "Swift/SwiftUI + SwiftData + PencilKit")
  System(backend, "Backend", "Flask API (8005) + Relay (8008)")
  System(frontend, "Web Frontend", "React 18 + Vite")
  System_Ext(ai_providers, "AI Providers", "OpenAI, Anthropic, Gemini, Groq, ...")
  Rel(ios_user, ios, "Draw, type, record")
  Rel(web_user, frontend, "View notes")
  Rel(ios, backend, "HTTPS", "Snapshot upload + auth")
  Rel(frontend, backend, "HTTPS", "Read API (Vite proxy)")
  Rel(ios, ai_providers, "HTTP", "Direct AI inference")
```

"""


def ios_container_diagram() -> str:
    """iOS app container / C4 Level-2 diagram."""
    return """

## iOS App Container Diagram

```mermaid
C4Container
  title iOS App Containers — Notes.ai

  System_Boundary(ios, "iOS App") {
    Container(views, "SwiftUI Views", "SwiftUI", "22 views across 5 groups")
    Container(services, "Services", "Swift", "8 singleton service objects")
    Container(models, "SwiftData Models", "SwiftData", "14 entity classes")
    ContainerDb(store, "SQLite Store", "SwiftData", "On-device persistence")

    Rel(views, services, "→", "Observe via @Published / @Observable")
    Rel(services, models, "→", "CRUD via SwiftData context")
    Rel(models, store, "→", "Persist to SQLite")

    Rel(services, ai_providers, "→", "HTTP inference", $tags="external")
    Rel(services, relay, "→", "Snapshot upload", $tags="external")
  }

  System_Ext(ai_providers, "AI Providers", "OpenAI, Anthropic, ...")
  System_Ext(relay, "Relay Server", "Backend port 8008")
```

"""


def backend_container_diagram() -> str:
    """Backend container / C4 Level-2 diagram."""
    return """

## Backend Container Diagram

```mermaid
C4Container
  title Backend Containers — Notes.ai

  System_Boundary(backend, "Backend") {
    Container(flask, "Flask API", "Python / Flask", "Read-only REST (port 8005)")
    Container(relay, "Relay Server", "Python / http.server", "Sync & auth (port 8008)")
    ContainerDb(snapshot, "Snapshot Store", "SQLite", "iPad snapshot (.store)")
    ContainerDb(main_db, "Main Database", "SQLite", "kali_notes.db — 12 tables")
    Container(scripts, "DB Scripts", "Python", "init, add_user, migrate")

    Rel(flask, snapshot, "→", "Read-only (:mode=ro)")
    Rel(relay, main_db, "→", "Read/write merge + auth")
    Rel(flask, main_db, "→", "Read users table")
    Rel(relay, snapshot, "→", "Creates during merge")
    Rel(scripts, main_db, "→", "Schema management")
  }

  System_Ext(ios, "iOS App", "Snapshot upload + auth")
  System_Ext(frontend, "Web Frontend", "Read API (Vite proxy)")

  Rel(ios, relay, "→", "POST /upload + POST /api/auth/*")
  Rel(frontend, flask, "→", "GET /api/* via proxy")
```

"""


def frontend_container_diagram() -> str:
    """Frontend container / C4 Level-2 diagram."""
    return """

## Frontend Container Diagram

```mermaid
C4Container
  title Web Frontend Containers — Notes.ai

  System_Boundary(frontend, "Web Frontend") {
    Container(shell, "App Shell", "React", "Root state & layout composition")
    Container(lock, "LockScreen", "React", "Password authentication gate")
    Container(sidebar, "Sidebar", "React", "Workspace/notebook navigation tree")
    Container(grid, "PageGrid", "React + framer-motion", "Page card layout")
    Container(ai, "AIPanel", "React + framer-motion", "Slide-in AI chat panel")
    Container(nav, "Navbar", "React", "Top bar with controls")
    Container(traffic, "TrafficMonitor", "React", "Live API log feed")
    Container(settings, "SettingsPanel", "React", "App configuration")
  }

  System_Ext(flask, "Flask API", "Backend port 8005")

  Rel(shell, lock, "→", "Gates access")
  Rel(shell, sidebar, "→", "Passes state")
  Rel(shell, grid, "→", "Passes selected notebook")
  Rel(shell, ai, "→", "Toggles visibility")
  Rel(shell, nav, "→", "Provides control callbacks")
  Rel(sidebar, flask, "→", "GET /api/workspaces & notebooks")
  Rel(grid, flask, "→", "GET /api/notebooks/<id>/pages")
  Rel(traffic, flask, "→", "GET /api/logs (poll every 2s)")
  Rel(nav, ai, "→", "Toggle panel")
```

"""


def sync_sequence_diagram() -> str:
    """Sequence diagram for the snapshot sync flow."""
    return """

## Snapshot Sync Sequence

```mermaid
sequenceDiagram
    participant iPad as iOS App
    participant SM as SyncManager
    participant SD as SwiftData Store
    participant FS as File System
    participant RS as Relay Server
    participant DB as kali_notes.db

    Note over iPad: User creates/edits notes
    SM->>SD: Observe changes
    SM->>FS: exportLiveStoreToSnapshots()
    FS->>SM: .store + .wal + .shm files
    SM->>RS: POST /upload (File-Name header)
    RS->>RS: Save file, rename .store→.sqlite
    RS->>RS: Auto-merge WAL + SHM
    RS->>DB: merge_snapshot_into_main_db(user_id, path)
    DB->>DB: CREATE TABLE IF NOT EXISTS
    DB->>DB: DELETE WHERE server_user_id=?
    DB->>DB: INSERT all rows
    RS->>FS: DELETE snapshot file
    RS-->>SM: 200 OK
    SM->>SM: Update sync status
```

"""


def deployment_diagram() -> str:
    """Deployment / network topology diagram."""
    return """

## Deployment Architecture

```mermaid
graph TB
  subgraph "Home Network"
    subgraph "Server Network"
      FS1["Backend Server<br/>FlaskAPI :8005<br/>RelayServer :8008<br/>kali_notes.db"]
    end
  end

  subgraph "iPadOS"
    IOS["iPad App<br/>SwiftData Store<br/>SyncManager<br/>AIService (actor)"]
  end

  subgraph "Development Machine"
    FE["Vite Dev Server<br/>Proxy /api → :8005<br/>React 18 SPA"]
  end

  IOS -- "Snapshot upload" --> FS1
  IOS -- "Auth" --> FS1
  FE -- "GET /api/*" --> FS1
  IOS -- "Chat completions" --> AI["OpenAI / Anthropic / Gemini / ..."]

  style IOS fill:#7b2ff7,color:#fff
  style FE fill:#2196f3,color:#fff
  style FS1 fill:#4caf50,color:#fff
```

"""


def model_hierarchy_diagram() -> str:
    """SwiftData model entity relationship diagram."""
    return """

## SwiftData Model Hierarchy

```mermaid
erDiagram
  Workspace ||--o{ Notebook : contains
  Notebook ||--o{ Page : contains
  Page ||--o{ NoteImage : has
  Page ||--o{ NoteText : has
  Page ||--o{ AudioObject : has
  Page ||--o{ ShapeObject : has
  Page ||--o{ TableObject : has
  Page ||--o{ BrowserObject : has
  Page ||--o{ AIChatSession : has
  AIChatSession ||--o{ AIChatMessage : contains

  Workspace {
    UUID id
    string name
    string accentColor
    date creationDate
  }
  Notebook {
    UUID id
    string name
    date creationDate
  }
  Page {
    UUID id
    string title
    string content
    string ocrText
    binary drawingData
  }
  AIChatSession {
    UUID id
    string title
    date creationDate
  }
  AIChatMessage {
    UUID id
    string role
    string content
    date timestamp
  }
```

"""
