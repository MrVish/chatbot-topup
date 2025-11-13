"use client"

import * as React from "react"
import { useChatStore } from "@/hooks/useChatStore"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Send, Square } from "lucide-react"
import { cn } from "@/lib/utils"

/**
 * ChatInput Component Props
 */
interface ChatInputProps {
    onSend?: (message: string) => void
    onStop?: () => void
}

/**
 * ChatInput Component
 * 
 * Multiline text input for chat messages with:
 * - Auto-resize textarea
 * - Send button with loading state
 * - Stop button to cancel streaming (visible when running)
 * - Enter key to send (Shift+Enter for new line)
 * - Clear input after sending
 * - Disabled state when running
 * 
 * Requirements: 1.1, 2.1
 */
export function ChatInput({ onSend, onStop }: ChatInputProps) {
    const { running } = useChatStore()
    const [input, setInput] = React.useState("")
    const textareaRef = React.useRef<HTMLTextAreaElement>(null)

    // Auto-resize textarea based on content
    const adjustTextareaHeight = React.useCallback(() => {
        const textarea = textareaRef.current
        if (!textarea) return

        // Reset height to auto to get the correct scrollHeight
        textarea.style.height = "auto"

        // Set height based on scrollHeight, with min and max constraints
        const newHeight = Math.min(Math.max(textarea.scrollHeight, 80), 200)
        textarea.style.height = `${newHeight}px`
    }, [])

    // Adjust height when input changes
    React.useEffect(() => {
        adjustTextareaHeight()
    }, [input, adjustTextareaHeight])

    // Handle input change
    const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        setInput(e.target.value)
    }

    // Handle send message
    const handleSend = React.useCallback(() => {
        const trimmedInput = input.trim()
        if (!trimmedInput || running) return

        // Call onSend callback if provided
        if (onSend) {
            onSend(trimmedInput)
        }

        // Clear input after sending
        setInput("")

        // Reset textarea height
        if (textareaRef.current) {
            textareaRef.current.style.height = "auto"
        }
    }, [input, running, onSend])

    // Handle stop streaming
    const handleStop = React.useCallback(() => {
        if (onStop) {
            onStop()
        }
    }, [onStop])

    // Handle keyboard events
    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        // Enter key to send (Shift+Enter for new line)
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault()
            handleSend()
        }
    }

    return (
        <div className="border-t bg-background p-4">
            <div className="flex items-end gap-2">
                {/* Multiline textarea with auto-resize */}
                <Textarea
                    ref={textareaRef}
                    value={input}
                    onChange={handleInputChange}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask a question about your marketing data..."
                    disabled={running}
                    className={cn(
                        "min-h-[80px] max-h-[200px] resize-none",
                        running && "opacity-50 cursor-not-allowed"
                    )}
                    rows={1}
                />

                {/* Send or Stop button */}
                {running ? (
                    <Button
                        onClick={handleStop}
                        variant="destructive"
                        size="icon"
                        className="flex-shrink-0"
                        aria-label="Stop streaming"
                    >
                        <Square className="h-4 w-4" />
                    </Button>
                ) : (
                    <Button
                        onClick={handleSend}
                        disabled={!input.trim() || running}
                        size="icon"
                        className="flex-shrink-0"
                        aria-label="Send message"
                    >
                        <Send className="h-4 w-4" />
                    </Button>
                )}
            </div>

            {/* Helper text */}
            <div className="mt-2 text-xs text-muted-foreground">
                Press Enter to send, Shift+Enter for new line
            </div>
        </div>
    )
}
