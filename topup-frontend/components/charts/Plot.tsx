"use client"

import React, { useEffect, useState } from "react"
import dynamic from "next/dynamic"
import { useTheme } from "@/components/theme-provider"
import type { PlotParams } from "react-plotly.js"

// Dynamically import Plotly to avoid SSR issues
const PlotlyComponent = dynamic(() => import("react-plotly.js"), {
    ssr: false,
    loading: () => (
        <div className="flex items-center justify-center h-96 bg-muted/20 rounded-lg">
            <div className="text-muted-foreground">Loading chart...</div>
        </div>
    ),
})

interface PlotProps {
    plotly: Partial<PlotParams>
    className?: string
}

export function Plot({ plotly, className = "" }: PlotProps) {
    const { theme } = useTheme()
    const [resolvedTheme, setResolvedTheme] = useState<"light" | "dark">("light")

    // Resolve system theme to actual light/dark
    useEffect(() => {
        if (theme === "system") {
            const systemTheme = window.matchMedia("(prefers-color-scheme: dark)")
                .matches
                ? "dark"
                : "light"
            setResolvedTheme(systemTheme)
        } else {
            setResolvedTheme(theme as "light" | "dark")
        }
    }, [theme])

    // Theme-aware colors
    const themeColors = {
        light: {
            plot_bgcolor: "rgba(255, 255, 255, 0)",
            paper_bgcolor: "rgba(255, 255, 255, 0)",
            font_color: "hsl(222.2, 84%, 4.9%)",
            grid_color: "hsl(214.3, 31.8%, 91.4%)",
        },
        dark: {
            plot_bgcolor: "rgba(0, 0, 0, 0)",
            paper_bgcolor: "rgba(0, 0, 0, 0)",
            font_color: "hsl(210, 40%, 98%)",
            grid_color: "hsl(217.2, 32.6%, 17.5%)",
        },
    }

    const colors = themeColors[resolvedTheme]

    // Merge theme-aware layout with provided plotly spec
    const themedLayout = {
        ...plotly.layout,
        plot_bgcolor: colors.plot_bgcolor,
        paper_bgcolor: colors.paper_bgcolor,
        font: {
            ...plotly.layout?.font,
            color: colors.font_color,
        },
        xaxis: {
            ...plotly.layout?.xaxis,
            gridcolor: colors.grid_color,
            color: colors.font_color,
        },
        yaxis: {
            ...plotly.layout?.yaxis,
            gridcolor: colors.grid_color,
            color: colors.font_color,
        },
        // Responsive sizing
        autosize: true,
        margin: {
            l: 60,
            r: 40,
            t: 40,
            b: 60,
            ...plotly.layout?.margin,
        },
    }

    // Configuration for interactivity
    const config: Partial<PlotParams["config"]> = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ["lasso2d", "select2d"],
        toImageButtonOptions: {
            format: "png",
            filename: "chart",
            height: 800,
            width: 1200,
            scale: 2,
        },
        ...plotly.config,
    }

    return (
        <div className={`w-full ${className}`}>
            <PlotlyComponent
                data={plotly.data || []}
                layout={themedLayout}
                config={config}
                useResizeHandler={true}
                style={{ width: "100%", height: "100%" }}
                className="min-h-[400px]"
            />
        </div>
    )
}
