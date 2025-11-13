"use client"

import * as React from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { type Message } from "@/hooks/useChatStore"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import { formatRelativeTime } from "@/lib/date-utils"
import dynamic from "next/dynamic"

// Dynamically import Plotly to avoid SSR issues
const Plot = dynamic(() => import("react-plotly.js"), { ssr: false })

/**
 * ChatMessage Component Props
 */
interface ChatMessageProps {
    message: Message
}

/**
 * ChatMessage Component
 * 
 * Renders individual chat messages with:
 * - User messages: right-aligned styling
 * - Assistant messages: left-aligned styling
 * - Markdown formatting support
 * - Relative timestamp display
 * - Chart cards for data visualizations
 * 
 * Requirements: 2.3, 4.5
 */
export function ChatMessage({ message }: ChatMessageProps) {
    const isUser = message.role === "user"
    const [relativeTime, setRelativeTime] = React.useState(formatRelativeTime(message.timestamp))

    // Update relative time every minute
    React.useEffect(() => {
        const interval = setInterval(() => {
            setRelativeTime(formatRelativeTime(message.timestamp))
        }, 60000) // Update every minute

        return () => clearInterval(interval)
    }, [message.timestamp])

    return (
        <div className={cn("flex items-start gap-3", isUser && "flex-row-reverse")}>
            {/* Avatar */}
            <div
                className={cn(
                    "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium",
                    isUser
                        ? "bg-secondary text-secondary-foreground"
                        : "bg-primary text-primary-foreground"
                )}
            >
                {isUser ? "U" : "AI"}
            </div>

            {/* Message content container */}
            <div className={cn("flex-1 max-w-[80%] space-y-2", isUser && "flex flex-col items-end")}>
                {/* Text message bubble */}
                {message.content.text && (
                    <div
                        className={cn(
                            "rounded-lg px-4 py-3",
                            isUser
                                ? "bg-secondary text-secondary-foreground"
                                : "bg-muted text-foreground"
                        )}
                    >
                        <div className="prose prose-sm dark:prose-invert max-w-none">
                            <ReactMarkdown
                                remarkPlugins={[remarkGfm]}
                                components={{
                                    // Customize markdown rendering
                                    p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                                    ul: ({ children }) => <ul className="mb-2 last:mb-0 list-disc pl-4">{children}</ul>,
                                    ol: ({ children }) => <ol className="mb-2 last:mb-0 list-decimal pl-4">{children}</ol>,
                                    li: ({ children }) => <li className="mb-1">{children}</li>,
                                    code: ({ inline, children, ...props }: any) =>
                                        inline ? (
                                            <code className="bg-muted px-1 py-0.5 rounded text-sm" {...props}>
                                                {children}
                                            </code>
                                        ) : (
                                            <code className="block bg-muted p-2 rounded text-sm overflow-x-auto" {...props}>
                                                {children}
                                            </code>
                                        ),
                                    strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                                    em: ({ children }) => <em className="italic">{children}</em>,
                                    a: ({ children, href }) => (
                                        <a
                                            href={href}
                                            className="text-primary underline hover:no-underline"
                                            target="_blank"
                                            rel="noopener noreferrer"
                                        >
                                            {children}
                                        </a>
                                    ),
                                }}
                            >
                                {message.content.text}
                            </ReactMarkdown>
                        </div>
                    </div>
                )}

                {/* Chart card */}
                {message.content.card && (
                    <Card className="w-full">
                        <CardHeader>
                            <CardTitle className="text-lg">
                                {message.content.card.insight?.title || "Chart"}
                            </CardTitle>
                            {message.content.card.insight?.summary && (
                                <CardDescription className="text-sm">
                                    {message.content.card.insight.summary}
                                </CardDescription>
                            )}
                        </CardHeader>
                        <CardContent className="space-y-4">
                            {/* Plotly chart */}
                            {message.content.card.plotly && (
                                <div className="w-full relative" style={{ minHeight: '400px' }}>
                                    <Plot
                                        data={message.content.card.plotly.data}
                                        layout={{
                                            ...message.content.card.plotly.layout,
                                            autosize: true,
                                            height: 400,
                                        }}
                                        config={{
                                            responsive: true,
                                            displayModeBar: true,
                                            displaylogo: false,
                                            modeBarButtonsToRemove: ["lasso2d", "select2d"],
                                        }}
                                        className="w-full"
                                        useResizeHandler
                                        style={{ width: '100%', height: '400px' }}
                                    />
                                </div>
                            )}

                            {/* Insight bullets */}
                            {message.content.card.insight?.bullets && message.content.card.insight.bullets.length > 0 && (
                                <div className="space-y-2">
                                    <h4 className="text-sm font-semibold">Key Insights:</h4>
                                    <ul className="space-y-1 text-sm text-muted-foreground">
                                        {message.content.card.insight.bullets.map((bullet, index) => (
                                            <li key={index} className="flex items-start gap-2">
                                                <span className="text-primary mt-1">•</span>
                                                <span>{bullet}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {/* Drivers */}
                            {message.content.card.insight?.drivers && message.content.card.insight.drivers.length > 0 && (
                                <div className="space-y-2">
                                    <h4 className="text-sm font-semibold">Top Drivers:</h4>
                                    <div className="space-y-1">
                                        {message.content.card.insight.drivers.map((driver, index) => (
                                            <div
                                                key={index}
                                                className="flex items-center justify-between text-sm p-2 rounded bg-muted/50"
                                            >
                                                <span className="font-medium">{driver.segment}</span>
                                                <div className="flex items-center gap-2">
                                                    <span className="text-muted-foreground">
                                                        {driver.value.toLocaleString()}
                                                    </span>
                                                    <span
                                                        className={cn(
                                                            "font-semibold",
                                                            driver.delta_pct >= 0 ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"
                                                        )}
                                                    >
                                                        {driver.delta_pct >= 0 ? "+" : ""}
                                                        {driver.delta_pct.toFixed(1)}%
                                                    </span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                )}

                {/* Timestamp */}
                <div
                    className={cn(
                        "text-xs text-muted-foreground px-1",
                        isUser && "text-right"
                    )}
                >
                    {relativeTime}
                </div>
            </div>
        </div>
    )
}
