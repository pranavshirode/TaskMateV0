"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { apiClient, type Project, type Task } from "@/lib/api-client";
import {
  errorMessage,
  humanize,
  PRIORITY_LABELS,
  TASK_PRIORITIES,
  TASK_STATUSES,
} from "@/lib/format";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import ErrorState from "@/components/ui/ErrorState";
import EmptyState from "@/components/ui/EmptyState";
import Button from "@/components/ui/Button";
import Pagination from "@/components/ui/Pagination";
import PageHeader from "@/components/ui/PageHeader";
import Icon from "@/components/ui/Icon";
import { priorityDotClass, statusDotClass } from "@/components/ui/Badge";
import TaskRow, { CompleteToggle, DueLabel } from "@/components/tasks/TaskRow";
import { useTaskActions } from "@/components/tasks/useTaskActions";
import { useWorkspaceUI } from "@/components/layout/WorkspaceUI";

type ViewMode = "list" | "board";
const VIEW_KEY = "taskmate_tasks_view";
const PAGE_SIZE = 25;
const BOARD_LIMIT = 100; // API maximum page size

export default function TasksPage() {
  const { openQuickAdd, dataVersion } = useWorkspaceUI();
  const [view, setView] = useState<ViewMode>("list");
  const [tasks, setTasks] = useState<Task[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");
  const [projectFilter, setProjectFilter] = useState("");
  const [sort, setSort] = useState("created_at:desc");

  // Restore view preference and read filters from the URL (e.g. /tasks?status=BLOCKED).
  useEffect(() => {
    try {
      const saved = localStorage.getItem(VIEW_KEY);
      if (saved === "board" || saved === "list") setView(saved);
    } catch {
      /* storage unavailable */
    }
    const params = new URLSearchParams(window.location.search);
    if (params.get("status")) setStatusFilter(params.get("status")!);
    if (params.get("priority")) setPriorityFilter(params.get("priority")!);
    if (params.get("project")) setProjectFilter(params.get("project")!);
    apiClient
      .listProjects({ page_size: "100" })
      .then((res) => setProjects(res.items || []))
      .catch(() => {});
  }, []);

  const changeView = (mode: ViewMode) => {
    setView(mode);
    try {
      localStorage.setItem(VIEW_KEY, mode);
    } catch {
      /* storage unavailable */
    }
  };

  // Debounce the search box so results update as you type.
  useEffect(() => {
    const handle = setTimeout(() => {
      setSearch(searchInput.trim());
      setPage(1);
    }, 250);
    return () => clearTimeout(handle);
  }, [searchInput]);

  const fetchTasks = useCallback(
    async (silent = false) => {
      try {
        if (!silent) setIsLoading(true);
        setError(null);
        const [sortBy, sortOrder] = sort.split(":");
        const isBoard = view === "board";
        const params: Record<string, string> = {
          page: isBoard ? "1" : String(page),
          page_size: String(isBoard ? BOARD_LIMIT : PAGE_SIZE),
          sort_by: sortBy,
          sort_order: sortOrder,
        };
        if (search) params.search = search;
        // The board shows every status as a column, so the status filter only applies to the list.
        if (statusFilter && !isBoard) params.status = statusFilter;
        if (priorityFilter) params.priority = priorityFilter;
        if (projectFilter) params.project_id = projectFilter;
        const res = await apiClient.listTasks(params);
        setTasks(res.items);
        setTotal(res.total);
      } catch (err: unknown) {
        setError(errorMessage(err, "Failed to load tasks"));
      } finally {
        setIsLoading(false);
      }
    },
    [page, search, statusFilter, priorityFilter, projectFilter, sort, view]
  );

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  useEffect(() => {
    if (dataVersion > 0) fetchTasks(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dataVersion]);

  const replaceTask = useCallback((task: Task) => {
    setTasks((prev) => prev.map((t) => (t.id === task.id ? task : t)));
  }, []);
  const { toggleComplete, setStatus } = useTaskActions(replaceTask);

  const projectNames = useMemo(() => {
    const map: Record<string, string> = {};
    projects.forEach((p) => (map[p.id] = p.name));
    return map;
  }, [projects]);

  const hasFilters = !!(
    search ||
    statusFilter ||
    priorityFilter ||
    projectFilter
  );
  const clearFilters = () => {
    setSearchInput("");
    setSearch("");
    setStatusFilter("");
    setPriorityFilter("");
    setProjectFilter("");
    setPage(1);
  };

  const chip = (value: string, label: string, dot?: string) => (
    <button
      key={value || "all"}
      onClick={() => {
        setStatusFilter(value);
        setPage(1);
      }}
      className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
        statusFilter === value
          ? "border-[var(--primary)] bg-[var(--primary-soft)] text-[var(--primary)]"
          : "border-[var(--sidebar-border)] bg-[var(--sidebar-bg)] text-[var(--text-muted)] hover:text-[var(--foreground)]"
      }`}
    >
      {dot && <span className={`h-1.5 w-1.5 rounded-full ${dot}`} />}
      {label}
    </button>
  );

  return (
    <div
      className={`mx-auto pb-12 ${view === "board" ? "max-w-[1400px]" : "max-w-5xl"}`}
    >
      <PageHeader
        title="Tasks"
        description={
          isLoading
            ? " "
            : `${total} task${total === 1 ? "" : "s"}${hasFilters ? " match your filters" : ""}`
        }
        actions={
          <>
            <div
              className="flex rounded-lg border border-[var(--sidebar-border)] bg-[var(--sidebar-bg)] p-0.5"
              role="group"
              aria-label="View"
            >
              {(["list", "board"] as ViewMode[]).map((mode) => (
                <button
                  key={mode}
                  onClick={() => changeView(mode)}
                  aria-pressed={view === mode}
                  className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm transition-colors ${
                    view === mode
                      ? "bg-[var(--surface-hover)] font-medium text-[var(--foreground)]"
                      : "text-[var(--text-muted)] hover:text-[var(--foreground)]"
                  }`}
                >
                  <Icon name={mode} size={15} />
                  {mode === "list" ? "List" : "Board"}
                </button>
              ))}
            </div>
            <Button
              onClick={() =>
                openQuickAdd({ projectId: projectFilter || undefined })
              }
            >
              <Icon name="plus" size={16} /> New task
            </Button>
          </>
        }
      />

      {/* Filters */}
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <div className="relative min-w-[200px] flex-1">
          <Icon
            name="search"
            size={16}
            className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]"
          />
          <input
            type="search"
            placeholder="Search tasks..."
            aria-label="Search tasks"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="field !bg-[var(--sidebar-bg)] pl-9"
          />
        </div>
        <select
          value={projectFilter}
          onChange={(e) => {
            setProjectFilter(e.target.value);
            setPage(1);
          }}
          aria-label="Filter by project"
          className="field !w-auto !bg-[var(--sidebar-bg)]"
        >
          <option value="">All projects</option>
          {projects.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
        <select
          value={priorityFilter}
          onChange={(e) => {
            setPriorityFilter(e.target.value);
            setPage(1);
          }}
          aria-label="Filter by priority"
          className="field !w-auto !bg-[var(--sidebar-bg)]"
        >
          <option value="">Any priority</option>
          {TASK_PRIORITIES.map((p) => (
            <option key={p} value={p}>
              {PRIORITY_LABELS[p]}
            </option>
          ))}
        </select>
        <select
          value={sort}
          onChange={(e) => {
            setSort(e.target.value);
            setPage(1);
          }}
          aria-label="Sort tasks"
          className="field !w-auto !bg-[var(--sidebar-bg)]"
        >
          <option value="created_at:desc">Newest first</option>
          <option value="created_at:asc">Oldest first</option>
          <option value="due_date:asc">Due soonest</option>
          <option value="due_date:desc">Due latest</option>
          <option value="priority:desc">Priority: high to low</option>
          <option value="priority:asc">Priority: low to high</option>
          <option value="updated_at:desc">Recently updated</option>
        </select>
      </div>

      {view === "list" && (
        <div className="mb-4 flex gap-2 overflow-x-auto pb-1">
          {chip("", "All")}
          {TASK_STATUSES.map((s) => chip(s, humanize(s), statusDotClass(s)))}
        </div>
      )}

      {hasFilters && (
        <button
          onClick={clearFilters}
          className="mb-4 inline-flex items-center gap-1 text-xs text-[var(--text-muted)] hover:text-[var(--foreground)]"
        >
          <Icon name="x" size={12} /> Clear filters
        </button>
      )}

      {isLoading ? (
        <div className="flex justify-center py-16">
          <LoadingSpinner />
        </div>
      ) : error ? (
        <ErrorState message={error} onRetry={() => fetchTasks()} />
      ) : tasks.length === 0 && view === "list" ? (
        hasFilters ? (
          <EmptyState
            title="No tasks match"
            description="Try a different search or clear the filters."
            actionLabel="Clear filters"
            onAction={clearFilters}
          />
        ) : (
          <EmptyState
            title="No tasks yet"
            description="Create your first task, or ask the AI assistant to create some for you."
            actionLabel="Create task"
            onAction={() => openQuickAdd()}
          />
        )
      ) : view === "list" ? (
        <>
          <div className="card divide-y divide-[var(--sidebar-border)] overflow-hidden">
            {tasks.map((task) => (
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
          <Pagination
            page={page}
            pageSize={PAGE_SIZE}
            total={total}
            onPageChange={setPage}
          />
        </>
      ) : (
        <>
          {total > BOARD_LIMIT && (
            <p className="mb-3 text-xs text-[var(--text-muted)]">
              Showing the first {BOARD_LIMIT} of {total} tasks. Use filters to
              narrow the board.
            </p>
          )}
          <TaskBoard
            tasks={tasks}
            projectNames={projectNames}
            onMove={setStatus}
            onToggle={toggleComplete}
            onAdd={(status) =>
              openQuickAdd({ status, projectId: projectFilter || undefined })
            }
          />
        </>
      )}
    </div>
  );
}

function TaskBoard({
  tasks,
  projectNames,
  onMove,
  onToggle,
  onAdd,
}: {
  tasks: Task[];
  projectNames: Record<string, string>;
  onMove: (task: Task, status: string) => void;
  onToggle: (task: Task) => void;
  onAdd: (status: string) => void;
}) {
  const [dragId, setDragId] = useState<string | null>(null);
  const [overColumn, setOverColumn] = useState<string | null>(null);

  return (
    <div className="-mx-4 overflow-x-auto px-4 pb-4 md:-mx-8 md:px-8">
      <div className="flex min-w-max gap-3">
        {TASK_STATUSES.map((status) => {
          const columnTasks = tasks.filter((t) => t.status === status);
          return (
            <section
              key={status}
              aria-label={humanize(status)}
              onDragOver={(e) => {
                e.preventDefault();
                setOverColumn(status);
              }}
              onDragLeave={() =>
                setOverColumn((c) => (c === status ? null : c))
              }
              onDrop={(e) => {
                e.preventDefault();
                const task = tasks.find((t) => t.id === dragId);
                if (task) onMove(task, status);
                setDragId(null);
                setOverColumn(null);
              }}
              className={`flex w-72 flex-col rounded-xl border p-2 transition-colors ${
                overColumn === status
                  ? "border-[color-mix(in_srgb,var(--primary)_50%,transparent)] bg-[var(--primary-soft)]"
                  : "border-transparent bg-[color-mix(in_srgb,var(--surface-hover)_60%,transparent)]"
              }`}
            >
              <header className="flex items-center gap-2 px-2 py-1.5">
                <span
                  className={`h-2 w-2 rounded-full ${statusDotClass(status)}`}
                />
                <h3 className="text-sm font-medium">{humanize(status)}</h3>
                <span className="text-xs text-[var(--text-muted)]">
                  {columnTasks.length}
                </span>
                <button
                  onClick={() => onAdd(status)}
                  aria-label={`Add task to ${humanize(status)}`}
                  className="ml-auto rounded-md p-1 text-[var(--text-muted)] hover:bg-[var(--sidebar-bg)] hover:text-[var(--foreground)]"
                >
                  <Icon name="plus" size={14} />
                </button>
              </header>
              <div className="flex min-h-[4rem] flex-1 flex-col gap-2 p-1">
                {columnTasks.map((task) => (
                  <Link
                    key={task.id}
                    href={`/tasks/${task.id}`}
                    draggable
                    onDragStart={(e) => {
                      setDragId(task.id);
                      e.dataTransfer.effectAllowed = "move";
                    }}
                    onDragEnd={() => {
                      setDragId(null);
                      setOverColumn(null);
                    }}
                    className={`card block cursor-grab p-3 transition-shadow hover:border-[color-mix(in_srgb,var(--primary)_40%,transparent)] active:cursor-grabbing ${
                      dragId === task.id ? "opacity-50" : ""
                    }`}
                  >
                    <div className="flex items-start gap-2.5">
                      <span className="mt-0.5">
                        <CompleteToggle task={task} onToggle={onToggle} />
                      </span>
                      <span
                        className={`flex-1 text-sm ${task.status === "COMPLETED" ? "text-[var(--text-muted)] line-through" : "font-medium"}`}
                      >
                        {task.title}
                      </span>
                    </div>
                    <div className="mt-2.5 flex flex-wrap items-center gap-x-3 gap-y-1 pl-[1.75rem]">
                      <span className="inline-flex items-center gap-1 text-xs text-[var(--text-muted)]">
                        <span
                          className={`h-1.5 w-1.5 rounded-full ${priorityDotClass(task.priority)}`}
                        />
                        {PRIORITY_LABELS[task.priority] || task.priority}
                      </span>
                      <DueLabel task={task} />
                      {task.project_id && projectNames[task.project_id] && (
                        <span className="truncate text-xs text-[var(--text-muted)]">
                          {projectNames[task.project_id]}
                        </span>
                      )}
                    </div>
                  </Link>
                ))}
                {columnTasks.length === 0 && (
                  <p className="rounded-lg border border-dashed border-[var(--sidebar-border)] px-3 py-4 text-center text-xs text-[var(--text-muted)]">
                    Drop tasks here
                  </p>
                )}
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
}
