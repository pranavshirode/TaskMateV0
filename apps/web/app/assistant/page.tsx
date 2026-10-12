"use client";

import { useState, useRef, useEffect } from "react";
import { apiClient, type AIChatAction } from "@/lib/api-client";

// Types for local state
interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  actions?: AIChatAction[];
  context_summary?: {
    task_count?: number;
    project_count?: number;
    overdue_count?: number;
    due_today_count?: number;
    [key: string]: unknown;
  };
  requires_clarification?: boolean;
  suggestions?: string[];
  intent?: string;
  timestamp: Date;
}

const QUICK_ACTIONS = [
  { label: "📅 What should I work on today?", prompt: "What should I work on today?" },
  { label: "⚠️ Show overdue tasks", prompt: "Show me all overdue tasks" },
  { label: "➕ Create a task", prompt: "Create a task " },
  { label: "🔴 High-priority tasks", prompt: "Show all high-priority tasks" },
  { label: "🐙 Connect to GitHub", prompt: "Summarize my open issues on GitHub" }
];

export default function AssistantPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [agentMode, setAgentMode] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const sendMessage = async (text?: string) => {
    const messageText = text || input.trim();
    if (!messageText || isLoading) return;

    setInput("");
    setError(null);

    // Add user message
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: messageText,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      if (agentMode) {
        const response = await apiClient.runAgent({
          prompt: messageText,
          conversation_id: conversationId || undefined,
        });

        if (response.error) {
          setError(response.error.message || "Failed to run agent");
          setMessages((prev) => [
            ...prev,
            {
              id: crypto.randomUUID(),
              role: "assistant",
              content: response.error?.message || "Agent execution failed.",
              timestamp: new Date(),
            },
          ]);
        } else if (response.data) {
          const data = response.data;
          if (data.conversation_id) {
            setConversationId(data.conversation_id);
          }

          const assistantMessage: Message = {
            id: crypto.randomUUID(),
            role: "assistant",
            content: data.message || data.result || "Agent executed successfully.",
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, assistantMessage]);
        }
      } else {
        const response = await apiClient.sendMessage({
          message: messageText,
          conversation_id: conversationId || undefined,
        });

        if (response.error) {
          setError(response.error.message || "Failed to get AI response");
          setMessages((prev) => [
            ...prev,
            {
              id: crypto.randomUUID(),
              role: "assistant",
              content: response.error?.message || "I'm having trouble processing your request.",
              timestamp: new Date(),
            },
          ]);
        } else if (response.data) {
          const data = response.data;
          setConversationId(data.conversation_id);

          const assistantMessage: Message = {
            id: crypto.randomUUID(),
            role: "assistant",
            content: data.message,
            actions: data.actions,
            context_summary: (data.context_summary as Message['context_summary']) || undefined,
            requires_clarification: data.requires_clarification,
            suggestions: data.suggestions,
            intent: data.intent || undefined,
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, assistantMessage]);
        }
      }
    } catch {
      setError("Network error. Please check your connection.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleQuickAction = (prompt: string) => {
    setInput(prompt);
    inputRef.current?.focus();
    // If the prompt is a complete sentence (not ending with space), send immediately
    if (!prompt.endsWith(" ")) {
      sendMessage(prompt);
    }
  };

  return (
    <div className="flex flex-col h-full max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex flex-row justify-between items-center flex-shrink-0 pb-4 border-b border-[var(--sidebar-border)]">
        <div>
          <h1 className="text-2xl font-bold">🤖 TaskMate AI</h1>
          <p className="text-sm text-[var(--text-muted)]">
            Ask me to manage your tasks, check your schedule, or interact with GitHub.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium">Agent Mode</label>
          <button
            onClick={() => setAgentMode(!agentMode)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${
              agentMode ? "bg-blue-600" : "bg-gray-400"
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                agentMode ? "translate-x-6" : "translate-x-1"
              }`}
            />
          </button>
        </div>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto py-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full space-y-6">
            <div className="text-center">
              <p className="text-4xl mb-2">🤖</p>
              <h2 className="text-xl font-semibold">How can I help you today?</h2>
              <p className="text-[var(--text-muted)] mt-1">
                I can create tasks, check your schedule, and manage your workspace.
              </p>
            </div>
            <div className="grid grid-cols-2 gap-2 w-full max-w-lg">
              {QUICK_ACTIONS.map((action) => (
                <button
                  key={action.prompt}
                  onClick={() => handleQuickAction(action.prompt)}
                  className="text-left px-4 py-3 rounded-lg border border-[var(--sidebar-border)] hover:bg-[var(--sidebar-border)] transition-colors text-sm"
                >
                  {action.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[80%] rounded-lg px-4 py-3 ${
                msg.role === "user"
                  ? "bg-[var(--primary)] text-white"
                  : "bg-[var(--sidebar-border)]"
              }`}
            >
              <p className="text-sm whitespace-pre-wrap">{msg.content}</p>

              {/* Action results */}
              {msg.actions && msg.actions.length > 0 && (
                <div className="mt-2 space-y-1">
                  {msg.actions.map((action, i) => (
                    <div
                      key={i}
                      className={`text-xs px-2 py-1 rounded ${
                        action.success
                          ? "bg-green-500/20 text-green-300"
                          : "bg-red-500/20 text-red-300"
                      }`}
                    >
                      {action.success ? "✓" : "✗"}{" "}
                      {(action.action_type || action.type || "action").replace(/_/g, " ").toLowerCase()}
                      {Boolean(action.data && action.data.title) && (
                        <span className="font-medium"> — {String(action.data?.title)}</span>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Context summary */}
              {msg.context_summary && (
                <div className="mt-2 text-xs text-[var(--text-muted)] border-t border-[var(--sidebar-border)] pt-1">
                  Based on: {msg.context_summary.task_count} tasks,{" "}
                  {msg.context_summary.project_count} projects
                  {(msg.context_summary.overdue_count || 0) > 0 && (
                    <span>, {msg.context_summary.overdue_count} overdue</span>
                  )}
                </div>
              )}

              {/* Suggestions */}
              {msg.suggestions && msg.suggestions.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {msg.suggestions.map((s, i) => (
                    <button
                      key={i}
                      onClick={() => handleQuickAction(s)}
                      className="text-xs px-2 py-1 rounded border border-[var(--sidebar-border)] hover:bg-[var(--sidebar-border)] transition-colors"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Typing indicator */}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-[var(--sidebar-border)] rounded-lg px-4 py-3 flex items-center gap-3">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-[var(--text-muted)] rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                <div className="w-2 h-2 bg-[var(--text-muted)] rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                <div className="w-2 h-2 bg-[var(--text-muted)] rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
              {agentMode && <span className="text-xs text-[var(--text-muted)]">Agent is thinking and using tools...</span>}
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Error banner */}
      {error && (
        <div className="flex-shrink-0 bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-2 rounded-lg text-sm mb-2 flex justify-between items-center">
          <span>{error}</span>
          <button
            onClick={() => setError(null)}
            className="ml-2 text-red-300 hover:text-red-100"
          >
            ✕
          </button>
        </div>
      )}

      {/* Input area */}
      <div className="flex-shrink-0 border-t border-[var(--sidebar-border)] pt-4 pb-2">
        <div className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask TaskMate..."
            disabled={isLoading}
            className="flex-1 px-4 py-2 rounded-lg border border-[var(--sidebar-border)] bg-[var(--background)] text-[var(--foreground)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)] disabled:opacity-50"
          />
          <button
            onClick={() => sendMessage()}
            disabled={!input.trim() || isLoading}
            className="px-6 py-2 rounded-lg bg-[var(--primary)] text-white font-medium hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
