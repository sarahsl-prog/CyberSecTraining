# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

An accessible, educational cybersecurity tool for learning network security through real network scanning and interactive scenarios.

## Tech Stack

- **Frontend**: React + TypeScript + Radix UI + Cytoscape.js
- **Desktop**: Tauri
- **Backend**: Python FastAPI + SQLAlchemy
- **Database**: SQLite

## Development Commands

### Frontend
```bash
cd frontend
npm install          # Install dependencies
npm run dev          # Start dev server (http://localhost:1420)
npm run build        # Build for production
npm run lint         # Run ESLint
npm run test         # Run tests with Vitest
npm run tauri dev    # Run Tauri desktop app in dev mode
npm run tauri build  # Build Tauri desktop app
```

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

uvicorn app.main:app --reload  # Start API server (http://localhost:8000)
pytest                          # Run tests
black app tests                 # Format code
```

## Architecture

### Frontend Structure
```
frontend/src/
├── components/
│   ├── common/         # Reusable UI (Button, Modal, etc.)
│   ├── layout/         # Header, Sidebar, MainLayout
│   ├── network/        # Network visualization
│   └── accessibility/  # A11y controls
├── context/            # React Context (AccessibilityContext, ThemeContext)
├── hooks/              # Custom hooks
├── pages/              # Route components
├── services/           # API clients
└── styles/themes/      # CSS themes (light, dark, colorblind modes)
```

### Backend Structure
```
backend/app/
├── api/routes/         # FastAPI endpoints
├── models/             # SQLAlchemy models
├── services/
│   ├── datastore/      # Data abstraction layer (critical for multi-user)
│   ├── scanner/        # Network scanning
│   ├── vulnerability/  # Vulnerability detection
│   └── llm/            # LLM routing
└── db/                 # Database session/init
```

### Critical Abstractions

**DataStore (`backend/app/services/datastore/base.py`)**: Abstract interface for user data. All data operations go through this. `LocalDataStore` uses SQLite; future `RemoteDataStore` enables multi-user.

**AccessibilityContext (`frontend/src/context/AccessibilityContext.tsx`)**: Global accessibility state. All components consume this for color mode, font size, motion preferences.

## Key Patterns

### Accessibility (WCAG 2.1 AA)
- All interactive elements: min 44x44px touch targets
- Color modes: light, dark, high-contrast, protanopia, deuteranopia, tritanopia
- Skip links, focus management, screen reader announcements
- Never rely solely on color to convey information

### Network Scanning Safety
- Only private networks: 10.x, 192.168.x, 172.16-31.x
- User must confirm network ownership
- All scans are audit logged

### LLM Routing
Fallback chain: Ollama (local) → Hosted API → Static knowledge base

## Database Schema

SQLite tables: `devices`, `vulnerabilities`, `scans`, `topology`, `progress`, `preferences`

## Content Packs

```
packs/
├── core/               # Vulnerability definitions (20 types)
├── home-basics/        # Pack 1: Home Network Basics
└── small-office/       # Pack 2: Small Office Security
```

## Design Documents

- `CyberSec-Teaching-Tool-Design-Doc.md` - Full architecture
- `CyberSec-Tool-UserFlow-Diagrams.md` - User flow diagrams
