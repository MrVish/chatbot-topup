# Frontend Components Documentation

This document provides comprehensive documentation for all components in the Topup CXO Assistant frontend.

## Overview

The frontend is built with Next.js 14, TypeScript, TailwindCSS, and shadcn/ui components.

## Component Structure

```
components/
├── chat/           # Chat UI components
├── charts/         # Chart rendering components
├── filters/        # Segment filter components
├── ui/             # shadcn/ui base components
├── theme-provider.tsx
└── theme-toggle.tsx
```

## Chat Components

### ChatWindow

**File**: `components/chat/ChatWindow.tsx`

Displays the chat message history with user messages and assistant responses.

### ChatInput

**File**: `components/chat/ChatInput.tsx`

Text input component for sending messages with auto-resize and keyboard shortcuts.

**Features:**
- Auto-resize textarea (min 80px, max 200px)
- Keyboard shortcuts (Enter to send, Shift+Enter for new line)
- Stop button during streaming
- Disabled state during processing

**Usage:**
```tsx
<ChatInput 
  onSend={(message) => handleSend(message)} 
  onStop={() => handleStop()} 
/>
```

### ChatMessage

**File**: `components/chat/ChatMessage.tsx`

Renders individual chat messages with role-based styling.

### Toolbar

**File**: `components/chat/Toolbar.tsx`

Provides quick access to time period filters, segment filters, and theme toggle.

**Features:**
- 4 time period chips (Last 7 days, Last full week, Last full month, Last 3 full months)
- 7 segment filter dropdowns
- Theme toggle button

**Usage:**
```tsx
<Toolbar onSendQuery={(query) => handleQuery(query)} />
```

## Chart Components

### Plot

**File**: `components/charts/Plot.tsx`

Theme-aware Plotly chart wrapper for rendering interactive visualizations.

**Features:**
- Theme-aware colors (light/dark mode)
- Responsive sizing
- Interactive hover tooltips, zoom, pan
- SSR-safe (dynamically loaded)
- Export functionality via mode bar

**Props:**
```typescript
interface PlotProps {
  plotly: Partial<PlotParams>  // Plotly JSON specification
  className?: string
}
```

**Usage:**
```tsx
<Plot plotly={chartSpec} />
```

**Theme Colors:**

Light Theme:
- Background: Transparent
- Font: Dark gray
- Grid: Light gray

Dark Theme:
- Background: Transparent
- Font: Light gray
- Grid: Dark gray

### ChartCard

**File**: `components/charts/ChartCard.tsx`

Comprehensive card container for displaying charts with export functionality.

**Features:**
- Card container with title and description
- Integrated Plot component
- CSV export via `/export` endpoint
- PNG export with client-side rendering
- Explain button for insights
- Error handling and loading states

**Props:**
```typescript
interface ChartCardProps {
  title?: string
  description?: string
  plotly: Partial<PlotParams>
  cacheKey?: string
  onExplain?: () => void
  className?: string
}
```

**Usage:**
```tsx
<ChartCard
  title="Weekly Issuance Trend"
  description="Last 4 weeks"
  plotly={chartSpec}
  cacheKey="abc123"
  onExplain={() => showInsights()}
/>
```

**Export Functionality:**

CSV Export:
1. Calls `GET /export?cache_key={cacheKey}&format=csv`
2. Backend retrieves cached DataFrame
3. Converts to CSV format
4. Browser triggers download

PNG Export:
1. Calls `GET /export?cache_key={cacheKey}&format=png`
2. Backend returns chart spec
3. Uses Plotly's `downloadImage()` function
4. Downloads PNG file

## Filter Components

### SegmentFilter

**File**: `components/filters/SegmentFilter.tsx`

Single-select dropdown for filtering data by business segments.

**Features:**
- Single-select dropdown using shadcn/ui Select
- Clear/reset button
- Badge display for selected values
- Type-safe with TypeScript
- Zustand integration

**Props:**
```typescript
interface SegmentFilterProps {
  name: string
  label: string
  options: readonly FilterOption[]
  value: string | number | undefined
  onChange: (value: string | number | undefined) => void
  className?: string
  placeholder?: string
}
```

**Usage:**
```tsx
<SegmentFilter
  name="channel"
  label="Channel"
  options={CHANNEL_OPTIONS}
  value={filters.channel}
  onChange={(value) => setFilters({ ...filters, channel: value })}
/>
```

**Supported Segments:**
- Channel (9 options)
- Grade (6 options)
- Product Type (3 options)
- Repeat Type (2 options)
- Term (5 options)
- FICO Band (4 options)
- Purpose (6 options)

## Theme Components

### ThemeProvider

**File**: `components/theme-provider.tsx`

Manages global theme state and persists user preferences.

**Features:**
- Supports light, dark, and system modes
- Persists to localStorage
- Automatic system detection
- DOM updates with theme classes

**Usage:**
```tsx
<ThemeProvider defaultTheme="system" storageKey="topup-ui-theme">
  {children}
</ThemeProvider>
```

### ThemeToggle

**File**: `components/theme-toggle.tsx`

Dropdown menu button for switching between themes.

**Features:**
- Sun/Moon icon animation
- Light, Dark, and System options
- Integrated into Toolbar

**Usage:**
```tsx
<ThemeToggle />
```

## UI Components

Base components from shadcn/ui:

- **Badge**: Display tags and labels
- **Button**: Interactive buttons with variants
- **Card**: Container with header and content
- **DropdownMenu**: Dropdown menus
- **Input**: Text input fields
- **Select**: Dropdown select
- **Skeleton**: Loading placeholders
- **Tabs**: Tabbed interfaces
- **Textarea**: Multi-line text input

## State Management

### useChatStore

**File**: `hooks/useChatStore.ts`

Zustand store for managing chat state.

**State:**
```typescript
{
  messages: Message[]
  filters: SegmentFilters
  running: boolean
  pushUser: (text: string) => void
  pushAssistant: (text: string) => void
  setFilters: (filters: SegmentFilters) => void
  setRunning: (running: boolean) => void
  clearMessages: () => void
}
```

### useSSE

**File**: `hooks/useSSE.ts`

Custom hook for handling Server-Sent Events streaming.

**Usage:**
```typescript
const { connect, disconnect } = useSSE({
  onPartial: (text) => console.log(text),
  onPlan: (plan) => console.log(plan),
  onCard: (card) => console.log(card),
  onDone: () => console.log('Done'),
  onError: (error) => console.error(error),
})
```

## Styling

### TailwindCSS

All components use Tailwind utility classes for styling.

### Theme-Aware Styling

Use Tailwind's `dark:` modifier for theme-specific styles:

```tsx
<div className="bg-white dark:bg-gray-900 text-black dark:text-white">
  Content
</div>
```

### CSS Variables

Theme-specific CSS variables defined in `app/globals.css`:

- Background, foreground
- Card, primary, secondary
- Muted, accent, destructive
- Border, input, ring

## Testing

Frontend tests are located in `tests/`:

```bash
# Run all tests
npm test

# Run with coverage
npm test -- --coverage
```

## Accessibility

All components follow accessibility best practices:
- Proper ARIA labels
- Keyboard navigation
- Screen reader support
- Focus management
- Color contrast compliance

## Performance

- Components use React.memo where appropriate
- Lazy loading for heavy components
- Optimized re-renders with Zustand
- Debounced inputs
- Virtual scrolling for long lists

## Browser Compatibility

- ✅ Chrome/Edge (Chromium)
- ✅ Firefox
- ✅ Safari
- ✅ Mobile browsers
