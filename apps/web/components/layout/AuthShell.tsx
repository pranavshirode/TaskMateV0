import React from "react";
import Icon, { type IconName } from "@/components/ui/Icon";

const HIGHLIGHTS: { icon: IconName; title: string; text: string }[] = [
  {
    icon: "requirements",
    title: "Brief to tasks",
    text: "Paste a client brief and get requirements, questions and a task plan.",
  },
  {
    icon: "sparkles",
    title: "An assistant that acts",
    text: "Ask in plain English to create, update or find work.",
  },
  {
    icon: "today",
    title: "Know what's next",
    text: "One Today view of overdue, due and high-priority work.",
  },
];

export default function AuthShell({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}) {
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="hidden flex-col justify-between bg-[var(--primary)] p-12 text-white lg:flex">
        <div className="flex items-center gap-2.5">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/15">
            <Icon name="check" size={18} strokeWidth={2.5} />
          </span>
          <span className="text-lg font-semibold">TaskMate</span>
        </div>
        <div>
          <h2 className="max-w-md text-3xl font-semibold leading-tight">
            The workspace that runs the admin side of freelancing for you.
          </h2>
          <ul className="mt-10 space-y-6">
            {HIGHLIGHTS.map((h) => (
              <li key={h.title} className="flex gap-4">
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white/15">
                  <Icon name={h.icon} size={18} />
                </span>
                <span>
                  <span className="block font-medium">{h.title}</span>
                  <span className="block text-sm text-white/75">{h.text}</span>
                </span>
              </li>
            ))}
          </ul>
        </div>
        <p className="text-xs text-white/60">TaskMate AI v1.0.0</p>
      </div>

      <div className="flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-sm">
          <div className="mb-8">
            <span className="mb-6 flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--primary)] text-white lg:hidden">
              <Icon name="check" size={18} strokeWidth={2.5} />
            </span>
            <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
            <p className="mt-1 text-sm text-[var(--text-muted)]">{subtitle}</p>
          </div>
          {children}
        </div>
      </div>
    </div>
  );
}
