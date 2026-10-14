"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { apiClient, type Task, type TaskEvent } from "@/lib/api-client";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import ErrorState from "@/components/ui/ErrorState";
import Button from "@/components/ui/Button";

const STATUSES = [
  "BACKLOG",
  "TODO",
  "IN_PROGRESS",
  "BLOCKED",
  "REVIEW",
  "COMPLETED",
];
const PRIORITIES = ["LOW", "MEDIUM", "HIGH", "URGENT"];
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
  const [task, setTask] = useState<Task | null>(null);
  const [events, setEvents] = useState<TaskEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState("");
  const [editDesc, setEditDesc] = useState("");

  const fetchTask = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const [taskData, eventsData] = await Promise.all([
        apiClient.getTask(id),
        apiClient.getTaskEvents(id),
      ]);
      setTask(taskData);
      setEvents(eventsData.items || []);
      setEditTitle(taskData.title);
      setEditDesc(taskData.description || "");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load task");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTask();
  }, [id]);

  const handleStatusChange = async (newStatus: string) => {
    try {
      await apiClient.changeTaskStatus(id, newStatus);
      fetchTask();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to change status");
    }
  };

  const handlePriorityChange = async (newPriority: string) => {
    try {
      await apiClient.changeTaskPriority(id, newPriority);
      fetchTask();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to change priority");
    }
  };

  const handleSaveEdit = async () => {
    try {
      await apiClient.updateTask(id, {
        title: editTitle,
        description: editDesc,
      });
      setIsEditing(false);
      fetchTask();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to save");
    }
  };

  const handleArchive = async () => {
    if (!confirm("Archive this task?")) return;
    try {
      await apiClient.archiveTask(id);
      router.push("/tasks");
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to archive");
    }
  };

  if (isLoading)
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner />
      </div>
    );
  if (error) return <ErrorState message={error} onRetry={fetchTask} />;
  if (!task) return null;

  return (
    <div className="max-w-3xl mx-auto pb-12">
      <div className="mb-4">
        <Link
          href="/tasks"
          className="text-sm text-[var(--text-muted)] hover:text-[var(--foreground)]"
        >
          ← Back to Tasks
        </Link>
      </div>

      <div className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-6 mb-6">
        {isEditing ? (
          <div className="space-y-4">
            <input
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              className="w-full text-xl font-bold bg-[var(--background)] border border-[var(--sidebar-border)] rounded-lg px-3 py-2 text-[var(--foreground)]"
            />
            <textarea
              value={editDesc}
              onChange={(e) => setEditDesc(e.target.value)}
              rows={3}
              className="w-full bg-[var(--background)] border border-[var(--sidebar-border)] rounded-lg px-3 py-2 text-[var(--foreground)]"
            />
            <div className="flex gap-2">
              <Button onClick={handleSaveEdit}>Save</Button>
              <Button variant="secondary" onClick={() => setIsEditing(false)}>
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <>
            <div className="flex items-start justify-between mb-4">
              <h1 className="text-xl font-bold">{task.title}</h1>
              <div className="flex gap-2">
                <Button variant="ghost" onClick={() => setIsEditing(true)}>
                  Edit
                </Button>
                <Button variant="danger" onClick={handleArchive}>
                  Archive
                </Button>
              </div>
            </div>
            {task.description && (
              <p className="text-[var(--text-muted)] mb-4">
                {task.description}
              </p>
            )}
          </>
        )}

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
          <div>
            <label className="text-xs text-[var(--text-muted)] block mb-1">
              Status
            </label>
            <select
              value={task.status}
              onChange={(e) => handleStatusChange(e.target.value)}
              className="w-full px-2 py-1 bg-[var(--background)] border border-[var(--sidebar-border)] rounded text-sm text-[var(--foreground)]"
            >
              {STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s.replace("_", " ")}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs text-[var(--text-muted)] block mb-1">
              Priority
            </label>
            <select
              value={task.priority}
              onChange={(e) => handlePriorityChange(e.target.value)}
              className="w-full px-2 py-1 bg-[var(--background)] border border-[var(--sidebar-border)] rounded text-sm text-[var(--foreground)]"
            >
              {PRIORITIES.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs text-[var(--text-muted)] block mb-1">
              Due Date
            </label>
            <span className="text-sm">{task.due_date || "—"}</span>
          </div>
          <div>
            <label className="text-xs text-[var(--text-muted)] block mb-1">
              Estimated
            </label>
            <span className="text-sm">
              {task.estimated_minutes ? `${task.estimated_minutes} min` : "—"}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4 pt-4 border-t border-[var(--sidebar-border)]">
          <div>
            <label className="text-xs text-[var(--text-muted)] block mb-1">
              Project
            </label>
            {task.project_id ? (
              <Link
                href={`/projects/${task.project_id}`}
                className="text-sm text-[var(--primary)] hover:underline"
              >
                {task.project_id.substring(0, 8)}...
              </Link>
            ) : (
              <span className="text-sm text-[var(--text-muted)]">—</span>
            )}
          </div>
          <div>
            <label className="text-xs text-[var(--text-muted)] block mb-1">
              Client
            </label>
            {task.client_id ? (
              <Link
                href={`/clients/${task.client_id}`}
                className="text-sm text-[var(--primary)] hover:underline"
              >
                {task.client_id.substring(0, 8)}...
              </Link>
            ) : (
              <span className="text-sm text-[var(--text-muted)]">—</span>
            )}
          </div>
          <div>
            <label className="text-xs text-[var(--text-muted)] block mb-1">
              Created
            </label>
            <span className="text-sm">
              {task.created_at
                ? new Date(task.created_at).toLocaleDateString()
                : "—"}
            </span>
          </div>
          <div>
            <label className="text-xs text-[var(--text-muted)] block mb-1">
              Updated
            </label>
            <span className="text-sm">
              {task.updated_at
                ? new Date(task.updated_at).toLocaleDateString()
                : "—"}
            </span>
          </div>
        </div>

        {task.labels && task.labels.length > 0 && (
          <div className="mt-4 pt-4 border-t border-[var(--sidebar-border)]">
            <label className="text-xs text-[var(--text-muted)] block mb-2">
              Labels
            </label>
            <div className="flex gap-2 flex-wrap">
              {(
                task.labels as unknown as {
                  id?: string;
                  name?: string;
                  color?: string;
                }[]
              ).map((l, i) => {
                const name = typeof l === "string" ? l : l.name || "";
                const key = typeof l === "string" ? l : l.id || String(i);
                const color =
                  typeof l === "object" && l.color ? l.color : undefined;
                return (
                  <span
                    key={key}
                    className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-[var(--primary)]/20 text-[var(--primary)]"
                    style={
                      color ? { backgroundColor: color + "20", color } : {}
                    }
                  >
                    {name}
                  </span>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Activity Timeline */}
      <div className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-6">
        <h2 className="text-lg font-semibold mb-4">Activity</h2>
        {events.length > 0 ? (
          <div className="space-y-4">
            {events.map((event: TaskEvent) => (
              <div key={event.id} className="flex gap-3 text-sm">
                <div className="w-2 h-2 rounded-full bg-[var(--primary)] mt-1.5 flex-shrink-0" />
                <div>
                  <span className="font-medium">
                    {EVENT_LABELS[event.event_type] || event.event_type}
                  </span>
                  {Boolean(event.data?.old_value && event.data?.new_value) && (
                    <span className="text-[var(--text-muted)]">
                      {" "}
                      — {String(event.data?.old_value).replace("_", " ")} →{" "}
                      {String(event.data?.new_value).replace("_", " ")}
                    </span>
                  )}
                  <div className="text-xs text-[var(--text-muted)] mt-0.5">
                    {new Date(event.created_at).toLocaleString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-[var(--text-muted)]">
            No activity recorded yet.
          </p>
        )}
      </div>
    </div>
  );
}
