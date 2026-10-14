// ─── Display helpers shared across pages ─────────────────────────────────────

export const TASK_STATUSES = [
  "BACKLOG",
  "TODO",
  "IN_PROGRESS",
  "BLOCKED",
  "REVIEW",
  "COMPLETED",
] as const;

export const TASK_PRIORITIES = ["LOW", "MEDIUM", "HIGH", "URGENT"] as const;

export const STATUS_LABELS: Record<string, string> = {
  BACKLOG: "Backlog",
  TODO: "To do",
  IN_PROGRESS: "In progress",
  BLOCKED: "Blocked",
  REVIEW: "In review",
  COMPLETED: "Done",
  PLANNING: "Planning",
  ACTIVE: "Active",
  ON_HOLD: "On hold",
  ARCHIVED: "Archived",
  LEAD: "Lead",
  DRAFT: "Draft",
  APPROVED: "Approved",
};

export const PRIORITY_LABELS: Record<string, string> = {
  LOW: "Low",
  MEDIUM: "Medium",
  HIGH: "High",
  URGENT: "Urgent",
};

export function humanize(value?: string | null): string {
  if (!value) return "";
  return (
    STATUS_LABELS[value] ||
    PRIORITY_LABELS[value] ||
    value.charAt(0) + value.slice(1).toLowerCase().replace(/_/g, " ")
  );
}

/** Local YYYY-MM-DD for a date offset from today (avoids UTC drift). */
export function isoDate(offsetDays = 0): string {
  const d = new Date();
  d.setDate(d.getDate() + offsetDays);
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${m}-${day}`;
}

function daysFromToday(dateStr: string): number {
  const [y, m, d] = dateStr.slice(0, 10).split("-").map(Number);
  const target = new Date(y, m - 1, d);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.round((target.getTime() - today.getTime()) / 86_400_000);
}

export type DueTone = "overdue" | "today" | "soon" | "later" | "none";

/** Friendly due-date text ("Tomorrow", "3d overdue") plus a tone for colouring. */
export function describeDue(
  dateStr?: string | null,
  done = false
): { text: string; tone: DueTone } {
  if (!dateStr) return { text: "No date", tone: "none" };
  const diff = daysFromToday(dateStr);
  if (done) return { text: formatDate(dateStr), tone: "later" };
  if (diff < -1) return { text: `${-diff}d overdue`, tone: "overdue" };
  if (diff === -1) return { text: "Yesterday", tone: "overdue" };
  if (diff === 0) return { text: "Today", tone: "today" };
  if (diff === 1) return { text: "Tomorrow", tone: "soon" };
  if (diff < 7) return { text: `In ${diff} days`, tone: "soon" };
  return { text: formatDate(dateStr), tone: "later" };
}

export function formatDate(dateStr?: string | null): string {
  if (!dateStr) return "—";
  const [y, m, d] = dateStr.slice(0, 10).split("-").map(Number);
  const date = new Date(y, m - 1, d);
  const sameYear = date.getFullYear() === new Date().getFullYear();
  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    ...(sameYear ? {} : { year: "numeric" }),
  });
}

/** The API returns naive UTC timestamps (no "Z"); parse them as UTC, not local time. */
export function parseServerDate(iso: string): Date {
  const hasZone = /([zZ]|[+-]\d\d:?\d\d)$/.test(iso);
  return new Date(iso.includes("T") && !hasZone ? `${iso}Z` : iso);
}

export function timeAgo(iso?: string | null): string {
  if (!iso) return "";
  const seconds = Math.max(
    0,
    Math.round((Date.now() - parseServerDate(iso).getTime()) / 1000)
  );
  if (seconds < 60) return "just now";
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.round(hours / 24);
  if (days < 30) return `${days}d ago`;
  return parseServerDate(iso).toLocaleDateString();
}

export function initials(name?: string | null): string {
  if (!name) return "?";
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]!.toUpperCase())
    .join("");
}

export function errorMessage(err: unknown, fallback: string): string {
  return err instanceof Error ? err.message : fallback;
}
