# Cybersecurity Teaching Tool - User Flow Diagrams

## Main User Flow

```mermaid
flowchart TD
    Start([User Launches App]) --> FirstTime{First Time<br/>User?}
    
    FirstTime -->|Yes| Onboarding[Onboarding Wizard]
    FirstTime -->|No| MainMenu[Main Menu]
    
    Onboarding --> AcceptEULA[Accept EULA & Disclaimer]
    AcceptEULA --> AccessibilitySetup[Choose Accessibility Settings]
    AccessibilitySetup --> Tutorial[Quick Tutorial]
    Tutorial --> MainMenu
    
    MainMenu --> Choice{Choose Mode}
    
    Choice -->|Scan Real Network| RealScan[Real Network Scan Flow]
    Choice -->|Practice Scenario| Scenario[Scenario Flow]
    Choice -->|Browse Community| Community[Community Scenarios]
    Choice -->|Settings| Settings[Settings & Preferences]
    
    RealScan --> ScanFlow
    Scenario --> ScenarioFlow
    Community --> BrowseGitHub[Browse GitHub Scenarios]
    BrowseGitHub --> ImportScenario[Import Selected Scenario]
    ImportScenario --> ScenarioFlow
    
    Settings --> MainMenu
```

## Real Network Scan Flow

```mermaid
flowchart TD
    Start([Start Real Scan]) --> Disclaimer{Accept Network<br/>Ownership Disclaimer?}
    
    Disclaimer -->|No| Cancel([Return to Main Menu])
    Disclaimer -->|Yes| DetectNetwork[Auto-detect Local Network]
    
    DetectNetwork --> Confirm{Confirm Network<br/>to Scan?}
    Confirm -->|No| Manual[Manually Enter Network Range]
    Confirm -->|Yes| ScanType{Choose Scan Type}
    Manual --> ScanType
    
    ScanType -->|Quick Scan| QuickScan[Scan Common Ports]
    ScanType -->|Deep Scan| DeepScan[Comprehensive Scan]
    
    QuickScan --> Scanning[Scanning Network...]
    DeepScan --> Scanning
    
    Scanning --> Progress[Show Progress:<br/>5/254 IPs checked]
    Progress --> Complete{Scan Complete}
    
    Complete --> Dashboard[Display Network Dashboard]
    Dashboard --> AnalyzeFlow
```

## Network Dashboard & Analysis Flow

```mermaid
flowchart TD
    Dashboard([Network Dashboard Displayed]) --> Visual[Visual Network Map]
    
    Visual --> Devices[Devices Shown with<br/>Color-coded Severity]
    Devices --> Summary[Summary Stats:<br/>X Critical, Y High, Z Medium]
    
    Summary --> UserAction{User Action}
    
    UserAction -->|Click Device| DeviceDetail[Show Device Details]
    UserAction -->|Click Vulnerability| VulnDetail[Show Vulnerability Details]
    UserAction -->|Filter View| FilterDevices[Filter by Severity/Type]
    UserAction -->|Export Report| ExportReport[Export Scan Report]
    UserAction -->|Re-scan| RescanPrompt{Re-scan Network?}
    
    DeviceDetail --> ShowInfo[Display:<br/>- IP/MAC/Hostname<br/>- Device Type<br/>- Open Ports<br/>- Detected Vulnerabilities]
    
    ShowInfo --> VulnList[List Vulnerabilities<br/>on This Device]
    VulnList --> SelectVuln[User Selects Vulnerability]
    SelectVuln --> VulnDetail
    
    VulnDetail --> LearnFlow
    
    FilterDevices --> Visual
    RescanPrompt -->|Yes| ReScan[Start New Scan]
    RescanPrompt -->|No| UserAction
```

## Learning & Vulnerability Detail Flow

```mermaid
flowchart TD
    Start([Vulnerability Selected]) --> ShowVuln[Display Vulnerability Card]
    
    ShowVuln --> VulnInfo[Show:<br/>- Severity Level<br/>- Description<br/>- Affected Device/Service]
    
    VulnInfo --> UserChoice{User Choice}
    
    UserChoice -->|"Explain This"| LLMExplain[Request LLM Explanation]
    UserChoice -->|"How to Fix"| ShowRemediation[Show Remediation Steps]
    UserChoice -->|"Why Dangerous?"| ShowExploitation[Show Exploitation Details]
    UserChoice -->|"More Info"| ShowResources[Show CVE/External Links]
    
    LLMExplain --> LLMFlow
    
    ShowRemediation --> Steps[Display Step-by-Step Fix]
    Steps --> StepChoice{User Action}
    
    StepChoice -->|"Need Help"| LLMFlow
    StepChoice -->|"Mark as Fixed"| MarkFixed[Mark Vulnerability Fixed]
    StepChoice -->|"Skip for Now"| SaveProgress[Save Progress]
    
    ShowExploitation --> AttackScenario[Show Attack Scenario]
    AttackScenario --> Impact[Explain Potential Impact]
    Impact --> UserChoice
    
    ShowResources --> External[Open External Resources]
    External --> UserChoice
    
    MarkFixed --> VerifyPrompt{Verify Fix?}
    VerifyPrompt -->|Yes| ReScan[Trigger Re-scan]
    VerifyPrompt -->|No| Confirmed[Mark as Resolved]
    
    ReScan --> CheckFixed{Still Vulnerable?}
    CheckFixed -->|Yes| NotFixed[Show: Still Detected]
    CheckFixed -->|No| SuccessFixed[Success! Show Before/After]
    
    NotFixed --> Steps
    SuccessFixed --> UpdateDashboard[Update Dashboard]
    Confirmed --> UpdateDashboard
    SaveProgress --> UpdateDashboard
    
    UpdateDashboard --> NextAction{Continue?}
    NextAction -->|Yes| Dashboard([Return to Dashboard])
    NextAction -->|No| MainMenu([Return to Main Menu])
```

## LLM Interaction Flow

```mermaid
flowchart TD
    Start([LLM Explanation Requested]) --> RouteCheck{Check LLM<br/>Availability}
    
    RouteCheck -->|Ollama Running| UseLocal[Use Local Ollama]
    RouteCheck -->|Ollama Not Found| CheckHosted{Check Hosted<br/>API}
    
    CheckHosted -->|Online + API Available| UseHosted[Use Hosted LLM API]
    CheckHosted -->|Offline or API Down| UseStatic[Use Static Knowledge Base]
    
    UseLocal --> GeneratePrompt[Generate Contextual Prompt]
    UseHosted --> GeneratePrompt
    UseStatic --> LookupStatic[Lookup Pre-written Answer]
    
    GeneratePrompt --> Context[Add Context:<br/>- User's Knowledge Level<br/>- Specific Vulnerability<br/>- Device Type<br/>- Previous Interactions]
    
    Context --> CallLLM[Call LLM]
    CallLLM --> Streaming[Stream Response]
    
    Streaming --> Display[Display Explanation]
    LookupStatic --> Display
    
    Display --> Followup{User Asks<br/>Follow-up?}
    
    Followup -->|Yes| FollowupQ[User Enters Question]
    Followup -->|No| Satisfied[Mark as Helpful?]
    
    FollowupQ --> GeneratePrompt
    
    Satisfied -->|Thumbs Up| LogPositive[Log Positive Feedback]
    Satisfied -->|Thumbs Down| LogNegative[Log Negative Feedback]
    Satisfied -->|No Feedback| Done([Return to Previous Screen])
    
    LogPositive --> Done
    LogNegative --> Done
```

## Scenario-Based Learning Flow

```mermaid
flowchart TD
    Start([Scenario Mode Selected]) --> Browse{Browse Scenarios}
    
    Browse --> PackList[Show Available Packs]
    PackList --> SelectPack[User Selects Pack]
    
    SelectPack --> ScenarioList[Show Scenarios in Pack]
    ScenarioList --> FilterScenarios{Filter Options}
    
    FilterScenarios -->|By Difficulty| FilterDiff[Beginner/Intermediate/Advanced]
    FilterScenarios -->|By Topic| FilterTopic[IoT/Router/Office/etc.]
    FilterScenarios -->|By Completion| FilterStatus[Completed/In Progress/New]
    FilterScenarios -->|Show All| ScenarioList
    
    FilterDiff --> ScenarioList
    FilterTopic --> ScenarioList
    FilterStatus --> ScenarioList
    
    ScenarioList --> SelectScenario[User Selects Scenario]
    SelectScenario --> ShowPreview[Show Scenario Preview:<br/>- Description<br/>- Difficulty<br/>- Est. Time<br/>- Learning Objectives]
    
    ShowPreview --> StartChoice{User Action}
    StartChoice -->|Start Scenario| LoadScenario[Load Fake Network]
    StartChoice -->|Go Back| ScenarioList
    
    LoadScenario --> GenerateNetwork[Generate Network Topology<br/>with Planted Vulnerabilities]
    
    GenerateNetwork --> ScenarioDashboard[Display Scenario Network]
    ScenarioDashboard --> SameAsRealDashboard[Uses Same Dashboard UI<br/>as Real Scans]
    
    SameAsRealDashboard --> UserExplores{User Explores}
    
    UserExplores -->|Click Device| DeviceDetails[Show Device Info]
    UserExplores -->|Click Vulnerability| VulnDetails[Show Vulnerability]
    UserExplores -->|Request Hint| ShowHint[Show Contextual Hint]
    UserExplores -->|Check Progress| ShowObjectives[Show Learning Objectives<br/>Progress]
    
    DeviceDetails --> LearnAndFix[Learning & Fix Flow]
    VulnDetails --> LearnAndFix
    ShowHint --> UserExplores
    ShowObjectives --> UserExplores
    
    LearnAndFix --> UpdateProgress[Update Scenario Progress]
    UpdateProgress --> CheckComplete{All Objectives<br/>Complete?}
    
    CheckComplete -->|No| UserExplores
    CheckComplete -->|Yes| ScenarioComplete[Scenario Complete!]
    
    ScenarioComplete --> ShowResults[Display:<br/>- Time Taken<br/>- Hints Used<br/>- Score/Grade<br/>- Key Learnings]
    
    ShowResults --> NextAction{User Action}
    
    NextAction -->|Try Again| LoadScenario
    NextAction -->|Next Scenario| ScenarioList
    NextAction -->|Main Menu| MainMenu([Return to Main Menu])
```

## Import/Export Custom Scenario Flow

```mermaid
flowchart TD
    Start([User Wants Custom Scenario]) --> Choice{Action}
    
    Choice -->|Import Scenario| Import[Click Import Button]
    Choice -->|Create Scenario| Create[Open Scenario Editor]
    Choice -->|Export Scenario| Export[Select Scenario to Export]
    
    Import --> SelectFile[Select JSON File]
    SelectFile --> Validate[Validate Scenario Format]
    
    Validate --> Valid{Valid Format?}
    Valid -->|Yes| AddToLibrary[Add to User Scenarios]
    Valid -->|No| ShowError[Show Validation Errors]
    
    ShowError --> FixChoice{User Choice}
    FixChoice -->|Try Another| SelectFile
    FixChoice -->|Cancel| Done([Return])
    
    AddToLibrary --> Success[Show Success Message]
    Success --> LaunchPrompt{Launch Now?}
    
    LaunchPrompt -->|Yes| LoadScenario[Load Scenario]
    LaunchPrompt -->|No| Done
    
    Create --> Editor[Scenario Editor Interface]
    Editor --> DefineNetwork[Define Network:<br/>- Add Devices<br/>- Set IPs/MACs<br/>- Configure Services]
    
    DefineNetwork --> PlantVulns[Plant Vulnerabilities:<br/>- Select Vuln Types<br/>- Assign to Devices<br/>- Set Difficulty]
    
    PlantVulns --> SetObjectives[Set Learning Objectives]
    SetObjectives --> AddHints[Add Hints/Guidance]
    AddHints --> Preview[Preview Scenario]
    
    Preview --> PreviewChoice{Satisfied?}
    PreviewChoice -->|No| Editor
    PreviewChoice -->|Yes| SaveScenario[Save Scenario]
    
    SaveScenario --> SaveChoice{Save As}
    SaveChoice -->|Local Only| SaveLocal[Save to User Library]
    SaveChoice -->|Export to Share| ExportFile[Export as JSON]
    
    SaveLocal --> Done
    ExportFile --> ExportLoc[Choose Save Location]
    ExportLoc --> Saved[File Saved]
    Saved --> SharePrompt[Show: Ready to Share<br/>via GitHub or Direct]
    SharePrompt --> Done
    
    Export --> SelectExport[Select Scenario]
    SelectExport --> ExportFile
```

## Accessibility Mode Switching Flow

```mermaid
flowchart TD
    Start([User Accesses Accessibility]) --> Entry{Entry Point}
    
    Entry -->|First Launch| Onboarding[Onboarding Wizard]
    Entry -->|Settings Menu| Settings[Settings Screen]
    Entry -->|Quick Toggle| QuickSwitch[Quick Accessibility Panel]
    
    Onboarding --> AccessibilityOptions[Show Accessibility Options]
    Settings --> AccessibilityOptions
    QuickSwitch --> AccessibilityOptions
    
    AccessibilityOptions --> Options{Select Options}
    
    Options -->|Screen Reader| ScreenReader[Enable Screen Reader Mode]
    Options -->|Visual Mode| VisualMode[Enable Visual Enhancements]
    Options -->|Keyboard Nav| KeyboardMode[Optimize Keyboard Navigation]
    Options -->|Color Settings| ColorSettings[Choose Color Scheme]
    Options -->|Motion Settings| MotionSettings[Reduce Motion Options]
    Options -->|Font Settings| FontSettings[Adjust Font Size/Type]
    
    ScreenReader --> SROptions[Configure:<br/>- Audio Speed<br/>- Verbosity Level<br/>- Auto-read New Content]
    
    VisualMode --> VOptions[Configure:<br/>- Zoom Level<br/>- Focus Highlighting<br/>- High Contrast Mode]
    
    KeyboardMode --> KBOptions[Configure:<br/>- Tab Order<br/>- Shortcuts<br/>- Skip Links]
    
    ColorSettings --> ColorOptions[Choose:<br/>- Normal<br/>- Protanopia<br/>- Deuteranopia<br/>- Tritanopia<br/>- High Contrast]
    
    MotionSettings --> MotionOptions[Configure:<br/>- Disable Animations<br/>- Reduce Transitions<br/>- Static Elements Only]
    
    FontSettings --> FontOptions[Configure:<br/>- Font Size (100-200%)<br/>- Font Family<br/>- Line Spacing]
    
    SROptions --> Preview[Preview Changes]
    VOptions --> Preview
    KBOptions --> Preview
    ColorOptions --> Preview
    MotionOptions --> Preview
    FontOptions --> Preview
    
    Preview --> Satisfied{Satisfied?}
    
    Satisfied -->|No| AccessibilityOptions
    Satisfied -->|Yes| Save[Save Preferences]
    
    Save --> ApplyChanges[Apply Changes Globally]
    ApplyChanges --> ShowConfirmation[Show Confirmation]
    
    ShowConfirmation --> QuickAccessSetup{Add Quick<br/>Access Toggle?}
    
    QuickAccessSetup -->|Yes| AddToToolbar[Add Accessibility Button<br/>to Toolbar]
    QuickAccessSetup -->|No| Done([Return to Previous Screen])
    
    AddToToolbar --> Done
```

## Settings & Preferences Flow

```mermaid
flowchart TD
    Start([Settings Menu Opened]) --> Categories[Show Setting Categories]
    
    Categories --> Select{Select Category}
    
    Select -->|Accessibility| AccessibilityFlow[Accessibility Flow]
    Select -->|Account/Profile| Profile[Profile Settings]
    Select -->|LLM Preferences| LLMSettings[LLM Configuration]
    Select -->|Network Scanning| ScanSettings[Scan Preferences]
    Select -->|Data & Privacy| PrivacySettings[Privacy Controls]
    Select -->|About| AboutScreen[About & Help]
    
    Profile --> ProfileOptions[Configure:<br/>- Display Name<br/>- Knowledge Level<br/>- Learning Goals<br/>- Avatar/Icon]
    
    LLMSettings --> LLMOptions[Configure:<br/>- Prefer Local/Hosted<br/>- API Key (Optional)<br/>- Response Detail Level<br/>- Language]
    
    ScanSettings --> ScanOptions[Configure:<br/>- Default Scan Type<br/>- Timeout Settings<br/>- Port Ranges<br/>- Auto-scan Options]
    
    PrivacySettings --> PrivacyOptions[Configure:<br/>- Data Collection<br/>- Telemetry (Opt-in)<br/>- Export User Data<br/>- Delete All Data]
    
    AboutScreen --> AboutInfo[Show:<br/>- Version Info<br/>- Licenses<br/>- Contact/Support<br/>- Check for Updates]
    
    ProfileOptions --> SaveProfile[Save Changes]
    LLMOptions --> TestConnection[Test LLM Connection]
    ScanOptions --> SaveScan[Save Changes]
    PrivacyOptions --> SavePrivacy[Save Changes]
    
    TestConnection --> ConnectionResult{Connection OK?}
    ConnectionResult -->|Yes| SaveLLM[Save Changes]
    ConnectionResult -->|No| ShowError[Show Error Details]
    ShowError --> LLMOptions
    
    SaveProfile --> Confirm[Show Confirmation]
    SaveLLM --> Confirm
    SaveScan --> Confirm
    SavePrivacy --> Confirm
    
    AboutInfo --> UpdateCheck{Update Available?}
    UpdateCheck -->|Yes| PromptUpdate[Prompt to Update]
    UpdateCheck -->|No| UpToDate[Show: Up to Date]
    
    PromptUpdate --> UpdateChoice{User Choice}
    UpdateChoice -->|Update Now| Download[Download Update]
    UpdateChoice -->|Later| Done([Return])
    
    Download --> Install[Install & Restart]
    Install --> RestartApp([App Restarts])
    
    UpToDate --> Done
    Confirm --> Done
```

## Simplified High-Level User Journey

```mermaid
flowchart LR
    Start([Launch App]) --> Setup{First Time?}
    Setup -->|Yes| Onboard[Onboarding &<br/>Accessibility Setup]
    Setup -->|No| Menu[Main Menu]
    Onboard --> Menu
    
    Menu --> Mode{Choose Mode}
    
    Mode -->|Real Scan| Scan[Scan Network]
    Mode -->|Practice| Scenarios[Load Scenario]
    Mode -->|Community| Browse[Browse & Import]
    
    Scan --> Analyze[Analyze Results]
    Scenarios --> Analyze
    Browse --> Scenarios
    
    Analyze --> Learn[Learn & Fix<br/>Vulnerabilities]
    
    Learn --> LLM[Get AI Help]
    LLM --> Learn
    
    Learn --> Complete{Done?}
    Complete -->|More to Learn| Analyze
    Complete -->|Finished| Menu
    
    style Start fill:#e1f5e1
    style Complete fill:#ffe1e1
    style Learn fill:#e1e5ff
    style LLM fill:#fff4e1
```

## Key Decision Points Summary

```mermaid
flowchart TD
    User([User]) --> Q1{Real Network<br/>or Practice?}
    
    Q1 -->|Real| Q2{Which Device<br/>to Examine?}
    Q1 -->|Practice| Q3{Which Scenario<br/>to Try?}
    
    Q2 --> Q4{How to Learn<br/>About This Issue?}
    Q3 --> Q4
    
    Q4 -->|Read Static Info| Static[Knowledge Base]
    Q4 -->|Ask AI| AI[LLM Explanation]
    Q4 -->|View External| External[CVE/OWASP Links]
    
    Static --> Q5{Try to Fix?}
    AI --> Q5
    External --> Q5
    
    Q5 -->|Yes| Fix[Follow Remediation Steps]
    Q5 -->|Not Yet| Save[Save Progress]
    
    Fix --> Q6{Verify Fixed?}
    Q6 -->|Yes| Rescan[Re-scan to Confirm]
    Q6 -->|No| Trust[Mark as Fixed]
    
    Rescan --> Success[Success!]
    Trust --> Success
    Save --> Next
    Success --> Next[Next Vulnerability]
    
    Next --> Q7{Continue<br/>Learning?}
    Q7 -->|Yes| Q1
    Q7 -->|No| Done([Complete])
    
    style Q4 fill:#fff4e1
    style AI fill:#e1f5ff
    style Success fill:#e1f5e1
```

---

## How to Use These Diagrams

### Viewing the Diagrams
These diagrams are written in Mermaid syntax. To view them rendered:

1. **GitHub/GitLab**: Paste into a .md file in a repository (renders automatically)
2. **Mermaid Live Editor**: Copy/paste into https://mermaid.live/
3. **VS Code**: Install "Markdown Preview Mermaid Support" extension
4. **Notion**: Use /code block with mermaid language
5. **Online Markdown Editors**: Most support Mermaid (Typora, StackEdit, etc.)

### Diagram Legend

**Shapes:**
- `([Rounded])` = Start/End points
- `[Rectangle]` = Process/Action
- `{Diamond}` = Decision point
- `((Circle))` = Connection point

**Flow Types:**
- `-->` = Standard flow
- `-->|Label|` = Conditional flow with label

### Using These Flows for Development

1. **UI Design**: Each box represents a screen or modal that needs designing
2. **API Endpoints**: Each action suggests backend endpoints needed
3. **User Testing**: Follow these paths during usability testing
4. **Feature Planning**: Each branch represents a feature to implement
5. **Bug Tracking**: Reference specific flow paths when reporting issues

### Key Patterns to Notice

1. **Consistency**: Dashboard experience is the same for real scans and scenarios
2. **Help Always Available**: LLM help is accessible from any learning context
3. **Progressive Disclosure**: Users aren't overwhelmed - information revealed as needed
4. **Accessibility First**: Mode switching available throughout the experience
5. **Multiple Paths**: Users can learn by doing OR by reading, their choice

---

## Next Steps for User Flow

Once these flows are validated:

1. **Create Wireframes**: Design actual screens for each box in the flows
2. **Write User Stories**: Convert each flow path into development user stories
3. **Identify Edge Cases**: What happens when things go wrong in each flow?
4. **Plan Transitions**: How do screens transition? Animations? Loading states?
5. **Accessibility Audit**: Review each flow for accessibility compliance
6. **User Testing**: Test these flows with target users before building

---

*Document Version: 1.0*  
*Last Updated: December 6, 2024*  
*Related Document: CyberSec-Teaching-Tool-Design-Doc.md*
