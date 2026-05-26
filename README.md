<div align="center">
  <img src="https://img.shields.io/badge/swift-5.9%2B-orange" alt="Swift">
  <img src="https://img.shields.io/badge/framework-SwiftUI-blue" alt="SwiftUI">
  <img src="https://img.shields.io/badge/persistence-SwiftData-purple" alt="SwiftData">
  <img src="https://img.shields.io/badge/canvas-PencilKit-red" alt="PencilKit">
  <img src="https://img.shields.io/badge/architecture-MVVM-brightgreen" alt="MVVM">
  <br/><br/>
  <h1>📱 Notes.ai — iOS App</h1>
  <p><strong>Native iPad application · MVVM + SwiftData + PencilKit · Multi-provider AI</strong></p>
</div>

---

## 📋 Table of Contents

- [Architecture Overview](#-architecture-overview)
- [Model Layer](#-model-layer)
- [Services Layer](#-services-layer)
- [View Layer](#-view-layer)
- [Data Flow](#-data-flow)
- [Design Patterns](#-design-patterns)

---

## 🏛️ Architecture Overview

The iOS app follows **MVVM (Model-View-ViewModel)** with **SwiftData** for persistence and **PencilKit** for freeform canvas drawing. Service classes are implemented as **singletons** observable by SwiftUI via `ObservableObject` or `@Observable`.

```mermaid
C4Container
  title iOS App Architecture — Notes.ai

  System_Boundary(ios, "iOS App") {
    Container(views, "SwiftUI Views", "SwiftUI", "22+ views across 5 groups")
    Container(services, "Services", "Swift", "8 singleton service objects")
    Container(models, "SwiftData Models", "SwiftData", "14 entity classes")
    ContainerDb(store, "SQLite Store", "SwiftData", "On-device persistence")
  }

  Rel(views, services, "Observe via @Published / @Observable")
  Rel(services, models, "CRUD via SwiftData ModelContext")
  Rel(models, store, "Persist to SQLite store")
```

---

## 🧩 Model Layer

14 SwiftData entity classes form the data backbone of the application.

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
    string serverID "Optional"
    string syncStatus
  }

  Notebook {
    UUID id
    string name
    date creationDate
    string serverID "Optional"
    string syncStatus
  }

  Page {
    UUID id
    string title
    string content
    string ocrText
    binary drawingData "PencilKit canvas"
    string backgroundStyle
    string backgroundColorHex
  }

  NoteImage {
    UUID id
    binary data "External storage"
    float x "Position"
    float y
    float width
    float height
    float zIndex
    float opacity
    bool isLocked
  }

  NoteText {
    UUID id
    string text
    float x, y, width, height
    float fontSize
    string colorHex
    bool isLocked
  }

  AudioObject {
    UUID id
    binary data "External storage"
    string transcription
    float duration
    float x, y
    bool isLocked
  }

  ShapeObject {
    UUID id
    string type "circle, rectangle, triangle..."
    float x, y, width, height
    string colorHex
    bool isFilled
    int zIndex
  }

  TableObject {
    UUID id
    int rows
    int cols
    array cellContent "[[String]]"
    float x, y
  }

  BrowserObject {
    UUID id
    string urlString
    string title
    float x, y, width, height
    bool isLocked
  }

  AIChatSession {
    UUID id
    string title
    date creationDate
  }

  AIChatMessage {
    UUID id
    string role "user | assistant"
    string content
    string imageURL "Optional"
    date timestamp
  }
```

### Supporting Types

| Type | Description |
|------|-------------|
| `AIProvider` | Multi-provider configuration (Codable, Identifiable) |
| `ProviderType` | Enum with 12 provider cases (openai, anthropic, gemini, groq, …) |
| `RecordingSource` | Enum: none, session, aiPrompt |
| `OCRResponse` | Codable struct for Vision framework results |
| `SummarizeResponse` | Codable struct for AI summary responses |

---

## 🔧 Services Layer

Eight singleton services encapsulate all business logic:

### SyncManager
```mermaid
graph LR
  A[SyncManager] -->|exportLiveStoreToSnapshots| B[(SwiftData Store)]
  A -->|uploadFileSilently| C[Relay Server :8008]
  A -->|probeServer| D{Server Reachable?}
  A -->|importFromCloud| C
```

Orchestrates the entire sync lifecycle — exports the live SwiftData store to snapshot files, probes for server connectivity, uploads with retry, and downloads cloud snapshots for restore.

### AIService
```mermaid
graph LR
  A[AIService actor] --> B{Provider Router}
  B --> C[OpenAI /chat/completions]
  B --> D[Anthropic /v1/messages]
  B --> E[Gemini /generateContent]
  B --> F[OpenAI-compatible API]
  A --> G[Apple Vision OCR]
  A --> H[DALL-E 3 / Pollinations]
```

A thread-safe actor that routes prompts to the active AI provider, generates images, performs on-device OCR, and assembles context-aware system prompts.

### Service Matrix

| Service | Pattern | Role | Key Dependencies |
|---------|---------|------|------------------|
| **SyncManager** | Singleton @ObservableObject | Sync lifecycle | FileManager, URLSession |
| **AuthService** | Singleton @ObservableObject | Email/password login | URLSession |
| **AIService** | Singleton actor | Multi-provider AI routing | URLSession, Vision |
| **AIProviderStore** | Singleton @MainActor | Provider CRUD, benchmarking | UserDefaults |
| **AudioRecorder** | Singleton @Observable | AVAudioEngine capture | AVFoundation |
| **DrawingSettings** | Singleton @ObservableObject | PencilKit config | PKTool, UIFeedbackGenerator |
| **SecurityService** | Singleton @ObservableObject | FaceID/TouchID lock | LocalAuthentication |
| **TranscriptionService** | Singleton @Observable | Speech-to-text | SFSpeechRecognizer |

---

## 🎨 View Layer

### View Hierarchy

```mermaid
graph TB
  CV[ContentView] --> LS[LoginSheet]
  CV --> NDV[NoteDetailView]
  CV --> AIP[AIProviderSettingsView]
  CV --> AS[AppSettingsSheet]

  NDV --> CV_View[CanvasView<br/>UIViewRepresentable]
  NDV --> NI[NoteImageView]
  NDV --> NT[NoteTextView]
  NDV --> SH[ShapeView]
  NDV --> TB[TableView]
  NDV --> AU[AudioObjectView]
  NDV --> MB[MiniBrowserView]
  NDV --> PS[PageContextSelector]

  AIP --> CPC[CompareProvidersView]
  AIP --> APC[ActiveProviderCard]
  AIP --> PR[ProviderRow]
  AIP --> APS[AddProviderSheet]
  AIP --> EPS[EditProviderSheet]
```

### View Groups

| Group | Views | Purpose |
|-------|-------|---------|
| **Root** | `ContentView` | NavigationSplitView with workspace switcher |
| **Note Editing** | `NoteDetailView`, `CanvasView`, `NoteImageView`, `NoteTextView`, `ShapeView`, `TableView`, `AudioObjectView`, `MiniBrowserView`, `FullScreenImageView`, `RegionSelectorOverlay`, `PageHeaderToolbar`, `PageBackgroundView`, `PageCanvasObjectsLayer` | Full PencilKit canvas with rich object overlays |
| **AI** | `AIProviderSettingsView`, `CompareProvidersView`, `ActiveProviderCard`, `ProviderRow`, `AddProviderSheet`, `EditProviderSheet`, `PageContextSelector`, `AppSettingsSheet` | Multi-provider management and AI chat context |
| **Auth & Settings** | `LoginSheet`, `AccountSettingsView`, `CloudSettingsView`, `PageInfoSheet` | Authentication, sync settings, cloud browsing |
| **Shapes** | `TriangleShape`, `StarShape`, `HexagonShape`, `DiamondShape`, `ArrowShape`, `XYAxisShape`, `XYZAxisShape`, `NumberLineShape`, `ParabolaShape`, `SineWaveShape`, `VectorArrowShape` | Reusable `Shape` protocol implementations |

---

## 🔄 Data Flow

```mermaid
sequenceDiagram
    participant U as User
    participant V as SwiftUI View
    participant S as Service
    participant M as SwiftData Model
    participant B as Backend

    Note over U,B: Note Creation
    U->>V: Draw / type on canvas
    V->>S: Service method call
    S->>M: Save to SwiftData context
    M->>M: Persist to SQLite store

    Note over U,B: Sync
    S->>S: exportLiveStoreToSnapshots()
    S->>B: POST /upload (.store snapshot)
    B->>B: merge_snapshot_into_main_db()

    Note over U,B: AI Chat
    U->>V: Send prompt
    V->>S: sendChatMessage()
    S->>S: Route to active provider
    S-->>V: Stream response
    S->>M: Save AIChatMessage
```

---

## 🧠 Design Patterns

| Pattern | Application |
|---------|-------------|
| **MVVM** | SwiftUI Views observe @Published Services via ObservableObject |
| **Singleton** | All 8 services use shared instance pattern |
| **Actor Isolation** | AIService — thread-safe multi-provider routing |
| **Offline-First** | SwiftData local persistence, syncs when online |
| **Snapshot Sync** | Full SQLite store copy → upload → server merge |
| **Provider Abstraction** | Common interface over 12 AI providers with capability matrix |
| **Repository** | Direct SQLite queries via SwiftData (no separate ORM) |

---

<div align="center">
  <sub>iOS architecture · Notes.ai</sub>
</div>
