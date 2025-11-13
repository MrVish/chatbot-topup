import { create } from 'zustand';

/**
 * Segment filter criteria matching backend SegmentFilters schema
 */
export interface SegmentFilters {
  channel?: string;
  grade?: string;
  prod_type?: string;
  repeat_type?: string;
  term?: number;
  cr_fico_band?: string;
  purpose?: string;
}

/**
 * Chart card attachment for assistant messages
 */
export interface ChartCard {
  plotly: any; // Plotly JSON specification
  insight?: {
    title: string;
    summary: string;
    bullets: string[];
    drivers?: Array<{
      segment: string;
      value: number;
      delta: number;
      delta_pct: number;
    }>;
  };
}

/**
 * Message content can be text or include chart cards
 */
export interface MessageContent {
  text?: string;
  card?: ChartCard;
}

/**
 * Chat message with role, content, and timestamp
 */
export interface Message {
  role: 'user' | 'assistant';
  content: MessageContent;
  timestamp: Date;
}

/**
 * Chat store state and actions
 */
interface ChatStore {
  // State
  messages: Message[];
  running: boolean;
  filters: SegmentFilters;

  // Actions
  pushUser: (text: string) => void;
  pushAssistant: (content: MessageContent) => void;
  updateLastAssistant: (content: MessageContent) => void;
  setRunning: (running: boolean) => void;
  setFilters: (filters: SegmentFilters) => void;
  clearMessages: () => void;
}

/**
 * Zustand store for chat state management
 * 
 * Manages:
 * - Message history (user and assistant messages)
 * - Loading state (running indicator)
 * - Segment filters for queries
 * 
 * Usage:
 * ```tsx
 * const { messages, running, pushUser, setRunning } = useChatStore();
 * ```
 */
export const useChatStore = create<ChatStore>((set) => ({
  // Initial state
  messages: [],
  running: false,
  filters: {},

  // Push user message
  pushUser: (text: string) =>
    set((state) => ({
      messages: [
        ...state.messages,
        {
          role: 'user',
          content: { text },
          timestamp: new Date(),
        },
      ],
    })),

  // Push assistant message (supports text and card attachments)
  pushAssistant: (content: MessageContent) =>
    set((state) => ({
      messages: [
        ...state.messages,
        {
          role: 'assistant',
          content,
          timestamp: new Date(),
        },
      ],
    })),

  // Update last assistant message (for streaming partial updates)
  updateLastAssistant: (content: MessageContent) =>
    set((state) => {
      const messages = [...state.messages];
      const lastIndex = messages.length - 1;

      if (lastIndex >= 0 && messages[lastIndex].role === 'assistant') {
        messages[lastIndex] = {
          ...messages[lastIndex],
          content,
        };
      } else {
        // If last message is not assistant, push new one
        messages.push({
          role: 'assistant',
          content,
          timestamp: new Date(),
        });
      }

      return { messages };
    }),

  // Set running state for loading indicator
  setRunning: (running: boolean) =>
    set({ running }),

  // Update segment filters
  setFilters: (filters: SegmentFilters) =>
    set({ filters }),

  // Clear all messages
  clearMessages: () =>
    set({ messages: [] }),
}));
