"""
Data Flow — End-to-end data movement descriptions for key scenarios.

Each scenario traces a user action across surfaces, describing how data
moves, transforms, and is persisted at each step.
"""


class SyncCycleFlow:
    """iPad snapshot upload → RelayServer merge → kali_notes.db.

    This is the primary write path — all data originates on the iPad.

    Steps:
        1. SyncManager detects SwiftData store changes.
        2. SyncManager.exportLiveStoreToSnapshots() copies the SwiftData
           store file (default.store) to iPad_snapshot.store, plus its
           .wal and .shm companion files.
        3. SyncManager.uploadFileSilently() sends a POST /upload request
           to the RelayServer with the .store file, setting File-Name header.
        4. RelayServer saves the file to its UPLOAD_DIR, renames .store → .sqlite.
        5. RelayServer auto-merges WAL: if .sqlite-wal exists, forces SQLite
           to merge WAL + SHM into the main .sqlite file.
        6. merge_snapshot_into_main_db() is called with user_id and snapshot path:
           a. For each non-internal table (ZWORKSPACE, ZNOTEBOOK, ZPAGE, etc.):
              - CREATE TABLE IF NOT EXISTS in kali_notes.db
              - DELETE existing rows WHERE server_user_id = user_id
              - INSERT all rows with server_user_id tag
        7. Snapshot file is deleted after successful merge.
        8. kali_notes.db now reflects the latest iPad state.
    """


class ReadAPIFlow:
    """Client reads data through FlaskAPI from the latest snapshot.

    Steps:
        1. Client (frontend or iOS) sends GET request to FlaskAPI endpoint.
        2. FlaskAPI opens iPad_snapshot.store in read-only mode (:mode=ro).
        3. SQLite query is executed against the snapshot tables.
        4. Results are serialized to JSON and returned to the client.
        5. Client renders the data (page grid, notebook tree, etc.).
    """


class AuthFlow:
    """User authentication via RelayServer.

    Steps:
        1. Client sends POST /api/auth/login with email and password.
        2. RelayServer queries the users table in kali_notes.db.
        3. If email + password match, returns {success: true, user: {...}}.
        4. Client stores the user session and navigates to the main app.
        5. On signup: POST /api/auth/signup creates a new user record.
    """


class AIChatFlow:
    """iOS-only AI chat with multi-provider routing.

    Steps:
        1. User opens AI chat on a Page in NoteDetailView.
        2. AIService captures context:
           a. Canvas drawing → composite UIImage (max 1024px).
           b. Vision OCR stream via performLocalOCR.
           c. Notebook/Page metadata from SwiftData models.
        3. AIService reads active provider from AIProviderStore.
        4. AIService routes the request to the correct provider API:
           - OpenAI-compatible: POST /chat/completions
           - Anthropic: POST /v1/messages
           - Gemini: POST /:generateContent
        5. Response is saved as AIChatMessage in the current AIChatSession.
        6. Image generation (optional):
           - Primary: DALL-E 3 via fetchDALLEImage
           - Fallback: Pollinations Flux via fetchPollinationsURL
    """


class SnapshotDownloadFlow:
    """Restore iPad from cloud snapshot.

    Steps:
        1. User navigates to CloudSettingsView in the iOS app.
        2. SyncManager calls GET /api/cloud/workspaces to list snapshots.
        3. User selects a snapshot to restore.
        4. SyncManager calls GET /api/cloud/download?timestamp=&ext=.
        5. RelayServer returns the raw snapshot file.
        6. SyncManager saves and applies the snapshot to the local SwiftData store.
    """


DATA_FLOW_DIAGRAM = """
## End-to-End Data Flow

┌──────────────────────────────────────────────────────────────────────┐
│                           iOS App (iPad)                             │
│                                                                      │
│  ┌──────────────┐     ┌─────────────────┐     ┌──────────────────┐  │
│  │ SwiftData     │────►│ SyncManager     │────►│ POST /upload     │  │
│  │ Store         │     │ exportLiveStore │     │ (.store + WAL)   │  │
│  │ (live)        │     │ toSnapshots()   │     │                  │  │
│  └──────────────┘     └─────────────────┘     └────────┬─────────┘  │
│                                                        │            │
│  ┌──────────────┐     ┌─────────────────┐              │            │
│  │ AIService     │     │ AuthService     │              │            │
│  │ (actor,       │     │ (ObservableObj) │              │            │
│  │ multi-provider)    │ email/password  │              │            │
│  └──────┬───────┘     └────────┬────────┘              │            │
│         │                      │                       │            │
└─────────┼──────────────────────┼───────────────────────┼────────────┘
          │                      │                       │
          │ AI API calls         │ POST /api/auth/login  │ HTTP snapshot
          ▼                      ▼                       ▼
┌──────────────────────────────────────────────────────────────────────┐
│                          Backend                                     │
│                                                                      │
│  ┌──────────────────────┐     ┌──────────────────────────────┐      │
│  │ FlaskAPI               │     │ RelayServer                   │      │
│  │ Read-only GET enpoints│     │ Upload + merge + auth        │      │
│  │ iPad_snapshot.store   │     │ merge_snapshot_into_main_db()│      │
│  └──────────┬───────────┘     └──────────────┬───────────────┘      │
│             │                                │                       │
│             └──────────┬─────────────────────┘                       │
│                        ▼                                             │
│              ┌─────────────────────┐                                 │
│              │  kali_notes.db       │                                 │
│              │  12 tables           │                                 │
│              │  server_user_id tags │                                 │
│              └─────────────────────┘                                 │
└──────────────────────┬───────────────────────────────────────────────┘
                       │
           Vite proxy /api/*
                       ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      Web Frontend                                    │
│  React 18 + Vite + framer-motion + lucide-react                     │
│                                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐    │
│  │ LockScreen│  │ Sidebar  │  │ PageGrid │  │ TrafficMonitor   │    │
│  │ (auth)   │  │ (nav)    │  │ (content)│  │ (polls /api/logs) │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘    │
│  ┌──────────┐  ┌──────────┐                                         │
│  │ AIPanel  │  │ Navbar   │                                         │
│  │ (chat)   │  │ (controls)                                         │
│  └──────────┘  └──────────┘                                         │
└──────────────────────────────────────────────────────────────────────┘
"""
