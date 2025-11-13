"use client"

import React, { useState } from "react"
import { Download, FileText, Image, MessageSquare } from "lucide-react"
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Plot } from "./Plot"
import type { PlotParams } from "react-plotly.js"

interface ChartCardProps {
    title?: string
    description?: string
    plotly: Partial<PlotParams>
    cacheKey?: string
    onExplain?: () => void
    className?: string
}

export function ChartCard({
    title = "Chart",
    description,
    plotly,
    cacheKey,
    onExplain,
    className = "",
}: ChartCardProps) {
    const [isExporting, setIsExporting] = useState(false)
    const [exportError, setExportError] = useState<string | null>(null)

    const apiUrl = process.env.NEXT_PUBLIC_API || "http://localhost:8000"

    /**
     * Handle CSV export by calling the /export endpoint
     */
    const handleExportCSV = async () => {
        if (!cacheKey) {
            setExportError("No cache key available for export")
            return
        }

        setIsExporting(true)
        setExportError(null)

        try {
            const response = await fetch(
                `${apiUrl}/export?cache_key=${encodeURIComponent(cacheKey)}&format=csv`,
                {
                    method: "GET",
                }
            )

            if (!response.ok) {
                const errorData = await response.json()
                throw new Error(errorData.detail || "Export failed")
            }

            // Trigger file download
            const blob = await response.blob()
            const url = window.URL.createObjectURL(blob)
            const a = document.createElement("a")
            a.href = url
            a.download = `topup_export_${cacheKey.substring(0, 8)}.csv`
            document.body.appendChild(a)
            a.click()
            window.URL.revokeObjectURL(url)
            document.body.removeChild(a)
        } catch (error) {
            console.error("CSV export error:", error)
            setExportError(
                error instanceof Error ? error.message : "Failed to export CSV"
            )
        } finally {
            setIsExporting(false)
        }
    }

    /**
     * Handle PNG export using Plotly's built-in download functionality
     * The backend returns the chart spec for client-side rendering
     */
    const handleExportPNG = async () => {
        if (!cacheKey) {
            setExportError("No cache key available for export")
            return
        }

        setIsExporting(true)
        setExportError(null)

        try {
            const response = await fetch(
                `${apiUrl}/export?cache_key=${encodeURIComponent(cacheKey)}&format=png`,
                {
                    method: "GET",
                }
            )

            if (!response.ok) {
                const errorData = await response.json()
                throw new Error(errorData.detail || "Export failed")
            }

            const data = await response.json()

            // Use Plotly's downloadImage function via the mode bar
            // For now, we'll use the browser's built-in Plotly download
            // which is already available in the Plot component's mode bar

            // Alternative: Trigger the Plotly mode bar download button programmatically
            // This is a workaround since we're using client-side rendering
            const plotlyDiv = document.querySelector(".js-plotly-plot") as any
            if (plotlyDiv && (window as any).Plotly) {
                await (window as any).Plotly.downloadImage(plotlyDiv, {
                    format: "png",
                    filename: data.filename || `topup_chart_${cacheKey.substring(0, 8)}`,
                    height: 800,
                    width: 1200,
                    scale: 2,
                })
            } else {
                // Fallback: Show message to use mode bar
                setExportError(
                    "Please use the camera icon in the chart toolbar to download as PNG"
                )
            }
        } catch (error) {
            console.error("PNG export error:", error)
            setExportError(
                error instanceof Error ? error.message : "Failed to export PNG"
            )
        } finally {
            setIsExporting(false)
        }
    }

    return (
        <Card className={className}>
            <CardHeader>
                <div className="flex items-start justify-between">
                    <div className="flex-1">
                        <CardTitle className="text-lg">{title}</CardTitle>
                        {description && (
                            <CardDescription className="mt-1">
                                {description}
                            </CardDescription>
                        )}
                    </div>
                    <div className="flex items-center gap-2">
                        {/* Explain button */}
                        {onExplain && (
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={onExplain}
                                className="gap-2"
                            >
                                <MessageSquare className="h-4 w-4" />
                                Explain
                            </Button>
                        )}

                        {/* Export dropdown menu */}
                        {cacheKey && (
                            <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        disabled={isExporting}
                                        className="gap-2"
                                    >
                                        <Download className="h-4 w-4" />
                                        Export
                                    </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end">
                                    <DropdownMenuItem
                                        onClick={handleExportCSV}
                                        disabled={isExporting}
                                        className="gap-2"
                                    >
                                        <FileText className="h-4 w-4" />
                                        Export as CSV
                                    </DropdownMenuItem>
                                    <DropdownMenuItem
                                        onClick={handleExportPNG}
                                        disabled={isExporting}
                                        className="gap-2"
                                    >
                                        <Image className="h-4 w-4" />
                                        Export as PNG
                                    </DropdownMenuItem>
                                </DropdownMenuContent>
                            </DropdownMenu>
                        )}
                    </div>
                </div>
                {exportError && (
                    <div className="mt-2 text-sm text-destructive">
                        {exportError}
                    </div>
                )}
            </CardHeader>
            <CardContent>
                <Plot plotly={plotly} />
            </CardContent>
        </Card>
    )
}
