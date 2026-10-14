"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  apiClient,
  type Project,
  type Repository,
  type Task,
} from "@/lib/api-client";
import { describeDue, errorMessage, formatDate } from "@/lib/format";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import ErrorState from "@/components/ui/ErrorState";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Modal from "@/components/ui/Modal";
import Icon, { type IconName } from "@/components/ui/Icon";
import TaskRow from "@/components/tasks/TaskRow";
import { useTaskActions } from "@/components/tasks/useTaskActions";
import { useFeedback } from "@/components/ui/Feedback";
import { useWorkspaceUI } from "@/components/layout/WorkspaceUI";

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { toast, confirm } = useFeedback();
  const { openQuickAdd, dataVersion } = useWorkspaceUI();
  const [project, setProject] = useState<Project | null>(null);
  const [clientName, setClientName] = useState<string | null>(null);
  const [repos, setRepos] = useState<Repository[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showRepoForm, setShowRepoForm] = useState(false);
  const [repoName, setRepoName] = useState("");
  const [repoUrl, setRepoUrl] = useState("");
  const [summary, setSummary] = useState<string | null>(null);
  const [isSummarizing, setIsSummarizing] = useState(false);

  const fetchData = useCallback(
    async (silent = false) => {
      try {
        if (!silent) setIsLoading(true);
        setError(null);
        const [proj, repoList, taskList] = await Promise.all([
          apiClient.getProject(id),
          apiClient.listProjectRepos(id),
          apiClient.listTasks({
            project_id: id,
            page_size: "50",
            sort_by: "updated_at",
            sort_order: "desc",
          }),
        ]);
        setProject(proj);
        setRepos(repoList || []);
        setTasks(taskList.items || []);
        if (proj.client_id) {
          apiClient
            .getClient(proj.client_id)
            .then((c) => setClientName(c.name))
            .catch(() => {});
        }
      } catch (err: unknown) {
        setError(errorMessage(err, "Failed to load project"));
      } finally {
        setIsLoading(false);
      }
    },
    [id]
  );

  useEffect(() => {
    fetchData(dataVersion > 0);
  }, [fetchData, dataVersion]);

  const replaceTask = useCallback((task: Task) => {
    setTasks((prev) => prev.map((t) => (t.id === task.id ? task : t)));
  }, []);
  const { toggleComplete, setStatus } = useTaskActions(replaceTask);

  const handleAddRepo = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoName.trim() || !repoUrl.trim()) return;
    try {
      await apiClient.createRepo(id, {
        name: repoName.trim(),
        url: repoUrl.trim(),
        provider: "GITHUB",
        default_branch: "main",
      });
      setRepoName("");
      setRepoUrl("");
      setShowRepoForm(false);
      toast("Repository linked");
      fetchData(true);
    } catch (err: unknown) {
      toast(errorMessage(err, "Failed to add repo"), "error");
    }
  };

  const handleArchive = async () => {
    const ok = await confirm({
      title: "Archive this project?",
      message: "It will be hidden from your project list. Its tasks are kept.",
      confirmLabel: "Archive",
      danger: true,
    });
    if (!ok) return;
    try {
      await apiClient.archiveProject(id);
      toast("Project archived");
      router.push("/projects");
    } catch (err: unknown) {
      toast(errorMessage(err, "Failed to archive project"), "error");
    }
  };

  const handleSummary = async () => {
    setIsSummarizing(true);
    try {
      const res = await apiClient.generateDailyProjectSummary(id);
      setSummary(res.summary_text || res.summary);
    } catch (e: unknown) {
      toast(errorMessage(e, "Failed to generate summary"), "error");
    } finally {
      setIsSummarizing(false);
    }
  };

  if (isLoading)
    return (
      <div className="flex justify-center py-16">
        <LoadingSpinner />
      </div>
    );
  if (error) return <ErrorState message={error} onRetry={() => fetchData()} />;
  if (!project) return null;

  const ts = project.task_summary || {};
  const totalTasks = ts.total ?? 0;
  const completed = ts.completed ?? 0;
  const pct = totalTasks > 0 ? Math.round((completed / totalTasks) * 100) : 0;
  const deadline = project.deadline ? describeDue(project.deadline) : null;
  const openTasks = tasks.filter((t) => t.status !== "COMPLETED");
  const doneTasks = tasks.filter((t) => t.status === "COMPLETED");

  const workflows: {
    href: string;
    icon: IconName;
    title: string;
    text: string;
  }[] = [
    {
      href: `/projects/${id}/requirements`,
      icon: "requirements",
      title: "Requirements",
      text: "Analyze briefs and generate tasks",
    },
    {
      href: `/projects/${id}/context`,
      icon: "brain",
      title: "Project memory",
      text: "Decisions the AI should remember",
    },
    {
      href: `/projects/${id}/requests`,
      icon: "message",
      title: "Client requests",
      text: "Assess change requests and scope",
    },
  ];

  return (
    <div className="mx-auto max-w-5xl pb-12">
      <Link
        href="/projects"
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-[var(--text-muted)] hover:text-[var(--foreground)]"
      >
        <Icon name="arrowLeft" size={14} /> Projects
      </Link>

      {/* Overview */}
      <section className="card mb-6 p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-2xl font-semibold tracking-tight">
                {project.name}
              </h1>
              <Badge type="status" value={project.status} />
            </div>
            <div className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-sm text-[var(--text-muted)]">
              {project.client_id && (
                <Link
                  href={`/clients/${project.client_id}`}
                  className="inline-flex items-center gap-1.5 hover:text-[var(--primary)]"
                >
                  <Icon name="users" size={14} /> {clientName || "Client"}
                </Link>
              )}
              {project.start_date && (
                <span className="inline-flex items-center gap-1.5">
                  <Icon name="calendar" size={14} /> Started{" "}
                  {formatDate(project.start_date)}
                </span>
              )}
              {deadline && (
                <span
                  className={`inline-flex items-center gap-1.5 ${deadline.tone === "overdue" ? "text-[var(--danger)]" : ""}`}
                >
                  <Icon name="clock" size={14} /> Deadline{" "}
                  {formatDate(project.deadline)}
                  {deadline.tone !== "later" &&
                    ` (${deadline.text.toLowerCase()})`}
                </span>
              )}
            </div>
            {project.description && (
              <p className="mt-3 max-w-2xl text-sm text-[color-mix(in_srgb,var(--foreground)_80%,transparent)]">
                {project.description}
              </p>
            )}
          </div>
          <div className="flex shrink-0 gap-2">
            <Button
              variant="secondary"
              onClick={handleSummary}
              disabled={isSummarizing}
            >
              <Icon name="chart" size={16} />{" "}
              {isSummarizing ? "Summarizing..." : "Daily summary"}
            </Button>
            <Button
              variant="ghost"
              onClick={handleArchive}
              title="Archive project"
              aria-label="Archive project"
            >
              <Icon name="archive" size={16} />
            </Button>
          </div>
        </div>

        {/* Progress */}
        <div className="mt-6 grid grid-cols-2 gap-3 border-t border-[var(--sidebar-border)] pt-5 sm:grid-cols-5">
          <div className="col-span-2 sm:col-span-1">
            <p className="text-2xl font-semibold">{pct}%</p>
            <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-[var(--surface-hover)]">
              <div
                className="h-full rounded-full bg-[var(--primary)]"
                style={{ width: `${pct}%` }}
              />
            </div>
            <p className="mt-1 text-xs text-[var(--text-muted)]">complete</p>
          </div>
          <Stat label="Total tasks" value={totalTasks} />
          <Stat label="Done" value={completed} tone="text-[var(--success)]" />
          <Stat
            label="In progress"
            value={ts.in_progress ?? 0}
            tone="text-[var(--warning)]"
          />
          <Stat
            label="Overdue"
            value={ts.overdue ?? 0}
            tone={(ts.overdue ?? 0) > 0 ? "text-[var(--danger)]" : ""}
          />
        </div>
      </section>

      {/* Workflows */}
      <div className="mb-6 grid grid-cols-1 gap-3 sm:grid-cols-3">
        {workflows.map((w) => (
          <Link
            key={w.href}
            href={w.href}
            className="card group flex items-center gap-3 p-4 transition-colors hover:border-[color-mix(in_srgb,var(--primary)_40%,transparent)]"
          >
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[var(--primary-soft)] text-[var(--primary)]">
              <Icon name={w.icon} size={18} />
            </span>
            <span className="min-w-0 flex-1">
              <span className="block text-sm font-medium">{w.title}</span>
              <span className="block truncate text-xs text-[var(--text-muted)]">
                {w.text}
              </span>
            </span>
            <Icon
              name="chevronRight"
              size={16}
              className="text-[var(--text-muted)] transition-transform group-hover:translate-x-0.5"
            />
          </Link>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Tasks */}
        <section className="card overflow-hidden lg:col-span-2">
          <div className="flex items-center justify-between border-b border-[var(--sidebar-border)] px-4 py-3">
            <h2 className="text-sm font-semibold">
              Tasks{" "}
              <span className="font-normal text-[var(--text-muted)]">
                {openTasks.length} open
              </span>
            </h2>
            <div className="flex gap-1">
              <Link href={`/tasks?project=${id}`}>
                <Button variant="ghost" size="sm">
                  View all
                </Button>
              </Link>
              <Button size="sm" onClick={() => openQuickAdd({ projectId: id })}>
                <Icon name="plus" size={14} /> Add task
              </Button>
            </div>
          </div>
          {tasks.length > 0 ? (
            <div className="divide-y divide-[var(--sidebar-border)]">
              {[...openTasks, ...doneTasks].map((task) => (
                <TaskRow
                  key={task.id}
                  task={task}
                  onToggle={toggleComplete}
                  onStatusChange={setStatus}
                />
              ))}
            </div>
          ) : (
            <div className="px-6 py-10 text-center text-sm text-[var(--text-muted)]">
              <p>No tasks yet.</p>
              <p className="mt-1">
                Add one, or{" "}
                <Link
                  href={`/projects/${id}/requirements`}
                  className="text-[var(--primary)] hover:underline"
                >
                  generate tasks from a client brief
                </Link>
                .
              </p>
            </div>
          )}
        </section>

        {/* Repositories */}
        <section className="card self-start p-5">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold">Repositories</h2>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowRepoForm(!showRepoForm)}
            >
              {showRepoForm ? (
                "Cancel"
              ) : (
                <>
                  <Icon name="plus" size={14} /> Link
                </>
              )}
            </Button>
          </div>
          {showRepoForm && (
            <form onSubmit={handleAddRepo} className="mb-4 space-y-2">
              <Input
                placeholder="Repo name"
                aria-label="Repo name"
                value={repoName}
                onChange={(e) => setRepoName(e.target.value)}
                required
              />
              <Input
                placeholder="https://github.com/..."
                aria-label="Repo URL"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                required
              />
              <Button type="submit" size="sm" className="w-full">
                Link repository
              </Button>
            </form>
          )}
          {repos.length > 0 ? (
            <div className="space-y-1">
              {repos.map((r: Repository) => (
                <a
                  key={r.id}
                  href={r.url}
                  target="_blank"
                  rel="noreferrer"
                  className="-mx-2 flex items-center gap-2.5 rounded-lg px-2 py-2 hover:bg-[var(--surface-hover)]"
                >
                  <Icon
                    name="github"
                    size={16}
                    className="text-[var(--text-muted)]"
                  />
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm font-medium">
                      {r.name}
                    </span>
                    <span className="block text-xs text-[var(--text-muted)]">
                      {r.default_branch}
                    </span>
                  </span>
                  <Icon
                    name="external"
                    size={14}
                    className="text-[var(--text-muted)]"
                  />
                </a>
              ))}
            </div>
          ) : (
            !showRepoForm && (
              <p className="text-sm text-[var(--text-muted)]">
                No repositories linked yet.
              </p>
            )
          )}
        </section>
      </div>

      <Modal
        isOpen={summary !== null}
        onClose={() => setSummary(null)}
        title="Daily summary"
        size="lg"
      >
        <p className="whitespace-pre-wrap text-sm leading-relaxed">{summary}</p>
      </Modal>
    </div>
  );
}

function Stat({
  label,
  value,
  tone = "",
}: {
  label: string;
  value: number;
  tone?: string;
}) {
  return (
    <div>
      <p className={`text-2xl font-semibold ${tone}`}>{value}</p>
      <p className="mt-1 text-xs text-[var(--text-muted)]">{label}</p>
    </div>
  );
}
