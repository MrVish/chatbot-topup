# Filter Components

This directory contains filter components for the Topup CXO Assistant.

## Components

- **SegmentFilter** (`SegmentFilter.tsx`): Single-select dropdown for segment filtering

## Quick Start

```tsx
import { SegmentFilter } from "@/components/filters"

<SegmentFilter
  name="channel"
  label="Channel"
  options={CHANNEL_OPTIONS}
  value={filters.channel}
  onChange={(value) => setFilters({ ...filters, channel: value })}
/>
```

## Supported Segments

- Channel (9 options)
- Grade (6 options)
- Product Type (3 options)
- Repeat Type (2 options)
- Term (5 options)
- FICO Band (4 options)
- Purpose (6 options)

## Documentation

For comprehensive component documentation, see:
- **[docs/frontend/COMPONENTS.md](../../docs/frontend/COMPONENTS.md)** - Complete component reference
