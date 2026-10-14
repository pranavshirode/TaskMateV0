"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  apiClient,
  type AgentPendingAction,
  type AIChatAction,
  type Conversation,
} from "@/lib/api-client";
import { useWorkspaceUI } from "@/components/layout/WorkspaceUI";
import { timeAgo } from "@/lib/format";
import Icon, { type IconName } from "@/components/ui/Icon";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import MarkdownRenderer from "@/components/ui/MarkdownRenderer";

type Mode = "chat" | "agent";

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  intent?: string;
  confidence?: number;
  actions?: AIChatAction[];
  suggestions?: string[];
  /** The assistant asked a question instead of acting. */
  clarify?: boolean;
  /** An agent action waiting for the user's approval. */
  approval?: {
    executionId: string;
    action: AgentPendingAction;
    state: "pending" | "working" | "approved" | "rejected";
  };
  context_summary?: {
    tasks_count?: number;
    projects_count?: number;
    task_count?: number;
    project_count?: number;
    overdue_count?: number;
    [key: string]: unknown;
  };
  failed?: boolean;
}

const QUICK_ACTIONS: {
  label: string;
  prompt: string;
  icon: IconName;
  send: boolean;
}[] = [
  {
    label: "What should I work on today?",
    prompt: "What should I work on today?",
    icon: "today",
    send: true,
  },
  {
    label: "Show overdue tasks",
    prompt: "Show me all overdue tasks",
    icon: "alert",
    send: true,
  },
  {
    label: "Create a task",
    prompt: "Create a task to ",
    icon: "plus",
    send: false,
  },
  {
    label: "High-priority tasks",
    prompt: "Show all high-priority tasks",
    icon: "flame",
    send: true,
  },
  {
    label: "Summarize open GitHub issues",
    prompt: "Summarize my open issues on GitHub",
    icon: "github",
    send: true,
  },
  {
    label: "Which project is at risk?",
    prompt: "Which of my projects is most at risk of missing its deadline?",
    icon: "chart",
    send: true,
  },
];

const MODES: { id: Mode; label: string; hint: string }[] = [
  { id: "chat", label: "Chat", hint: "Fast answers and simple task changes" },
  {
    id: "agent",
    label: "Agent",
    hint: "Multi-step work using tools like GitHub; asks before making changes",
  },
];

const newId = () =>
  typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random()}`;

function actionLabel(action: AIChatAction) {
  if (action.message) return action.message;
  const type = (action.action_type || action.type || "action")
    .replace(/_/g, " ")
    .toLowerCase();
  const title = action.data?.title ? ` — ${String(action.data.title)}` : "";
  return type + title;
}

export default function AssistantChat({
  defaultMode = "chat",
}: {
  defaultMode?: Mode;
}) {
  const { notifyDataChanged } = useWorkspaceUI();
  const [mode, setMode] = useState<Mode>(defaultMode);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const initialPromptSent = useRef(false);

  useEffect(() => {
    endRef.current?.scrollIntoView?.({ behavior: "smooth", block: "end" });
  }, [messages, isSending]);

  // Auto-grow the textarea
  useEffect(() => {
    const el = inputRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, [input]);

  const loadConversations = useCallback(async () => {
    try {
      const list = await apiClient.listAiConversations();
      setConversations(list || []);
    } catch {
      /* history is optional */
    }
  }, []);

  const send = useCallback(
    async (text?: string) => {
      const messageText = (text ?? input).trim();
      if (!messageText || isSending) return;

      setInput("");
      setMessages((prev) => [
        ...prev,
        { id: newId(), role: "user", content: messageText },
      ]);
      setIsSending(true);

      try {
        if (mode === "agent") {
          const response = await apiClient.runAgent({
            prompt: messageText,
            conversation_id: conversationId || undefined,
          });
          if (response.error || !response.data) {
            throw response.error || new Error("Agent execution failed.");
          }
          const data = response.data;
          if (data.conversation_id) setConversationId(data.conversation_id);
          const waiting =
            data.status === "WAITING_FOR_APPROVAL" &&
            data.pending_action &&
            data.execution_id;
          setMessages((prev) => [
            ...prev,
            {
              id: newId(),
              role: "assistant",
              content: data.message || data.result || "Done.",
              approval: waiting
                ? {
                    executionId: data.execution_id!,
                    action: data.pending_action!,
                    state: "pending",
                  }
                : undefined,
            },
          ]);
        } else {
          const response = await apiClient.sendMessage({
            message: messageText,
            conversation_id: conversationId || undefined,
          });
          if (response.error || !response.data) {
            throw response.error || new Error("No response from TaskMate.");
          }
          const data = response.data;
          if (!conversationId && data.conversation_id) loadConversations();
          setConversationId(data.conversation_id);
          setMessages((prev) => [
            ...prev,
            {
              id: newId(),
              role: "assistant",
              content: data.message,
              intent: data.intent,
              confidence: data.confidence,
              actions: data.actions,
              suggestions: data.suggestions,
              clarify: data.requires_clarification,
              context_summary:
                data.context_summary as Message["context_summary"],
            },
          ]);
        }
      } catch (err) {
        setMessages((prev) => [
          ...prev,
          {
            id: newId(),
            role: "assistant",
            failed: true,
            content:
              err instanceof Error && err.message
                ? err.message
                : "Something went wrong. Check your connection and try again.",
          },
        ]);
      } finally {
        setIsSending(false);
        inputRef.current?.focus();
      }
    },
    [input, isSending, mode, conversationId, loadConversations]
  );

  // Load history, focus the box, and send a prompt passed as ?q= (from the dashboard, palette, etc.)
  useEffect(() => {
    loadConversations();
    inputRef.current?.focus();
    if (initialPromptSent.current) return;
    initialPromptSent.current = true;
    const q = new URLSearchParams(window.location.search).get("q");
    if (q) {
      window.history.replaceState(null, "", window.location.pathname);
      send(q);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const selectConversation = async (id: string) => {
    setConversationId(id);
    setHistoryOpen(false);
    setLoadingHistory(true);
    try {
      const detail = await apiClient.getAiConversation(id);
      setMessages(
        ((detail.messages as Message[]) || []).filter(
          (m) => m.role !== "system"
        )
      );
    } catch {
      setMessages([
        {
          id: newId(),
          role: "assistant",
          failed: true,
          content: "Couldn't load that conversation.",
        },
      ]);
    } finally {
      setLoadingHistory(false);
    }
  };

  const decide = async (messageId: string, decision: "approve" | "reject") => {
    const target = messages.find((m) => m.id === messageId);
    if (!target?.approval || target.approval.state !== "pending") return;
    const setState = (state: NonNullable<Message["approval"]>["state"]) =>
      setMessages((prev) =>
        prev.map((m) =>
          m.id === messageId && m.approval
            ? { ...m, approval: { ...m.approval, state } }
            : m
        )
      );
    setState("working");
    try {
      const res = await apiClient.decideAgentAction(
        target.approval.executionId,
        decision
      );
      setState(decision === "approve" ? "approved" : "rejected");
      const failed = res.status === "FAILED";
      setMessages((prev) => [
        ...prev,
        { id: newId(), role: "assistant", content: res.message, failed },
      ]);
      if (decision === "approve" && !failed) notifyDataChanged();
    } catch (err) {
      setState("pending");
      setMessages((prev) => [
        ...prev,
        {
          id: newId(),
          role: "assistant",
          failed: true,
          content:
            err instanceof Error
              ? err.message
              : "Could not record your decision.",
        },
      ]);
    }
  };

  const newChat = () => {
    setConversationId(null);
    setMessages([]);
    setHistoryOpen(false);
    inputRef.current?.focus();
  };

  const deleteConversation = async (id: string) => {
    try {
      await apiClient.deleteAiConversation(id);
      if (conversationId === id) newChat();
      loadConversations();
    } catch {
      /* ignore */
    }
  };

  const runQuickAction = (action: (typeof QUICK_ACTIONS)[number]) => {
    if (action.send) {
      send(action.prompt);
    } else {
      setInput(action.prompt);
      inputRef.current?.focus();
    }
  };

  const lastFailedPrompt = (() => {
    const last = messages[messages.length - 1];
    if (!last?.failed) return null;
    return (
      [...messages].reverse().find((m) => m.role === "user")?.content || null
    );
  })();

  return (
    <div className="flex h-full min-h-0">
      {/* History */}
      {historyOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/30 lg:hidden"
          onClick={() => setHistoryOpen(false)}
        />
      )}
      <aside
        className={`${historyOpen ? "fixed inset-y-0 left-0 z-40 flex" : "hidden"} w-64 shrink-0 flex-col border-r border-[var(--sidebar-border)] bg-[var(--sidebar-bg)] lg:static lg:flex`}
      >
        <div className="p-3">
          <button
            onClick={newChat}
            className="flex w-full items-center justify-center gap-2 rounded-lg border border-[var(--sidebar-border)] px-3 py-2 text-sm font-medium hover:bg-[var(--surface-hover)]"
          >
            <Icon name="plus" size={16} /> New conversation
          </button>
        </div>
        <p className="px-4 pb-1 text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
          Recent
        </p>
        <div className="flex-1 space-y-0.5 overflow-y-auto px-2 pb-3">
          {conversations.length === 0 ? (
            <p className="px-2 py-4 text-xs text-[var(--text-muted)]">
              Your conversations will appear here.
            </p>
          ) : (
            conversations.map((c) => (
              <div
                key={c.id}
                className={`group flex items-center gap-2 rounded-lg px-2 py-2 text-sm ${
                  conversationId === c.id
                    ? "bg-[var(--primary-soft)] text-[var(--foreground)]"
                    : "text-[var(--text-muted)] hover:bg-[var(--surface-hover)] hover:text-[var(--foreground)]"
                }`}
              >
                <button
                  onClick={() => selectConversation(c.id)}
                  className="min-w-0 flex-1 text-left"
                >
                  <span className="block truncate">
                    {c.title || c.last_message || "Conversation"}
                  </span>
                  <span className="block text-[11px] text-[var(--text-muted)]">
                    {timeAgo(c.updated_at)}
                  </span>
                </button>
                <button
                  onClick={() => deleteConversation(c.id)}
                  aria-label="Delete conversation"
                  className="rounded p-1 opacity-0 hover:text-[var(--danger)] focus:opacity-100 group-hover:opacity-100"
                >
                  <Icon name="trash" size={14} />
                </button>
              </div>
            ))
          )}
        </div>
      </aside>

      {/* Conversation */}
      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex items-center gap-3 border-b border-[var(--sidebar-border)] px-4 py-2.5 md:px-6">
          <button
            onClick={() => setHistoryOpen(true)}
            aria-label="Show conversations"
            className="rounded-md p-1.5 text-[var(--text-muted)] hover:bg-[var(--surface-hover)] lg:hidden"
          >
            <Icon name="message" size={18} />
          </button>
          <h1 className="flex items-center gap-2 text-sm font-semibold">
            <Icon name="sparkles" size={16} className="text-[var(--primary)]" />
            TaskMate AI
          </h1>
          <div
            className="ml-auto flex rounded-lg border border-[var(--sidebar-border)] p-0.5"
            role="group"
            aria-label="Assistant mode"
          >
            {MODES.map((m) => (
              <button
                key={m.id}
                onClick={() => setMode(m.id)}
                title={m.hint}
                aria-pressed={mode === m.id}
                className={`inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                  mode === m.id
                    ? "bg-[var(--primary)] text-white"
                    : "text-[var(--text-muted)] hover:text-[var(--foreground)]"
                }`}
              >
                <Icon name={m.id === "agent" ? "bot" : "message"} size={13} />
                {m.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-6 md:px-6">
          <div className="mx-auto max-w-3xl space-y-5">
            {loadingHistory ? (
              <div className="flex justify-center py-16">
                <LoadingSpinner />
              </div>
            ) : messages.length === 0 ? (
              <div className="flex flex-col items-center pt-[6vh] text-center">
                <span className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--primary-soft)] text-[var(--primary)]">
                  <Icon name="sparkles" size={24} />
                </span>
                <h2 className="text-xl font-semibold">
                  How can I help you today?
                </h2>
                <p className="mt-1 max-w-md text-sm text-[var(--text-muted)]">
                  Ask about your workload, or tell me what to do: create tasks,
                  update statuses, check deadlines, or look at GitHub.
                </p>
                <div className="mt-8 grid w-full max-w-xl grid-cols-1 gap-2 sm:grid-cols-2">
                  {QUICK_ACTIONS.map((action) => (
                    <button
                      key={action.label}
                      onClick={() => runQuickAction(action)}
                      className="flex items-center gap-3 rounded-xl border border-[var(--sidebar-border)] bg-[var(--sidebar-bg)] px-4 py-3 text-left text-sm transition-colors hover:border-[color-mix(in_srgb,var(--primary)_40%,transparent)] hover:bg-[var(--surface-hover)]"
                    >
                      <Icon
                        name={action.icon}
                        size={16}
                        className="text-[var(--text-muted)]"
                      />
                      {action.label}
                    </button>
                  ))}
                </div>
                <p className="mt-6 text-xs text-[var(--text-muted)]">
                  {MODES.find((m) => m.id === mode)?.label} mode:{" "}
                  {MODES.find((m) => m.id === mode)?.hint}.
                </p>
              </div>
            ) : (
              messages.map((m) => (
                <MessageBubble
                  key={m.id}
                  message={m}
                  onSuggestion={send}
                  onDecide={(decision) => decide(m.id, decision)}
                />
              ))
            )}

            {isSending && (
              <div className="flex items-center gap-3 text-sm text-[var(--text-muted)]">
                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-[var(--primary-soft)] text-[var(--primary)]">
                  <Icon name="sparkles" size={14} />
                </span>
                <span className="flex gap-1">
                  {[0, 150, 300].map((delay) => (
                    <span
                      key={delay}
                      className="h-1.5 w-1.5 animate-bounce rounded-full bg-[var(--text-muted)]"
                      style={{ animationDelay: `${delay}ms` }}
                    />
                  ))}
                </span>
                {mode === "agent" && (
                  <span className="text-xs">Working through the steps...</span>
                )}
              </div>
            )}

            {lastFailedPrompt && !isSending && (
              <button
                onClick={() => {
                  setMessages((prev) => prev.slice(0, -2));
                  send(lastFailedPrompt);
                }}
                className="ml-10 text-xs font-medium text-[var(--primary)] hover:underline"
              >
                Try again
              </button>
            )}
            <div ref={endRef} />
          </div>
        </div>

        <div className="border-t border-[var(--sidebar-border)] bg-[var(--background)] px-4 py-3 md:px-6">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              send();
            }}
            className="mx-auto flex max-w-3xl items-end gap-2 rounded-xl border border-[var(--sidebar-border)] bg-[var(--sidebar-bg)] p-2 focus-within:border-[var(--primary)] focus-within:ring-2 focus-within:ring-[var(--primary-soft)]"
          >
            <textarea
              ref={inputRef}
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  send();
                }
              }}
              placeholder={
                mode === "agent"
                  ? "Ask TaskMate to do something, e.g. 'Check open PRs and create review tasks'"
                  : "Ask TaskMate anything, e.g. 'Create a high priority task to fix login, due tomorrow'"
              }
              aria-label="Message"
              disabled={isSending}
              className="max-h-[200px] flex-1 resize-none bg-transparent px-2 py-1.5 text-sm placeholder:text-[var(--text-muted)] focus:outline-none disabled:opacity-60"
            />
            <button
              type="submit"
              disabled={!input.trim() || isSending}
              className="inline-flex items-center gap-1.5 rounded-lg bg-[var(--primary)] px-3.5 py-2 text-sm font-medium text-white transition-opacity hover:bg-[var(--primary-hover)] disabled:cursor-not-allowed disabled:opacity-40"
            >
              <Icon name="send" size={14} />
              Send
            </button>
          </form>
          <p className="mx-auto mt-1.5 max-w-3xl px-1 text-[11px] text-[var(--text-muted)]">
            <span className="kbd">Enter</span> to send,{" "}
            <span className="kbd">Shift</span>+
            <span className="kbd">Enter</span> for a new line
          </p>
        </div>
      </div>
    </div>
  );
}

function MessageBubble({
  message: m,
  onSuggestion,
  onDecide,
}: {
  message: Message;
  onSuggestion: (text: string) => void;
  onDecide: (decision: "approve" | "reject") => void;
}) {
  if (m.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-br-md bg-[var(--primary)] px-4 py-2.5 text-sm text-white">
          {m.content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-3">
      <span
        className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${
          m.failed
            ? "bg-[var(--danger-soft)] text-[var(--danger)]"
            : "bg-[var(--primary-soft)] text-[var(--primary)]"
        }`}
      >
        <Icon name={m.failed ? "alert" : "sparkles"} size={14} />
      </span>
      <div className="min-w-0 flex-1 space-y-2.5">
        <MarkdownRenderer
          content={m.content}
          className={m.failed ? "!text-[var(--danger)]" : ""}
        />

        {m.clarify && (
          <p className="inline-flex items-center gap-1 rounded-full bg-[var(--warning-soft)] px-2 py-0.5 text-[11px] font-medium text-[var(--warning)]">
            <Icon name="message" size={11} /> Waiting for your answer
          </p>
        )}

        {m.approval && (
          <ApprovalCard approval={m.approval} onDecide={onDecide} />
        )}

        {m.actions && m.actions.length > 0 && (
          <div className="space-y-1.5">
            {m.actions.map((action, i) => (
              <div
                key={i}
                className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-xs ${
                  action.success
                    ? "border-[color-mix(in_srgb,var(--success)_30%,transparent)] bg-[var(--success-soft)]"
                    : "border-[color-mix(in_srgb,var(--danger)_30%,transparent)] bg-[var(--danger-soft)]"
                }`}
              >
                <Icon
                  name={action.success ? "check" : "x"}
                  size={14}
                  className={
                    action.success
                      ? "text-[var(--success)]"
                      : "text-[var(--danger)]"
                  }
                />
                <span className="flex-1">{actionLabel(action)}</span>
                {!!action.data?.task_id && (
                  <Link
                    href={`/tasks/${String(action.data.task_id)}`}
                    className="inline-flex items-center gap-1 font-medium text-[var(--primary)] hover:underline"
                  >
                    Open task <Icon name="arrowRight" size={12} />
                  </Link>
                )}
              </div>
            ))}
          </div>
        )}

        {m.suggestions && m.suggestions.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {m.suggestions.map((s, i) => (
              <button
                key={i}
                onClick={() => onSuggestion(s)}
                className="rounded-full border border-[var(--sidebar-border)] px-2.5 py-1 text-xs text-[var(--text-muted)] hover:border-[color-mix(in_srgb,var(--primary)_40%,transparent)] hover:text-[var(--foreground)]"
              >
                {s}
              </button>
            ))}
          </div>
        )}

        {m.context_summary && <ContextNote summary={m.context_summary} />}
      </div>
    </div>
  );
}

function ContextNote({
  summary,
}: {
  summary: NonNullable<Message["context_summary"]>;
}) {
  const tasks = summary.tasks_count ?? summary.task_count;
  const projects = summary.projects_count ?? summary.project_count;
  if (!tasks && !projects) return null;
  return (
    <p className="text-[11px] text-[var(--text-muted)]">
      Looked at {tasks ?? 0} recent tasks across {projects ?? 0} projects
      {(summary.overdue_count || 0) > 0 && `, ${summary.overdue_count} overdue`}
    </p>
  );
}

function ApprovalCard({
  approval,
  onDecide,
}: {
  approval: NonNullable<Message["approval"]>;
  onDecide: (decision: "approve" | "reject") => void;
}) {
  const { action, state } = approval;
  const args = Object.entries(action.arguments).filter(
    ([, v]) => v !== null && v !== undefined && v !== ""
  );
  return (
    <div className="rounded-xl border border-[color-mix(in_srgb,var(--warning)_40%,transparent)] bg-[var(--warning-soft)] p-3 text-sm">
      <p className="mb-1 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-[var(--warning)]">
        <Icon name="alert" size={13} /> Needs your approval
      </p>
      <p className="font-medium">{action.summary}</p>
      {args.length > 0 && (
        <dl className="mt-2 grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5 text-xs">
          {args.map(([k, v]) => (
            <div key={k} className="contents">
              <dt className="text-[var(--text-muted)]">
                {k.replace(/_/g, " ")}
              </dt>
              <dd className="break-all font-mono">{String(v)}</dd>
            </div>
          ))}
        </dl>
      )}
      {state === "pending" || state === "working" ? (
        <div className="mt-3 flex gap-2">
          <button
            onClick={() => onDecide("approve")}
            disabled={state === "working"}
            className="inline-flex items-center gap-1.5 rounded-lg bg-[var(--primary)] px-3 py-1.5 text-xs font-medium text-white hover:bg-[var(--primary-hover)] disabled:opacity-50"
          >
            <Icon name="check" size={13} />{" "}
            {state === "working" ? "Working..." : "Approve"}
          </button>
          <button
            onClick={() => onDecide("reject")}
            disabled={state === "working"}
            className="rounded-lg border border-[var(--sidebar-border)] bg-[var(--sidebar-bg)] px-3 py-1.5 text-xs font-medium hover:bg-[var(--surface-hover)] disabled:opacity-50"
          >
            Reject
          </button>
        </div>
      ) : (
        <p className="mt-2 text-xs font-medium text-[var(--text-muted)]">
          {state === "approved" ? "Approved" : "Rejected"}
        </p>
      )}
    </div>
  );
}
