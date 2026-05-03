# UI Implementation Plan v2 – Agentic SDLC Orchestrator
Stack: React (latest) + Vite + TypeScript + Tailwind CSS v4

---

## 0. Key Improvements Over Previous Version

This version includes:
- Component library-first approach
- Domain-driven UI components
- Better state architecture
- Cleaner separation of concerns
- Codex-friendly modular prompts

---

## 1. Project Setup (Modern Vite + Tailwind v4)

### Prompt 1: Create Project + Install Tailwind (NEW METHOD)

Create React + TypeScript app using Vite.

Commands:
- npm create vite@latest orchestrator-ui -- --template react-ts
- cd orchestrator-ui
- npm install

Install Tailwind using Vite plugin:

- npm install tailwindcss @tailwindcss/vite

Update vite.config.ts:


import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
plugins: [react(), tailwindcss()]
});


Create src/index.css:

@import "tailwindcss";


Ensure app runs.

---

## 2. Folder Structure (IMPORTANT)

### Prompt 2: Setup Scalable Structure

Create folders:

src/
  components/
    ui/
    domain/
  layouts/
  pages/
  store/
  services/
  hooks/
  types/

Explanation:
- ui/ → generic reusable components
- domain/ → business-specific components (Agents, Sections, etc.)

---

## 3. Design System (Tailwind Layer)

### Prompt 3: Tailwind Config Extension

Update theme:

- colors:
  primary: blue-500
  success: green-500
  warning: yellow-500

Add:
- borderRadius: xl
- boxShadow: card

---

## 4. UI Component Library (CRITICAL CHANGE)

### Prompt 4: Create Base UI Components

Create:

src/components/ui/

- Card.tsx
- Button.tsx
- Badge.tsx
- Input.tsx
- Textarea.tsx
- Tabs.tsx

Rules:
- Accept props for variant (primary, secondary)
- Use Tailwind internally
- No business logic

---

## 5. Domain Components (Your Product Logic)

### Prompt 5: Create Domain Components

Create:

src/components/domain/

- AgentCard.tsx
- AgentsPanel.tsx
- SectionEditor.tsx
- SectionTabs.tsx
- SectionHistory.tsx
- HITLPanel.tsx
- LogsTable.tsx

Each must:
- use UI components
- accept typed props

---

## 6. App Layout (3-Panel System)

### Prompt 6: Create Layout

File: layouts/AppLayout.tsx

Structure:


Sidebar (240px)
Main (flex-1)
ActionPanel (320px)


Use:
- flex
- h-screen
- overflow-hidden

---

## 7. Sidebar

### Prompt 7: Sidebar Component

File: components/domain/Sidebar.tsx

Features:
- Project selector
- Navigation:
  - PRD
  - BA
  - Architecture
- Execution:
  - Agents
  - Logs

---

## 8. Agents at Work (TOP PRIORITY UI)

### Prompt 8: AgentsPanel

Position:
- MUST be above section tabs

Features:
- horizontal cards
- workflow arrows
- progress bar
- current active node highlight

AgentCard props:

{
name,
role,
status,
progress,
eta
}


---

## 9. Section Tabs

### Prompt 9: Tabs Component

Tabs:
- Overview
- Features
- User Flow
- Non-Functional

Behavior:
- controlled state
- active styling

---

## 10. Section Editor

### Prompt 10: Editor Component

Features:
- editable textarea
- version display
- save + regenerate buttons

Props:
- value
- onChange
- onSave
- onRegenerate

---

## 11. Section History

### Prompt 11: History Table

Features:
- table layout
- version list
- view button

Columns:
- Version
- Updated By
- Time
- Summary

---

## 12. HITL Action Panel (RIGHT SIDE)

### Prompt 12: HITLPanel

Sections:

1. Actions:
   - Approve
   - Edit
   - Regenerate

2. Mode:
   - Single
   - Cascade

3. Input:
   - textarea

4. Impact Preview:
   - list

5. Execution Info:
   - current node
   - next node

---

## 13. Logs Table

### Prompt 13: LogsTable

Columns:
- Node
- Model
- Tokens
- Latency
- Status

Feature:
- expandable row (show prompt + response)

---

## 14. State Management (Zustand)

### Prompt 14: Create Store

File: store/useAppStore.ts

State:

projectId
currentNode
selectedSection
artifacts
agents
logs


Actions:
- setProject
- updateSection
- setAgents
- setLogs

---

## 15. API Layer

### Prompt 15: API Service

File: services/api.ts

Use axios.

Functions:
- startWorkflow()
- getSections()
- updateSection()
- hitlAction()
- getLogs()

---

## 16. HITL Integration

### Prompt 16: Connect UI to Backend

Actions:
- Approve → hitlAction("approve")
- Regenerate → send section + mode
- Edit → send content

Update store after response.

---

## 17. UX Behavior Rules (IMPORTANT)

### Prompt 17: Add UI Logic

Implement:

1. Disable buttons during execution
2. Show loading spinners
3. Highlight active agent
4. Show impact preview before regeneration
5. Keep AgentsPanel always visible

---

## 18. Page Composition

### Prompt 18: Dashboard Page

File: pages/Dashboard.tsx

Layout:

AppLayout
  ├── Sidebar
  ├── Main
  │     ├── Header
  │     ├── AgentsPanel
  │     ├── SectionTabs
  │     ├── SectionEditor
  │     ├── SectionHistory
  └── HITLPanel

---

## 19. Optional Enhancements

### Prompt 19: Add Enhancements

- Toast notifications
- Dark mode toggle
- Skeleton loaders

---

## FINAL RULES

- Do NOT mix UI + business logic
- Use domain components for workflow logic
- Keep AgentsPanel always visible
- All actions must go through HITL panel
- Reuse components aggressively

---