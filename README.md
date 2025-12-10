# CyberSec Teaching Tool

An accessible, educational cybersecurity tool for learning network security through real network scanning and interactive scenarios.

## Features

- **Real Network Scanning** - Scan your home network to discover devices and vulnerabilities
- **Interactive Scenarios** - Learn through guided practice scenarios
- **LLM-Powered Explanations** - Get AI-assisted explanations tailored to your knowledge level
- **Accessibility-First** - WCAG 2.1 AA compliant with full screen reader support

## Tech Stack

- **Frontend**: React + TypeScript + Radix UI
- **Desktop**: Tauri
- **Backend**: Python FastAPI
- **Database**: SQLite
- **Visualization**: Cytoscape.js

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.9+
- Rust (for Tauri)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/CyberSecTraining.git
cd CyberSecTraining
```

2. Set up the backend:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up the frontend:
```bash
cd frontend
npm install
```

4. Copy environment file:
```bash
cp .env.example .env
```

### Development

Start the backend:
```bash
cd backend
uvicorn app.main:app --reload
```

Start the frontend:
```bash
cd frontend
npm run dev
```

For desktop development with Tauri:
```bash
cd frontend
npm run tauri dev
```

### Testing

Run all backend tests:
```bash
cd backend
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pytest                      # Run all tests
pytest -v                   # Verbose output
pytest --cov=app           # With coverage report
pytest tests/services/     # Run specific test directory
```

Run all frontend tests:
```bash
cd frontend
npm test                   # Run all tests in watch mode
npm run test:ui           # Run with Vitest UI
npm run test:coverage     # Generate coverage report
```

For comprehensive testing documentation, see [TESTING.md](./TESTING.md)

## Project Structure

```
CyberSecTraining/
├── frontend/          # React + Tauri application
├── backend/           # Python FastAPI backend
├── packs/             # Content packs (scenarios, vulnerabilities)
├── knowledge-base/    # Static knowledge base
├── tests/             # Test files
└── docs/              # Documentation
```

## Documentation

- [Design Document](./CyberSec-Teaching-Tool-Design-Doc.md)
- [User Flow Diagrams](./CyberSec-Tool-UserFlow-Diagrams.md)

## License

[To be determined]

## Disclaimer

This application is designed for **educational and research purposes only**. It contains components for security testing and scanning. Do not use in production environments or on public networks without permission.
