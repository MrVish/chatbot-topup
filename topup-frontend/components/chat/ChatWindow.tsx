"use client"

import * as React from "react"
import { useChatStore } from "@/hooks/useChatStore"
import { Button } from "@/components/ui/button"
import { ArrowDown } from "lucide-react"
import { ChatMessage } from "./ChatMessage"

/**
 * ChatWindow Component
 * 
 * Displays the chat message list with:
 * - Auto-scroll to bottom on new messages
 * - Scroll-to-bottom button when user scrolls up
 * - User and assistant messages
 * - Typing indicator when processing
 * 
 * Requirements: 2.1, 2.3, 19.1, 19.2, 19.3, 19.4, 19.5
 */
export function ChatWindow() {
    const { messages, running } = useChatStore()
    const scrollContainerRef = React.useRef<HTMLDivElement>(null)
    const [showScrollButton, setShowScrollButton] = React.useState(false)
    const [autoScroll, setAutoScroll] = React.useState(true)

    // Auto-scroll to bottom on new messages
    React.useEffect(() => {
        if (autoScroll && scrollContainerRef.current) {
            scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight
        }
    }, [messages, running, autoScroll])

    // Handle scroll events to show/hide scroll-to-bottom button
    const handleScroll = React.useCallback(() => {
        if (!scrollContainerRef.current) return

        const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current
        const isNearBottom = scrollHeight - scrollTop - clientHeight < 100

        setShowScrollButton(!isNearBottom)
        setAutoScroll(isNearBottom)
    }, [])

    // Scroll to bottom function
    const scrollToBottom = React.useCallback(() => {
        if (scrollContainerRef.current) {
            scrollContainerRef.current.scrollTo({
                top: scrollContainerRef.current.scrollHeight,
                behavior: "smooth",
            })
            setAutoScroll(true)
        }
    }, [])

    return (
        <div className="relative flex flex-col h-full">
            {/* Message list with scroll container */}
            <div
                ref={scrollContainerRef}
                onScroll={handleScroll}
                className="flex-1 overflow-y-auto px-4 py-6 space-y-4"
            >
                {messages.length === 0 && (
                    <div className="flex items-center justify-center h-full text-muted-foreground">
                        <p className="text-center">
                            Ask a question about your marketing data to get started
                        </p>
                    </div>
                )}

                {messages.map((message, index) => (
                    <ChatMessage key={index} message={message} />
                ))}

                {/* Typing indicator */}
                {running && (
                    <div className="flex items-start gap-3">
                        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary flex items-center justify-center text-primary-foreground text-sm font-medium">
                            AI
                        </div>
                        <div className="flex-1 bg-muted rounded-lg px-4 py-3">
                            <div className="flex items-center gap-1">
                                <div className="w-2 h-2 rounded-full bg-muted-foreground animate-bounce" style={{ animationDelay: "0ms" }} />
                                <div className="w-2 h-2 rounded-full bg-muted-foreground animate-bounce" style={{ animationDelay: "150ms" }} />
                                <div className="w-2 h-2 rounded-full bg-muted-foreground animate-bounce" style={{ animationDelay: "300ms" }} />
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Scroll to bottom button */}
            {showScrollButton && (
                <div className="absolute bottom-4 right-4">
                    <Button
                        size="icon"
                        variant="outline"
                        onClick={scrollToBottom}
                        className="rounded-full shadow-lg"
                        aria-label="Scroll to bottom"
                    >
                        <ArrowDown className="h-4 w-4" />
                    </Button>
                </div>
            )}
        </div>
    )
}
