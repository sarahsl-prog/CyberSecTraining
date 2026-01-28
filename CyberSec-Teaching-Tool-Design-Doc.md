# Cybersecurity Teaching Tool - Design Document
**Version:** 1.0  
**Date:** December 6, 2024  
**Status:** Initial Design Phase

---

## 1. Project Overview

### Vision
An accessible, educational cybersecurity tool that runs on PC/tablet devices, capable of mapping and analyzing home networks, identifying security vulnerabilities, and teaching users how to fix them through interactive scenarios.

### Target Audiences
- Home users learning network security
- Students in cybersecurity courses
- Educators teaching network security concepts
- IT professionals seeking training resources

### Key Differentiators
- **Accessibility-first design** (screen reader support, colorblind-friendly, keyboard navigation)
- **Real network scanning** with educational overlays
- **LLM-powered explanations** tailored to user knowledge level
- **Modular content packs** for expandability
- **Community scenario sharing** via GitHub

---

## 2. Architecture Decisions

### 2.1 Frontend
**Decision:** Web-based UI  
**Rationale:** 
- Best-in-class accessibility support (WCAG 2.1 standards)
- Mature ecosystem of accessible component libraries
- Native screen reader compatibility
- Cross-platform (Windows/Mac/Linux/tablets) without separate builds
- Built-in browser DevTools for accessibility auditing

**Technology Stack:**
- React or Vue.js for UI framework
- Dash (Plotly) for network visualization and dashboards
- Tauri for desktop packaging (lighter than Electron)
- Or run as web app via browser

### 2.2 Backend
**Decision:** Python FastAPI  
**Rationale:**
- Python excellent for network scanning libraries
- Fast, modern async framework
- Easy integration with ML/LLM libraries
- Good for building REST APIs
- Familiar language for security tools

### 2.3 LLM Integration Strategy
**Decision:** Hybrid routing system with multiple fallbacks

**Architecture:**
```
1. Check if Ollama running locally → Use local LLM (free, private, fast)
2. Fall back to hosted API → Freemium model with rate limits
3. Fall back to static knowledge base → Instant responses for common queries
```

**Rationale:**
- Zero barrier to entry (works without any setup)
- Privacy for users who want it (local-only option)
- Sustainable for developer (hosting costs manageable)
- Works offline with degraded capability

**Hosted Model:**
- Deploy on HuggingFace Inference Endpoints or Modal/Replicate
- Fine-tune Llama 3.1 8B or Mistral 7B on security content
- Training data: CVE database, MITRE ATT&CK, OWASP, Security Stack Exchange


---

## 3. Data Storage Strategy

### 3.1 Storage Architecture
**Decision:** Hybrid approach using SQLite + JSON files

### 3.2 Data Categories

#### Static Knowledge Base (JSON, shipped with app)
- Vulnerability definitions and remediation guides
- CVE database
- Device type profiles (expected ports/services)
- MITRE ATT&CK technique mappings
- **Update mechanism:** Monthly releases or auto-update check

#### User Network Scans (SQLite, private/local only)
```sql
-- Database Schema
networks/
  ├─ devices (id, network_id, ip, mac, hostname, device_type, os, last_seen)
  ├─ vulnerabilities (id, device_id, vuln_type, severity, discovered_at, fixed_at)
  ├─ scans (id, network_id, timestamp, scan_type)
  └─ topology (device_id, connected_to_device_id)

user_data/
  ├─ progress (scenario_id, completed, score, timestamp)
  ├─ preferences (key, value)
  └─ assessments (id, scenario_id, answers, score)
```

**Privacy Guarantee:** Network scan data NEVER leaves the device

#### Classroom Scenarios (JSON templates)
```json
{
  "scenarios": [
    {
      "id": "home_network_101",
      "difficulty": "beginner",
      "network": {
        "devices": [...],
        "vulnerabilities": [...]
      },
      "learning_objectives": [...]
    }
  ]
}
```


### 3.3 Multi-User Support (Future)
**Decision:** Build abstraction layer now, implement later

**Architecture Pattern:**
```python
class DataStore(ABC):
    @abstractmethod
    def save_progress(self, user_id, scenario_id, score): pass
    
    @abstractmethod
    def get_leaderboard(self, scenario_id): pass

class LocalDataStore(DataStore):
    # Uses SQLite, user_id is always "local"
    pass

class RemoteDataStore(DataStore):
    # Hits API for multi-user features (future)
    pass
```

**Rationale:**
- 10% more work upfront saves months of refactoring later
- Enables competitive features when needed (leaderboards, CTF-style competitions)
- Critical for classroom adoption
- API designed as if multi-user exists from day 1

---

## 4. Modular Architecture

### 4.1 Content Packs System
**Decision:** Modular pack architecture from day 1

**Pack Structure:**
```
packs/
  home-basics/
    ├─ manifest.json  # metadata, version, dependencies
    ├─ scenarios/     # JSON scenario definitions
    ├─ knowledge/     # pack-specific vulnerability data
    └─ assets/        # icons, images for this pack
```


**Manifest Example:**
```json
{
  "id": "home-basics",
  "version": "1.0.0",
  "requires_core": ">=2.0.0",
  "name": "Home Network Basics",
  "scenarios": 12,
  "description": "...",
  "author": "...",
  "license": "..."
}
```

**Benefits:**
- Ship v1 with minimal content, expand systematically
- Develop and test packs in isolation
- Version independently
- Community contributions possible
- Natural monetization path (free core + premium packs)

### 4.2 User-Created Scenarios
**Decision:** Users can create, import, and export custom scenarios

**Scenario Format (JSON):**
```json
{
  "schema_version": "1.0",
  "metadata": {
    "title": "Insecure Smart Home",
    "author": "Prof. Smith",
    "difficulty": "intermediate",
    "estimated_time": "30min"
  },
  "network": {
    "devices": [
      {
        "type": "router",
        "ip": "192.168.1.1",
        "vulnerabilities": ["default_creds", "outdated_firmware"]
      }
    ]
  },
  "learning_objectives": [...],
  "hints": [...],
  "solution": [...]
}
```


**Features Required:**
- Import/Export scenarios (JSON files)
- Validation (uses only valid vulnerability types)
- Sandboxing (no arbitrary code execution)
- Local sharing via file exchange

### 4.3 Community Marketplace
**Decision:** GitHub-based "marketplace lite" for v1

**Phase 1 Implementation:**
- GitHub repository: "awesome-cybersec-scenarios"
- Users submit scenarios via Pull Request
- Community review before merging
- App's "Browse Community Scenarios" hits GitHub API
- Download scenarios directly from GitHub

**Benefits:**
- Zero infrastructure cost
- GitHub handles auth, versioning, issue tracking
- Community moderation via PR review
- Easy migration to full marketplace later if needed

**Phase 2 (Future):**
- Real marketplace with ratings/reviews only if community demands it
- Estimated complexity: 6-10 weeks additional work + ongoing costs

---

## 5. Network Scanning

### 5.1 Real Network Scanning
**Decision:** Support real network scanning with safety guardrails


**Technical Stack:**
```python
import nmap  # Port scanning
import scapy  # Packet crafting (requires root/admin)
from mac_vendor_lookup import MacLookup  # Device identification
import netifaces  # Get local network info
```

**Technical Safeguards:**
```python
def scan_network():
    # 1. Require user confirmation
    if not user_confirmed_ownership():
        show_warning_dialog()
        return
    
    # 2. Only allow private networks
    if not is_private_network(target_ip):
        raise Exception("Only private networks allowed (10.x, 192.168.x, 172.16-31.x)")
    
    # 3. Audit log all scans
    audit_log.record(timestamp, network, user_consent=True)
```

**Disclaimer Strategy:**
- Installation EULA
- First-launch wizard (cannot skip)
- Before every real network scan (checkbox required)
- In "About" section

**Disclaimer Text:**
> "This application is designed for **educational and research purposes only**. 
> It contains components for security testing and scanning. Do not use in 
> production environments or on public networks without permission."


**Scanning Challenges:**
1. **Permissions:** Requires elevated privileges on most systems
2. **Performance:** 30 seconds to 5 minutes depending on network size
3. **False positives:** Routers/firewalls complicate detection
4. **Device identification:** Distinguishing device types is difficult

**Required UX Features:**
- Progress indicators (scanning... 5/254 addresses checked)
- Device fingerprinting logic (OS detection, service banners)
- "Safe mode" option (common ports only, not aggressive scan)

### 5.2 Training vs Live Modes

**Decision:** Support two distinct operating modes to balance learning safety with real-world applicability

#### Training Mode (Default)

**Purpose:** Safe practice environment for learning without risk

**Implementation:**
- Uses `FakeNetworkGenerator` to create simulated scan results
- Deterministic generation based on IP range hash (same input → same output)
- Generates 3-15 realistic fake devices with appropriate:
  - Device types (router, printer, laptop, NAS, IoT)
  - Open ports based on device type
  - Service banners and version information
  - MAC addresses with realistic vendor prefixes
  - OS fingerprints
- Completes instantly (<1 second) with simulated progress for UX
- No nmap dependency required
- Works on any system without special permissions

**Rationale:**
- Enables classroom environments where real scanning isn't permitted
- Consistent results allow creating reproducible lesson plans
- No security/legal concerns
- No network overhead or permissions issues
- Students can practice without fear of mistakes

**Use Cases:**
- Educational institutions
- Self-paced online learning
- Testing the application
- Demonstrations
- Environments where nmap unavailable

#### Live Mode

**Purpose:** Real network scanning for practical security audits

**Implementation:**
- Uses `NmapScanner` for actual network discovery (existing functionality)
- Performs real nmap scans on specified networks
- Returns actual discovered devices with real data
- Requires nmap installation and proper system permissions
- All existing safety guardrails remain (private networks only, user consent, rate limiting)

**Rationale:**
- Necessary for home network security audits
- Teaches how real security tools work
- Validates learning against actual systems
- Advanced users need real-world practice

**Use Cases:**
- Personal home network audits
- Advanced users with their own lab networks
- Validating security configurations
- Professional security training

#### Mode Switching

**UI/UX:**
- Persistent banner across top of application indicates current mode:
  - Training: Blue banner "🎓 Training Mode Active"
  - Live: Orange banner "⚡ Live Scanning Mode Active"
- Settings page provides mode toggle with radio buttons
- Switching to Live mode requires explicit confirmation dialog
- Mode persists across sessions (stored in database + localStorage)

**Architecture:**
```python
class ScanOrchestrator:
    def _get_scanner(self):
        mode = self._get_application_mode()  # from database
        if mode == "live":
            return NmapScanner(self.settings)
        else:  # training mode (default)
            return FakeNetworkGenerator(self.settings)
```

**Scanner Abstraction:**
Both `FakeNetworkGenerator` and `NmapScanner` implement the same interface:
- `scan_network(target, scan_type) -> ScanResult`
- `is_available() -> bool`

This ensures the frontend receives consistent data structures regardless of mode, requiring zero frontend changes for result handling.

**Benefits:**
- Single codebase supports both use cases
- Clear mode indication reduces confusion
- Explicit confirmation prevents accidental real scans
- Deterministic training mode enables curriculum development
- Easy to add more scanner types in future (cloud scanning, API-based, etc.)

---

## 6. Accessibility Requirements

### 6.1 Core Accessibility Features (WCAG 2.1 AA Compliance)

**Must-Have Features:**

1. **Screen Reader Support**
   - NVDA, JAWS, VoiceOver, Narrator compatibility
   - Semantic HTML with proper ARIA labels
   - ARIA landmarks and roles
   - Live regions for dynamic content updates

2. **Keyboard Navigation**
   - Full keyboard control (no mouse required)
   - Logical tab order
   - Skip links for main content
   - Visible focus indicators
   - Focus management for modals/dynamic content

3. **Visual Accessibility**
   - Color contrast: WCAG AA minimum (4.5:1 for text, 3:1 for UI)
   - Colorblind modes (not relying solely on color to convey info)
   - Zoom support up to 200% without breaking layout
   - Text resizing independent of zoom
   - Reduced motion option for animations


4. **Touch Accessibility**
   - Minimum touch target size: 44x44px
   - Works on tablets without mouse/keyboard

5. **Mode Switching**
   - Narrator mode (audio descriptions for all content)
   - Visual mode (zoom on focus, high contrast)
   - Easy switching between modes

### 6.2 Implementation Approach

**Why Web-Based Wins:**
- 90% of accessibility features come from proper HTML/ARIA
- Mature testing tools (Lighthouse, axe DevTools, WAVE)
- Large ecosystem of accessible component libraries
- Extensive documentation and resources

**Component Libraries to Consider:**
- Radix UI (unstyled, accessible primitives)
- Chakra UI (accessible by default)
- React Aria (Adobe's accessibility library)

**Testing Strategy:**
- Automated: Lighthouse CI, axe-core in tests
- Manual: Screen reader testing on Windows/Mac
- User testing with disabled users (critical!)

---

## 7. MVP Scope (Version 1.0)

### 7.1 Features Included in v1

**Core Functionality:**
✅ Real network scanning with safeguards
✅ Interactive network visualization dashboard
✅ Top 20 vulnerability types detection
✅ LLM-powered explanations (hybrid routing)
✅ Static knowledge base fallback
✅ 2 scenario packs (~15-18 scenarios total)
✅ Exploration/teaching mode
✅ User scenario import/export
✅ WCAG 2.1 AA accessibility compliance


**Deferred to v1.1+:**
❌ Assessment/quiz mode (focus on teaching first)
❌ Multi-user competitive features (infrastructure in place)
❌ Additional content packs
❌ Advanced gamification (achievements, progression trees)
❌ Full marketplace (using GitHub "lite" version)

### 7.2 Scenario Packs (v1)

**Pack 1: Home Network Basics** (8-10 scenarios)
- Topics: Router security, default credentials, guest networks, IoT devices
- Difficulty: Beginner to Intermediate
- Estimated completion time: 3-4 hours total

**Pack 2: Small Office/Router Security** (6-8 scenarios)
- Topics: Network segmentation, firmware updates, VPN setup, port forwarding risks
- Difficulty: Intermediate
- Estimated completion time: 2-3 hours total

**Total v1 Content:** 15-18 scenarios

### 7.3 Top 20 Vulnerability Types (v1)

**To be defined in detail, but likely includes:**
1. Default credentials
2. Open Telnet (port 23)
3. Open FTP (port 21)
4. Outdated firmware
5. Open SNMP with default community strings
6. Unencrypted services (HTTP vs HTTPS)
7. UPnP enabled unnecessarily
8. Open database ports (MySQL, PostgreSQL, MongoDB)
9. Weak WiFi encryption (WEP, WPA vs WPA2/WPA3)
10. Guest network issues
11. Port forwarding misconfigurations
12. Open SMB shares
13. Unnecessary services running
14. Missing security patches (CVE-specific)
15. IoT device vulnerabilities
16. DNS configuration issues
17. DHCP misconfigurations
18. Firewall rule problems
19. VPN misconfigurations
20. Certificate/SSL issues


*(Final list to be refined based on research and prioritization)*

---

## 8. Offline & Online Modes

### 8.1 Hybrid Approach
**Decision:** Works offline, enhanced when online

**Online Mode Benefits:**
- CVE database updates
- New scenario pack downloads
- Hosted LLM access (if Ollama not available)
- Community scenario browsing

**Offline Mode Capabilities:**
- Full network scanning functionality
- All installed scenario packs work
- Local LLM via Ollama (if installed)
- Static knowledge base for common vulnerabilities
- All user data and progress preserved

**Implementation:**
```python
class App:
    def __init__(self):
        self.online_mode = self.check_connectivity()
        
        if self.online_mode:
            self.check_for_updates()
            self.llm_router.prefer_hosted()
        else:
            self.show_offline_banner()
            self.llm_router.prefer_local()
```

---

## 9. Development Timeline Estimate

### 9.1 Estimated Effort (v1.0)

**Component Breakdown:**
- Accessibility-first UI: **3-4 weeks**
- Real network scanning engine: **2-3 weeks**
- LLM integration & routing: **1-2 weeks**
- Static knowledge base (20 vuln types): **1-2 weeks**
- 2 scenario packs (15-18 scenarios): **1-2 weeks**
- Testing & polish: **2-3 weeks**

**Total Estimated Timeline: 10-16 weeks of focused development**


### 9.2 Development Phases

**Phase 1: Foundation (Weeks 1-4)**
- Set up project structure
- Implement basic UI framework with accessibility
- Create data models and storage layer
- Set up multi-user abstraction layer

**Phase 2: Core Features (Weeks 5-8)**
- Implement network scanning engine
- Build LLM routing system
- Create vulnerability detection logic
- Develop network visualization dashboard

**Phase 3: Content & Polish (Weeks 9-12)**
- Build static knowledge base
- Create scenario packs
- Implement scenario import/export
- Comprehensive accessibility testing

**Phase 4: Testing & Launch (Weeks 13-16)**
- User testing with target audiences
- Bug fixes and refinements
- Documentation and tutorials
- Launch preparation

---

## 10. Critical Dependencies & Requirements

### 10.1 Technical Dependencies
- Python 3.9+ with pip
- Node.js (for frontend build tools)
- Elevated privileges for network scanning
- Ollama (optional, for local LLM)

### 10.2 External Services
- HuggingFace Inference Endpoints (for hosted LLM)
- GitHub API (for community scenarios)
- CVE database APIs (for vulnerability data updates)

### 10.3 Legal & Compliance
- EULA/Terms of Service (network scanning disclaimer)
- Privacy Policy (data handling, especially network scans)
- Accessibility compliance documentation (WCAG 2.1 AA)
- Open source licenses (if using GPL/MIT dependencies)


---

## 11. Next Steps

### 11.1 Immediate Actions (Pre-Development)

1. **Map User Flow**
   - Define step-by-step user journey from launch to completion
   - Identify key interaction points and decision trees
   - Validate flow with potential users

2. **Finalize Top 20 Vulnerabilities**
   - Research most common/important vulnerabilities for target audience
   - Define detection methods for each
   - Create remediation guides

3. **Design Network Visualization**
   - Sketch dashboard layouts
   - Determine how to represent devices, connections, and vulnerabilities visually
   - Ensure colorblind-friendly indicators

4. **LLM Training Data Collection**
   - Scrape and organize CVE database
   - Collect MITRE ATT&CK documentation
   - Curate OWASP resources
   - Create custom Q&A pairs for common scenarios

5. **Prototype Testing**
   - Build minimal UI prototype
   - Test with screen readers
   - Validate accessibility approach

### 11.2 Open Questions to Resolve

**Technical:**
- Specific React vs Vue decision (both viable, need to choose)
- Exact LLM model to fine-tune (Llama 3.1 8B vs Mistral 7B vs other)
- Device fingerprinting strategy details
- Database schema refinements

**Content:**
- Final list of 20 vulnerability types (prioritization needed)
- Scenario difficulty progression
- Learning objective frameworks
- Assessment criteria (for future v1.1)

**Business/Legal:**
- Licensing strategy (open source vs proprietary)
- Pricing model (if any)
- Insurance/liability for network scanning tool
- EULA final language review


**User Experience:**
- Onboarding flow for first-time users
- Help system design (contextual help vs documentation)
- Error message clarity and helpfulness
- Feedback mechanisms

---

## 12. Key Design Principles

### 12.1 Accessibility First
Accessibility is not a feature to be added later—it's foundational to every decision. If a feature can't be made accessible, it doesn't ship.

### 12.2 Privacy by Default
User network data never leaves their device. Only anonymized queries go to LLMs. Transparency about data handling is paramount for a security tool.

### 12.3 Progressive Disclosure
Start simple, reveal complexity as needed. Beginners shouldn't be overwhelmed; experts should have depth available.

### 12.4 Educational, Not Just Diagnostic
The goal isn't just to find problems—it's to teach users *why* they're problems and *how* to fix them. The LLM should be a patient teacher.

### 12.5 Fail Gracefully
- No LLM available? Fall back to static knowledge.
- No internet? Work offline.
- Scan fails? Explain why and how to troubleshoot.
- Every failure is an opportunity to teach.

### 12.6 Modular & Extensible
Build for today, architect for tomorrow. The pack system and abstraction layers enable growth without technical debt.

---

## 13. Risk Assessment & Mitigation

### 13.1 Technical Risks

**Risk: Network scanning false positives**
- Mitigation: Conservative detection, clear confidence indicators, manual override options

**Risk: LLM hallucinations about security**
- Mitigation: Static knowledge base as source of truth, RAG with verified sources, disclaimer about AI limitations

**Risk: Performance issues on large networks**
- Mitigation: Scan throttling, progress indicators, cancelable operations, "quick scan" vs "deep scan" modes


**Risk: Accessibility compliance gaps**
- Mitigation: Early testing with disabled users, automated testing CI/CD, accessibility-first component library

### 13.2 Legal & Ethical Risks

**Risk: Tool used for malicious scanning**
- Mitigation: Technical limits (private networks only), comprehensive disclaimers, audit logging, clear terms of service

**Risk: Liability for bad security advice**
- Mitigation: "Educational purposes only" disclaimers, review LLM outputs, cite authoritative sources, professional legal review

**Risk: Privacy violations**
- Mitigation: Network data stays local, transparent privacy policy, no telemetry without explicit opt-in

### 13.3 Market & Adoption Risks

**Risk: Too complex for beginners**
- Mitigation: Excellent onboarding, progressive disclosure, multiple difficulty levels, clear tutorials

**Risk: Not deep enough for experts**
- Mitigation: Advanced scenarios, detailed technical explanations, extensibility for custom content

**Risk: Hosting costs spiral**
- Mitigation: Aggressive caching, rate limiting, encourage local LLM use, tiered access if needed

---

## 14. Success Metrics

### 14.1 Technical Metrics
- Lighthouse accessibility score: 95+
- Scan completion rate: >80%
- Average scan time: <2 minutes for typical home network
- LLM response time: <3 seconds
- App load time: <5 seconds

### 14.2 User Engagement Metrics
- Scenario completion rate: >60%
- Time to first scan: <5 minutes from install
- Return usage: >40% use it more than once
- Community scenario submissions: >10 in first 3 months

### 14.3 Educational Metrics
- Vulnerabilities fixed after using tool: Track via before/after scans
- User confidence increase: Survey before/after
- Retention of knowledge: Follow-up quizzes (v1.1+)


---

## 15. Conclusion

This design document outlines a comprehensive, accessibility-first cybersecurity teaching tool that balances educational value with technical sophistication. The modular architecture enables iterative development while maintaining long-term extensibility.

### Key Strengths of This Design:
1. **Accessibility leadership** in a field that typically neglects it
2. **Hybrid LLM strategy** removes barriers to entry while remaining sustainable
3. **Modular architecture** enables rapid iteration and community contribution
4. **Real scanning** provides immediate practical value beyond pure education
5. **Privacy-first approach** builds trust in a security-focused tool

### Path Forward:
The immediate next step is to map detailed user flows, which will inform UI mockups and help validate the architectural decisions documented here. With 10-16 weeks of focused development, v1.0 represents an achievable but ambitious goal that could significantly impact cybersecurity education accessibility.

---

## Document Control

**Version History:**
- v1.0 (Dec 6, 2024): Initial design document created

**Next Review Date:** After user flow mapping completion

**Document Owner:** [To be filled]

**Status:** Living document - will be updated as decisions evolve

---

## Appendix A: Technology Stack Summary

**Frontend:**
- Framework: React or Vue.js
- Visualization: Dash (Plotly Cytoscape)
- Component Library: Radix UI or Chakra UI (for accessibility)
- Packaging: Tauri (or web-based)

**Backend:**
- API Framework: Python FastAPI
- Database: SQLite (local data)
- Static Data: JSON files

**Network Scanning:**
- python-nmap
- scapy
- mac-vendor-lookup
- netifaces

**LLM:**
- Local: Ollama
- Hosted: HuggingFace Inference Endpoints
- Models: Llama 3.1 8B or Mistral 7B (fine-tuned)

**Testing/Accessibility:**
- Lighthouse CI
- axe-core
- React Testing Library
- Manual screen reader testing


---

## Appendix B: Glossary

**ARIA (Accessible Rich Internet Applications):** W3C specification for making web content accessible to assistive technologies

**CVE (Common Vulnerabilities and Exposures):** System for identifying and cataloging cybersecurity vulnerabilities

**MITRE ATT&CK:** Knowledge base of adversary tactics and techniques based on real-world observations

**OWASP:** Open Web Application Security Project - nonprofit focused on software security

**RAG (Retrieval Augmented Generation):** Technique for enhancing LLM responses with retrieved knowledge

**Tauri:** Framework for building desktop applications using web technologies (lighter than Electron)

**WCAG (Web Content Accessibility Guidelines):** International standards for web accessibility

**Dash:** Python framework for building analytical web applications

**FastAPI:** Modern Python web framework for building APIs

**Ollama:** Tool for running large language models locally

---

## Appendix C: Reference Links

**Accessibility Resources:**
- WCAG 2.1 Guidelines: https://www.w3.org/WAI/WCAG21/quickref/
- Radix UI: https://www.radix-ui.com/
- axe DevTools: https://www.deque.com/axe/devtools/

**Security Knowledge Bases:**
- CVE Database: https://cve.mitre.org/
- MITRE ATT&CK: https://attack.mitre.org/
- OWASP Top 10: https://owasp.org/www-project-top-ten/

**LLM Resources:**
- HuggingFace: https://huggingface.co/
- Ollama: https://ollama.ai/
- Llama Models: https://ai.meta.com/llama/

**Python Libraries:**
- python-nmap: https://pypi.org/project/python-nmap/
- Scapy: https://scapy.net/
- FastAPI: https://fastapi.tiangolo.com/

---

*End of Design Document*
