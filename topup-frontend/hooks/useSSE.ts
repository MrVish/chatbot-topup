import { useEffect, useRef } from 'react';

/**
 * SSE hook for streaming server-sent events
 * 
 * Manages EventSource connection lifecycle:
 * - Initializes connection with provided URL
 * - Parses JSON messages and invokes callback
 * - Handles errors and cleanup
 * - Provides manual close function
 * 
 * @param url - SSE endpoint URL
 * @param onMessage - Callback for each message (receives parsed JSON)
 * @param onDone - Optional callback when connection closes or errors
 * @returns Object with close() function for manual termination
 * 
 * @example
 * ```tsx
 * const { close } = useSSE(
 *   'http://localhost:8000/chat',
 *   (data) => console.log('Message:', data),
 *   () => console.log('Connection closed')
 * );
 * ```
 */
export function useSSE(
  url: string,
  onMessage: (data: any) => void,
  onDone?: () => void
): { close: () => void } {
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    // Initialize EventSource with provided URL
    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    // Set up onmessage handler to parse JSON and call onMessage callback
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (error) {
        console.error('Failed to parse SSE message:', error);
      }
    };

    // Set up onerror handler to close connection and call onDone callback
    eventSource.onerror = (error) => {
      console.error('SSE connection error:', error);
      eventSource.close();
      eventSourceRef.current = null;
      if (onDone) {
        onDone();
      }
    };

    // Clean up EventSource on unmount
    return () => {
      if (eventSource.readyState !== EventSource.CLOSED) {
        eventSource.close();
      }
      eventSourceRef.current = null;
    };
  }, [url, onMessage, onDone]);

  // Return close() function for manual connection termination
  const close = () => {
    if (eventSourceRef.current && eventSourceRef.current.readyState !== EventSource.CLOSED) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      if (onDone) {
        onDone();
      }
    }
  };

  return { close };
}
