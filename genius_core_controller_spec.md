# 🧠 GENIUS CORE Controller Module – TRAXORA System Orchestrator

## Purpose
Centralize flow control, UI navigation, agent status, and data context across TRAXORA.

---

## 🔧 Components

### 1. DashboardController (React Context Provider)
- Holds app-wide state:
  - `activePage`
  - `uploadedFiles`
  - `agentStatus: { driverClassifier, geoValidator, reportGenerator, outputFormatter }`
  - `lastRunStatus`
  - `errorLog`

### 2. Sidebar Navigation
- Permanent links to:
  - Dashboard
  - Upload Files
  - View Reports
  - Asset Manager
  - Logs
  - Settings

### 3. Agent Pipeline Monitor
- Tracks readiness:
  - `isFileUploaded(type)`
  - `isAgentReady(name)`
  - `wasReportGenerated(date)`
- Display badge/status in UI per stage

### 4. Flow Resync + Reset
- Button to re-run ingestion/classification if downstream report failed
- Clears agent cache and resets errors

---

## 🔄 State Sync

- Use React Context to persist state between module views
- On upload, trigger `.onFileReceived()` → update context → ping agents

---

## 🗃 Example: Global Context Schema (TypeScript)
```ts
interface GeniusCoreContext {
  activePage: string;
  uploadedFiles: { [fileType: string]: FileMeta };
  agentStatus: {
    driverClassifier: AgentStatus;
    geoValidator: AgentStatus;
    reportGenerator: AgentStatus;
    outputFormatter: AgentStatus;
  };
  lastRunStatus: {
    date: string;
    success: boolean;
    error?: string;
  };
  logs: string[];
}
```

---

## ✅ Outcomes

- No more dangling modules or dead-ends
- Unified flow across ingestion → classification → output
- Clear navigation + persistent state
- Replit knows what worked, what failed, and what to retry

---

## Optional Enhancements
- Use localStorage/sessionStorage to preserve flow across refreshes
- Add notification banners for errors, completion, or dependency blockers
