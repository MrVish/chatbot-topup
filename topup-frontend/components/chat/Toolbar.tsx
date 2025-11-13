"use client"

import * as React from "react"
import { useChatStore } from "@/hooks/useChatStore"
import { Badge } from "@/components/ui/badge"
import { ThemeToggle } from "@/components/theme-toggle"
import { SegmentFilter } from "@/components/filters"
import { cn } from "@/lib/utils"

/**
 * Time period options for quick filtering
 */
const TIME_PERIODS = [
    { label: "Last 7 days", value: "last 7 days" },
    { label: "Last full week", value: "last full week" },
    { label: "Last full month", value: "last full month" },
    { label: "Last 3 full months", value: "last 3 full months" },
] as const

/**
 * Segment filter options based on SEGMENT_VALUES.md
 */
const CHANNEL_OPTIONS = [
    { label: "OMB", value: "OMB" },
    { label: "Email", value: "Email" },
    { label: "Search", value: "Search" },
    { label: "D2LC", value: "D2LC" },
    { label: "DM", value: "DM" },
    { label: "LT", value: "LT" },
    { label: "Experian", value: "Experian" },
    { label: "Karma", value: "Karma" },
    { label: "Small Partners", value: "Small Partners" },
] as const

const GRADE_OPTIONS = [
    { label: "P1", value: "P1" },
    { label: "P2", value: "P2" },
    { label: "P3", value: "P3" },
    { label: "P4", value: "P4" },
    { label: "P5", value: "P5" },
    { label: "P6", value: "P6" },
] as const

const PROD_TYPE_OPTIONS = [
    { label: "Prime", value: "Prime" },
    { label: "NP", value: "NP" },
    { label: "D2P", value: "D2P" },
] as const

const REPEAT_TYPE_OPTIONS = [
    { label: "Repeat", value: "Repeat" },
    { label: "New", value: "New" },
] as const

const TERM_OPTIONS = [
    { label: "36 months", value: 36 },
    { label: "48 months", value: 48 },
    { label: "60 months", value: 60 },
    { label: "72 months", value: 72 },
    { label: "84 months", value: 84 },
] as const

const FICO_BAND_OPTIONS = [
    { label: "<640", value: "<640" },
    { label: "640-699", value: "640-699" },
    { label: "700-759", value: "700-759" },
    { label: "760+", value: "760+" },
] as const

const PURPOSE_OPTIONS = [
    { label: "Debt Consolidation", value: "debt_consolidation" },
    { label: "Home Improvement", value: "home_improvement" },
    { label: "Major Purchase", value: "major_purchase" },
    { label: "Medical", value: "medical" },
    { label: "Car", value: "car" },
    { label: "Other", value: "other" },
] as const

/**
 * Toolbar Component Props
 */
interface ToolbarProps {
    onSendQuery?: (query: string) => void
    className?: string
}

/**
 * Toolbar Component
 * 
 * Provides quick access to:
 * - Time period filter chips
 * - Segment filter dropdowns (SegmentFilter component - Task 23)
 * - Theme toggle button
 * 
 * Time chips can append to current query or create new query.
 * Selected filters are applied to the next query via Zustand store.
 * 
 * Requirements: 20.1, 20.2, 20.3
 */
export function Toolbar({ onSendQuery, className }: ToolbarProps) {
    const { filters, setFilters } = useChatStore()
    const [selectedPeriod, setSelectedPeriod] = React.useState<string | null>(null)

    /**
     * Handle time period chip click
     * Creates a new query with the selected time period
     */
    const handleTimePeriodClick = React.useCallback(
        (period: string) => {
            setSelectedPeriod(period)

            // Create a query with the time period
            // This will trigger a new query to be sent
            if (onSendQuery) {
                onSendQuery(`Show trends for ${period}`)
            }
        },
        [onSendQuery]
    )

    return (
        <div className={cn("border-b bg-background p-4", className)}>
            <div className="flex flex-col gap-4">
                {/* Top row: Time period chips */}
                <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-muted-foreground">
                        Quick filters:
                    </span>
                    <div className="flex flex-wrap gap-2">
                        {TIME_PERIODS.map((period) => (
                            <Badge
                                key={period.value}
                                variant={selectedPeriod === period.value ? "default" : "outline"}
                                className={cn(
                                    "cursor-pointer transition-colors",
                                    "hover:bg-primary/10 hover:border-primary",
                                    selectedPeriod === period.value && "bg-primary text-primary-foreground"
                                )}
                                onClick={() => handleTimePeriodClick(period.value)}
                            >
                                {period.label}
                            </Badge>
                        ))}
                    </div>
                </div>

                {/* Bottom row: Segment filters and theme toggle */}
                <div className="flex items-center justify-between gap-4">
                    <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-muted-foreground">
                            Filters:
                        </span>
                        {/* Segment filter dropdowns */}
                        <div className="flex flex-wrap gap-2">
                            <SegmentFilter
                                name="channel"
                                label="Channel"
                                options={CHANNEL_OPTIONS}
                                value={filters.channel}
                                onChange={(value) => setFilters({ ...filters, channel: value as string | undefined })}
                                placeholder="All channels"
                            />
                            <SegmentFilter
                                name="grade"
                                label="Grade"
                                options={GRADE_OPTIONS}
                                value={filters.grade}
                                onChange={(value) => setFilters({ ...filters, grade: value as string | undefined })}
                                placeholder="All grades"
                            />
                            <SegmentFilter
                                name="prod_type"
                                label="Product"
                                options={PROD_TYPE_OPTIONS}
                                value={filters.prod_type}
                                onChange={(value) => setFilters({ ...filters, prod_type: value as string | undefined })}
                                placeholder="All products"
                            />
                            <SegmentFilter
                                name="repeat_type"
                                label="Customer"
                                options={REPEAT_TYPE_OPTIONS}
                                value={filters.repeat_type}
                                onChange={(value) => setFilters({ ...filters, repeat_type: value as string | undefined })}
                                placeholder="All customers"
                            />
                            <SegmentFilter
                                name="term"
                                label="Term"
                                options={TERM_OPTIONS}
                                value={filters.term}
                                onChange={(value) => setFilters({ ...filters, term: value as number | undefined })}
                                placeholder="All terms"
                            />
                            <SegmentFilter
                                name="cr_fico_band"
                                label="FICO"
                                options={FICO_BAND_OPTIONS}
                                value={filters.cr_fico_band}
                                onChange={(value) => setFilters({ ...filters, cr_fico_band: value as string | undefined })}
                                placeholder="All FICO bands"
                            />
                            <SegmentFilter
                                name="purpose"
                                label="Purpose"
                                options={PURPOSE_OPTIONS}
                                value={filters.purpose}
                                onChange={(value) => setFilters({ ...filters, purpose: value as string | undefined })}
                                placeholder="All purposes"
                            />
                        </div>
                    </div>

                    {/* Theme toggle button */}
                    <ThemeToggle />
                </div>
            </div>
        </div>
    )
}
