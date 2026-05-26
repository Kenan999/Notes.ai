# Notes.ai — Frontend Architecture

_2026-05-26_

---

## Web Frontend Architecture
### Authentication gate component.

Responsibilities:
    - Present a password entry screen on initial load.
    - Validate against a hardcoded access code.
    - Unlock access to the main application on success.
    - Provide animated UI feedback on incorrect attempts.

State:
    - password: string (input buffer)
    - isLocked: bool (gate state)

Interactions:
    - App.jsx: controls whether LockScreen or main App is rendered.

---

### Workspace and notebook navigation tree.

Responsibilities:
    - Display a collapsible tree of workspaces and notebooks.
    - Track expanded/collapsed state per notebook.
    - Highlight the selected notebook.
    - Load notebooks when a workspace is selected.

State:
    - workspaces: list (fetched from API)
    - notebooks: dict (keyed by workspace ID)
    - expandedNotebooks: Set
    - selectedNotebook: string?

Interactions:
    - App.jsx: communicates selection state for PageGrid updates.
    - FlaskAPI: fetches /api/workspaces and /api/workspaces/<id>/notebooks.

---

### Card layout grid of pages within a notebook.

Responsibilities:
    - Render pages as cards with hover animation (framer-motion).
    - Fetch pages when a notebook is selected from Sidebar.
    - Display page title and metadata on each card.

State:
    - pages: list (fetched from API)
    - selectedNotebook: string? (from Sidebar)

Interactions:
    - App.jsx: positioned as the main content area.
    - FlaskAPI: fetches /api/notebooks/<id>/pages.
    - Sidebar: reads selected notebook from shared state.

---

### Slide-in AI chat panel.

Responsibilities:
    - Toggle visibility via Navbar button.
    - Provide an interface for AI interactions (future use).
    - Animate slide-in/out with framer-motion.

State:
    - isOpen: bool

Interactions:
    - Navbar: toggle button triggers open/close.
    - App.jsx: positioned as an overlay panel.

---

### Top application bar with controls.

Responsibilities:
    - Display settings, tools, recording status, and AI toggle.
    - Render a recording pill indicator.
    - Provide global action buttons.

Interactions:
    - AIPanel: toggle button triggers panel visibility.
    - SettingsPanel: opens settings on click.

---

### Live API traffic feed component.

Responsibilities:
    - Poll the FlaskAPI /api/logs endpoint every 2 seconds.
    - Render a scrolling list of recent API requests.
    - Display method, path, status code, and timestamp.

State:
    - logs: list (fetched periodically)

Interactions:
    - FlaskAPI: polls GET /api/logs.
    - Positioned as a floating overlay or sidebar panel.

---

### Root application component.

Responsibilities:
    - Manage top-level state: lock status, workspace/notebook/page selections.
    - Effect: unlock triggers fetch of /api/workspaces.
    - Effect: workspace change triggers fetch of notebooks.
    - Effect: notebook change triggers fetch of pages.
    - Compose LockScreen, Sidebar, Navbar, PageGrid, AIPanel, TrafficMonitor.

State:
    - isLocked, password
    - workspaces, selectedWorkspace
    - notebooks, selectedNotebook
    - pages
    - expandedNotebooks: Set
    - isSelectionMode, isSidebarHidden, isAIPanelOpen

Interactions:
    - All sub-components: passes state as props or via shared context.
    - FlaskAPI: fetches workspace/notebook/page data.

---

### Application settings interface.

Responsibilities:
    - Provide user-facing configuration options.
    - (Future) manage theme, notification, and account settings.

Interactions:
    - Navbar: triggered from settings button.

---

### Architecture Diagram


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

  System_Ext(flask, "Flask API", "Backend")

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

