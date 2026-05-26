"""
Core System — Top-level architecture overview for Notes.ai.

Describes the three codebase surfaces, their boundaries,
and how they compose to form the full system.
"""

SYSTEM_OVERVIEW = {
    "name": "Notes.ai",
    "description": "Cross-platform AI-powered note-taking system",
    "version": "2.0.0",
    "branches": ["main", "backend", "ios", "frontend"],
    "surfaces": {
        "ios": "Swift/SwiftUI — MVVM with SwiftData + PencilKit",
        "backend": "Flask/Python — API server + sync relay",
        "frontend": "React 18 + Vite — single-page application",
    },
}


class SystemArchitecture:
    """Top-level system descriptor."""

    @staticmethod
    def describe() -> str:
        return """
## System Architecture

Notes.ai is composed of three codebases that form a unified note-taking
platform with offline-first iOS at the center:

┌────────────────────────────────────────────────────────────┐
│                     iOS App (iPad)                          │
│   Swift/SwiftUI — MVVM with SwiftData + PencilKit          │
│                                                            │
│   ┌──────────┐  ┌──────────┐  ┌───────────────────────┐   │
│   │  Views    │  │ Services  │  │  SwiftData Models     │   │
│   │(22 views) │  │ (8 svcs)  │  │  (14 entity classes)  │   │
│   └─────┬────┘  └─────┬────┘  └───────────┬───────────┘   │
│         │              │                   │               │
│         └──────┬───────┴───────────────────┘               │
│                │                                           │
│                │  SQLite snapshot (.store file)             │
└────────────────┼───────────────────────────────────────────┘
                 │
                 │ HTTP POST /upload (snapshot sync)
                 │ HTTP GET /api/* (read-only data access)
                 │ HTTP POST /api/auth/* (authentication)
                 ▼
┌────────────────────────────────────────────────────────────┐
│                      Backend                                │
│   Flask/Python — Two-server architecture                    │
│                                                            │
│   ┌─────────────────┐      ┌──────────────────────┐        │
│   │  Flask API       │      │  Relay Server         │       │
  │   │                  │      │                       │       │
│   │  Read-only data  │      │  Snapshot ingest      │       │
│   │  GET endpoints   │      │  Auth endpoints       │       │
│   └────────┬────────┘      └───────────┬──────────┘        │
│            │                           │                   │
│            └───────────┬───────────────┘                   │
│                        ▼                                   │
│              ┌──────────────────┐                          │
│              │   SQLite (kali_notes.db) — 12 tables        │
│              └──────────────────┘                          │
└──────────────┼─────────────────────────────────────────────┘
               │
               │ Vite proxy /api/*
               ▼
┌────────────────────────────────────────────────────────────┐
│                   Web Frontend                              │
│   React 18 + Vite — Single-page application                │
│                                                            │
│   ┌──────────┐  ┌──────────┐  ┌───────────────────────┐   │
│   │ LockScreen│  │  Sidebar  │  │  PageGrid / AIPanel   │   │
│   │  Auth     │  │ Navigation│  │  + TrafficMonitor     │   │
│   └──────────┘  └──────────┘  └───────────────────────┘   │
└────────────────────────────────────────────────────────────┘
"""


class DeploymentBoundaries:
    """Describes deployment targets for each surface."""

    BOUNDARIES = {
        "ios": {
            "deployment": "Xcode project (Kali Notes.xcodeproj), iPadOS target",
            "language": "Swift 5.9+",
            "framework": "SwiftUI + SwiftData",
            "sync": "SQLite snapshot upload (export live store → HTTP POST)",
            "auth": "Email/password (custom), biometric (FaceID/TouchID)",
        },
        "backend": {
            "deployment": "Python scripts on private server",
            "language": "Python 3.x",
            "servers": ["Flask API", "Relay Server"],
            "database": "SQLite (kali_notes.db) — 12 tables",
            "protocols": ["HTTP REST", "SQLite direct access"],
        },
        "frontend": {
            "deployment": "Vite dev server / static build",
            "language": "JavaScript (JSX, React 18)",
            "bundler": "Vite 5",
            "dependencies": ["framer-motion", "lucide-react"],
        },
    }
