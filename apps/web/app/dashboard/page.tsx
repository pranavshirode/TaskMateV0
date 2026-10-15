"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import {
  apiClient,
  type DashboardToday,
  type Project,
  type Task,
} from "@/lib/api-client";
import { describeDue, errorMessage, formatDate, isoDate } from "@/lib/format";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import ErrorState from "@/components/ui/ErrorState";
import Icon, { type IconName } from "@/components/ui/Icon";
import TaskRow from "@/components/tasks/TaskRow";
import { useTaskActions } from "@/components/tasks/useTaskActions";
import { useWorkspaceUI } from "@/components/layout/WorkspaceUI";
import { useFeedback } from "@/components/ui/Feedback";

type FocusTab = "focus" | "priority" | "recent";

const AI_SUGGESTIONS = [
  "What should I work on today?",
  "Summarize my overdue tasks",
  "Which project is most at risk?",
];

function greeting() {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

function dedupe(tasks: Task[]) {
  const seen = new Set<string>();
  return tasks.filter((t) => (seen.has(t.id) ? false : (seen.add(t.id), true)));
}

export default function DashboardPage() {
  const { user } = useAuth();
  const router = useRouter();
  const { dataVersion, openQuickAdd } = useWorkspaceUI();
  const { toast } = useFeedback();
  const [data, setData] = useState<DashboardToday | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<FocusTab>("focus");
  const [newTitle, setNewTitle] = useState("");
  const [aiPrompt, setAiPrompt] = useState("");

  const fetchDashboard = useCallback(async (silent = false) => {
    try {
      if (!silent) setIsLoading(true);
      setError(null);
      setData(await apiClient.getDashboardToday());
    } catch (err: unknown) {
      setError(errorMessage(err, "Failed to load dashboard data"));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboard(dataVersion > 0);
  }, [fetchDashboard, dataVersion]);

  // Update a task in place across every list so completed items stay visible (with undo).
  const replaceTask = useCallback((task: Task) => {
    setData((prev) => {
      if (!prev) return prev;
      const swap = (list: Task[] = []) =>
        list.map((t) => (t.id === task.id ? task : t));
      return {
        ...prev,
        due_today: swap(prev.due_today),
        overdue: swap(prev.overdue),
        high_priority: swap(prev.high_priority),
        recently_updated: swap(prev.recently_updated),
      };
    });
  }, []);
  const { toggleComplete, setStatus } = useTaskActions(replaceTask);

  const projectNames = useMemo(() => {
    const map: Record<string, string> = {};
    data?.active_projects?.forEach((p) => (map[p.id] = p.name));
    return map;
  }, [data]);

  const addTaskForToday = async (e: React.FormEvent) => {
    e.preventDefault();
    const title = newTitle.trim();
    if (!title) return;
    setNewTitle("");
    try {
      await apiClient.createTask({
        title,
        due_date: isoDate(0),
        status: "TODO",
        priority: "MEDIUM",
      });
      toast(`Added "${title}" for today`);
      setTab("focus");
      fetchDashboard(true);
    } catch (err) {
      setNewTitle(title);
      toast(errorMessage(err, "Could not add the task"), "error");
    }
  };

  const askAI = (prompt: string) => {
    if (prompt.trim())
      router.push(`/ai?q=${encodeURIComponent(prompt.trim())}`);
  };

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return <ErrorState message={error} onRetry={() => fetchDashboard()} />;
  }

  if (!data) {
    return null;
  }

  const overdue = data.overdue || [];
  const dueToday = data.due_today || [];
  const highPriority = data.high_priority || [];
  const recent = data.recently_updated || [];
  const projects = data.active_projects || [];
  const openOverdue = overdue.filter((t) => t.status !== "COMPLETED").length;
  const openToday = dueToday.filter((t) => t.status !== "COMPLETED").length;
  const isEmptyWorkspace =
    projects.length === 0 &&
    recent.length === 0 &&
    overdue.length === 0 &&
    dueToday.length === 0;

  const tabs: { id: FocusTab; label: string; tasks: Task[]; empty: string }[] =
    [
      {
        id: "focus",
        label: "Overdue & today",
        tasks: dedupe([...overdue, ...dueToday]),
        empty:
          "Nothing overdue or due today. Plan ahead or pick something from High priority.",
      },
      {
        id: "priority",
        label: "High priority",
        tasks: highPriority,
        empty: "No high or urgent tasks right now.",
      },
      {
        id: "recent",
        label: "Recently updated",
        tasks: recent.slice(0, 10),
        empty: "No recent activity yet.",
      },
    ];
  const current = tabs.find((t) => t.id === tab)!;

  const summary =
    openOverdue + openToday === 0
      ? "You're all caught up for today."
      : [
          openOverdue > 0 && `${openOverdue} overdue`,
          openToday > 0 && `${openToday} due today`,
        ]
          .filter(Boolean)
          .join(" and ") + " need your attention.";

  return (
    <div className="mx-auto max-w-6xl space-y-6 pb-12">
      <header>
        <p className="text-sm text-[var(--text-muted)]">
          {new Date().toLocaleDateString(undefined, {
            weekday: "long",
            month: "long",
            day: "numeric",
          })}
        </p>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight sm:text-3xl">
          {greeting()}, {user?.name?.split(" ")[0] || "Developer"}
        </h1>
        <p className="mt-1 text-[var(--text-muted)]">{summary}</p>
      </header>

      {isEmptyWorkspace ? (
        <GettingStarted onAddTask={() => openQuickAdd()} />
      ) : (
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <StatTile
            icon="alert"
            label="Overdue"
            value={openOverdue}
            tone="danger"
            active={tab === "focus" && openOverdue > 0}
            onClick={() => setTab("focus")}
          />
          <StatTile
            icon="clock"
            label="Due today"
            value={openToday}
            tone="warning"
            onClick={() => setTab("focus")}
          />
          <StatTile
            icon="flame"
            label="High priority"
            value={highPriority.filter((t) => t.status !== "COMPLETED").length}
            tone="primary"
            active={tab === "priority"}
            onClick={() => setTab("priority")}
          />
          <StatTile
            icon="folder"
            label="Active projects"
            value={projects.length}
            tone="success"
            onClick={() => router.push("/projects")}
          />
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Focus list */}
        <section className="card overflow-hidden lg:col-span-2">
          <div className="flex flex-wrap items-center gap-1 border-b border-[var(--sidebar-border)] px-3 pt-3">
            {tabs.map((t) => {
              const count = t.tasks.filter(
                (x) => x.status !== "COMPLETED"
              ).length;
              return (
                <button
                  key={t.id}
                  onClick={() => setTab(t.id)}
                  className={`-mb-px flex items-center gap-2 border-b-2 px-3 pb-2.5 pt-1 text-sm transition-colors ${
                    tab === t.id
                      ? "border-[var(--primary)] font-medium text-[var(--foreground)]"
                      : "border-transparent text-[var(--text-muted)] hover:text-[var(--foreground)]"
                  }`}
                >
                  {t.label}
                  {t.id !== "recent" && count > 0 && (
                    <span className="rounded-full bg-[var(--surface-hover)] px-1.5 text-xs">
                      {count}
                    </span>
                  )}
                </button>
              );
            })}
            <Link
              href="/tasks"
              className="mb-2 ml-auto hidden items-center gap-1 px-2 text-xs text-[var(--text-muted)] hover:text-[var(--primary)] sm:inline-flex"
            >
              All tasks <Icon name="arrowRight" size={12} />
            </Link>
          </div>

          <form
            onSubmit={addTaskForToday}
            className="flex items-center gap-3 border-b border-[var(--sidebar-border)] px-4 py-2.5"
          >
            <Icon name="plus" size={18} className="text-[var(--primary)]" />
            <input
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder="Add a task for today and press Enter"
              aria-label="Add a task for today"
              className="flex-1 bg-transparent py-1 text-sm placeholder:text-[var(--text-muted)] focus:outline-none"
            />
            {newTitle && <span className="kbd">Enter</span>}
          </form>

          {current.tasks.length > 0 ? (
            <div className="divide-y divide-[var(--sidebar-border)]">
              {current.tasks.map((task) => (
                <TaskRow
                  key={task.id}
                  task={task}
                  projectName={
                    task.project_id ? projectNames[task.project_id] : undefined
                  }
                  onToggle={toggleComplete}
                  onStatusChange={setStatus}
                />
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center px-6 py-12 text-center">
              <span className="mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-[var(--success-soft)] text-[var(--success)]">
                <Icon name="check" />
              </span>
              <p className="max-w-xs text-sm text-[var(--text-muted)]">
                {current.empty}
              </p>
            </div>
          )}
        </section>

        {/* Side column */}
        <div className="space-y-6">
          <section className="card p-5">
            <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold">
              <Icon
                name="sparkles"
                size={16}
                className="text-[var(--primary)]"
              />
              Ask TaskMate
            </h2>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                askAI(aiPrompt);
              }}
              className="flex gap-2"
            >
              <input
                value={aiPrompt}
                onChange={(e) => setAiPrompt(e.target.value)}
                placeholder="e.g. Plan my afternoon"
                aria-label="Ask TaskMate"
                className="field"
              />
              <button
                type="submit"
                aria-label="Ask"
                disabled={!aiPrompt.trim()}
                className="rounded-lg bg-[var(--primary)] px-3 text-white disabled:opacity-40"
              >
                <Icon name="send" size={16} />
              </button>
            </form>
            <div className="mt-3 flex flex-wrap gap-1.5">
              {AI_SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => askAI(s)}
                  className="rounded-full border border-[var(--sidebar-border)] px-2.5 py-1 text-xs text-[var(--text-muted)] hover:border-[color-mix(in_srgb,var(--primary)_40%,transparent)] hover:text-[var(--foreground)]"
                >
                  {s}
                </button>
              ))}
            </div>
          </section>

          <section className="card p-5">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-semibold">Active projects</h2>
              <Link
                href="/projects"
                className="text-xs text-[var(--text-muted)] hover:text-[var(--primary)]"
              >
                View all
              </Link>
            </div>
            {projects.length > 0 ? (
              <div className="space-y-1">
                {projects.slice(0, 5).map((project) => (
                  <ProjectProgress key={project.id} project={project} />
                ))}
              </div>
            ) : (
              <p className="text-sm text-[var(--text-muted)]">
                No active projects.{" "}
                <Link
                  href="/projects/new"
                  className="text-[var(--primary)] hover:underline"
                >
                  Create one
                </Link>
              </p>
            )}
          </section>

          <Link
            href="/requirements"
            className="card group block p-5 transition-colors hover:border-[color-mix(in_srgb,var(--primary)_40%,transparent)]"
          >
            <h2 className="mb-1 flex items-center gap-2 text-sm font-semibold">
              <Icon
                name="requirements"
                size={16}
                className="text-[var(--primary)]"
              />
              Got a new client brief?
            </h2>
            <p className="text-sm text-[var(--text-muted)]">
              Paste it in and TaskMate will extract requirements, ask clarifying
              questions, and draft the tasks for you.
            </p>
            <div className="mt-3 flex items-center gap-2 text-xs text-[var(--text-muted)]">
              <span>Brief</span>
              <Icon name="chevronRight" size={12} />
              <span>Requirements</span>
              <Icon name="chevronRight" size={12} />
              <span>Tasks</span>
              <Icon
                name="arrowRight"
                size={14}
                className="ml-auto text-[var(--primary)] transition-transform group-hover:translate-x-0.5"
              />
            </div>
          </Link>
        </div>
      </div>
    </div>
  );
}

const TILE_TONES = {
  danger: "text-[var(--danger)] bg-[var(--danger-soft)]",
  warning: "text-[var(--warning)] bg-[var(--warning-soft)]",
  primary: "text-[var(--primary)] bg-[var(--primary-soft)]",
  success: "text-[var(--success)] bg-[var(--success-soft)]",
};

function StatTile({
  icon,
  label,
  value,
  tone,
  active,
  onClick,
}: {
  icon: IconName;
  label: string;
  value: number;
  tone: keyof typeof TILE_TONES;
  active?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`card flex items-center gap-3 p-4 text-left transition-colors hover:border-[color-mix(in_srgb,var(--primary)_40%,transparent)] ${
        active
          ? "!border-[color-mix(in_srgb,var(--primary)_50%,transparent)]"
          : ""
      }`}
    >
      <span
        className={`flex h-9 w-9 items-center justify-center rounded-lg ${TILE_TONES[tone]}`}
      >
        <Icon name={icon} size={18} />
      </span>
      <span>
        <span className="block text-xl font-semibold leading-tight">
          {value}
        </span>
        <span className="block text-xs text-[var(--text-muted)]">{label}</span>
      </span>
    </button>
  );
}

function ProjectProgress({ project }: { project: Project }) {
  const total = project.task_summary?.total ?? 0;
  const completed = project.task_summary?.completed ?? 0;
  const pct = total > 0 ? Math.round((completed / total) * 100) : 0;
  const deadline = project.deadline ? describeDue(project.deadline) : null;

  return (
    <Link
      href={`/projects/${project.id}`}
      className="-mx-2 block rounded-lg px-2 py-2 transition-colors hover:bg-[var(--surface-hover)]"
    >
      <div className="flex items-center justify-between gap-2">
        <span className="truncate text-sm font-medium">{project.name}</span>
        {deadline && (
          <span
            className={`shrink-0 text-xs ${deadline.tone === "overdue" ? "text-[var(--danger)]" : "text-[var(--text-muted)]"}`}
            title={`Deadline ${formatDate(project.deadline)}`}
          >
            {deadline.tone === "later"
              ? formatDate(project.deadline)
              : deadline.text}
          </span>
        )}
      </div>
      {total > 0 && (
        <div className="mt-1.5 flex items-center gap-2">
          <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-[var(--surface-hover)]">
            <div
              className="h-full rounded-full bg-[var(--primary)]"
              style={{ width: `${pct}%` }}
            />
          </div>
          <span className="text-[11px] text-[var(--text-muted)]">
            {completed}/{total}
          </span>
        </div>
      )}
    </Link>
  );
}

function GettingStarted({ onAddTask }: { onAddTask: () => void }) {
  const steps: {
    title: string;
    text: string;
    href?: string;
    onClick?: () => void;
    icon: IconName;
  }[] = [
    {
      title: "Add a client",
      text: "Who are you working for?",
      href: "/clients/new",
      icon: "users",
    },
    {
      title: "Create a project",
      text: "Group work under a client and deadline.",
      href: "/projects/new",
      icon: "folder",
    },
    {
      title: "Analyze a brief",
      text: "Let AI turn a client brief into tasks.",
      href: "/requirements",
      icon: "requirements",
    },
    {
      title: "Add your first task",
      text: "Or press C anywhere.",
      onClick: onAddTask,
      icon: "plus",
    },
  ];
  return (
    <section className="card p-5">
      <h2 className="text-base font-semibold">Set up your workspace</h2>
      <p className="mb-4 text-sm text-[var(--text-muted)]">
        Four quick steps to get TaskMate working for you.
      </p>
      <ol className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {steps.map((step, i) => {
          const body = (
            <>
              <span className="mb-3 flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--primary-soft)] text-[var(--primary)]">
                <Icon name={step.icon} size={16} />
              </span>
              <span className="block text-sm font-medium">
                {i + 1}. {step.title}
              </span>
              <span className="mt-0.5 block text-xs text-[var(--text-muted)]">
                {step.text}
              </span>
            </>
          );
          const cls =
            "block h-full w-full rounded-lg border border-[var(--sidebar-border)] p-4 text-left transition-colors hover:border-[color-mix(in_srgb,var(--primary)_40%,transparent)] hover:bg-[var(--surface-hover)]";
          return (
            <li key={step.title}>
              {step.href ? (
                <Link href={step.href} className={cls}>
                  {body}
                </Link>
              ) : (
                <button onClick={step.onClick} className={cls}>
                  {body}
                </button>
              )}
            </li>
          );
        })}
      </ol>
    </section>
  );
}
