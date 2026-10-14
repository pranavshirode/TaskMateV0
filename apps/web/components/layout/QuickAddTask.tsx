"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { apiClient, type Project } from "@/lib/api-client";
import {
  errorMessage,
  isoDate,
  PRIORITY_LABELS,
  TASK_PRIORITIES,
} from "@/lib/format";
import Modal from "@/components/ui/Modal";
import Button from "@/components/ui/Button";
import Icon from "@/components/ui/Icon";
import { priorityDotClass } from "@/components/ui/Badge";
import { useFeedback } from "@/components/ui/Feedback";

export interface QuickAddDefaults {
  title?: string;
  projectId?: string;
  dueDate?: string;
  status?: string;
}

const DUE_CHIPS = [
  { label: "Today", offset: 0 },
  { label: "Tomorrow", offset: 1 },
  { label: "Next week", offset: 7 },
];

export default function QuickAddTask({
  defaults,
  onClose,
  onCreated,
}: {
  defaults: QuickAddDefaults;
  onClose: () => void;
  onCreated: () => void;
}) {
  const router = useRouter();
  const { toast } = useFeedback();
  const titleRef = useRef<HTMLInputElement>(null);
  const [title, setTitle] = useState(defaults.title || "");
  const [dueDate, setDueDate] = useState(defaults.dueDate || "");
  const [priority, setPriority] = useState("MEDIUM");
  const [projectId, setProjectId] = useState(defaults.projectId || "");
  const [projects, setProjects] = useState<Project[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    titleRef.current?.focus();
    apiClient
      .listProjects({ page_size: "100" })
      .then((res) => setProjects(res.items || []))
      .catch(() => {});
  }, []);

  const submit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!title.trim()) {
      setError("Give the task a title");
      return;
    }
    setIsSaving(true);
    setError("");
    try {
      const data: Record<string, string> = {
        title: title.trim(),
        priority,
        status: defaults.status || "TODO",
      };
      if (dueDate) data.due_date = dueDate;
      if (projectId) data.project_id = projectId;
      const task = await apiClient.createTask(data);
      onCreated();
      onClose();
      toast(`Task created: ${task.title}`, "success", {
        label: "Open",
        onClick: () => router.push(`/tasks/${task.id}`),
      });
    } catch (err) {
      setError(errorMessage(err, "Could not create the task"));
    } finally {
      setIsSaving(false);
    }
  };

  const chipClass = (active: boolean) =>
    `rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
      active
        ? "border-[var(--primary)] bg-[var(--primary-soft)] text-[var(--primary)]"
        : "border-[var(--sidebar-border)] text-[var(--text-muted)] hover:text-[var(--foreground)] hover:bg-[var(--surface-hover)]"
    }`;

  return (
    <Modal isOpen onClose={onClose} title="New task">
      <form
        onSubmit={submit}
        onKeyDown={(e) => {
          // After clicking a chip, focus sits on that button; Enter should still submit.
          const target = e.target as HTMLElement;
          if (
            e.key === "Enter" &&
            target.tagName === "BUTTON" &&
            target.getAttribute("type") === "button"
          ) {
            e.preventDefault();
            submit();
          }
        }}
        className="space-y-5"
      >
        <input
          ref={titleRef}
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="What needs to be done?"
          aria-label="Task title"
          className="w-full bg-transparent text-lg font-medium placeholder:text-[var(--text-muted)] focus:outline-none"
        />
        {error && <p className="text-sm text-[var(--danger)]">{error}</p>}

        <div className="space-y-2">
          <p className="text-xs font-medium uppercase tracking-wide text-[var(--text-muted)]">
            Due
          </p>
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              className={chipClass(!dueDate)}
              onClick={() => setDueDate("")}
            >
              No date
            </button>
            {DUE_CHIPS.map((chip) => {
              const value = isoDate(chip.offset);
              return (
                <button
                  key={chip.label}
                  type="button"
                  className={chipClass(dueDate === value)}
                  onClick={() => setDueDate(value)}
                >
                  {chip.label}
                </button>
              );
            })}
            <input
              type="date"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
              aria-label="Pick a due date"
              className="field !w-auto !py-1 text-xs"
            />
          </div>
        </div>

        <div className="space-y-2">
          <p className="text-xs font-medium uppercase tracking-wide text-[var(--text-muted)]">
            Priority
          </p>
          <div className="flex flex-wrap gap-2">
            {TASK_PRIORITIES.map((p) => (
              <button
                key={p}
                type="button"
                className={`${chipClass(priority === p)} inline-flex items-center gap-1.5`}
                onClick={() => setPriority(p)}
              >
                <span
                  className={`h-2 w-2 rounded-full ${priorityDotClass(p)}`}
                />
                {PRIORITY_LABELS[p]}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <label
            htmlFor="quick-add-project"
            className="text-xs font-medium uppercase tracking-wide text-[var(--text-muted)]"
          >
            Project
          </label>
          <select
            id="quick-add-project"
            value={projectId}
            onChange={(e) => setProjectId(e.target.value)}
            className="field"
          >
            <option value="">No project</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center justify-between gap-3 border-t border-[var(--sidebar-border)] pt-4">
          <button
            type="button"
            onClick={() => {
              onClose();
              router.push("/tasks/new");
            }}
            className="inline-flex items-center gap-1 text-sm text-[var(--text-muted)] hover:text-[var(--foreground)]"
          >
            More options <Icon name="arrowRight" size={14} />
          </button>
          <div className="flex gap-2">
            <Button type="button" variant="ghost" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSaving}>
              {isSaving ? "Adding..." : "Add task"}
            </Button>
          </div>
        </div>
      </form>
    </Modal>
  );
}
