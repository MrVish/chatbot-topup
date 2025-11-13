"use client"

import * as React from "react"
import { X } from "lucide-react"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

/**
 * Segment filter option
 */
interface FilterOption {
    label: string
    value: string | number
}

/**
 * SegmentFilter Component Props
 */
interface SegmentFilterProps {
    /**
     * Filter name (e.g., "channel", "grade", "term")
     */
    name: string

    /**
     * Display label for the filter
     */
    label: string

    /**
     * Available filter options
     */
    options: readonly FilterOption[]

    /**
     * Currently selected value
     */
    value?: string | number

    /**
     * Callback when selection changes
     */
    onChange: (value: string | number | undefined) => void

    /**
     * Optional className for styling
     */
    className?: string

    /**
     * Optional placeholder text
     */
    placeholder?: string
}

/**
 * SegmentFilter Component
 * 
 * Single-select dropdown for segment filtering.
 * Supports channel, grade, prod_type, repeat_type, term, cr_fico_band, and purpose filters.
 * 
 * Features:
 * - Single-select dropdown using shadcn Select
 * - Clear/reset button to remove selection
 * - Updates Zustand store on selection change
 * - Displays selected value as a badge
 * 
 * Requirements: 5.1, 5.2, 5.3, 5.4, 20.3, 20.4
 * 
 * @example
 * ```tsx
 * <SegmentFilter
 *   name="channel"
 *   label="Channel"
 *   options={channelOptions}
 *   value={filters.channel}
 *   onChange={(value) => setFilters({ ...filters, channel: value })}
 * />
 * ```
 */
export function SegmentFilter({
    name,
    label,
    options,
    value,
    onChange,
    className,
    placeholder = "Select...",
}: SegmentFilterProps) {
    /**
     * Handle selection change
     */
    const handleValueChange = React.useCallback(
        (newValue: string) => {
            // Convert to number if the filter is for term
            if (name === "term") {
                onChange(parseInt(newValue, 10))
            } else {
                onChange(newValue)
            }
        },
        [name, onChange]
    )

    /**
     * Handle clear button click
     */
    const handleClear = React.useCallback(
        (e: React.MouseEvent) => {
            e.stopPropagation()
            onChange(undefined)
        },
        [onChange]
    )

    /**
     * Get display value for the selected option
     */
    const displayValue = React.useMemo(() => {
        if (value === undefined || value === null) return undefined
        const option = options.find((opt) => opt.value === value)
        return option?.label || String(value)
    }, [value, options])

    return (
        <div className={cn("flex items-center gap-2", className)}>
            <Select
                value={value !== undefined && value !== null ? String(value) : undefined}
                onValueChange={handleValueChange}
            >
                <SelectTrigger className="w-[180px]">
                    <SelectValue placeholder={placeholder}>
                        {displayValue && (
                            <Badge variant="secondary" className="font-normal">
                                {label}: {displayValue}
                            </Badge>
                        )}
                    </SelectValue>
                </SelectTrigger>
                <SelectContent>
                    {options.map((option) => (
                        <SelectItem key={String(option.value)} value={String(option.value)}>
                            {option.label}
                        </SelectItem>
                    ))}
                </SelectContent>
            </Select>

            {/* Clear button - only show when a value is selected */}
            {value !== undefined && value !== null && (
                <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 w-8 p-0"
                    onClick={handleClear}
                    aria-label={`Clear ${label} filter`}
                >
                    <X className="h-4 w-4" />
                </Button>
            )}
        </div>
    )
}
