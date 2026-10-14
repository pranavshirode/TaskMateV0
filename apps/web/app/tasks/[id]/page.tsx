"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { apiClient, type Task, type TaskEvent } from "@/lib/api-client";
import {
  describeDue,
  errorMessage,
  formatDate,
  humanize,
  isoDate,
  parseServerDate,
  PRIORITY_LABELS,
  TASK_PRIORITIES,
  TASK_STATUSES,
  timeAgo,
} from "@/lib/format";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import ErrorState from "@/components/ui/ErrorState";
import Button from "@/components/ui/Button";
import Icon from "@/components/ui/Icon";
import { priorityDotClass, statusDotClass } from "@/components/ui/Badge";
import { useFeedback } from "@/components/ui/Feedback";

const EVENT_LABELS: Record<string, string> = {
  TASK_CREATED: "Task created",
  TASK_UPDATED: "Task updated",
  STATUS_CHANGED: "Status changed",
  PRIORITY_CHANGED: "Priority changed",
  DUE_DATE_CHANGED: "Due date changed",
  TASK_COMPLETED: "Task completed",
  TASK_ARCHIVED: "Task archived",
};

export default function TaskDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { toast, confirm } = useFeedback();
  const [task, setTask] = useState<Task | null>(null);
  const [events, setEvents] = useState<TaskEvent[]>([]);
  const [projectName, setProjectName] = useState<string | null>(null);
  const [clientName, setClientName] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState("");
  const [editDesc, setEditDesc] = useState("");

  const fetchTask = useCallback(
    async (silent = false) => {
      try {
        if (!silent) setIsLoading(true);
        setError(null);
        const [taskData, eventsData] = await Promise.all([
          apiClient.getTask(id),
          apiClient.getTaskEvents(id),
        ]);
        setTask(taskData);
        setEvents(eventsData.items || []);
        setEditTitle(taskData.title);
        setEditDesc(taskData.description || "");
        if (taskData.project_id) {
          apiClient
            .getProject(taskData.project_id)
            .then((p) => setProjectName(p.name))
            .catch(() => {});
        }
        if (taskData.client_id) {
          apiClient
            .getClient(taskData.client_id)
            .then((c) => setClientName(c.name))
            .catch(() => {});
        }
      } catch (err: unknown) {
        setError(errorMessage(err, "Failed to load task"));
      } finally {
        setIsLoading(false);
      }
    },
    [id]
  );

  useEffect(() => {
    fetchTask();
  }, [fetchTask]);

  const run = async (
    action: () => Promise<unknown>,
    success: string,
    failure: string
  ) => {
    try {
      await action();
      toast(success);
      fetchTask(true);
    } catch (err: unknown) {
      toast(errorMessage(err, failure), "error");
    }
  };

  const handleStatusChange = (status: string) =>
    run(
      () => apiClient.changeTaskStatus(id, status),
      `Status set to ${humanize(status)}`,
      "Failed to change status"
    );

  const handlePriorityChange = (priority: string) =>
    run(
      () => apiClient.changeTaskPriority(id, priority),
      `Priority set to ${PRIORITY_LABELS[priority]}`,
      "Failed to change priority"
    );

  const handleDueChange = (due: string) =>
    run(
      // An explicit null clears the date (the API applies only fields that are sent).
      () =>
        apiClient.updateTask(id, {
          due_date: (due || null) as string | undefined,
        }),
      due ? `Due ${formatDate(due)}` : "Due date cleared",
      "Failed to update due date"
    );

  const handleSaveEdit = async () => {
    if (!editTitle.trim()) {
      toast("Title can't be empty", "error");
      return;
    }
    await run(
      () =>
        apiClient.updateTask(id, {
          title: editTitle.trim(),
          description: editDesc,
        }),
      "Changes saved",
      "Failed to save"
    );
    setIsEditing(false);
  };

  const handleArchive = async () => {
    const ok = await confirm({
      title: "Archive this task?",
      message: "It will be hidden from your lists and dashboard.",
      confirmLabel: "Archive",
      danger: true,
    });
    if (!ok) return;
    try {
      await apiClient.archiveTask(id);
      toast("Task archived");
      router.push("/tasks");
    } catch (err: unknown) {
      toast(errorMessage(err, "Failed to archive"), "error");
    }
  };

  if (isLoading)
    return (
      <div className="flex justify-center py-16">
        <LoadingSpinner />
      </div>
    );
  if (error) return <ErrorState message={error} onRetry={() => fetchTask()} />;
  if (!task) return null;

  const done = task.status === "COMPLETED";
  const due = describeDue(task.due_date, done);

  return (
    <div className="mx-auto max-w-5xl pb-12">
      <Link
        href="/tasks"
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-[var(--text-muted)] hover:text-[var(--foreground)]"
      >
        <Icon name="arrowLeft" size={14} /> Tasks
      </Link>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <section className="card p-6">
            {isEditing ? (
              <div className="space-y-3">
                <input
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  aria-label="Title"
                  autoFocus
                  className="field !text-lg font-semibold"
                />
                <textarea
                  value={editDesc}
                  onChange={(e) => setEditDesc(e.target.value)}
                  rows={5}
                  aria-label="Description"
                  placeholder="Add details, acceptance criteria, links..."
                  className="field"
                />
                <div className="flex gap-2">
                  <Button onClick={handleSaveEdit}>Save</Button>
                  <Button
                    variant="ghost"
                    onClick={() => {
                      setIsEditing(false);
                      setEditTitle(task.title);
                      setEditDesc(task.description || "");
                    }}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            ) : (
              <>
                <div className="flex items-start justify-between gap-4">
                  <h1
                    className={`text-xl font-semibold tracking-tight ${done ? "text-[var(--text-muted)] line-through" : ""}`}
                  >
                    {task.title}
                  </h1>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setIsEditing(true)}
                  >
                    <Icon name="edit" size={14} /> Edit
                  </Button>
                </div>
                <button
                  onClick={() => setIsEditing(true)}
                  className="mt-3 block w-full text-left text-sm"
                >
                  {task.description ? (
                    <p className="whitespace-pre-wrap text-[color-mix(in_srgb,var(--foreground)_85%,transparent)]">
                      {task.description}
                    </p>
                  ) : (
                    <p className="text-[var(--text-muted)] hover:text-[var(--foreground)]">
                      + Add a description
                    </p>
                  )}
                </button>
              </>
            )}

            <div className="mt-6 flex flex-wrap gap-2 border-t border-[var(--sidebar-border)] pt-5">
              <Button
                variant={done ? "secondary" : "primary"}
                onClick={() => handleStatusChange(done ? "TODO" : "COMPLETED")}
              >
                <Icon name="check" size={16} />
                {done ? "Reopen task" : "Mark as done"}
              </Button>
              <Link
                href={`/ai?q=${encodeURIComponent(`Help me plan the task "${task.title}"`)}`}
              >
                <Button variant="secondary">
                  <Icon
                    name="sparkles"
                    size={16}
                    className="text-[var(--primary)]"
                  />{" "}
                  Ask AI about this
                </Button>
              </Link>
            </div>
          </section>

          <section className="card p-6">
            <h2 className="mb-3 text-sm font-semibold">Status</h2>
            <div className="flex flex-wrap gap-2">
              {TASK_STATUSES.map((s) => (
                <button
                  key={s}
                  onClick={() => handleStatusChange(s)}
                  aria-pressed={task.status === s}
                  className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${
                    task.status === s
                      ? "border-[var(--primary)] bg-[var(--primary-soft)] text-[var(--primary)]"
                      : "border-[var(--sidebar-border)] text-[var(--text-muted)] hover:bg-[var(--surface-hover)] hover:text-[var(--foreground)]"
                  }`}
                >
                  <span
                    className={`h-1.5 w-1.5 rounded-full ${statusDotClass(s)}`}
                  />
                  {humanize(s)}
                </button>
              ))}
            </div>

            <h2 className="mb-3 mt-6 text-sm font-semibold">Priority</h2>
            <div className="flex flex-wrap gap-2">
              {TASK_PRIORITIES.map((p) => (
                <button
                  key={p}
                  onClick={() => handlePriorityChange(p)}
                  aria-pressed={task.priority === p}
                  className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${
                    task.priority === p
                      ? "border-[var(--primary)] bg-[var(--primary-soft)] text-[var(--primary)]"
                      : "border-[var(--sidebar-border)] text-[var(--text-muted)] hover:bg-[var(--surface-hover)] hover:text-[var(--foreground)]"
                  }`}
                >
                  <span
                    className={`h-2 w-2 rounded-full ${priorityDotClass(p)}`}
                  />
                  {PRIORITY_LABELS[p]}
                </button>
              ))}
            </div>
          </section>

          <section className="card p-6">
            <h2 className="mb-4 text-sm font-semibold">Activity</h2>
            {events.length > 0 ? (
              <ol className="relative space-y-4 border-l border-[var(--sidebar-border)] pl-5">
                {events.map((event: TaskEvent) => (
                  <li key={event.id} className="relative text-sm">
                    <span className="absolute -left-[1.4rem] top-1.5 h-2 w-2 rounded-full bg-[var(--primary)] ring-4 ring-[var(--sidebar-bg)]" />
                    <span className="font-medium">
                      {EVENT_LABELS[event.event_type] ||
                        humanize(event.event_type)}
                    </span>
                    {Boolean(
                      event.data?.old_value && event.data?.new_value
                    ) && (
                      <span className="text-[var(--text-muted)]">
                        {" "}
                        {humanize(String(event.data?.old_value))} →{" "}
                        {humanize(String(event.data?.new_value))}
                      </span>
                    )}
                    <div
                      className="mt-0.5 text-xs text-[var(--text-muted)]"
                      title={parseServerDate(event.created_at).toLocaleString()}
                    >
                      {timeAgo(event.created_at)}
                    </div>
                  </li>
                ))}
              </ol>
            ) : (
              <p className="text-sm text-[var(--text-muted)]">
                No activity recorded yet.
              </p>
            )}
          </section>
        </div>

        <aside className="space-y-6">
          <section className="card divide-y divide-[var(--sidebar-border)] text-sm">
            <Detail label="Due date">
              <div className="flex flex-col items-end gap-1.5">
                <input
                  type="date"
                  value={task.due_date?.slice(0, 10) || ""}
                  onChange={(e) => handleDueChange(e.target.value)}
                  aria-label="Due date"
                  className="field !w-auto !py-1 text-xs"
                />
                <span className="flex gap-2 text-xs">
                  {due.tone !== "none" && (
                    <span
                      className={
                        due.tone === "overdue"
                          ? "text-[var(--danger)]"
                          : "text-[var(--text-muted)]"
                      }
                    >
                      {due.text}
                    </span>
                  )}
                  {task.due_date !== isoDate(1) && (
                    <button
                      className="text-[var(--primary)] hover:underline"
                      onClick={() => handleDueChange(isoDate(1))}
                    >
                      Tomorrow
                    </button>
                  )}
                </span>
              </div>
            </Detail>
            <Detail label="Project">
              {task.project_id ? (
                <Link
                  href={`/projects/${task.project_id}`}
                  className="text-[var(--primary)] hover:underline"
                >
                  {projectName || "View project"}
                </Link>
              ) : (
                <span className="text-[var(--text-muted)]">None</span>
              )}
            </Detail>
            <Detail label="Client">
              {task.client_id ? (
                <Link
                  href={`/clients/${task.client_id}`}
                  className="text-[var(--primary)] hover:underline"
                >
                  {clientName || "View client"}
                </Link>
              ) : (
                <span className="text-[var(--text-muted)]">None</span>
              )}
            </Detail>
            <Detail label="Estimate">
              {task.estimated_minutes ? (
                task.estimated_minutes >= 60 ? (
                  `${Math.round((task.estimated_minutes / 60) * 10) / 10} h`
                ) : (
                  `${task.estimated_minutes} min`
                )
              ) : (
                <span className="text-[var(--text-muted)]">—</span>
              )}
            </Detail>
            {task.labels && task.labels.length > 0 && (
              <Detail label="Labels">
                <div className="flex flex-wrap justify-end gap-1.5">
                  {task.labels.map((l, i) => {
                    const name = typeof l === "string" ? l : l.name;
                    const color = typeof l === "object" ? l.color : undefined;
                    return (
                      <span
                        key={typeof l === "string" ? l : l.id || i}
                        className="rounded-full bg-[var(--primary-soft)] px-2 py-0.5 text-xs font-medium text-[var(--primary)]"
                        style={
                          color
                            ? { backgroundColor: color + "22", color }
                            : undefined
                        }
                      >
                        {name}
                      </span>
                    );
                  })}
                </div>
              </Detail>
            )}
            <Detail label="Created">
              {task.created_at ? formatDate(task.created_at) : "—"}
            </Detail>
            <Detail label="Updated">
              {task.updated_at ? timeAgo(task.updated_at) : "—"}
            </Detail>
          </section>

          <Button variant="danger" className="w-full" onClick={handleArchive}>
            <Icon name="archive" size={16} /> Archive task
          </Button>
        </aside>
      </div>
    </div>
  );
}

function Detail({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-start justify-between gap-4 px-5 py-3">
      <span className="pt-0.5 text-[var(--text-muted)]">{label}</span>
      <div className="text-right">{children}</div>
    </div>
  );
}
