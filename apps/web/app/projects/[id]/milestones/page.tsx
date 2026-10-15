"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  apiClient,
  type Project,
  type Milestone,
  type Task,
  type TaskDependency,
} from "@/lib/api-client";
import { errorMessage, formatDate } from "@/lib/format";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import ErrorState from "@/components/ui/ErrorState";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Select from "@/components/ui/Select";
import Modal from "@/components/ui/Modal";
import Icon from "@/components/ui/Icon";
import { useFeedback } from "@/components/ui/Feedback";

export default function ProjectMilestonesPage() {
  const { id: projectId } = useParams<{ id: string }>();
  const { toast, confirm } = useFeedback();

  const [project, setProject] = useState<Project | null>(null);
  const [milestones, setMilestones] = useState<Milestone[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Milestone Create/Edit modal
  const [showMilestoneModal, setShowMilestoneModal] = useState(false);
  const [editingMilestone, setEditingMilestone] = useState<Milestone | null>(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState("OPEN");
  const [dueDate, setDueDate] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Dependency modal
  const [showDepModal, setShowDepModal] = useState(false);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [taskDependencies, setTaskDependencies] = useState<TaskDependency[]>([]);
  const [dependsOnTaskId, setDependsOnTaskId] = useState("");
  const [isDepLoading, setIsDepLoading] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const [proj, milestoneList, taskList] = await Promise.all([
        apiClient.getProject(projectId),
        apiClient.listProjectMilestones(projectId),
        apiClient.listTasks({ project_id: projectId, page_size: "100" }),
      ]);
      setProject(proj);
      setMilestones(milestoneList || []);
      setTasks(taskList.items || []);
    } catch (err: unknown) {
      setError(errorMessage(err, "Failed to load milestones"));
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const openCreateModal = () => {
    setEditingMilestone(null);
    setTitle("");
    setDescription("");
    setStatus("OPEN");
    setDueDate("");
    setShowMilestoneModal(true);
  };

  const openEditModal = (m: Milestone) => {
    setEditingMilestone(m);
    setTitle(m.title);
    setDescription(m.description || "");
    setStatus(m.status);
    setDueDate(m.due_date ? m.due_date.split("T")[0] : "");
    setShowMilestoneModal(true);
  };

  const handleSaveMilestone = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    try {
      setIsSubmitting(true);
      if (editingMilestone) {
        await apiClient.updateMilestone(editingMilestone.id, {
          title: title.trim(),
          description: description.trim() || undefined,
          status,
          due_date: dueDate || undefined,
        });
        toast("Milestone updated", "success");
      } else {
        await apiClient.createMilestone({
          project_id: projectId,
          title: title.trim(),
          description: description.trim() || undefined,
          status,
          due_date: dueDate || undefined,
        });
        toast("Milestone created", "success");
      }
      setShowMilestoneModal(false);
      await fetchData();
    } catch (err: unknown) {
      toast(errorMessage(err, "Failed to save milestone"), "error");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteMilestone = async (id: string, mTitle: string) => {
    const ok = await confirm({
      title: "Delete Milestone",
      message: `Delete "${mTitle}"? Tasks in this milestone will not be deleted, only unlinked.`,
      confirmLabel: "Delete",
      danger: true,
    });
    if (!ok) return;

    try {
      await apiClient.deleteMilestone(id);
      toast("Milestone deleted", "success");
      await fetchData();
    } catch (err: unknown) {
      toast(errorMessage(err, "Failed to delete milestone"), "error");
    }
  };

  // Open dependencies modal for a specific task
  const openDependenciesModal = async (task: Task) => {
    setSelectedTask(task);
    setDependsOnTaskId("");
    setShowDepModal(true);
    try {
      setIsDepLoading(true);
      const deps = await apiClient.getTaskDependencies(task.id);
      setTaskDependencies(deps || []);
    } catch (err: unknown) {
      toast(errorMessage(err, "Failed to load dependencies"), "error");
    } finally {
      setIsDepLoading(false);
    }
  };

  const handleAddDependency = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTask || !dependsOnTaskId) return;

    try {
      setIsDepLoading(true);
      await apiClient.addTaskDependency(selectedTask.id, dependsOnTaskId);
      toast("Dependency added", "success");
      setDependsOnTaskId("");
      const deps = await apiClient.getTaskDependencies(selectedTask.id);
      setTaskDependencies(deps || []);
    } catch (err: unknown) {
      toast(errorMessage(err, "Failed to add dependency"), "error");
    } finally {
      setIsDepLoading(false);
    }
  };

  const handleRemoveDependency = async (depId: string, dependsOnId: string) => {
    if (!selectedTask) return;
    try {
      setIsDepLoading(true);
      await apiClient.removeTaskDependency(selectedTask.id, dependsOnId);
      toast("Dependency removed", "success");
      const deps = await apiClient.getTaskDependencies(selectedTask.id);
      setTaskDependencies(deps || []);
    } catch (err: unknown) {
      toast(errorMessage(err, "Failed to remove dependency"), "error");
    } finally {
      setIsDepLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-16">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return <ErrorState message={error} onRetry={() => fetchData()} />;
  }

  return (
    <div className="mx-auto max-w-5xl pb-16">
      {/* Breadcrumb */}
      <Link
        href={`/projects/${projectId}`}
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-[var(--text-muted)] hover:text-[var(--foreground)]"
      >
        <Icon name="arrowLeft" size={14} /> Back to {project?.name || "Project"}
      </Link>

      {/* Header */}
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Milestones</h1>
          <p className="mt-1 text-sm text-[var(--text-muted)]">
            Organize project deliveries into milestones and track task dependencies.
          </p>
        </div>
        <Button onClick={openCreateModal} className="flex items-center gap-2">
          <Icon name="plus" size={16} /> Add Milestone
        </Button>
      </div>

      {/* Milestones List */}
      {milestones.length === 0 ? (
        <div className="card p-12 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-[var(--surface-muted)] text-[var(--text-muted)]">
            <Icon name="calendar" size={24} />
          </div>
          <h3 className="mt-4 text-base font-medium">No milestones yet</h3>
          <p className="mt-1 text-sm text-[var(--text-muted)]">
            Create milestones to segment your deliverables into trackable phases.
          </p>
          <div className="mt-6">
            <Button onClick={openCreateModal}>Create First Milestone</Button>
          </div>
        </div>
      ) : (
        <div className="grid gap-4">
          {milestones.map((m) => {
            const pct =
              m.task_count > 0
                ? Math.round((m.completed_task_count / m.task_count) * 100)
                : 0;

            const statusColors: Record<string, string> = {
              OPEN: "bg-blue-500/10 text-blue-500 border-blue-500/20",
              IN_PROGRESS: "bg-amber-500/10 text-amber-500 border-amber-500/20",
              COMPLETED: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
              CANCELLED: "bg-zinc-500/10 text-zinc-500 border-zinc-500/20",
            };

            return (
              <div key={m.id} className="card p-5 transition hover:border-[var(--border-strong)]">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div className="space-y-1">
                    <div className="flex items-center gap-3">
                      <h3 className="text-lg font-medium">{m.title}</h3>
                      <span
                        className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${
                          statusColors[m.status] || statusColors.OPEN
                        }`}
                      >
                        {m.status.replace("_", " ")}
                      </span>
                    </div>
                    {m.description && (
                      <p className="text-sm text-[var(--text-muted)]">{m.description}</p>
                    )}
                    <div className="flex flex-wrap items-center gap-4 text-xs text-[var(--text-muted)]">
                      {m.due_date && (
                        <span className="inline-flex items-center gap-1">
                          <Icon name="clock" size={12} /> Due {formatDate(m.due_date)}
                        </span>
                      )}
                      <span>
                        {m.completed_task_count} of {m.task_count} tasks completed ({pct}%)
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => openEditModal(m)}
                    >
                      <Icon name="edit" size={14} />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDeleteMilestone(m.id, m.title)}
                    >
                      <Icon name="trash" size={14} />
                    </Button>
                  </div>
                </div>

                {/* Progress bar */}
                <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-[var(--surface-muted)]">
                  <div
                    className="h-full bg-emerald-500 transition-all duration-300"
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Task Dependency Manager Section */}
      <div className="mt-12">
        <div className="mb-4">
          <h2 className="text-lg font-semibold tracking-tight">Task Dependencies</h2>
          <p className="text-sm text-[var(--text-muted)]">
            Define blocking relationships between tasks. A task cannot proceed until its dependencies are done.
          </p>
        </div>

        <div className="card divide-y divide-[var(--border)]">
          {tasks.length === 0 ? (
            <p className="p-6 text-sm text-[var(--text-muted)]">No tasks in this project.</p>
          ) : (
            tasks.map((task) => (
              <div
                key={task.id}
                className="flex items-center justify-between p-4 transition hover:bg-[var(--surface-hover)]"
              >
                <div>
                  <span className="font-medium text-sm">{task.title}</span>
                  <div className="flex items-center gap-2 text-xs text-[var(--text-muted)] mt-0.5">
                    <span>Status: {task.status}</span>
                    <span>•</span>
                    <span>Priority: {task.priority}</span>
                  </div>
                </div>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => openDependenciesModal(task)}
                >
                  Manage Dependencies
                </Button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Create / Edit Milestone Modal */}
      <Modal
        isOpen={showMilestoneModal}
        onClose={() => setShowMilestoneModal(false)}
        title={editingMilestone ? "Edit Milestone" : "Create Milestone"}
      >
        <form onSubmit={handleSaveMilestone} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium">Title *</label>
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Beta Release, Sprint 1 Deliverable"
              required
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium">Description</label>
            <textarea
              className="w-full rounded-md border border-[var(--border)] bg-[var(--surface)] p-2.5 text-sm text-[var(--foreground)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]"
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Scope and goals for this milestone..."
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="mb-1 block text-sm font-medium">Status</label>
              <Select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                options={[
                  { label: "Open", value: "OPEN" },
                  { label: "In Progress", value: "IN_PROGRESS" },
                  { label: "Completed", value: "COMPLETED" },
                  { label: "Cancelled", value: "CANCELLED" },
                ]}
              />
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium">Due Date</label>
              <Input
                type="date"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setShowMilestoneModal(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting || !title.trim()}>
              {isSubmitting ? "Saving..." : editingMilestone ? "Save Changes" : "Create Milestone"}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Dependencies Modal */}
      <Modal
        isOpen={showDepModal}
        onClose={() => setShowDepModal(false)}
        title={`Dependencies for: ${selectedTask?.title || "Task"}`}
      >
        <div className="space-y-6">
          <div>
            <h4 className="text-sm font-medium mb-2">Depends On (Blocks this task)</h4>
            {isDepLoading ? (
              <div className="flex justify-center py-4">
                <LoadingSpinner />
              </div>
            ) : taskDependencies.length === 0 ? (
              <p className="text-sm text-[var(--text-muted)] italic">
                No dependencies configured. This task can be started anytime.
              </p>
            ) : (
              <div className="divide-y divide-[var(--border)] border rounded-md overflow-hidden">
                {taskDependencies.map((dep) => (
                  <div
                    key={dep.id}
                    className="flex items-center justify-between p-3 bg-[var(--surface)] text-sm"
                  >
                    <div>
                      <span className="font-medium">{dep.depends_on_title || dep.depends_on_task_id}</span>
                      {dep.depends_on_status && (
                        <span className="ml-2 text-xs text-[var(--text-muted)]">
                          ({dep.depends_on_status})
                        </span>
                      )}
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRemoveDependency(dep.id, dep.depends_on_task_id)}
                    >
                      <Icon name="x" size={14} />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <form onSubmit={handleAddDependency} className="space-y-3 pt-2 border-t border-[var(--border)]">
            <label className="block text-sm font-medium">Add Dependency</label>
            <Select
              value={dependsOnTaskId}
              onChange={(e) => setDependsOnTaskId(e.target.value)}
              options={[
                { label: "-- Select a blocking task --", value: "" },
                ...tasks
                  .filter((t) => t.id !== selectedTask?.id)
                  .map((t) => ({ label: `${t.title} (${t.status})`, value: t.id })),
              ]}
            />
            <div className="flex justify-end gap-3 pt-2">
              <Button
                type="button"
                variant="secondary"
                onClick={() => setShowDepModal(false)}
              >
                Close
              </Button>
              <Button type="submit" disabled={!dependsOnTaskId || isDepLoading}>
                Add Dependency
              </Button>
            </div>
          </form>
        </div>
      </Modal>
    </div>
  );
}
