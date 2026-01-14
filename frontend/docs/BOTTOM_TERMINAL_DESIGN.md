# Bottom Terminal with Status Bar - Design Specification

## Executive Summary

Transform Turbo's layout from a simple sidebar + content structure to a professional VS Code-style workspace with an integrated bottom terminal panel and persistent status bar. This provides quick terminal access without leaving context, improves space efficiency, and creates a familiar development environment.

## Layout Architecture

### Current Layout
```
┌─────────┬────────────────┐
│         │                │
│ Sidebar │    Content     │
│         │                │
└─────────┴────────────────┘
```

### Proposed Layout
```
┌────────────────────────────────────┐
│          Header Bar                │ ← Breadcrumbs, search, actions
├────────┬──────────────────┬────────┤
│        │                  │        │
│ Left   │   Workspace      │ Right  │ ← Main content area
│ Side   │   (content)      │ Side   │
│ bar    │                  │ (opt)  │
├────────┴──────────────────┴────────┤
│ Terminal Panel (resizable)         │ ← Slides up when opened
├─────────────────────────────────────┤
│ Status Bar (always visible)        │ ← Terminal toggle, status info
└─────────────────────────────────────┘
```

**Key Insight**: Status bar is ALWAYS at the bottom. Terminal panel slides up from just above it when toggled.

## Component Architecture

### 1. Status Bar (Bottom, Always Visible)

**File**: `/components/layout/status-bar.tsx`

**Visual Design**:
```
┌──────────────────────────────────────────────────────────────┐
│ [≡] Terminal (2)  |  main  |  Issues: 5  |  [•] Live  |  👤 │
└──────────────────────────────────────────────────────────────┘
```

**Features**:
- **Left Section**:
  - Terminal icon with active session count: `[≡] Terminal (2)`
  - Click to toggle terminal panel
  - Hover shows session names
- **Center Section**:
  - Git branch indicator: `main ↑2 ↓1`
  - Current project context: `Turbo Code`
  - Active issues/tasks count: `Issues: 5 open`
- **Right Section**:
  - Connection status: `[•] Live` (WebSocket connected)
  - Notifications icon with count
  - User avatar/menu
- **Height**: 28px (compact, always visible)
- **Interactions**:
  - Click terminal icon → Toggle terminal panel
  - Click branch → Show git quick actions
  - Click issues → Open issues panel
  - Right-click → Context menu

**State Indicators**:
```typescript
interface StatusBarInfo {
  terminal: {
    activeCount: number;
    isConnected: boolean;
  };
  git: {
    branch: string;
    ahead: number;
    behind: number;
    dirty: boolean;
  };
  project: {
    name: string;
    openIssues: number;
  };
  system: {
    isLive: boolean; // WebSocket connection
    notifications: number;
  };
}
```

### 2. Terminal Panel (Slides Up from Above Status Bar)

**File**: `/components/layout/terminal-panel.tsx`

**Visual Design** (when open):
```
┌─────────────────────────────────────────────────────────────┐
│ ▬▬▬ [drag to resize] ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬│ ← Resize handle
├─────────────────────────────────────────────────────────────┤
│ [bash] Terminal 1  [zsh] Terminal 2  [+] New  [×] Close    │ ← Tab bar
├─────────────────────────────────────────────────────────────┤
│ $ npm run dev                                               │
│ > turbo@1.0.0 dev                                          │
│ > next dev                                                  │
│   ▲ Next.js 15.5.4                                         │ ← Terminal content
│   - Local:        http://localhost:3001                    │
│                                                             │
│ _                                                           │
└─────────────────────────────────────────────────────────────┘
```

**Features**:
- **Resize Handle** (top):
  - 4px draggable area
  - Visual indicator on hover
  - Constrains height: min 200px, max 80vh
  - Smooth drag performance (60fps)
- **Tab Bar**:
  - Multiple terminal sessions in tabs
  - Active tab highlighted
  - Close button per tab
  - "+" button for new session
  - Right-click for tab context menu
- **Terminal Content**:
  - Full xterm.js terminal
  - Connection status indicator
  - Scroll to top/bottom buttons
  - Clear terminal button
  - Split terminal option
- **Animations**:
  - Slide up: 200ms ease-out
  - Slide down: 150ms ease-in
  - Resize: Real-time (no animation)
- **Default Height**: 300px
- **Persisted State**:
  - isOpen (boolean)
  - height (number)
  - activeSessionId (string)
  - sessionIds (string[])

### 3. Workspace Layout Container

**File**: `/components/layout/workspace-layout.tsx`

**CSS Grid Structure**:
```css
.workspace-layout {
  display: grid;
  height: 100vh;
  width: 100vw;
  grid-template-columns:
    var(--sidebar-width, 256px)  /* Left sidebar */
    1fr                          /* Workspace */
    var(--right-sidebar-width, 0px); /* Right sidebar (optional) */

  grid-template-rows:
    56px                           /* Header */
    1fr                            /* Workspace content */
    var(--terminal-height, 0px)    /* Terminal panel */
    28px;                          /* Status bar */

  transition: grid-template-rows 0.2s ease-out;
}

/* When terminal is open */
.workspace-layout[data-terminal-open="true"] {
  --terminal-height: var(--terminal-panel-height, 300px);
}

/* When sidebar is collapsed */
.workspace-layout[data-sidebar-collapsed="true"] {
  --sidebar-width: 64px;
}
```

**Areas**:
```
┌─────────┬──────────────┬─────────┐
│ header  │ header       │ header  │
├─────────┼──────────────┼─────────┤
│ sidebar │ workspace    │ right   │
│         │              │         │
├─────────┴──────────────┴─────────┤
│ terminal                          │
├───────────────────────────────────┤
│ status                            │
└───────────────────────────────────┘
```

### 4. Resizable Handle Component

**File**: `/components/layout/resizable-handle.tsx`

**Implementation**:
```typescript
interface ResizableHandleProps {
  onResize: (delta: number) => void;
  minHeight: number;
  maxHeight: number;
  className?: string;
}

// Visual states:
// Default: 4px height, border-t
// Hover: cursor-ns-resize, background-accent
// Active (dragging): cursor-ns-resize, background-primary

// Drag behavior:
// - Track mouse Y position
// - Calculate delta from start
// - Call onResize with delta
// - Enforce min/max constraints
// - Update CSS variable --terminal-height
```

### 5. Header Component (Top)

**File**: `/components/layout/header.tsx` (existing - enhance)

**Visual Design**:
```
┌────────────────────────────────────────────────────────────┐
│ Home › Projects › Turbo Code    [Search] [⌘K]    [+] [☀] │
└────────────────────────────────────────────────────────────┘
```

**Features**:
- Dynamic breadcrumbs based on route
- Global search (Cmd+K command palette)
- Quick action buttons
- Theme toggle
- Height: 56px

## State Management

### Terminal Panel Store (Zustand)

**File**: `/hooks/use-terminal-panel.ts`

```typescript
interface TerminalPanelState {
  // Panel state
  isOpen: boolean;
  height: number; // 200-80vh

  // Terminal sessions
  sessions: TerminalSession[];
  activeSessionId: string | null;

  // Actions
  toggle: () => void;
  open: () => void;
  close: () => void;
  setHeight: (height: number) => void;

  // Session management
  createSession: (options?: SessionOptions) => Promise<string>;
  closeSession: (sessionId: string) => void;
  setActiveSession: (sessionId: string) => void;

  // Context injection
  createSessionWithContext: (
    projectId?: string,
    issueId?: string
  ) => Promise<string>;
}

interface TerminalSession {
  id: string;
  sessionId: string; // Backend session ID
  title: string;
  shell: string;
  isConnected: boolean;
  createdAt: Date;
  projectId?: string;
  issueId?: string;
}
```

**Persistence**:
- Store: Zustand with persist middleware
- Key: `terminal-panel-storage`
- Persisted fields:
  - `isOpen` (boolean)
  - `height` (number)
  - `sessions` (partial - IDs only)
  - `activeSessionId` (string)
- On mount: Restore sessions from backend API

### Keyboard Shortcuts

**File**: `/hooks/use-keyboard-shortcuts.ts`

```typescript
const shortcuts = {
  'ctrl+`': () => terminalPanel.toggle(),
  'ctrl+shift+`': () => terminalPanel.createSession(),
  'ctrl+j': () => terminalPanel.toggle(), // Alternative
  'ctrl+b': () => sidebar.toggle(),
  'cmd+k': () => commandPalette.open(),
  'ctrl+w': () => terminalPanel.closeSession(activeSessionId),
};
```

## Implementation Plan

### Phase 1: Core Layout Structure (2-3 hours)

**Goal**: Get the basic grid layout working with all regions

1. Create `workspace-layout.tsx` with CSS Grid
2. Update `app/layout.tsx` to use new layout
3. Add `status-bar.tsx` with basic content
4. Test responsive behavior

**Deliverables**:
- ✓ Header, Sidebar, Workspace, Status Bar visible
- ✓ CSS Grid working properly
- ✓ No layout shifts or visual bugs

### Phase 2: Terminal Panel Integration (3-4 hours)

**Goal**: Terminal panel slides up/down from above status bar

1. Create `terminal-panel.tsx` wrapper component
2. Create `use-terminal-panel.ts` Zustand store
3. Add slide up/down animations
4. Integrate existing Terminal component into panel
5. Add basic tab support

**Deliverables**:
- ✓ Terminal panel toggles on/off smoothly
- ✓ State persists across page reloads
- ✓ Terminal icon in status bar functional

### Phase 3: Resizable Terminal (2-3 hours)

**Goal**: User can drag to resize terminal panel

1. Create `resizable-handle.tsx` component
2. Implement mouse drag handlers
3. Add height constraints (min/max)
4. Persist height to localStorage
5. Add touch support for mobile

**Deliverables**:
- ✓ Drag handle works smoothly
- ✓ Height persists across sessions
- ✓ Constraints enforced (200px - 80vh)

### Phase 4: Polish & Interactions (2-3 hours)

**Goal**: Professional feel with smooth interactions

1. Add keyboard shortcuts (Ctrl+`)
2. Implement status bar info displays
3. Add terminal session management (tabs)
4. Smooth transitions and animations
5. Test on different screen sizes
6. Add loading states

**Deliverables**:
- ✓ Keyboard shortcuts working
- ✓ Status bar shows live data
- ✓ Multiple terminal tabs working
- ✓ Responsive on mobile/tablet
- ✓ No performance issues

### Phase 5: Advanced Features (2-3 hours)

**Goal**: Power user features

1. Context-aware terminal creation
2. Split terminal view
3. Terminal search (Ctrl+F)
4. Command history across sessions
5. Terminal themes

**Deliverables**:
- ✓ Terminal opens with project context
- ✓ Split view working
- ✓ Search functionality
- ✓ History persisted

## File Changes Summary

### New Files (6)
1. `/components/layout/workspace-layout.tsx` - Main grid container
2. `/components/layout/terminal-panel.tsx` - Terminal panel wrapper
3. `/components/layout/status-bar.tsx` - Bottom status bar
4. `/components/layout/resizable-handle.tsx` - Drag handle
5. `/hooks/use-terminal-panel.ts` - Terminal state management
6. `/hooks/use-keyboard-shortcuts.ts` - Global keyboard shortcuts

### Modified Files (3)
1. `/app/layout.tsx` - Replace simple flex with WorkspaceLayout
2. `/components/layout/sidebar.tsx` - Remove terminal navigation link
3. `/components/layout/header.tsx` - Enhance with breadcrumbs

### Unchanged (Reused)
1. `/components/terminal/terminal.tsx` - Existing terminal component
2. `/app/terminal/page.tsx` - Keep as dedicated terminal page
3. All API endpoints and backend code

## Responsive Behavior

### Desktop (≥1024px)
- Full layout with optional right sidebar
- Resizable terminal panel (200px - 80vh)
- All status bar sections visible

### Tablet (768px - 1023px)
- Right sidebar hidden
- Sidebar auto-collapses to icons
- Terminal panel (200px - 60vh)
- Status bar shows essential info only

### Mobile (<768px)
- Terminal becomes full-screen overlay
- Status bar shows minimal info
- Slide up animation from bottom edge
- Close button in top-right

## Design Tokens

```css
:root {
  /* Layout dimensions */
  --header-height: 56px;
  --status-bar-height: 28px;
  --sidebar-width: 256px;
  --sidebar-collapsed-width: 64px;
  --terminal-min-height: 200px;
  --terminal-max-height: 80vh;
  --terminal-default-height: 300px;

  /* Animations */
  --terminal-slide-duration: 200ms;
  --terminal-slide-timing: ease-out;

  /* Z-indexes */
  --z-status-bar: 100;
  --z-terminal-panel: 90;
  --z-sidebar: 80;
  --z-header: 70;
}
```

## Accessibility Considerations

1. **Keyboard Navigation**:
   - Tab through status bar items
   - Ctrl+` to toggle terminal (screen reader announced)
   - Arrow keys to switch terminal tabs
   - Escape to close terminal

2. **Screen Readers**:
   - Status bar items have aria-labels
   - Terminal state changes announced
   - Resize handle has role="separator"

3. **Focus Management**:
   - Terminal auto-focuses when opened
   - Focus returns to previous element when closed
   - Tab trap within terminal when active

4. **Color Contrast**:
   - Status bar meets WCAG AA (4.5:1)
   - Terminal themes have high contrast options
   - Resize handle visible in all themes

## Performance Considerations

1. **CSS Grid**: Hardware accelerated, smooth resizing
2. **Terminal Rendering**: xterm.js handles efficiently
3. **State Updates**: Zustand batches updates
4. **Animations**: Use transform/opacity (GPU accelerated)
5. **Lazy Loading**: Terminal component lazy loaded
6. **Memory**: Close inactive sessions after 30min

## Testing Strategy

### Unit Tests
- Terminal panel state transitions
- Resize handle constraints
- Keyboard shortcut handlers
- Session management logic

### Integration Tests
- Layout responds to state changes
- Terminal communicates with backend
- Status bar shows accurate info
- Keyboard shortcuts trigger actions

### E2E Tests
- User can toggle terminal
- User can resize terminal
- User can create multiple sessions
- State persists across page reloads

### Visual Regression
- Screenshot comparison tests
- Dark/light theme consistency
- Responsive breakpoints
- Animation smoothness

## Future Enhancements

1. **Right Sidebar**:
   - AI assistant panel
   - File outline/structure
   - Properties inspector
   - Toggleable like left sidebar

2. **Terminal Features**:
   - Terminal recording/playback
   - Share terminal session (read-only)
   - Terminal templates (common commands)
   - AI command suggestions

3. **Status Bar**:
   - Customizable sections
   - Extension system for plugins
   - Notification center
   - Quick actions menu

4. **Layout**:
   - Save/restore layouts
   - Multiple workspace configurations
   - Zen mode (hide all UI)
   - Picture-in-picture terminal

## Migration Path

**Non-Breaking Changes**:
- Keep `/terminal` page for dedicated view
- Existing functionality unchanged
- No API changes required
- Gradual feature rollout

**User Communication**:
- Tooltip on first visit: "New! Press Ctrl+` for quick terminal"
- Changelog entry explaining new layout
- Video tutorial showing features
- Keyboard shortcuts cheat sheet

## Success Metrics

- **Adoption**: 70% of users use bottom terminal within 30 days
- **Efficiency**: 30% reduction in context switching (measured by page navigation)
- **Satisfaction**: 4.5+ rating on terminal UX survey
- **Performance**: <50ms for terminal toggle animation
- **Reliability**: <1% terminal session failures

## Conclusion

This design provides a professional, efficient, and familiar workspace layout that matches industry-standard IDEs. The bottom terminal with status bar creates a seamless development experience without requiring users to leave their current context, while maintaining all existing functionality and improving space utilization.

The phased implementation approach allows for incremental delivery and testing, with clear deliverables at each stage. The design is extensible for future enhancements (right sidebar, advanced terminal features) while maintaining backward compatibility and a smooth migration path.