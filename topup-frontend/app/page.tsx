"use client"

import * as React from "react"
import { useChatStore, type ChartCard } from "@/hooks/useChatStore"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ChatWindow } from "@/components/chat/ChatWindow"
import { ChatInput } from "@/components/chat/ChatInput"
import { Toolbar } from "@/components/chat/Toolbar"

/**
 * SSE Message Types
 */
type SSEMessage =
    | { partial: string }
    | { plan: any }
    | { card: ChartCard }
    | { done: true }
    | { error: string }

/**
 * Main Chat Page Component
 * 
 * Integrates all chat components with SSE streaming:
 * - ChatWindow for message display
 * - ChatInput for user input
 * - Toolbar for filters and quick actions
 * - SSE connection to /chat endpoint
 * - Split-pane layout: left = chat thread, right = latest insight cards
 * 
 * Requirements: 1.1, 2.1, 2.2, 2.3, 2.4, 2.5
 */
export default function Home() {
    const { messages, running, filters, pushUser, pushAssistant, updateLastAssistant, setRunning } = useChatStore()
    const [eventSource, setEventSource] = React.useState<EventSource | null>(null)
    const [error, setError] = React.useState<string | null>(null)
    const [latestInsights, setLatestInsights] = React.useState<ChartCard[]>([])

    // Get API URL from environment
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

    /**
     * Get recent conversation history for context
     */
    const getRecentHistory = React.useCallback(() => {
        // Get last 10 messages (5 exchanges) for context
        const recentMessages = messages.slice(-10)
        return recentMessages.map((msg) => ({
            role: msg.role,
            content:
                msg.content.text ||
                msg.content.card?.insight?.summary ||
                (msg.content.card ? "Chart response" : "Response"),
        }))
    }, [messages])

    /**
     * Send message and initiate SSE connection to /chat endpoint
     */
    const send = React.useCallback(
        (message: string) => {
            // Clear any previous error
            setError(null)

            // Push user message to store
            pushUser(message)

            // Set running state
            setRunning(true)

            // Get conversation history for context
            const history = getRecentHistory()

            // Build query parameters
            const params = new URLSearchParams({
                message,
                history: JSON.stringify(history), // Add conversation history
            })

            // Add filters if present
            if (filters.channel) params.append("channel", filters.channel)
            if (filters.grade) params.append("grade", filters.grade)
            if (filters.prod_type) params.append("prod_type", filters.prod_type)
            if (filters.repeat_type) params.append("repeat_type", filters.repeat_type)
            if (filters.term) params.append("term", filters.term.toString())
            if (filters.cr_fico_band) params.append("cr_fico_band", filters.cr_fico_band)
            if (filters.purpose) params.append("purpose", filters.purpose)

            // Create SSE connection
            const url = `${apiUrl}/chat?${params.toString()}`
            const es = new EventSource(url)

            // Track partial message accumulation
            let partialText = ""

            // Handle SSE messages
            es.onmessage = (event) => {
                try {
                    const data: SSEMessage = JSON.parse(event.data)

                    // Handle partial messages by appending to last assistant message
                    if ("partial" in data) {
                        partialText += data.partial

                        // Update last assistant message with accumulated text
                        updateLastAssistant({ text: partialText })
                    }

                    // Handle plan messages by logging to console (optional display)
                    else if ("plan" in data) {
                        console.log("Query plan:", data.plan)
                    }

                    // Handle card messages by replacing partial text with card
                    else if ("card" in data) {
                        // Replace the last assistant message (which has partial text) with the card
                        updateLastAssistant({ card: data.card })

                        // Add to latest insights
                        setLatestInsights((prev) => [data.card, ...prev.slice(0, 4)])
                    }

                    // Handle done messages by closing SSE connection and setting running to false
                    else if ("done" in data) {
                        es.close()
                        setEventSource(null)
                        setRunning(false)
                    }

                    // Handle error messages by displaying error
                    else if ("error" in data) {
                        setError(data.error)
                        es.close()
                        setEventSource(null)
                        setRunning(false)
                    }
                } catch (err) {
                    console.error("Failed to parse SSE message:", err)
                }
            }

            // Handle SSE errors
            es.onerror = (err) => {
                console.error("SSE connection error:", err)
                setError("Connection error. Please try again.")
                es.close()
                setEventSource(null)
                setRunning(false)
            }

            // Store event source for cleanup
            setEventSource(es)
        },
        [apiUrl, filters, pushUser, pushAssistant, updateLastAssistant, setRunning, getRecentHistory]
    )

    /**
     * Stop streaming by closing SSE connection
     */
    const stop = React.useCallback(() => {
        if (eventSource) {
            eventSource.close()
            setEventSource(null)
        }
        setRunning(false)
    }, [eventSource, setRunning])

    /**
     * Handle example query clicks
     */
    const handleExampleClick = React.useCallback(
        (query: string) => {
            send(query)
        },
        [send]
    )

    // Cleanup on unmount
    React.useEffect(() => {
        return () => {
            if (eventSource) {
                eventSource.close()
            }
        }
    }, [eventSource])

    return (
        <div className="flex min-h-screen flex-col">
            {/* Header */}
            <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
                <div className="container flex h-14 items-center justify-between">
                    <div className="flex items-center gap-2">
                        <h1 className="text-xl font-semibold">Topup CXO Assistant</h1>
                        <Badge variant="secondary">Beta</Badge>
                    </div>
                </div>
            </header>

            {/* Toolbar with filters and quick actions */}
            <Toolbar onSendQuery={send} />

            {/* Main Content - Split-pane layout */}
            <main className="flex-1 container py-6">
                <div className="grid gap-6 lg:grid-cols-3">
                    {/* Chat Area - Takes 2 columns on large screens */}
                    <div className="lg:col-span-2">
                        <Card className="flex flex-col h-[calc(100vh-16rem)]">
                            {/* Messages Area */}
                            {messages.length === 0 ? (
                                <div className="flex-1 flex flex-col items-center justify-center p-8 space-y-6">
                                    <div className="space-y-2 text-center">
                                        <h2 className="text-2xl font-bold">Welcome to Topup</h2>
                                        <p className="text-muted-foreground max-w-md">
                                            Ask questions about your marketing data in natural language.
                                            I&apos;ll help you analyze trends, forecasts, and performance metrics.
                                        </p>
                                    </div>

                                    {/* Quick Start Examples */}
                                    <div className="flex flex-wrap gap-2 justify-center max-w-2xl">
                                        <Badge
                                            variant="outline"
                                            className="cursor-pointer hover:bg-accent transition-colors"
                                            onClick={() => handleExampleClick("Show WoW issuance by channel")}
                                        >
                                            Show WoW issuance by channel
                                        </Badge>
                                        <Badge
                                            variant="outline"
                                            className="cursor-pointer hover:bg-accent transition-colors"
                                            onClick={() => handleExampleClick("Last month's funnel for Email")}
                                        >
                                            Last month&apos;s funnel for Email
                                        </Badge>
                                        <Badge
                                            variant="outline"
                                            className="cursor-pointer hover:bg-accent transition-colors"
                                            onClick={() => handleExampleClick("Forecast vs actual by grade")}
                                        >
                                            Forecast vs actual by grade
                                        </Badge>
                                        <Badge
                                            variant="outline"
                                            className="cursor-pointer hover:bg-accent transition-colors"
                                            onClick={() => handleExampleClick("What is funding rate?")}
                                        >
                                            What is funding rate?
                                        </Badge>
                                    </div>
                                </div>
                            ) : (
                                <ChatWindow />
                            )}

                            {/* Error Display */}
                            {error && (
                                <div className="border-t bg-destructive/10 text-destructive px-4 py-3 text-sm">
                                    <strong>Error:</strong> {error}
                                </div>
                            )}

                            {/* Input Area */}
                            <ChatInput onSend={send} onStop={stop} />
                        </Card>
                    </div>

                    {/* Insights Sidebar - Takes 1 column on large screens */}
                    <div className="lg:col-span-1">
                        <Card className="h-[calc(100vh-16rem)] flex flex-col">
                            <CardHeader>
                                <CardTitle>Latest Insights</CardTitle>
                                <CardDescription>
                                    Recent chart insights from your queries
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="flex-1 overflow-y-auto space-y-4">
                                {latestInsights.length === 0 ? (
                                    <div className="flex items-center justify-center h-full text-center">
                                        <p className="text-sm text-muted-foreground">
                                            Insights from your queries will appear here
                                        </p>
                                    </div>
                                ) : (
                                    latestInsights.map((insight, index) => (
                                        <Card key={index} className="border-2">
                                            <CardHeader className="pb-3">
                                                <CardTitle className="text-base">
                                                    {insight.insight?.title || "Insight"}
                                                </CardTitle>
                                                {insight.insight?.summary && (
                                                    <CardDescription className="text-xs">
                                                        {insight.insight.summary}
                                                    </CardDescription>
                                                )}
                                            </CardHeader>
                                            {insight.insight?.bullets && insight.insight.bullets.length > 0 && (
                                                <CardContent className="pt-0">
                                                    <ul className="space-y-1 text-xs text-muted-foreground">
                                                        {insight.insight.bullets.slice(0, 2).map((bullet, i) => (
                                                            <li key={i} className="flex items-start gap-1">
                                                                <span className="text-primary mt-0.5">•</span>
                                                                <span className="line-clamp-2">{bullet}</span>
                                                            </li>
                                                        ))}
                                                    </ul>
                                                </CardContent>
                                            )}
                                        </Card>
                                    ))
                                )}
                            </CardContent>
                        </Card>
                    </div>
                </div>
            </main>
        </div>
    )
}
