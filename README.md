<div align="center">
  <img src="https://img.shields.io/badge/react-18-61DAFB" alt="React">
  <img src="https://img.shields.io/badge/bundler-Vite_5-646CFF" alt="Vite">
  <img src="https://img.shields.io/badge/animation-framer--motion-0055FF" alt="framer-motion">
  <img src="https://img.shields.io/badge/icons-lucide--react-yellow" alt="lucide-react">
  <img src="https://img.shields.io/badge/state-local+noproxy-brightgreen" alt="State">
  <br/><br/>
  <h1>🌐 Notes.ai — Web Frontend</h1>
  <p><strong>React 18 single-page application · Read-only note browser · Live traffic monitor</strong></p>
</div>

---

## 📋 Table of Contents

- [Architecture Overview](#-architecture-overview)
- [Component Tree](#-component-tree)
- [State Management](#-state-management)
- [API Integration](#-api-integration)
- [Styling & Animation](#-styling--animation)
- [Getting Started](#-getting-started)

---

## 🏛️ Architecture Overview

The frontend is a **React 18 single-page application** built with Vite. It connects to the Flask backend API via Vite's built-in proxy, providing a read-only browsing experience for notes created on the iPad. All data originates from the iOS app via snapshot sync.

```mermaid
C4Container
  title Frontend Architecture — Notes.ai

  System_Boundary(frontend, "Web Frontend") {
    Container(shell, "App Shell", "React", "Root state & layout composition")
    Container(lock, "LockScreen", "React", "Password authentication gate")
    Container(sidebar, "Sidebar", "React", "Workspace/notebook navigation tree")
    Container(grid, "PageGrid", "React + framer-motion", "Page card layout with hover animations")
    Container(ai, "AIPanel", "React + framer-motion", "Slide-in AI chat panel")
    Container(nav, "Navbar", "React", "Top bar with controls and recording pill")
    Container(traffic, "TrafficMonitor", "React", "Live API log feed (polls every 2s)")
    Container(settings, "SettingsPanel", "React", "App configuration")
  }

  System_Ext(flask, "Flask API", "Backend")

  Rel(shell, lock, "Authentication gate")
  Rel(shell, sidebar, "Passes workspace state")
  Rel(shell, grid, "Passes selected notebook")
  Rel(shell, ai, "Toggles visibility")
  Rel(shell, nav, "Control callbacks")
  Rel(sidebar, flask, "GET /api/workspaces, /api/workspaces/{id}/notebooks")
  Rel(grid, flask, "GET /api/notebooks/{id}/pages")
  Rel(traffic, flask, "GET /api/logs (poll every 2s)")
  Rel(nav, ai, "Open/close panel")
```

---

## 🌳 Component Tree

```mermaid
graph TB
  App[App Shell<br/>Root State] --> LS[LockScreen]
  App --> NB[Navbar]
  App --> SB[Sidebar]
  App --> PG[PageGrid]
  App --> AP[AIPanel]
  App --> TM[TrafficMonitor]
  App --> SP[SettingsPanel]

  SB --> WS[Workspace List]
  SB --> NB_Tree[Notebook Tree]

  PG --> PC[Page Cards<br/>framer-motion hover]

  AP --> AC[AI Chat Interface]
```

### Component Responsibilities

| Component | Role | Key Behaviors |
|-----------|------|---------------|
| **App Shell** | Root orchestrator | Manages lock state, workspace/notebook/page selections; composes all sub-views |
| **LockScreen** | Auth gate | Password input with animated UI feedback; unlocks on correct code |
| **Navbar** | Top toolbar | Settings, tools, recording pill indicator, AI panel toggle |
| **Sidebar** | Navigation tree | Expandable workspace > notebook hierarchy; highlights active selection |
| **PageGrid** | Content display | Card grid with hover animations; loads pages on notebook selection |
| **AIPanel** | AI interface | Slide-in panel with framer-motion; future AI chat interface |
| **TrafficMonitor** | Live feed | Polls `/api/logs` every 2s; scrolling list of recent API traffic |
| **SettingsPanel** | Configuration | Theme, notification, and account settings |

---

## 📊 State Management

The application uses **component-local state** with **prop drilling** from the root App shell. No external state library is required.

```mermaid
stateDiagram-v2
  state "App Shell State" as APP {
    isLocked --> isUnlocked : correct password
    state isUnlocked {
      workspaces --> selectedWorkspace : user clicks
      selectedWorkspace --> notebooks : effect
      selectedNotebook --> pages : effect
    }
  }

  state "Sidebar State" as SB {
    expandedNotebooks
    selectedNotebook
  }

  state "AIPanel State" as AI {
    isAIPanelOpen
  }
```

### State Inventory

| Variable | Type | Initial | Updated By |
|----------|------|---------|------------|
| `isLocked` | `bool` | `true` | LockScreen on correct code |
| `password` | `string` | `""` | LockScreen input |
| `workspaces` | `array` | `[]` | `useEffect` on unlock → fetch |
| `selectedWorkspace` | `string?` | `null` | Sidebar click |
| `notebooks` | `array` | `[]` | `useEffect` on workspace change |
| `selectedNotebook` | `string?` | `null` | Sidebar click |
| `pages` | `array` | `[]` | `useEffect` on notebook change |
| `expandedNotebooks` | `Set` | `new Set()` | Sidebar expand/collapse |
| `isSelectionMode` | `bool` | `false` | Navbar toggle |
| `isSidebarHidden` | `bool` | `false` | Navbar toggle |
| `isAIPanelOpen` | `bool` | `false` | Navbar toggle |

---

## 🔌 API Integration

All API calls are proxied through Vite's dev server to avoid CORS issues in development.

```mermaid
sequenceDiagram
    participant C as React Component
    participant V as Vite Proxy
    participant F as Flask API

    Note over C,F: Page Load Sequence
    C->>V: fetch /api/workspaces
    V->>F: Proxy
    F-->>V: JSON [{id, name}, ...]
    V-->>C: Response

    Note over C,F: Navigation Sequence
    C->>V: fetch /api/workspaces/{id}/notebooks
    V->>F: Proxy
    F-->>C: JSON [{id, title, color}, ...]

    C->>V: fetch /api/notebooks/{id}/pages
    V->>F: Proxy
    F-->>C: JSON [{id, title}, ...]

    Note over C,F: Traffic Monitor
    C->>V: fetch /api/logs (every 2s)
    V->>F: Proxy
    F-->>C: JSON [traffic entries]
```

### Vite Configuration

```js
// vite.config.js
{
  proxy: { "/api": "" },
  plugins: ["@vitejs/plugin-react"],
}
```

### Package Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `react` | 18.x | UI framework |
| `react-dom` | 18.x | DOM rendering |
| `framer-motion` | 11.x | Animations & transitions |
| `lucide-react` | 0.344 | Icon library |
| `vite` | 5.x | Build tool & dev server |
| `@vitejs/plugin-react` | 4.x | React integration |

---

## 🎨 Styling & Animation

| Feature | Implementation |
|---------|---------------|
| **Page Cards** | Grid layout with hover scale/opacity transitions via framer-motion |
| **AIPanel** | Slide-in/out animation with spring physics |
| **LockScreen** | Animated feedback on incorrect attempts |
| **Icons** | lucide-react for all UI icons |
| **Layout** | CSS Flexbox/Grid via index.css |
| **Typography** | System font stack, monospace for traffic monitor |

---

## 🚀 Getting Started

```bash
# Install dependencies
npm install

# Start development server
npm run dev        # → vite --host (default: localhost:5173)

# Build for production
npm run build      # → vite build (outputs to dist/)

# Preview production build
npm run preview    # → vite preview
```

The dev server automatically proxies `/api/*` requests to the Flask backend.

---

<div align="center">
  <sub>Frontend architecture · Notes.ai</sub>
</div>
