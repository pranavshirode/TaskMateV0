"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  apiClient,
  type Project,
  type RequirementsAnalysis,
  type PipelineExecutionResponse,
} from "@/lib/api-client";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import ErrorState from "@/components/ui/ErrorState";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Icon from "@/components/ui/Icon";
import { useFeedback } from "@/components/ui/Feedback";

export default function ProjectRequirementsPage() {
  const { toast, confirm } = useFeedback();
  const { id: projectId } = useParams<{ id: string }>();
  const router = useRouter();

  const [project, setProject] = useState<Project | null>(null);
  const [analyses, setAnalyses] = useState<RequirementsAnalysis[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form states
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState("");
  const [brief, setBrief] = useState("");
  const [desiredOutcome, setDesiredOutcome] = useState("");
  const [constraints, setConstraints] = useState("");
  const [deadline, setDeadline] = useState("");

  // Multi-Agent Pipeline state
  const [showPipelineModal, setShowPipelineModal] = useState(false);
  const [isPipelineRunning, setIsPipelineRunning] = useState(false);
  const [pipelineTitle, setPipelineTitle] = useState("");
  const [pipelineBrief, setPipelineBrief] = useState("");
  const [pipelineOutcome, setPipelineOutcome] = useState("");
  const [pipelineConstraints, setPipelineConstraints] = useState("");
  const [pipelineDeadline, setPipelineDeadline] = useState("");
  const [autoApproveReqs, setAutoApproveReqs] = useState(true);
  const [autoCreateTasks, setAutoCreateTasks] = useState(true);
  const [autoCreateProposal, setAutoCreateProposal] = useState(true);
  const [pipelineResult, setPipelineResult] = useState<PipelineExecutionResponse | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleDeleteAnalysis = async (
    e: React.MouseEvent,
    analysisId: string,
    analysisTitle: string
  ) => {
    e.preventDefault();
    e.stopPropagation();

    const ok = await confirm({
      title: "Delete Requirements Session?",
      message: `Are you sure you want to delete "${analysisTitle}"? All associated requirements and questions will be permanently removed.`,
      confirmLabel: "Delete",
      danger: true,
    });
    if (!ok) return;

    try {
      setDeletingId(analysisId);
      await apiClient.deleteAnalysis(analysisId);
      toast("Requirements session deleted", "success");
      setAnalyses((prev) => prev.filter((a) => a.id !== analysisId));
    } catch (err: unknown) {
      toast(
        err instanceof Error ? err.message : "Failed to delete session",
        "error"
      );
    } finally {
      setDeletingId(null);
    }
  };

  const fetchData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const [projRes, analysisRes] = await Promise.all([
        apiClient.getProject(projectId),
        apiClient.listProjectAnalyses(projectId),
      ]);
      setProject(projRes);
      setAnalyses(analysisRes || []);
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load project requirements"
      );
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [projectId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !brief.trim()) return;

    try {
      setIsSubmitting(true);
      const created = await apiClient.createAnalysis({
        project_id: projectId,
        title: title.trim(),
        brief: brief.trim(),
        desired_outcome: desiredOutcome.trim() || undefined,
        constraints: constraints.trim() || undefined,
        deadline: deadline.trim() || undefined,
      });

      // Automatically trigger initial AI analysis pipeline
      await apiClient.analyzeBrief(created.id);
      router.push(`/projects/${projectId}/requirements/${created.id}`);
    } catch (err: unknown) {
      toast(
        err instanceof Error ? err.message : "Failed to analyze brief",
        "error"
      );
      setIsSubmitting(false);
    }
  };

  const handleExecutePipeline = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!pipelineBrief.trim()) return;

    try {
      setIsPipelineRunning(true);
      setPipelineResult(null);
      const res = await apiClient.executeMultiAgentPipeline({
        project_id: projectId,
        brief: pipelineBrief.trim(),
        title: pipelineTitle.trim() || undefined,
        desired_outcome: pipelineOutcome.trim() || undefined,
        constraints: pipelineConstraints.trim() || undefined,
        deadline: pipelineDeadline.trim() || undefined,
        auto_approve_requirements: autoApproveReqs,
        auto_create_tasks: autoCreateTasks,
        auto_create_proposal: autoCreateProposal,
      });
      setPipelineResult(res);
      fetchData();
      if (res.status === "SUCCESS") {
        toast("Multi-agent delivery pipeline executed successfully!");
      } else if (res.status === "CLARIFICATION_REQUIRED") {
        toast(
          "Pipeline paused: clarification questions required from developer",
          "info"
        );
      } else if (res.status === "PENDING_REQUIREMENT_APPROVAL") {
        toast(
          "Pipeline paused: requirements generated and ready for approval",
          "info"
        );
      }
    } catch (err: unknown) {
      toast(
        err instanceof Error ? err.message : "Pipeline execution failed",
        "error"
      );
    } finally {
      setIsPipelineRunning(false);
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
    return <ErrorState message={error} onRetry={fetchData} />;
  }

  return (
    <div className="max-w-4xl mx-auto pb-12">
      <div className="mb-4">
        <Link
          href={`/projects/${projectId}`}
          className="text-sm text-[var(--text-muted)] hover:text-[var(--foreground)]"
        >
          ← Back to {project?.name || "Project"}
        </Link>
      </div>

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            Requirements Analysis: {project?.name}
          </h1>
          <p className="text-sm text-[var(--text-muted)] mt-1">
            Transform client briefs into reviewable functional requirements and
            actionable tasks.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="secondary"
            onClick={() => {
              setShowPipelineModal(true);
              setPipelineResult(null);
            }}
          >
            ⚡ Run Multi-Agent Pipeline
          </Button>
          <Button
            variant={showForm ? "secondary" : "primary"}
            onClick={() => setShowForm(!showForm)}
          >
            {showForm ? "Cancel" : "+ New Brief Submission"}
          </Button>
        </div>
      </div>

      {showForm && (
        <div className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-6 mb-8 shadow-sm">
          <h2 className="text-lg font-semibold mb-4">
            Submit Client Brief for AI Analysis
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-[var(--text-muted)] mb-1">
                Analysis / Request Title *
              </label>
              <Input
                placeholder="e.g. Stripe Checkout & Webhook Integration"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-[var(--text-muted)] mb-1">
                Client Brief / Specification *
              </label>
              <textarea
                rows={6}
                className="w-full bg-[var(--background)] border border-[var(--sidebar-border)] rounded-lg p-3 text-sm focus:outline-none focus:border-[var(--primary)] text-[var(--foreground)]"
                placeholder="Paste the raw client email, brief, requirements list, or meeting notes here..."
                value={brief}
                onChange={(e) => setBrief(e.target.value)}
                required
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-[var(--text-muted)] mb-1">
                  Desired Outcome (Optional)
                </label>
                <Input
                  placeholder="e.g. Working payment flow with confirmation email"
                  value={desiredOutcome}
                  onChange={(e) => setDesiredOutcome(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-[var(--text-muted)] mb-1">
                  Constraints / Tech Stack (Optional)
                </label>
                <Input
                  placeholder="e.g. Next.js, Stripe SDK, PostgreSQL"
                  value={constraints}
                  onChange={(e) => setConstraints(e.target.value)}
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-[var(--text-muted)] mb-1">
                Target Deadline (Optional)
              </label>
              <Input
                type="date"
                value={deadline}
                onChange={(e) => setDeadline(e.target.value)}
              />
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <Button
                type="button"
                variant="secondary"
                onClick={() => setShowForm(false)}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button type="submit" variant="primary" disabled={isSubmitting}>
                {isSubmitting ? "Analyzing Brief with AI..." : "Analyze Brief"}
              </Button>
            </div>
          </form>
        </div>
      )}

      {showPipelineModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-2xl w-full max-w-2xl p-6 shadow-2xl my-8">
            <div className="flex items-center justify-between pb-4 border-b border-[var(--sidebar-border)] mb-5">
              <div className="flex items-center gap-2">
                <span className="text-xl">🤖</span>
                <div>
                  <h3 className="font-semibold text-lg">Multi-Agent Delivery Pipeline</h3>
                  <p className="text-xs text-[var(--text-muted)]">
                    Sequential workflow: Requirement Analyzer → Approval Gate → Task Planner → Proposal Generator
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowPipelineModal(false)}
                className="text-[var(--text-muted)] hover:text-[var(--foreground)] text-lg"
              >
                ✕
              </button>
            </div>

            {!pipelineResult ? (
              <form onSubmit={handleExecutePipeline} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-[var(--text-muted)] mb-1">
                    Workflow / Analysis Title (Optional)
                  </label>
                  <Input
                    placeholder="e.g. Stripe Checkout & Customer Portal Delivery"
                    value={pipelineTitle}
                    onChange={(e) => setPipelineTitle(e.target.value)}
                    disabled={isPipelineRunning}
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-[var(--text-muted)] mb-1">
                    Client Brief / Specification *
                  </label>
                  <textarea
                    rows={5}
                    className="w-full bg-[var(--background)] border border-[var(--sidebar-border)] rounded-lg p-3 text-sm focus:outline-none focus:border-[var(--primary)] text-[var(--foreground)]"
                    placeholder="Paste the client brief. The Requirement Analyzer parses functional requirements, risks, and assumptions. If critical facts are missing, the pipeline pauses for developer clarification instead of fabricating answers."
                    value={pipelineBrief}
                    onChange={(e) => setPipelineBrief(e.target.value)}
                    required
                    disabled={isPipelineRunning}
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-[var(--text-muted)] mb-1">
                      Desired Outcome (Optional)
                    </label>
                    <Input
                      placeholder="e.g. Working payment flow with receipts"
                      value={pipelineOutcome}
                      onChange={(e) => setPipelineOutcome(e.target.value)}
                      disabled={isPipelineRunning}
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-[var(--text-muted)] mb-1">
                      Constraints / Tech Stack (Optional)
                    </label>
                    <Input
                      placeholder="e.g. Next.js, Stripe SDK, PostgreSQL"
                      value={pipelineConstraints}
                      onChange={(e) => setPipelineConstraints(e.target.value)}
                      disabled={isPipelineRunning}
                    />
                  </div>
                </div>

                <div className="bg-[var(--background)] border border-[var(--sidebar-border)] rounded-lg p-4 space-y-3">
                  <p className="text-xs font-medium text-[var(--foreground)]">Orchestration & Approval Options</p>
                  
                  <label className="flex items-center gap-2 text-xs text-[var(--text-muted)] cursor-pointer">
                    <input
                      type="checkbox"
                      checked={autoApproveReqs}
                      onChange={(e) => setAutoApproveReqs(e.target.checked)}
                      disabled={isPipelineRunning}
                      className="rounded"
                    />
                    <span>Auto-approve requirements when no critical ambiguities are detected</span>
                  </label>

                  <label className="flex items-center gap-2 text-xs text-[var(--text-muted)] cursor-pointer">
                    <input
                      type="checkbox"
                      checked={autoCreateTasks}
                      onChange={(e) => setAutoCreateTasks(e.target.checked)}
                      disabled={isPipelineRunning}
                      className="rounded"
                    />
                    <span>Automatically plan and persist project tasks with bidirectional traceability</span>
                  </label>

                  <label className="flex items-center gap-2 text-xs text-[var(--text-muted)] cursor-pointer">
                    <input
                      type="checkbox"
                      checked={autoCreateProposal}
                      onChange={(e) => setAutoCreateProposal(e.target.checked)}
                      disabled={isPipelineRunning}
                      className="rounded"
                    />
                    <span>Automatically draft proposal with scope, deliverables, timeline, and pricing</span>
                  </label>
                </div>

                {isPipelineRunning && (
                  <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20 text-center space-y-2">
                    <LoadingSpinner />
                    <p className="text-xs font-medium text-blue-400">
                      Executing sequential pipeline: Analyzer → Gate → Planner → Proposal...
                    </p>
                    <p className="text-[11px] text-[var(--text-muted)]">
                      Enforcing authorization, tenant isolation, and non-fabrication guardrails.
                    </p>
                  </div>
                )}

                <div className="flex justify-end gap-3 pt-3 border-t border-[var(--sidebar-border)]">
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => setShowPipelineModal(false)}
                    disabled={isPipelineRunning}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" variant="primary" disabled={isPipelineRunning}>
                    {isPipelineRunning ? "Running Pipeline..." : "Execute Pipeline"}
                  </Button>
                </div>
              </form>
            ) : (
              <div className="space-y-5">
                <div className="p-4 rounded-xl border border-[var(--sidebar-border)] bg-[var(--background)] flex items-start justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold text-sm">Pipeline Status:</span>
                      <span
                        className={`text-xs px-2 py-0.5 rounded font-mono font-medium ${
                          pipelineResult.status === "SUCCESS"
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                            : pipelineResult.status === "CLARIFICATION_REQUIRED"
                            ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                            : pipelineResult.status === "PENDING_REQUIREMENT_APPROVAL"
                            ? "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                            : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                        }`}
                      >
                        {pipelineResult.status}
                      </span>
                    </div>
                    <p className="text-xs text-[var(--text-muted)] mt-1">{pipelineResult.message}</p>
                  </div>
                  <span className="text-xs text-[var(--text-muted)] font-mono whitespace-nowrap">
                    ⏱ {pipelineResult.total_duration_ms}ms
                  </span>
                </div>

                <div className="space-y-2">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">
                    Agent Stage Telemetry
                  </h4>
                  <div className="space-y-2">
                    {pipelineResult.stages.map((stg) => (
                      <div
                        key={stg.stage_name}
                        className="p-3 rounded-lg border border-[var(--sidebar-border)] bg-[var(--background)] flex items-center justify-between text-xs"
                      >
                        <div className="flex items-center gap-2">
                          <span
                            className={`w-2 h-2 rounded-full ${
                              stg.status === "COMPLETED"
                                ? "bg-emerald-400"
                                : stg.status === "WAITING_FOR_APPROVAL" || stg.status === "WAITING_FOR_CLARIFICATION"
                                ? "bg-amber-400"
                                : stg.status === "SKIPPED"
                                ? "bg-zinc-500"
                                : "bg-rose-400"
                            }`}
                          />
                          <span className="font-medium">{stg.stage_name}</span>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="text-[var(--text-muted)] line-clamp-1 max-w-[220px]">
                            {stg.summary}
                          </span>
                          <span className="font-mono text-[var(--text-muted)]">{stg.duration_ms}ms</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="p-3 rounded-lg bg-[var(--background)] border border-[var(--sidebar-border)] text-center">
                    <p className="text-[11px] text-[var(--text-muted)]">Requirements</p>
                    <p className="text-base font-semibold mt-0.5">{pipelineResult.requirements_count}</p>
                  </div>
                  <div className="p-3 rounded-lg bg-[var(--background)] border border-[var(--sidebar-border)] text-center">
                    <p className="text-[11px] text-[var(--text-muted)]">Pending Questions</p>
                    <p className={`text-base font-semibold mt-0.5 ${pipelineResult.unresolved_questions_count > 0 ? "text-amber-400" : ""}`}>
                      {pipelineResult.unresolved_questions_count}
                    </p>
                  </div>
                  <div className="p-3 rounded-lg bg-[var(--background)] border border-[var(--sidebar-border)] text-center">
                    <p className="text-[11px] text-[var(--text-muted)]">Tasks Created</p>
                    <p className="text-base font-semibold mt-0.5">{pipelineResult.created_tasks_count}</p>
                  </div>
                  <div className="p-3 rounded-lg bg-[var(--background)] border border-[var(--sidebar-border)] text-center">
                    <p className="text-[11px] text-[var(--text-muted)]">Proposal</p>
                    <p className="text-base font-semibold mt-0.5">
                      {pipelineResult.proposal_id ? "Draft Created" : "None"}
                    </p>
                  </div>
                </div>

                <div className="flex flex-wrap justify-end gap-3 pt-4 border-t border-[var(--sidebar-border)]">
                  <Button
                    variant="secondary"
                    onClick={() => {
                      setPipelineResult(null);
                      setShowPipelineModal(false);
                    }}
                  >
                    Close
                  </Button>
                  {pipelineResult.analysis_id && (
                    <Button
                      variant="secondary"
                      onClick={() => {
                        setShowPipelineModal(false);
                        router.push(`/projects/${projectId}/requirements/${pipelineResult.analysis_id}`);
                      }}
                    >
                      {pipelineResult.unresolved_questions_count > 0 ? "Answer Clarifications →" : "Review Requirements →"}
                    </Button>
                  )}
                  {pipelineResult.proposal_id && (
                    <Button
                      variant="primary"
                      onClick={() => {
                        setShowPipelineModal(false);
                        router.push(`/projects/${projectId}/proposals`);
                      }}
                    >
                      View Generated Proposal →
                    </Button>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Existing Sessions List */}
      <h2 className="text-lg font-semibold mb-4">
        Saved Requirements Sessions
      </h2>
      {analyses.length > 0 ? (
        <div className="space-y-3">
          {analyses.map((a) => (
            <Link
              key={a.id}
              href={`/projects/${projectId}/requirements/${a.id}`}
              className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-5 hover:border-[var(--primary)] transition-colors flex flex-col md:flex-row md:items-center justify-between gap-4 block"
            >
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-semibold text-base">{a.title}</span>
                  <span className="text-xs px-2 py-0.5 rounded-full border border-[var(--sidebar-border)] text-[var(--text-muted)]">
                    v{a.version}
                  </span>
                </div>
                <p className="text-xs text-[var(--text-muted)] line-clamp-1 mb-2">
                  {a.brief}
                </p>
                <div className="flex gap-4 text-xs text-[var(--text-muted)]">
                  <span>
                    Requirements:{" "}
                    {a.total_requirements || a.requirements?.length || 0}
                  </span>
                  <span>Approved: {a.approved_requirements || 0}</span>
                  {(a.unresolved_questions || 0) > 0 && (
                    <span className="text-amber-400 font-medium">
                      ⚠️ {a.unresolved_questions} questions pending
                    </span>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Badge type="status" value={a.status} />
                <span className="text-xs text-[var(--primary)] hover:underline">
                  View Analysis →
                </span>
                <button
                  type="button"
                  title="Delete session"
                  disabled={deletingId === a.id}
                  onClick={(e) => handleDeleteAnalysis(e, a.id, a.title)}
                  className="rounded-lg p-2 text-[var(--text-muted)] transition-colors hover:bg-[var(--danger-soft)] hover:text-[var(--danger)] disabled:opacity-50"
                >
                  <Icon name="trash" size={15} />
                </button>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-10 text-center">
          <p className="text-sm text-[var(--text-muted)] mb-3">
            No requirements analyses recorded for this project.
          </p>
          <Button variant="primary" onClick={() => setShowForm(true)}>
            Submit First Client Brief
          </Button>
        </div>
      )}
    </div>
  );
}
