/**
 * ChartCard Component Usage Examples
 * 
 * This file demonstrates various use cases for the ChartCard component.
 * These examples are for reference and testing purposes.
 */

import { ChartCard } from "./ChartCard"

// Example 1: Basic Line Chart
export function BasicLineChartExample() {
    const plotlySpec: any = {
        data: [
            {
                x: ["2024-01-01", "2024-01-08", "2024-01-15", "2024-01-22"],
                y: [1200000, 1350000, 1280000, 1420000],
                type: "scatter" as const,
                mode: "lines+markers" as const,
                name: "Issuance",
                line: { color: "#3b82f6" },
            },
        ],
        layout: {
            title: "Weekly Issuance Trend",
            xaxis: { title: "Week" },
            yaxis: { title: "Amount ($)" },
        },
    }

    return (
        <ChartCard
            title="Weekly Issuance Trend"
            description="Last 4 weeks"
            plotly={plotlySpec}
            cacheKey="example_line_chart_123"
            onExplain={() => console.log("Explain clicked")}
        />
    )
}

// Example 2: Grouped Bar Chart (Forecast vs Actual)
export function ForecastVsActualExample() {
    const plotlySpec: any = {
        data: [
            {
                x: ["Grade A", "Grade B", "Grade C", "Grade D"],
                y: [1500000, 1200000, 900000, 600000],
                type: "bar" as const,
                name: "Forecast",
                marker: { color: "#94a3b8" },
            },
            {
                x: ["Grade A", "Grade B", "Grade C", "Grade D"],
                y: [1600000, 1100000, 950000, 580000],
                type: "bar" as const,
                name: "Actual",
                marker: { color: "#3b82f6" },
            },
        ],
        layout: {
            title: "Forecast vs Actual by Grade",
            xaxis: { title: "Grade" },
            yaxis: { title: "Issuance ($)" },
            barmode: "group" as const,
        },
    }

    return (
        <ChartCard
            title="Forecast vs Actual Issuance"
            description="Last month by grade"
            plotly={plotlySpec}
            cacheKey="example_forecast_actual_456"
            onExplain={() => console.log("Explain forecast variance")}
        />
    )
}

// Example 3: Funnel Chart
export function FunnelChartExample() {
    const plotlySpec: any = {
        data: [
            {
                type: "funnel" as const,
                y: ["Submissions", "Approvals", "Issuances"],
                x: [10000, 7500, 6000],
                textinfo: "value+percent initial" as const,
                marker: {
                    color: ["#3b82f6", "#8b5cf6", "#10b981"],
                },
            },
        ],
        layout: {
            title: "Conversion Funnel",
        },
    }

    return (
        <ChartCard
            title="Email Channel Funnel"
            description="Last full month"
            plotly={plotlySpec}
            cacheKey="example_funnel_789"
            onExplain={() => console.log("Explain funnel conversion")}
        />
    )
}

// Example 4: Pie Chart (Distribution)
export function DistributionPieExample() {
    const plotlySpec: any = {
        data: [
            {
                type: "pie" as const,
                labels: ["Email", "OMB", "Direct Mail", "Partner"],
                values: [45, 30, 15, 10],
                marker: {
                    colors: ["#3b82f6", "#8b5cf6", "#10b981", "#f59e0b"],
                },
            },
        ],
        layout: {
            title: "Issuance by Channel",
        },
    }

    return (
        <ChartCard
            title="Channel Distribution"
            description="Last 30 days"
            plotly={plotlySpec}
            cacheKey="example_pie_012"
        />
    )
}

// Example 5: Without Cache Key (No Export)
export function NoExportExample() {
    const plotlySpec: any = {
        data: [
            {
                x: [1, 2, 3, 4, 5],
                y: [10, 15, 13, 17, 20],
                type: "scatter" as const,
                mode: "lines" as const,
            },
        ],
        layout: {
            title: "Simple Trend",
        },
    }

    return (
        <ChartCard
            title="Simple Chart"
            description="No export functionality"
            plotly={plotlySpec}
        // No cacheKey - export buttons won't appear
        />
    )
}

// Example 6: With Custom Explain Handler
export function CustomExplainExample() {
    const handleExplain = () => {
        // Custom explain logic
        alert("Showing insights:\n\n" +
            "• Issuance increased 18% WoW\n" +
            "• Email channel drove 60% of growth\n" +
            "• Grade A segment up 25%")
    }

    const plotlySpec: any = {
        data: [
            {
                x: ["Week 1", "Week 2", "Week 3", "Week 4"],
                y: [1000000, 1100000, 1250000, 1420000],
                type: "bar" as const,
                marker: { color: "#3b82f6" },
            },
        ],
        layout: {
            title: "Weekly Growth",
            xaxis: { title: "Week" },
            yaxis: { title: "Amount ($)" },
        },
    }

    return (
        <ChartCard
            title="Weekly Issuance Growth"
            description="Last 4 weeks"
            plotly={plotlySpec}
            cacheKey="example_custom_explain_345"
            onExplain={handleExplain}
        />
    )
}

// Example 7: Multi-Series Line Chart
export function MultiSeriesExample() {
    const plotlySpec: any = {
        data: [
            {
                x: ["Jan", "Feb", "Mar", "Apr"],
                y: [1200000, 1350000, 1280000, 1420000],
                type: "scatter" as const,
                mode: "lines+markers" as const,
                name: "Email",
                line: { color: "#3b82f6" },
            },
            {
                x: ["Jan", "Feb", "Mar", "Apr"],
                y: [800000, 850000, 920000, 980000],
                type: "scatter" as const,
                mode: "lines+markers" as const,
                name: "OMB",
                line: { color: "#8b5cf6" },
            },
            {
                x: ["Jan", "Feb", "Mar", "Apr"],
                y: [400000, 420000, 450000, 480000],
                type: "scatter" as const,
                mode: "lines+markers" as const,
                name: "Direct Mail",
                line: { color: "#10b981" },
            },
        ],
        layout: {
            title: "Issuance by Channel",
            xaxis: { title: "Month" },
            yaxis: { title: "Amount ($)" },
        },
    }

    return (
        <ChartCard
            title="Multi-Channel Trend"
            description="Q1 2024"
            plotly={plotlySpec}
            cacheKey="example_multi_series_678"
            onExplain={() => console.log("Explain multi-channel trends")}
        />
    )
}

// Example 8: Scatter Plot (Relationship)
export function ScatterPlotExample() {
    const plotlySpec: any = {
        data: [
            {
                x: [640, 660, 680, 700, 720, 740, 760, 780],
                y: [5.2, 4.8, 4.5, 4.2, 3.9, 3.6, 3.3, 3.0],
                type: "scatter" as const,
                mode: "markers" as const,
                marker: {
                    size: 10,
                    color: "#3b82f6",
                },
            },
        ],
        layout: {
            title: "FICO vs APR Relationship",
            xaxis: { title: "FICO Score" },
            yaxis: { title: "APR (%)" },
        },
    }

    return (
        <ChartCard
            title="Credit Score vs Interest Rate"
            description="Last 30 days"
            plotly={plotlySpec}
            cacheKey="example_scatter_901"
            onExplain={() => console.log("Explain FICO-APR relationship")}
        />
    )
}
