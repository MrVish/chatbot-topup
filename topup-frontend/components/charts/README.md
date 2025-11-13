# Charts Components

This directory contains chart-related components for the Topup CXO Assistant.

## Components

- **Plot** (`Plot.tsx`): Theme-aware Plotly chart wrapper
- **ChartCard** (`ChartCard.tsx`): Card container with export functionality

## Quick Start

```tsx
import { Plot, ChartCard } from "@/components/charts"

// Simple chart
<Plot plotly={chartSpec} />

// Chart with export
<ChartCard
  title="Weekly Issuance"
  plotly={chartSpec}
  cacheKey="abc123"
  onExplain={() => showInsights()}
/>
```

## Documentation

For comprehensive component documentation, see:
- **[docs/frontend/COMPONENTS.md](../../docs/frontend/COMPONENTS.md)** - Complete component reference

## Examples

See `ChartCard.example.tsx` for usage examples with different chart types.
