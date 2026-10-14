"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiClient, type Client, type Project } from "@/lib/api-client";
import { describeDue, errorMessage, formatDate, humanize } from "@/lib/format";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import ErrorState from "@/components/ui/ErrorState";
import EmptyState from "@/components/ui/EmptyState";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import Pagination from "@/components/ui/Pagination";
import PageHeader from "@/components/ui/PageHeader";
import Icon from "@/components/ui/Icon";

const PROJECT_STATUSES = [
  "PLANNING",
  "ACTIVE",
  "ON_HOLD",
  "COMPLETED",
  "ARCHIVED",
];
const PAGE_SIZE = 20;

export default function ProjectsPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  useEffect(() => {
    apiClient
      .listClients({ page_size: "100" })
      .then((res) => setClients(res.items || []))
      .catch(() => {});
  }, []);

  const fetchProjects = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const params: Record<string, string> = {
        page: String(page),
        page_size: String(PAGE_SIZE),
      };
      if (search) params.search = search;
      if (statusFilter) params.status = statusFilter;
      const res = await apiClient.listProjects(params);
      setProjects(res.items);
      setTotal(res.total);
    } catch (err: unknown) {
      setError(errorMessage(err, "Failed to load projects"));
    } finally {
      setIsLoading(false);
    }
  }, [page, search, statusFilter]);

  useEffect(() => {
    const handle = setTimeout(fetchProjects, search ? 250 : 0);
    return () => clearTimeout(handle);
  }, [fetchProjects, search]);

  const clientNames = useMemo(() => {
    const map: Record<string, string> = {};
    clients.forEach((c) => (map[c.id] = c.name));
    return map;
  }, [clients]);

  return (
    <div className="mx-auto max-w-5xl pb-12">
      <PageHeader
        title="Projects"
        description="Everything you're building, with progress at a glance."
        actions={
          <Button onClick={() => router.push("/projects/new")}>
            <Icon name="plus" size={16} /> New project
          </Button>
        }
      />

      <div className="mb-6 flex flex-wrap gap-2">
        <div className="relative min-w-[200px] flex-1">
          <Icon
            name="search"
            size={16}
            className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]"
          />
          <input
            type="search"
            placeholder="Search projects..."
            aria-label="Search projects"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="field !bg-[var(--sidebar-bg)] pl-9"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setPage(1);
          }}
          aria-label="Filter by status"
          className="field !w-auto !bg-[var(--sidebar-bg)]"
        >
          <option value="">All statuses</option>
          {PROJECT_STATUSES.map((s) => (
            <option key={s} value={s}>
              {humanize(s)}
            </option>
          ))}
        </select>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16">
          <LoadingSpinner />
        </div>
      ) : error ? (
        <ErrorState message={error} onRetry={fetchProjects} />
      ) : projects.length === 0 ? (
        <EmptyState
          title={
            search || statusFilter ? "No projects match" : "No projects yet"
          }
          description={
            search || statusFilter
              ? "Try a different search or status."
              : "A project groups tasks, requirements and repos for one piece of client work."
          }
          actionLabel="Create project"
          onAction={() => router.push("/projects/new")}
        />
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {projects.map((project) => {
              const ts = project.task_summary || {};
              const totalTasks = ts.total ?? 0;
              const completed = ts.completed ?? 0;
              const pct =
                totalTasks > 0 ? Math.round((completed / totalTasks) * 100) : 0;
              const deadline = project.deadline
                ? describeDue(project.deadline)
                : null;
              return (
                <Link
                  key={project.id}
                  href={`/projects/${project.id}`}
                  className="card group flex flex-col p-5 transition-colors hover:border-[color-mix(in_srgb,var(--primary)_40%,transparent)]"
                >
                  <div className="mb-1 flex items-start justify-between gap-3">
                    <h3 className="font-semibold group-hover:text-[var(--primary)]">
                      {project.name}
                    </h3>
                    <Badge type="status" value={project.status} />
                  </div>
                  {project.client_id && clientNames[project.client_id] && (
                    <p className="mb-2 flex items-center gap-1 text-xs text-[var(--text-muted)]">
                      <Icon name="users" size={12} />{" "}
                      {clientNames[project.client_id]}
                    </p>
                  )}
                  {project.description && (
                    <p className="mb-4 line-clamp-2 text-sm text-[var(--text-muted)]">
                      {project.description}
                    </p>
                  )}
                  <div className="mt-auto space-y-3 pt-2">
                    <div>
                      <div className="mb-1 flex justify-between text-xs text-[var(--text-muted)]">
                        <span>
                          {completed} of {totalTasks} tasks done
                        </span>
                        <span>{pct}%</span>
                      </div>
                      <div className="h-1.5 overflow-hidden rounded-full bg-[var(--surface-hover)]">
                        <div
                          className="h-full rounded-full bg-[var(--primary)]"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-[var(--text-muted)]">
                      {deadline && (
                        <span
                          className={`inline-flex items-center gap-1 ${deadline.tone === "overdue" ? "text-[var(--danger)]" : ""}`}
                        >
                          <Icon name="calendar" size={12} />
                          Deadline{" "}
                          {deadline.tone === "later"
                            ? formatDate(project.deadline)
                            : deadline.text.toLowerCase()}
                        </span>
                      )}
                      {(ts.overdue ?? 0) > 0 && (
                        <span className="inline-flex items-center gap-1 text-[var(--danger)]">
                          <Icon name="alert" size={12} /> {ts.overdue} overdue
                        </span>
                      )}
                      {(ts.blocked ?? 0) > 0 && (
                        <span>{ts.blocked} blocked</span>
                      )}
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
          <Pagination
            page={page}
            pageSize={PAGE_SIZE}
            total={total}
            onPageChange={setPage}
          />
        </>
      )}
    </div>
  );
}
