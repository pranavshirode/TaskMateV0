"use client";

import Link from "next/link";
import type { Task } from "@/lib/api-client";
import {
  describeDue,
  humanize,
  PRIORITY_LABELS,
  TASK_STATUSES,
} from "@/lib/format";
import Icon from "@/components/ui/Icon";
import { priorityDotClass } from "@/components/ui/Badge";

const DUE_TONES = {
  overdue: "text-[var(--danger)] font-medium",
  today: "text-[var(--warning)] font-medium",
  soon: "text-[var(--foreground)]",
  later: "text-[var(--text-muted)]",
  none: "text-[color-mix(in_srgb,var(--text-muted)_60%,transparent)]",
};

export function CompleteToggle({
  task,
  onToggle,
}: {
  task: Task;
  onToggle: (task: Task) => void;
}) {
  const done = task.status === "COMPLETED";
  return (
    <button
      onClick={(e) => {
        e.preventDefault();
        e.stopPropagation();
        onToggle(task);
      }}
      role="checkbox"
      aria-checked={done}
      aria-label={
        done
          ? `Mark "${task.title}" as not done`
          : `Mark "${task.title}" as done`
      }
      title={done ? "Mark as not done" : "Mark as done"}
      className={`group/check flex h-[18px] w-[18px] shrink-0 items-center justify-center rounded-full border-[1.5px] transition-colors ${
        done
          ? "border-[var(--success)] bg-[var(--success)] text-white"
          : "border-[color-mix(in_srgb,var(--text-muted)_50%,transparent)] text-transparent hover:border-[var(--success)] hover:text-[var(--success)]"
      }`}
    >
      <Icon name="check" size={11} strokeWidth={3} />
    </button>
  );
}

export function DueLabel({ task }: { task: Task }) {
  const due = describeDue(task.due_date, task.status === "COMPLETED");
  if (due.tone === "none") return null;
  return (
    <span
      className={`inline-flex items-center gap-1 whitespace-nowrap text-xs ${DUE_TONES[due.tone]}`}
    >
      <Icon name="calendar" size={12} />
      {due.text}
    </span>
  );
}

export function StatusSelect({
  task,
  onChange,
  className = "",
}: {
  task: Task;
  onChange: (task: Task, status: string) => void;
  className?: string;
}) {
  return (
    <select
      value={task.status}
      onClick={(e) => e.stopPropagation()}
      onChange={(e) => onChange(task, e.target.value)}
      aria-label={`Status of "${task.title}"`}
      className={`cursor-pointer rounded-md border border-transparent bg-transparent py-1 pl-2 pr-6 text-xs text-[var(--text-muted)] hover:border-[var(--sidebar-border)] hover:bg-[var(--background)] focus:border-[var(--primary)] focus:outline-none ${className}`}
    >
      {TASK_STATUSES.map((s) => (
        <option key={s} value={s}>
          {humanize(s)}
        </option>
      ))}
    </select>
  );
}

export default function TaskRow({
  task,
  projectName,
  onToggle,
  onStatusChange,
  showStatus = true,
}: {
  task: Task;
  projectName?: string;
  onToggle: (task: Task) => void;
  onStatusChange?: (task: Task, status: string) => void;
  showStatus?: boolean;
}) {
  const done = task.status === "COMPLETED";
  return (
    <div className="group flex items-center gap-3 px-4 py-2.5 transition-colors hover:bg-[var(--surface-hover)]">
      <CompleteToggle task={task} onToggle={onToggle} />
      <Link
        href={`/tasks/${task.id}`}
        className="flex min-w-0 flex-1 flex-col gap-0.5 sm:flex-row sm:items-center sm:gap-3"
      >
        <span
          className={`truncate text-sm ${done ? "text-[var(--text-muted)] line-through" : "font-medium"}`}
        >
          {task.title}
        </span>
        <span className="flex items-center gap-3 sm:ml-auto">
          {projectName && (
            <span className="inline-flex max-w-[10rem] items-center gap-1 truncate text-xs text-[var(--text-muted)]">
              <Icon name="folder" size={12} />
              <span className="truncate">{projectName}</span>
            </span>
          )}
          <DueLabel task={task} />
        </span>
      </Link>
      <span
        title={`${PRIORITY_LABELS[task.priority] || task.priority} priority`}
        className={`h-2 w-2 shrink-0 rounded-full ${priorityDotClass(task.priority)}`}
      />
      {showStatus && onStatusChange && (
        <StatusSelect
          task={task}
          onChange={onStatusChange}
          className="hidden w-[7.5rem] sm:block"
        />
      )}
    </div>
  );
}
