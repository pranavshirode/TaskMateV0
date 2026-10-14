import React from "react";
import { humanize } from "@/lib/format";

type BadgeType = "status" | "priority";

interface BadgeProps {
  type: BadgeType;
  value?: string;
}

// [dot colour, pill classes]
const STATUS_STYLES: Record<string, [string, string]> = {
  BACKLOG: [
    "bg-slate-400",
    "bg-slate-500/10 text-slate-600 dark:text-slate-300",
  ],
  TODO: ["bg-sky-500", "bg-sky-500/10 text-sky-700 dark:text-sky-300"],
  IN_PROGRESS: [
    "bg-amber-500",
    "bg-amber-500/10 text-amber-700 dark:text-amber-300",
  ],
  BLOCKED: ["bg-red-500", "bg-red-500/10 text-red-700 dark:text-red-300"],
  REVIEW: [
    "bg-violet-500",
    "bg-violet-500/10 text-violet-700 dark:text-violet-300",
  ],
  COMPLETED: [
    "bg-emerald-500",
    "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300",
  ],
  ACTIVE: [
    "bg-emerald-500",
    "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300",
  ],
  APPROVED: [
    "bg-emerald-500",
    "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300",
  ],
  PLANNING: ["bg-sky-500", "bg-sky-500/10 text-sky-700 dark:text-sky-300"],
  LEAD: ["bg-sky-500", "bg-sky-500/10 text-sky-700 dark:text-sky-300"],
  ON_HOLD: [
    "bg-amber-500",
    "bg-amber-500/10 text-amber-700 dark:text-amber-300",
  ],
};

const PRIORITY_STYLES: Record<string, [string, string]> = {
  LOW: ["bg-slate-400", "bg-slate-500/10 text-slate-600 dark:text-slate-300"],
  MEDIUM: ["bg-sky-500", "bg-sky-500/10 text-sky-700 dark:text-sky-300"],
  HIGH: [
    "bg-orange-500",
    "bg-orange-500/10 text-orange-700 dark:text-orange-300",
  ],
  URGENT: ["bg-red-500", "bg-red-500/10 text-red-700 dark:text-red-300"],
};

const FALLBACK: [string, string] = [
  "bg-slate-400",
  "bg-slate-500/10 text-slate-600 dark:text-slate-300",
];

export function statusDotClass(status?: string) {
  return (STATUS_STYLES[status || ""] || FALLBACK)[0];
}

export function priorityDotClass(priority?: string) {
  return (PRIORITY_STYLES[priority || ""] || FALLBACK)[0];
}

export default function Badge({ type, value }: BadgeProps) {
  const safeVal = value || "ACTIVE";
  const table = type === "status" ? STATUS_STYLES : PRIORITY_STYLES;
  const [dot, pill] = table[safeVal] || FALLBACK;

  return (
    <span
      className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium ${pill}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${dot}`} />
      {humanize(safeVal)}
    </span>
  );
}
