# CyberSec Teaching Tool

An accessible, educational cybersecurity tool for learning network security through real network scanning and interactive scenarios.

## Features

- **Real Network Scanning** - Scan your home network to discover devices and vulnerabilities
- **Interactive Scenarios** - Learn through guided practice scenarios
- **LLM-Powered Explanations** - Get AI-assisted explanations tailored to your knowledge level
- **Accessibility-First** - WCAG 2.1 AA compliant with full screen reader support
- **Training & Live Modes** - Practice safely with simulated data or scan real networks

## Application Modes

CyberSec Teaching Tool supports two distinct operating modes to accommodate different learning needs and environments:

### Training Mode (Default, Recommended)

**Safe practice environment with simulated network data**

- **No real network scanning** - Generates realistic but fake network data for learning
- **No nmap required** - Works on any system without special permissions or tools
- **Deterministic results** - Same IP range always produces the same fake devices for consistent lessons
- **Fast execution** - Scans complete instantly (<1 second)
- **Perfect for learning** - Practice network security concepts without risk
- **Realistic simulation** - Generated devices include proper device types, open ports, services, and vendor information

Training mode is ideal for:
- Classroom environments
- Self-paced learning
- Testing the application
- Situations where real scanning isn't permitted

### Live Mode

**Real network scanning using nmap**

- **Actual network discovery** - Performs real nmap scans on your network
- **Requires nmap** - Must have nmap installed and proper system permissions
- **Real results** - Discovers actual devices on your network
- **Security considerations** - Only use on networks you own or have explicit permission to scan
- **Existing functionality** - Uses the same proven scanning engine as before

Live mode is ideal for:
- Home network security audits
- Learning how real tools work
- Testing actual network configurations
- Advanced users with their own networks

### Switching Between Modes

The current mode is always displayed in the banner at the top of the application:
- **Training Mode**: Blue banner with "🎓 Training Mode Active"
- **Live Mode**: Orange banner with "⚡ Live Scanning Mode Active"

**To change modes:**

1. Navigate to **Settings** → **Application Mode**
2. Select your desired mode (Training or Live)
3. For Live mode, confirm the change in the warning dialog
4. The mode persists across sessions

**Important:** Switching to Live mode requires explicit confirmation to ensure you understand the security implications of real network scanning.

## Tech Stack

- **Frontend**: React + TypeScript + Radix UI
- **Desktop**: Tauri
- **Backend**: Python FastAPI
- **Database**: SQLite
- **Visualization**: Cytoscape.js

## Getting Started

### Prerequisites

**Required:**
- **Node.js 18+** - JavaScript runtime for frontend development
- **Python 3.9+** - Backend API server
- **npm or yarn** - Package manager (comes with Node.js)

**Optional:**
- **nmap** - Network scanning tool (required only for Live Mode; Training Mode works without it)
- **Rust** - Required only for Tauri desktop builds

### Platform-Specific Setup

#### Linux (Ubuntu/Debian)

1. **Install Node.js using nvm (recommended):**
   ```bash
   # Install nvm
   curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash

   # Reload shell configuration
   source ~/.bashrc

   # Install Node.js LTS
   nvm install --lts

   # Verify installation
   node --version
   npm --version
   ```

2. **Install Python and system dependencies:**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-venv nmap

   # Verify installations
   python3 --version
   nmap --version
   ```

3. **For Tauri desktop builds (optional):**
   ```bash
   # Install Rust
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   source $HOME/.cargo/env

   # Install Tauri dependencies
   sudo apt install libwebkit2gtk-4.0-dev \
       build-essential \
       curl \
       wget \
       file \
       libssl-dev \
       libgtk-3-dev \
       libayatana-appindicator3-dev \
       librsvg2-dev
   ```

#### Windows

1. **Install Node.js:**
   - Download installer from [nodejs.org](https://nodejs.org/)
   - Run installer and follow prompts
   - Verify in PowerShell/CMD:
     ```cmd
     node --version
     npm --version
     ```

2. **Install Python:**
   - Download from [python.org](https://www.python.org/downloads/)
   - **Important:** Check "Add Python to PATH" during installation
   - Verify in PowerShell/CMD:
     ```cmd
     python --version
     ```

3. **Install nmap:**
   - Download from [nmap.org](https://nmap.org/download.html#windows)
   - Run the installer (choose "Nmap" and "Npcap" components)
   - Verify installation:
     ```cmd
     nmap --version
     ```

4. **For Tauri desktop builds (optional):**
   - Install Rust from [rustup.rs](https://rustup.rs/)
   - Install Visual Studio C++ Build Tools from [visualstudio.microsoft.com](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
   - Select "Desktop development with C++" workload

#### WSL (Windows Subsystem for Linux)

**Important:** If using WSL, install all tools natively within WSL (not the Windows versions) to avoid path and permission issues:

```bash
# Follow the Linux instructions above
# Use nvm to install Node.js within WSL
# Install nmap via apt
sudo apt update && sudo apt install nmap

# Verify
which node  # Should show /home/...
which nmap  # Should show /usr/bin/nmap
```

**Do NOT use Windows versions of Node.js or nmap from within WSL.**

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/CyberSecTraining.git
   cd CyberSecTraining
   ```

2. **Set up the backend:**

   **Linux/macOS:**
   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

   **Windows (PowerShell):**
   ```powershell
   cd backend
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

   **Windows (CMD):**
   ```cmd
   cd backend
   python -m venv .venv
   .venv\Scripts\activate.bat
   pip install -r requirements.txt
   ```

3. **Set up the frontend:**
   ```bash
   cd frontend
   npm install
   ```

4. **Copy environment file:**

   **Linux/macOS/WSL:**
   ```bash
   cp .env.example .env
   ```

   **Windows (PowerShell/CMD):**
   ```cmd
   copy .env.example .env
   ```

### Development

#### Running the Application

**Start the backend:**

Linux/macOS/WSL:
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

Windows (PowerShell):
```powershell
cd backend
.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

Windows (CMD):
```cmd
cd backend
.venv\Scripts\activate.bat
uvicorn app.main:app --reload
```

The backend API will be available at `http://localhost:8000`

**Start the frontend (in a new terminal):**

```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:1420`

**For desktop development with Tauri (optional):**
```bash
cd frontend
npm run tauri dev
```

#### Accessing the Application

Once both backend and frontend are running:
1. Open your browser to `http://localhost:1420`
2. The frontend will automatically connect to the backend at `http://localhost:8000`

#### Database Initialization

The SQLite database is automatically created when you first start the backend server. The database file will be created at `backend/data/cybersec.db`.

**For development/testing with sample data:**

```bash
cd backend
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m app.db.seed_data
```

This will populate the database with:
- 1 sample network scan
- 5 sample devices (router, desktop, laptop, smart TV, printer)
- 7 vulnerabilities across devices
- Network topology connections
- User progress for 3 scenarios
- User preferences

**Note:** The database is automatically initialized on first run. You only need to run the seed script if you want sample data for development/testing.

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

## Troubleshooting

### Common Issues

#### WSL: "UNC paths are not supported"

**Problem:** When running npm commands in WSL, you see errors about UNC paths or Windows executables.

**Solution:** Install Node.js natively in WSL using nvm:
```bash
# Install nvm in WSL
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
source ~/.bashrc

# Install Node.js
nvm install --lts

# Verify it's using WSL Node.js (should show /home/...)
which node
which npm
```

#### Windows: Python not found

**Problem:** `python` command not recognized after installation.

**Solution:**
1. Reinstall Python and check "Add Python to PATH"
2. Or use `py` command instead of `python`
3. Or manually add Python to PATH in System Environment Variables

#### Port Already in Use

**Problem:** Backend or frontend won't start due to port conflict.

**Solution:**

Linux/macOS:
```bash
# Find process using port 8000 (backend)
lsof -i :8000
# Kill the process
kill -9 <PID>

# Find process using port 1420 (frontend)
lsof -i :1420
kill -9 <PID>
```

Windows (PowerShell as Administrator):
```powershell
# Find process using port 8000
netstat -ano | findstr :8000
# Kill the process
taskkill /PID <PID> /F

# Find process using port 1420
netstat -ano | findstr :1420
taskkill /PID <PID> /F
```

#### Module Not Found Errors

**Problem:** Import errors when running backend or frontend.

**Solution:**

Backend:
```bash
# Ensure virtual environment is activated
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

Frontend:
```bash
# Delete node_modules and reinstall
rm -rf node_modules package-lock.json  # Linux/macOS
# Windows: delete node_modules folder manually

npm install
```

#### Nmap Not Found

**Problem:** Backend fails with "nmap command not found" or similar error.

**Solution:**

Linux/WSL:
```bash
sudo apt install nmap
nmap --version  # Verify installation
```

Windows:
1. Download nmap from https://nmap.org/download.html#windows
2. Run installer and select "Nmap" and "Npcap" components
3. Restart terminal/IDE
4. Verify: `nmap --version`

macOS:
```bash
brew install nmap
nmap --version
```

**Note:** The backend uses `python-nmap` (Python wrapper) which requires the `nmap` system tool to be installed.

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
