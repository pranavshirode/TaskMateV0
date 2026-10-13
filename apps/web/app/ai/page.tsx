"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  apiClient,
  type Conversation,
  type AIChatAction,
} from "@/lib/api-client";
import LoadingSpinner from "@/components/ui/LoadingSpinner";

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  intent?: string;
  confidence?: number;
  actions?: AIChatAction[];
  created_at?: string;
}

const QUICK_PROMPTS = [
  "What's on my plate today?",
  "Create a high priority task to fix login bug due tomorrow",
  "Show me overdue tasks",
  "Find tasks related to auth",
  "Mark login bug task as completed",
];

export default function AIAssistantPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    try {
      const list = await apiClient.listAiConversations();
      setConversations(list || []);
    } catch (e) {
      console.error("Failed to load conversations", e);
    }
  };

  const selectConversation = async (id: string) => {
    setActiveConvId(id);
    setLoadingHistory(true);
    setError(null);
    try {
      const detail = await apiClient.getAiConversation(id);
      setMessages((detail.messages as Message[]) || []);
    } catch (e: unknown) {
      setError(
        e instanceof Error ? e.message : "Failed to load conversation messages"
      );
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleNewChat = () => {
    setActiveConvId(null);
    setMessages([]);
    setError(null);
  };

  const handleSend = async (messageToSend?: string) => {
    const text = (messageToSend || input).trim();
    if (!text || loading) return;

    setInput("");
    setError(null);

    // Optimistically append user message
    const tempUserMsg: Message = {
      id: "temp-" + Date.now(),
      role: "user",
      content: text,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);
    setLoading(true);

    try {
      const response = await apiClient.aiChat(text, activeConvId || undefined);
      if (!activeConvId && response.conversation_id) {
        setActiveConvId(response.conversation_id);
        loadConversations();
      }

      const botMsg: Message = {
        id: "bot-" + Date.now(),
        role: "assistant",
        content: response.message,
        intent: response.intent,
        confidence: response.confidence,
        actions: response.actions,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (e: unknown) {
      setError(
        e instanceof Error
          ? e.message
          : "Failed to communicate with TaskMate AI"
      );
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteConversation = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await apiClient.deleteAiConversation(id);
      if (activeConvId === id) {
        handleNewChat();
      }
      loadConversations();
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to delete conversation"
      );
    }
  };

  return (
    <div className="flex h-[calc(100vh-4rem)] -m-6 bg-[var(--background)]">
      {/* Conversations Sidebar */}
      <div className="w-64 border-r border-[var(--sidebar-border)] bg-[var(--sidebar-bg)] flex flex-col">
        <div className="p-4 border-b border-[var(--sidebar-border)] flex items-center justify-between">
          <h2 className="text-sm font-semibold flex items-center gap-2">
            <span>✨</span> TaskMate AI
          </h2>
          <button
            onClick={handleNewChat}
            className="text-xs bg-[var(--primary)] text-white px-2 py-1 rounded hover:opacity-90 transition-opacity"
          >
            + New Chat
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {conversations.length === 0 ? (
            <p className="text-xs text-[var(--text-muted)] text-center py-6">
              No previous chats yet
            </p>
          ) : (
            conversations.map((c) => {
              const isSelected = activeConvId === c.id;
              return (
                <div
                  key={c.id}
                  onClick={() => selectConversation(c.id)}
                  className={`group flex items-center justify-between p-2 rounded text-xs cursor-pointer transition-colors ${
                    isSelected
                      ? "bg-[var(--sidebar-border)] text-white font-medium"
                      : "text-[var(--text-muted)] hover:bg-[var(--sidebar-border)] hover:text-white"
                  }`}
                >
                  <span className="truncate flex-1">
                    {c.last_message
                      ? c.last_message.slice(0, 28) + "..."
                      : "Conversation"}
                  </span>
                  <button
                    onClick={(e) => handleDeleteConversation(c.id, e)}
                    className="opacity-0 group-hover:opacity-100 hover:text-red-400 ml-2"
                    title="Delete"
                  >
                    ✕
                  </button>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Messages Feed */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {loadingHistory ? (
            <div className="flex justify-center items-center h-48">
              <LoadingSpinner />
            </div>
          ) : messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full max-w-lg mx-auto text-center space-y-6">
              <div className="w-16 h-16 rounded-2xl bg-[var(--primary)]/10 text-[var(--primary)] flex items-center justify-center text-3xl">
                ✨
              </div>
              <div>
                <h3 className="text-xl font-bold">How can I help you today?</h3>
                <p className="text-sm text-[var(--text-muted)] mt-1">
                  Manage your tasks, projects, deadlines, and workload with
                  natural language.
                </p>
              </div>

              {/* Quick Prompts */}
              <div className="flex flex-wrap gap-2 justify-center">
                {QUICK_PROMPTS.map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => handleSend(prompt)}
                    className="text-xs bg-[var(--sidebar-border)] hover:bg-[var(--sidebar-border)]/80 text-[var(--foreground)] px-3 py-2 rounded-lg border border-[var(--sidebar-border)] transition-colors text-left"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((m) => (
              <div
                key={m.id}
                className={`flex flex-col ${
                  m.role === "user" ? "items-end" : "items-start"
                }`}
              >
                <div
                  className={`max-w-2xl px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
                    m.role === "user"
                      ? "bg-[var(--primary)] text-white rounded-br-none"
                      : "bg-[var(--sidebar-border)] text-[var(--foreground)] rounded-bl-none border border-[var(--sidebar-border)]"
                  }`}
                >
                  {m.content}

                  {/* Actions Confirmation Cards */}
                  {m.actions && m.actions.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-[var(--foreground)]/10 space-y-2">
                      {m.actions.map((act, i) => (
                        <div
                          key={i}
                          className="flex items-center justify-between text-xs bg-black/20 p-2 rounded-lg"
                        >
                          <div className="flex items-center gap-2">
                            <span
                              className={
                                act.success ? "text-green-400" : "text-red-400"
                              }
                            >
                              {act.success ? "✓" : "✗"}
                            </span>
                            <span>{act.message}</span>
                          </div>
                          {!!act.data?.task_id && (
                            <Link
                              href={`/tasks/${String(act.data.task_id)}`}
                              className="text-[var(--primary)] underline hover:opacity-80"
                            >
                              View Task
                            </Link>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Intent & Confidence Meta */}
                {m.role === "assistant" && m.intent && (
                  <div className="flex items-center gap-2 mt-1 px-1">
                    <span className="text-[10px] text-[var(--text-muted)]">
                      Intent: <span className="font-mono">{m.intent}</span>
                    </span>
                    {m.confidence !== undefined && (
                      <span className="text-[10px] text-[var(--text-muted)]">
                        • {Math.round(m.confidence * 100)}% match
                      </span>
                    )}
                  </div>
                )}
              </div>
            ))
          )}

          {loading && (
            <div className="flex items-start">
              <div className="bg-[var(--sidebar-border)] text-[var(--foreground)] px-4 py-3 rounded-2xl rounded-bl-none text-sm flex items-center gap-2">
                <div className="scale-75 -ml-1">
                  <LoadingSpinner />
                </div>
                <span className="text-xs text-[var(--text-muted)]">
                  TaskMate is thinking...
                </span>
              </div>
            </div>
          )}

          {error && (
            <div className="p-3 bg-red-900/30 border border-red-800 text-red-200 text-xs rounded-lg">
              {error}
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Message Input Box */}
        <div className="p-4 border-t border-[var(--sidebar-border)] bg-[var(--sidebar-bg)]">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-center gap-2"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask anything or manage tasks: 'Create task to fix login bug due tomorrow'..."
              disabled={loading}
              className="flex-1 bg-[var(--background)] border border-[var(--sidebar-border)] rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-[var(--primary)] disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="bg-[var(--primary)] text-white px-5 py-2.5 rounded-xl text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Send
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
