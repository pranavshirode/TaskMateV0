"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { apiClient, type Project, type Task } from "@/lib/api-client";
import Icon, { type IconName } from "@/components/ui/Icon";
import { statusDotClass } from "@/components/ui/Badge";
import { ALL_NAV_ITEMS } from "./nav";
import type { QuickAddDefaults } from "./QuickAddTask";

interface PaletteItem {
  id: string;
  group: string;
  label: string;
  hint?: string;
  icon: IconName;
  dot?: string;
  run: () => void;
}

export default function CommandPalette({
  onClose,
  onQuickAdd,
}: {
  onClose: () => void;
  onQuickAdd: (defaults: QuickAddDefaults) => void;
}) {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);

  useEffect(() => {
    inputRef.current?.focus();
    apiClient
      .listProjects({ page_size: "100" })
      .then((res) => setProjects(res.items || []))
      .catch(() => {});
  }, []);

  // Debounced task search
  useEffect(() => {
    const q = query.trim();
    if (q.length < 2) {
      setTasks([]);
      return;
    }
    const handle = setTimeout(() => {
      apiClient
        .listTasks({ search: q, page_size: "6" })
        .then((res) => setTasks(res.items || []))
        .catch(() => setTasks([]));
    }, 200);
    return () => clearTimeout(handle);
  }, [query]);

  const go = (href: string) => {
    onClose();
    router.push(href);
  };

  const items = useMemo<PaletteItem[]>(() => {
    const q = query.trim();
    const ql = q.toLowerCase();
    const matches = (text: string) => !ql || text.toLowerCase().includes(ql);

    const actions: PaletteItem[] = [
      {
        id: "new-task",
        group: "Actions",
        label: q ? `Create task "${q}"` : "Create a task",
        hint: "C",
        icon: "plus",
        run: () => onQuickAdd({ title: q }),
      },
      {
        id: "ask-ai",
        group: "Actions",
        label: q ? `Ask AI: "${q}"` : "Ask the AI assistant",
        icon: "sparkles",
        run: () => go(q ? `/ai?q=${encodeURIComponent(q)}` : "/ai"),
      },
      {
        id: "new-project",
        group: "Actions",
        label: "Create a project",
        icon: "folder",
        run: () => go("/projects/new"),
      },
      {
        id: "new-client",
        group: "Actions",
        label: "Add a client",
        icon: "users",
        run: () => go("/clients/new"),
      },
      {
        id: "analyze",
        group: "Actions",
        label: "Analyze a client brief",
        icon: "requirements",
        run: () => go("/requirements"),
      },
    ];

    const pages: PaletteItem[] = ALL_NAV_ITEMS.filter(
      (n) => matches(n.name) || matches(n.description)
    ).map((n) => ({
      id: `nav-${n.href}`,
      group: "Go to",
      label: n.name,
      hint: n.description,
      icon: n.icon,
      run: () => go(n.href),
    }));

    const projectItems: PaletteItem[] = q
      ? projects
          .filter((p) => matches(p.name))
          .slice(0, 5)
          .map((p) => ({
            id: `project-${p.id}`,
            group: "Projects",
            label: p.name,
            icon: "folder" as IconName,
            run: () => go(`/projects/${p.id}`),
          }))
      : [];

    const taskItems: PaletteItem[] = tasks.map((t) => ({
      id: `task-${t.id}`,
      group: "Tasks",
      label: t.title,
      icon: "tasks" as IconName,
      dot: statusDotClass(t.status),
      run: () => go(`/tasks/${t.id}`),
    }));

    // With a query, results first; without one, actions then navigation.
    return q
      ? [...taskItems, ...projectItems, ...pages, ...actions.slice(0, 2)]
      : [...actions, ...pages];
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, tasks, projects]);

  useEffect(() => {
    setActive(0);
  }, [query, tasks.length]);

  useEffect(() => {
    listRef.current
      ?.querySelector(`[data-index="${active}"]`)
      ?.scrollIntoView?.({ block: "nearest" });
  }, [active]);

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive((i) => Math.min(i + 1, items.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      items[active]?.run();
    } else if (e.key === "Escape") {
      onClose();
    }
  };

  let lastGroup = "";

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center bg-black/40 p-4 pt-[12vh] backdrop-blur-sm"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        role="dialog"
        aria-label="Command palette"
        className="animate-pop w-full max-w-xl overflow-hidden rounded-xl border border-[var(--sidebar-border)] bg-[var(--sidebar-bg)]"
        style={{ boxShadow: "var(--shadow-lg)" }}
      >
        <div className="flex items-center gap-3 border-b border-[var(--sidebar-border)] px-4">
          <Icon name="search" className="text-[var(--text-muted)]" />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Search tasks, jump to a page, or type a command..."
            aria-label="Command"
            className="h-12 flex-1 bg-transparent text-sm placeholder:text-[var(--text-muted)] focus:outline-none"
          />
          <span className="kbd">Esc</span>
        </div>
        <div ref={listRef} className="max-h-[50vh] overflow-y-auto p-2">
          {items.length === 0 && (
            <p className="px-3 py-6 text-center text-sm text-[var(--text-muted)]">
              No matches
            </p>
          )}
          {items.map((item, index) => {
            const header = item.group !== lastGroup ? item.group : null;
            lastGroup = item.group;
            return (
              <div key={item.id}>
                {header && (
                  <p className="px-3 pb-1 pt-3 text-[11px] font-semibold uppercase tracking-wide text-[var(--text-muted)] first:pt-1">
                    {header}
                  </p>
                )}
                <button
                  data-index={index}
                  onMouseMove={() => setActive(index)}
                  onClick={item.run}
                  className={`flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-sm ${
                    index === active
                      ? "bg-[var(--primary-soft)] text-[var(--foreground)]"
                      : "text-[var(--foreground)]"
                  }`}
                >
                  {item.dot ? (
                    <span
                      className={`mx-[5px] h-2 w-2 rounded-full ${item.dot}`}
                    />
                  ) : (
                    <Icon
                      name={item.icon}
                      size={16}
                      className={
                        index === active
                          ? "text-[var(--primary)]"
                          : "text-[var(--text-muted)]"
                      }
                    />
                  )}
                  <span className="flex-1 truncate">{item.label}</span>
                  {item.hint && item.group !== "Go to" && (
                    <span className="kbd">{item.hint}</span>
                  )}
                  {item.hint && item.group === "Go to" && (
                    <span className="hidden truncate text-xs text-[var(--text-muted)] sm:block">
                      {item.hint}
                    </span>
                  )}
                </button>
              </div>
            );
          })}
        </div>
        <div className="flex items-center gap-4 border-t border-[var(--sidebar-border)] px-4 py-2 text-[11px] text-[var(--text-muted)]">
          <span>
            <span className="kbd">↑</span> <span className="kbd">↓</span> to
            move
          </span>
          <span>
            <span className="kbd">Enter</span> to select
          </span>
          <span className="ml-auto hidden sm:inline">
            Press <span className="kbd">C</span> anywhere for a new task
          </span>
        </div>
      </div>
    </div>
  );
}
