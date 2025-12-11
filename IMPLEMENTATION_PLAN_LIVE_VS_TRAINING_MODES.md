# Implementation Plan: Live vs Training Modes

**Created:** 2025-12-11
**Status:** Pending Approval
**Estimated Complexity:** High (Cross-stack feature requiring frontend, backend, and data generation components)

---

## Executive Summary

This plan adds two application modes to the CyberSec Teaching Tool:
- **Training Mode** (default): Generates realistic but fake network data for safe learning
- **Live Mode**: Performs actual network scans using nmap (existing behavior)

The mode will be clearly indicated via a persistent banner across the top of the application, and users can toggle between modes via the Settings page.

---

## Architecture Overview

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────┐
│  Mode Banner (Always Visible Below Header)                   │
│  "🎓 Training Mode Active" or "⚡ Live Scanning Mode Active" │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  User Initiates Scan (NetworkScan.tsx)                       │
│  - Enters IP range (e.g., 192.168.1.0/24)                   │
│  - Selects scan type (quick/deep)                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Backend: Scan Orchestrator (orchestrator.py)                │
│  - Checks application_mode from settings                     │
│  - Routes to appropriate scanner:                            │
│    • Training → FakeNetworkGenerator                         │
│    • Live → NmapScanner                                      │
└─────────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┴────────────────┐
            ▼                                ▼
┌──────────────────────┐       ┌──────────────────────┐
│  FakeNetworkGenerator│       │  NmapScanner         │
│  (NEW)               │       │  (Existing)          │
│  - Generate 3-15     │       │  - Real nmap scan    │
│    devices           │       │  - Real network      │
│  - Realistic ports   │       │    detection         │
│  - Deterministic     │       │                      │
│    based on IP range │       │                      │
└──────────────────────┘       └──────────────────────┘
            │                                │
            └───────────────┬────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Same ScanResult Interface                                   │
│  - Frontend receives identical data structure                │
│  - No frontend changes needed for result handling            │
└─────────────────────────────────────────────────────────────┘
```

### Design Decisions

1. **Mode as Application State**: Mode is global app state (not per-scan)
   - Simpler UX (one place to toggle)
   - Safer (prevents accidental live scans)
   - Aligns with educational use case

2. **Deterministic Fake Data**: Same IP range → Same fake devices
   - Enables consistent training scenarios
   - Allows creating lesson plans with predictable results
   - Uses hash of IP range as seed

3. **Shared Interface**: FakeNetworkGenerator implements same interface as NmapScanner
   - Minimal changes to orchestrator
   - Frontend remains unchanged
   - Easy to add more scanner types later

4. **Prominent Mode Banner**: Always visible banner below header
   - Clear visual indicator of current mode
   - Reduces risk of confusion
   - Meets accessibility standards (ARIA live region)

---

## Component Architecture

### New Components

#### 1. **ModeContext** (Frontend)
**File:** `frontend/src/context/ModeContext.tsx`

**Responsibilities:**
- Manage application mode state (training | live)
- Persist mode to localStorage
- Sync with backend API
- Provide mode toggle function with confirmation

**Interface:**
```typescript
interface ModeContextValue {
  mode: 'training' | 'live';
  isLoading: boolean;
  setMode: (mode: 'training' | 'live') => Promise<void>;
  toggleMode: () => Promise<void>;
}
```

**Behavior:**
- Default mode: 'training'
- Load from localStorage on mount
- Fetch from backend API after mount
- Backend is source of truth (overrides localStorage)
- Announce mode changes to screen readers

---

#### 2. **ModeBanner** (Frontend)
**File:** `frontend/src/components/layout/ModeBanner.tsx`

**Responsibilities:**
- Display current application mode prominently
- Show different styling for training vs live
- Provide optional quick toggle button (only on certain pages)
- Meet WCAG 2.1 AA standards

**Visual Design:**
- **Training Mode**: Blue/teal background, book/graduation cap icon
- **Live Mode**: Orange/red background, lightning bolt icon
- Full-width banner, 48px height (44px + 4px padding for touch target)
- Positioned between Header and main content
- Sticky positioning (stays visible on scroll)

**Accessibility:**
- ARIA role="banner" and aria-live="polite"
- Clear text: "Training Mode Active - Safe Practice Environment"
- Keyboard accessible toggle button
- High contrast in all color modes

---

#### 3. **FakeNetworkGenerator** (Backend)
**File:** `backend/app/services/scanner/fake_network_generator.py`

**Responsibilities:**
- Generate realistic fake network scan results
- Implement same interface as NmapScanner
- Create deterministic results based on IP range
- Simulate scan progress (for realistic UX)

**Generation Algorithm:**
```python
1. Parse target IP range (e.g., 192.168.1.0/24)
2. Use hash(network_address + salt) as seed for random generator
3. Determine device count: random(3, 15) devices
4. For each device:
   a. Generate IP from range
   b. Assign device type (router, printer, laptop, NAS, IoT, etc.)
   c. Generate MAC address with realistic vendor prefix
   d. Add ports based on device type:
      - Router: 80, 443, 22, 23, 53
      - Printer: 631, 9100, 80
      - NAS: 22, 80, 445, 548, 2049
      - Laptop: 22 or 3389, random high ports
      - IoT: 80, 443, 1883, 8883
   e. Add hostname (device-type-XXX)
   f. Optionally add OS fingerprint
   g. Simulate some devices being "down" (10% chance)
5. Add realistic timing delays (simulate progress)
6. Return ScanResult with generated devices
```

**Realism Features:**
- Use existing DeviceFingerprinter for vendor names
- Reference service name mappings from nmap_scanner.py
- Vary device types based on network class:
  - 192.168.x.x: Home devices (router, printer, laptops, IoT)
  - 10.x.x.x: Enterprise devices (servers, workstations, printers)
- Add some vulnerabilities (cross-reference with content packs)

---

#### 4. **Mode Management API** (Backend)
**File:** `backend/app/api/routes/settings.py` (extend existing)

**New Endpoints:**
```python
GET  /api/v1/settings/mode
POST /api/v1/settings/mode
```

**Schema:**
```python
class ModeSettings(BaseModel):
    mode: Literal['training', 'live'] = 'training'
    require_confirmation_for_live: bool = True
```

**Validation:**
- Only allow 'training' or 'live' values
- Log mode changes for audit trail
- Check if nmap is available when switching to live mode

---

### Modified Components

#### 1. **ScanOrchestrator** (Backend)
**File:** `backend/app/services/scanner/orchestrator.py`

**Changes:**
- Add `_get_application_mode()` method to fetch current mode from settings
- Modify `start_scan()` to route based on mode:
  ```python
  mode = self._get_application_mode()
  if mode == 'training':
      scanner = FakeNetworkGenerator(self.settings)
  else:
      scanner = NmapScanner(self.settings)
  ```
- Update logging to include mode in scan audit logs
- Add mode indicator to ScanResult metadata

**Lines to modify:** ~200-220 (in `start_scan` method)

---

#### 2. **MainLayout** (Frontend)
**File:** `frontend/src/components/layout/MainLayout.tsx`

**Changes:**
- Add `<ModeBanner />` component below `<Header />`
- Ensure proper spacing (no gap between header and banner)
- Pass mode from ModeContext

**Structural change:**
```tsx
<Header />
<ModeBanner />  {/* NEW */}
<Body>
  <Sidebar />
  <Main id="main-content">
    <Outlet />
  </Main>
</Body>
```

---

#### 3. **Settings Page** (Frontend)
**File:** `frontend/src/pages/Settings/Settings.tsx`

**Changes:**
- Add new "Application Mode" section
- Radio button group: Training Mode / Live Mode
- Description text explaining each mode
- Warning/confirmation dialog when switching to Live mode
- Save button updates mode via ModeContext

**UI Layout:**
```
Application Mode
───────────────────────────────────────────
○ Training Mode (Safe Practice Environment)
  Generate realistic fake network data for learning
  without performing actual network scans.

○ Live Mode (Real Network Scanning)
  ⚠️ WARNING: Performs real network scans on your network.
  Only use on networks you own or have permission to scan.

[Save Settings]
```

---

#### 4. **NetworkScan Page** (Frontend)
**File:** `frontend/src/pages/NetworkScan/NetworkScan.tsx`

**Changes:**
- Read mode from ModeContext
- Update consent checkbox text based on mode:
  - Training: "I understand this is simulated data"
  - Live: "I have permission to scan this network"
- Update page description to indicate current mode
- Show mode-specific tips/warnings

**Minor changes:** ~5-10 lines (conditional rendering)

---

#### 5. **Config** (Backend)
**File:** `backend/app/config.py`

**Changes:**
- Add default_application_mode field:
  ```python
  default_application_mode: Literal['training', 'live'] = 'training'
  ```
- Add to environment variable loading

---

#### 6. **App Initialization** (Frontend)
**File:** `frontend/src/main.tsx`

**Changes:**
- Add ModeProvider to context hierarchy:
  ```tsx
  <BrowserRouter>
    <AccessibilityProvider>
      <ThemeProvider>
        <ModeProvider>  {/* NEW */}
          <App />
        </ModeProvider>
      </ThemeProvider>
    </AccessibilityProvider>
  </BrowserRouter>
  ```

---

## Data Structure

### Mode Preference Storage

**Backend (SQLite - preferences table):**
```sql
user_id: 'local'
key: 'application_mode'
value: '{"mode": "training", "require_confirmation_for_live": true}'
```

**Frontend (localStorage):**
```javascript
'cybersec-app-mode': 'training'
```

### Fake Device Data Format

Same format as real NmapScanner output:
```python
DeviceInfo(
    ip="192.168.1.1",
    mac="00:11:22:33:44:55",
    hostname="router-gateway",
    vendor="TP-Link",
    device_type="router",
    os="Linux 3.x",
    os_accuracy=85,
    open_ports=[
        PortInfo(port=80, protocol="tcp", state="open", service="http"),
        PortInfo(port=443, protocol="tcp", state="open", service="https"),
        PortInfo(port=22, protocol="tcp", state="open", service="ssh"),
    ],
    is_up=True,
    last_seen=datetime.now()
)
```

---

## User Experience Flow

### Initial Launch (First Time User)

1. App starts in **Training Mode** (default)
2. Mode banner displays: "🎓 Training Mode Active - Safe Practice Environment"
3. User sees NetworkScan page with explanation: "You are in Training Mode. Scans will generate realistic practice data."
4. User performs scans, sees fake but realistic network data
5. User learns without risk

### Switching to Live Mode

1. User navigates to Settings page
2. User selects "Live Mode" radio button
3. Confirmation dialog appears:
   ```
   ⚠️ Enable Live Network Scanning?

   Live Mode will perform REAL network scans using nmap.

   Only enable this if you:
   • Own the network you're scanning
   • Have explicit permission to scan the network
   • Understand the security implications

   Training Mode is recommended for learning.

   [Cancel]  [Enable Live Mode]
   ```
4. User confirms, mode switches
5. Banner updates to: "⚡ Live Scanning Mode Active"
6. Screen reader announces: "Application mode changed to Live. Real network scanning is now enabled."

### Scanning in Each Mode

**Training Mode:**
- Form shows: "This will generate simulated network data"
- Consent checkbox: "I understand this is practice data"
- Scan executes quickly (1-3 seconds, simulated progress)
- Results show realistic but fake devices
- No nmap required, no sudo needed

**Live Mode:**
- Form shows: "⚠️ This will scan your actual network"
- Consent checkbox: "I have permission to scan this network"
- Scan uses real nmap (existing behavior)
- Results show actual discovered devices
- Requires nmap installation and proper permissions

---

## Implementation Phases

### Phase 1: Backend Mode Infrastructure (3-4 hours)
1. Add mode configuration to config.py
2. Extend settings API with mode endpoints
3. Add mode preference storage/retrieval
4. Update DataStore methods if needed
5. Add backend unit tests for mode settings

### Phase 2: Fake Network Generator (4-5 hours)
1. Create FakeNetworkGenerator class
2. Implement device generation algorithm
3. Add deterministic seeding
4. Add device type variations
5. Integrate with DeviceFingerprinter
6. Write comprehensive unit tests
7. Add realistic port/service mappings

### Phase 3: Scan Orchestrator Integration (2-3 hours)
1. Modify orchestrator to check mode
2. Route to fake vs real scanner
3. Add mode to scan metadata/logging
4. Update audit trail
5. Add integration tests

### Phase 4: Frontend Mode Context (2-3 hours)
1. Create ModeContext and provider
2. Add localStorage persistence
3. Add API integration for mode sync
4. Write context tests
5. Add screen reader announcements

### Phase 5: Mode Banner UI (2-3 hours)
1. Create ModeBanner component
2. Add styling for training vs live modes
3. Ensure accessibility compliance
4. Integrate into MainLayout
5. Add component tests

### Phase 6: Settings Page Integration (2 hours)
1. Add mode toggle to Settings page
2. Add confirmation dialog for live mode
3. Wire up to ModeContext
4. Add explanatory text
5. Test UX flow

### Phase 7: NetworkScan Page Updates (1-2 hours)
1. Update consent text based on mode
2. Add mode-specific messaging
3. Update tips/warnings
4. Test scan flow in both modes

### Phase 8: Documentation & Testing (3-4 hours)
1. Update README.md
2. Update design doc (CyberSec-Teaching-Tool-Design-Doc.md)
3. Update user flow diagrams
4. Add inline code comments
5. Write end-to-end tests
6. Create user guide for modes
7. Update .env.example

### Phase 9: Polish & Edge Cases (2-3 hours)
1. Handle mode switching during active scan
2. Add loading states
3. Error handling for failed mode switches
4. Visual polish on banner
5. Cross-browser testing
6. Accessibility audit

**Total Estimated Time:** 22-30 hours of development work

---

## Testing Strategy

### Unit Tests

**Backend:**
- `test_fake_network_generator.py`:
  - Test device generation for various IP ranges
  - Test deterministic behavior (same input → same output)
  - Test device type distributions
  - Test port assignments
  - Test MAC address generation
  - Test progress simulation

- `test_mode_settings.py`:
  - Test mode persistence to DataStore
  - Test mode validation
  - Test default mode
  - Test mode retrieval

- `test_orchestrator_mode_routing.py`:
  - Test orchestrator routes to fake scanner in training mode
  - Test orchestrator routes to nmap scanner in live mode
  - Test mode retrieval from settings
  - Test scan metadata includes mode

**Frontend:**
- `ModeContext.test.tsx`:
  - Test default mode is training
  - Test mode persistence to localStorage
  - Test mode toggle function
  - Test API synchronization
  - Test screen reader announcements

- `ModeBanner.test.tsx`:
  - Test renders in training mode
  - Test renders in live mode
  - Test accessibility attributes
  - Test keyboard navigation

- `Settings.test.tsx`:
  - Test mode selection updates context
  - Test confirmation dialog for live mode
  - Test cancel preserves current mode

### Integration Tests

- `test_training_mode_scan_flow.py`:
  - Full scan flow in training mode
  - Verify fake data returned
  - Verify no real nmap execution
  - Verify scan completes quickly

- `test_mode_switching.py`:
  - Switch from training to live and back
  - Verify persistence across sessions
  - Verify UI updates correctly

### End-to-End Tests

- User journey: Default training → perform scan → switch to live → confirm → perform scan
- Verify banner visibility and correctness
- Verify scan results differ between modes
- Test accessibility with screen reader

### Accessibility Testing

- Test with NVDA/JAWS screen readers
- Test keyboard-only navigation
- Test in high-contrast mode
- Test focus management on mode switch
- Verify ARIA announcements

---

## Documentation Updates

### 1. README.md
**Location:** `/home/sunds/Code/CyberSecTraining/README.md`

**Add section:**
```markdown
## Application Modes

CyberSec Teaching Tool supports two modes:

### Training Mode (Default)
- **Safe practice environment** with simulated network data
- No actual network scanning performed
- Generates realistic fake devices based on IP ranges
- Perfect for learning without risk
- No nmap installation required

### Live Mode
- **Real network scanning** using nmap
- Requires nmap installation and proper system permissions
- Only use on networks you own or have permission to scan
- Enables testing real security scenarios

**How to switch modes:**
1. Navigate to Settings → Application Mode
2. Select desired mode
3. Confirm the change (confirmation required for Live Mode)

The current mode is always displayed in the banner at the top of the application.
```

### 2. Design Document
**Location:** `/home/sunds/Code/CyberSecTraining/CyberSec-Teaching-Tool-Design-Doc.md`

**Add to "Features" section:**
```markdown
### Training vs Live Modes

**Training Mode (Default):**
- Generates deterministic fake network data for consistent learning
- Algorithms create realistic device types, ports, and services
- Safe for classroom environments and self-paced learning
- No nmap dependency, runs on any system

**Live Mode:**
- Enables real-world network scanning and discovery
- Uses actual nmap for production-quality scans
- Requires explicit user confirmation and permission
- Includes all safety validations (private networks only)
```

**Add to "Architecture" section:**
```markdown
### Scanner Abstraction

The ScanOrchestrator routes scan requests to the appropriate scanner based on application mode:

- **Training Mode**: FakeNetworkGenerator creates simulated scan results
- **Live Mode**: NmapScanner executes real nmap scans

Both implement the same interface (BaseScannerProtocol), ensuring the frontend receives consistent data structures regardless of mode.
```

### 3. User Flow Diagrams
**Location:** `/home/sunds/Code/CyberSecTraining/CyberSec-Tool-UserFlow-Diagrams.md`

**Add new diagram:**
```markdown
## Mode Selection Flow

```
[App Launch] → [Default: Training Mode]
                      ↓
            [Mode Banner Visible]
                      ↓
          ┌───────────┴───────────┐
          ↓                       ↓
   [Training Mode]          [Live Mode]
   - Safe practice          - Real scanning
   - Fake data              - Requires nmap
   - Fast results           - Network permissions
          ↓                       ↓
   [Perform Scan]           [Perform Scan]
          ↓                       ↓
   [Simulated Results]      [Real Results]
          ↓                       ↓
          └───────────┬───────────┘
                      ↓
          [Settings → Change Mode]
                      ↓
          [Confirmation Dialog]
                      ↓
            [Mode Switched]
```
```

### 4. .env.example
**Location:** `/home/sunds/Code/CyberSecTraining/.env.example`

**Add:**
```bash
# Application Mode (training or live)
DEFAULT_APPLICATION_MODE=training
```

### 5. Inline Code Comments

**Add JSDoc/docstrings to:**
- `FakeNetworkGenerator` class and methods (explain generation algorithm)
- `ModeContext` provider (explain state management)
- `ModeBanner` component (explain accessibility features)
- Modified orchestrator methods (explain mode routing logic)

---

## Security Considerations

### Training Mode
- **No security risk** - No actual network activity
- Cannot expose real network topology
- Cannot trigger IDS/IPS systems
- Safe for classroom demos

### Live Mode
- **Existing security controls remain** (from current implementation):
  - Private network validation (RFC 1918)
  - User consent required
  - Rate limiting (one scan at a time)
  - Audit logging
  - Network size limits (/24 max)
- **New controls:**
  - Explicit confirmation dialog before enabling
  - Visual mode indicator always present
  - Mode changes logged in audit trail

### Mode Switching
- No mid-scan mode changes (disable toggle during active scan)
- Mode persisted to backend (harder to tamper with than localStorage alone)
- Clear visual feedback on mode state

---

## Potential Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| User confuses training data for real data | Low | Clear mode banner, mode-specific messaging, different color schemes |
| Accidental live scan in training | None | Mode determines behavior, no live scanning possible in training mode |
| Fake data not realistic enough | Medium | Use DeviceFingerprinter, reference real scan patterns, deterministic seeding |
| Mode state desync between frontend/backend | Low | Backend is source of truth, periodic re-fetching |
| User enables live mode without understanding | Medium | Confirmation dialog with clear warnings, default to training |
| Poor accessibility for mode indicator | Medium | ARIA live regions, high contrast, screen reader announcements |

---

## Future Enhancements (Out of Scope for Initial Implementation)

1. **Per-Scan Mode Override**: Allow live scan from training mode for specific scans (with double confirmation)
2. **Training Scenarios Library**: Pre-defined fake networks (e.g., "Vulnerable Home Network", "Small Office with IoT")
3. **Custom Fake Networks**: UI to manually create specific fake network topologies
4. **Hybrid Mode**: Mix of fake and real devices for advanced training
5. **Vulnerability Injection**: Add specific vulnerabilities to fake devices for training
6. **Replay Mode**: Save real scan results and replay as fake data later
7. **Competition Mode**: Generate randomized networks for capture-the-flag style competitions

---

## Dependencies

### New Backend Dependencies
- None (uses existing libraries)

### New Frontend Dependencies
- None (uses existing React, TypeScript, and UI libraries)

### System Requirements
- **Training Mode**: No additional requirements
- **Live Mode**: Existing nmap requirement (unchanged)

---

## Rollback Plan

If issues arise, rollback is straightforward:

1. **Frontend**: Remove ModeContext and ModeBanner, restore original MainLayout
2. **Backend**: Remove FakeNetworkGenerator, restore orchestrator to always use NmapScanner
3. **Database**: Mode preference is just a key-value pair, can be ignored/deleted
4. **No schema changes**, so no migrations to rollback

The changes are largely additive, making rollback low-risk.

---

## Success Criteria

✅ **Functional Requirements:**
- [ ] Training mode generates realistic fake network data
- [ ] Live mode performs real scans (existing behavior)
- [ ] Default mode is Training on first launch
- [ ] Mode banner always visible and accurate
- [ ] Mode persists across sessions
- [ ] Settings page allows mode toggle with confirmation

✅ **Non-Functional Requirements:**
- [ ] Fake data generation completes within 3 seconds
- [ ] Mode banner meets WCAG 2.1 AA standards
- [ ] No performance degradation in live mode
- [ ] Training mode works without nmap installed
- [ ] All existing tests pass
- [ ] New tests achieve >80% coverage

✅ **User Experience:**
- [ ] Mode is always clear to the user
- [ ] Training mode feels realistic
- [ ] Live mode switch requires explicit confirmation
- [ ] Error messages are mode-aware
- [ ] Documentation is clear and complete

---

## Approval Checklist

Before implementation begins, confirm:

- [ ] Architecture approach is approved
- [ ] Mode banner design is acceptable
- [ ] Default to Training mode is confirmed
- [ ] Fake data generation algorithm is adequate
- [ ] Settings page UI is approved
- [ ] Testing strategy is sufficient
- [ ] Documentation plan is complete
- [ ] Timeline is reasonable

---

## Questions for Review

1. **Mode Toggle Location**: Should the mode toggle be:
   - Settings page only (proposed)
   - Also in the banner itself for quick access
   - Only accessible to "admin" users

2. **Mode Indicator Persistence**: Should the banner be:
   - Always visible (proposed)
   - Dismissible but returns on page reload
   - Collapsible

3. **Fake Data Complexity**: Should fake networks include:
   - Just devices and ports (proposed)
   - Also fake vulnerabilities matched to content packs
   - Fake network topology (subnets, VLANs)

4. **Live Mode Confirmation**: Should enabling live mode require:
   - Just a confirmation dialog (proposed)
   - Also a password/PIN
   - Admin-level permission

5. **Training Mode Customization**: Should users be able to:
   - Only get deterministic fake data (proposed)
   - Customize how many devices appear
   - Select specific device types to include

---

## Next Steps

1. **Review this plan** with stakeholders
2. **Answer questions** in the "Questions for Review" section
3. **Get approval** on architecture and approach
4. **Begin Phase 1** implementation (Backend Mode Infrastructure)
5. **Iterate** with regular check-ins after each phase

---

**Plan Document Version:** 1.0
**Last Updated:** 2025-12-11
