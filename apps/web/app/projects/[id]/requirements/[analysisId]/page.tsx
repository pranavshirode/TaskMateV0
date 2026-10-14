"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  apiClient,
  type RequirementsAnalysis,
  type TraceabilityReport,
  type TaskPlan,
  type AnalysisQuestion,
  type Requirement,
  type RequirementAssumption,
  type RequirementRisk,
  type TraceabilityItem,
  type ProposedTask,
} from "@/lib/api-client";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import ErrorState from "@/components/ui/ErrorState";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";

export default function RequirementsAnalysisDetailPage() {
  const { id: projectId, analysisId } = useParams<{
    id: string;
    analysisId: string;
  }>();

  const [analysis, setAnalysis] = useState<RequirementsAnalysis | null>(null);
  const [traceability, setTraceability] = useState<TraceabilityReport | null>(
    null
  );
  const [isLoading, setIsLoading] = useState(true);
  const [isActionLoading, setIsActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Active section tab
  const [activeTab, setActiveTab] = useState<
    "requirements" | "questions" | "assumptions" | "traceability"
  >("requirements");
  const [categoryFilter, setCategoryFilter] = useState<
    "ALL" | "FUNCTIONAL" | "NON_FUNCTIONAL"
  >("ALL");

  // Question answering state
  const [answeringQId, setAnsweringQId] = useState<string | null>(null);
  const [answerText, setAnswerText] = useState("");

  // Task planning state
  const [showPlanModal, setShowPlanModal] = useState(false);
  const [taskPlan, setTaskPlan] = useState<TaskPlan | null>(null);
  const [selectedTaskIndices, setSelectedTaskIndices] = useState<number[]>([]);
  const [isCreatingTasks, setIsCreatingTasks] = useState(false);

  const fetchAnalysisData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const [res, traceRes] = await Promise.all([
        apiClient.getAnalysis(analysisId),
        apiClient.getTraceability(analysisId).catch(() => null),
      ]);
      setAnalysis(res);
      setTraceability(traceRes);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load analysis");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalysisData();
  }, [analysisId]);

  const handleReanalyze = async () => {
    if (
      !confirm(
        "Re-run AI analysis on this brief? Existing answered questions will be preserved."
      )
    )
      return;
    try {
      setIsActionLoading(true);
      const res = await apiClient.analyzeBrief(analysisId);
      setAnalysis(res);
      alert("Analysis updated successfully!");
      fetchAnalysisData();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Operation failed");
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleApproveAnalysis = async () => {
    if (
      !confirm(
        "Approve this requirements specification? This confirms that requirements are ready for task planning."
      )
    )
      return;
    try {
      setIsActionLoading(true);
      const res = await apiClient.approveAnalysis(analysisId);
      setAnalysis(res);
      alert("Requirements specification approved!");
      fetchAnalysisData();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Operation failed");
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleAnswerQuestion = async (qId: string) => {
    if (!answerText.trim()) return;
    try {
      setIsActionLoading(true);
      await apiClient.answerClarification(analysisId, qId, answerText.trim());
      setAnsweringQId(null);
      setAnswerText("");
      fetchAnalysisData();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to save answer");
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleGenerateTaskPlan = async () => {
    try {
      setIsActionLoading(true);
      const res = await apiClient.generateTaskPlan(analysisId);
      setTaskPlan(res);
      setSelectedTaskIndices(
        (res.proposed_tasks || []).map((_: unknown, i: number) => i)
      );
      setShowPlanModal(true);
    } catch (err: unknown) {
      alert(
        err instanceof Error ? err.message : "Failed to generate task plan"
      );
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleApproveTaskPlan = async () => {
    if (!taskPlan || selectedTaskIndices.length === 0) return;
    const selected = selectedTaskIndices.map((i) => taskPlan.proposed_tasks[i]);

    try {
      setIsCreatingTasks(true);
      const res = await apiClient.approveTaskPlan(analysisId, selected);
      alert(res.message);
      setShowPlanModal(false);
      fetchAnalysisData();
      setActiveTab("traceability");
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to create tasks");
    } finally {
      setIsCreatingTasks(false);
    }
  };

  const toggleTaskSelection = (index: number) => {
    if (selectedTaskIndices.includes(index)) {
      setSelectedTaskIndices(selectedTaskIndices.filter((i) => i !== index));
    } else {
      setSelectedTaskIndices([...selectedTaskIndices, index]);
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-20">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchAnalysisData} />;
  }

  if (!analysis) return null;

  const overview = (analysis.overview_data || {}) as Record<string, unknown>;
  const unresolvedQuestions = (analysis.questions || []).filter(
    (q: AnalysisQuestion) => q.status === "UNRESOLVED"
  );

  return (
    <div className="max-w-5xl mx-auto pb-16">
      {/* Back Link */}
      <div className="mb-4">
        <Link
          href={`/projects/${projectId}/requirements`}
          className="text-sm text-[var(--text-muted)] hover:text-[var(--foreground)]"
        >
          ← Back to Project Requirements
        </Link>
      </div>

      {/* Header & Status Bar */}
      <div className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-6 mb-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-bold">{analysis.title}</h1>
              <span className="text-xs px-2.5 py-0.5 rounded-full border border-[var(--sidebar-border)] font-semibold text-[var(--text-muted)]">
                v{analysis.version}
              </span>
              <Badge type="status" value={analysis.status} />
            </div>
            <p className="text-xs text-[var(--text-muted)] mt-1">
              Created{" "}
              {analysis.created_at
                ? new Date(analysis.created_at).toLocaleDateString()
                : "—"}
              {analysis.approved_at && (
                <span className="text-green-400 font-medium ml-2">
                  ✓ Approved on{" "}
                  {new Date(analysis.approved_at).toLocaleDateString()}
                </span>
              )}
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            <Button
              variant="secondary"
              onClick={handleReanalyze}
              disabled={isActionLoading}
            >
              🔄 Re-analyze Brief
            </Button>

            {analysis.status !== "APPROVED" && (
              <Button
                variant="primary"
                onClick={handleApproveAnalysis}
                disabled={isActionLoading}
              >
                ✓ Approve Specification
              </Button>
            )}

            <Button
              variant="primary"
              onClick={handleGenerateTaskPlan}
              disabled={isActionLoading}
            >
              ⚡ Generate Task Plan
            </Button>
          </div>
        </div>

        {/* Unresolved Alert Banner */}
        {unresolvedQuestions.length > 0 && (
          <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3 text-xs text-amber-300 flex items-center justify-between">
            <span>
              ⚠️{" "}
              <strong>
                {unresolvedQuestions.length} clarification questions
              </strong>{" "}
              need developer input before finalizing scope.
            </span>
            <button
              onClick={() => setActiveTab("questions")}
              className="underline font-semibold hover:text-white"
            >
              Review Questions →
            </button>
          </div>
        )}
      </div>

      {/* Overview Card */}
      <div className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-6 mb-6">
        <h2 className="text-base font-semibold mb-3">Specification Overview</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm mb-4">
          <div>
            <span className="text-xs text-[var(--text-muted)] block font-medium">
              Project Objective
            </span>
            <p>{String(overview.project_objective || "") || analysis.title}</p>
          </div>
          <div>
            <span className="text-xs text-[var(--text-muted)] block font-medium">
              Intended Outcome
            </span>
            <p>
              {String(overview.intended_outcome || "") ||
                analysis.desired_outcome ||
                "—"}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs pt-3 border-t border-[var(--sidebar-border)]">
          <div>
            <span className="font-semibold text-green-400 block mb-1">
              In-Scope:
            </span>
            <ul className="list-disc pl-4 space-y-0.5 text-[var(--text-muted)]">
              {(
                (overview.in_scope as string[]) || [
                  "Core functional deliverable",
                ]
              ).map((s: string, i: number) => (
                <li key={i}>{s}</li>
              ))}
            </ul>
          </div>
          <div>
            <span className="font-semibold text-red-400 block mb-1">
              Out-of-Scope:
            </span>
            <ul className="list-disc pl-4 space-y-0.5 text-[var(--text-muted)]">
              {(
                (overview.out_of_scope as string[]) || [
                  "Third-party external dependencies outside agreed brief",
                ]
              ).map((s: string, i: number) => (
                <li key={i}>{s}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-[var(--sidebar-border)] mb-6 gap-2">
        <button
          onClick={() => setActiveTab("requirements")}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === "requirements"
              ? "border-[var(--primary)] text-[var(--foreground)]"
              : "border-transparent text-[var(--text-muted)] hover:text-[var(--foreground)]"
          }`}
        >
          Requirements ({analysis.requirements?.length || 0})
        </button>

        <button
          onClick={() => setActiveTab("questions")}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === "questions"
              ? "border-[var(--primary)] text-[var(--foreground)]"
              : "border-transparent text-[var(--text-muted)] hover:text-[var(--foreground)]"
          }`}
        >
          Clarification Questions ({analysis.questions?.length || 0})
        </button>

        <button
          onClick={() => setActiveTab("assumptions")}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === "assumptions"
              ? "border-[var(--primary)] text-[var(--foreground)]"
              : "border-transparent text-[var(--text-muted)] hover:text-[var(--foreground)]"
          }`}
        >
          Assumptions & Risks ({analysis.assumptions?.length || 0})
        </button>

        <button
          onClick={() => setActiveTab("traceability")}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === "traceability"
              ? "border-[var(--primary)] text-[var(--foreground)]"
              : "border-transparent text-[var(--text-muted)] hover:text-[var(--foreground)]"
          }`}
        >
          Task Traceability ({traceability?.total_requirements || 0})
        </button>
      </div>

      {/* Tab 1: Requirements */}
      {activeTab === "requirements" && (
        <div className="space-y-4">
          <div className="flex items-center gap-2 pb-2">
            <span className="text-xs text-[var(--text-muted)] font-medium">
              Filter:
            </span>
            <button
              onClick={() => setCategoryFilter("ALL")}
              className={`px-2.5 py-1 text-xs rounded-lg font-medium transition-colors ${
                categoryFilter === "ALL"
                  ? "bg-[var(--primary)] text-white"
                  : "bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] text-[var(--text-muted)] hover:text-[var(--foreground)]"
              }`}
            >
              All ({analysis.requirements?.length || 0})
            </button>
            <button
              onClick={() => setCategoryFilter("FUNCTIONAL")}
              className={`px-2.5 py-1 text-xs rounded-lg font-medium transition-colors ${
                categoryFilter === "FUNCTIONAL"
                  ? "bg-[var(--primary)] text-white"
                  : "bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] text-[var(--text-muted)] hover:text-[var(--foreground)]"
              }`}
            >
              Functional (
              {
                (analysis.requirements || []).filter(
                  (r) => r.category === "FUNCTIONAL" || r.key.startsWith("FR-")
                ).length
              }
              )
            </button>
            <button
              onClick={() => setCategoryFilter("NON_FUNCTIONAL")}
              className={`px-2.5 py-1 text-xs rounded-lg font-medium transition-colors ${
                categoryFilter === "NON_FUNCTIONAL"
                  ? "bg-[var(--primary)] text-white"
                  : "bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] text-[var(--text-muted)] hover:text-[var(--foreground)]"
              }`}
            >
              Non-Functional (
              {
                (analysis.requirements || []).filter(
                  (r) =>
                    r.category === "NON_FUNCTIONAL" || r.key.startsWith("NFR-")
                ).length
              }
              )
            </button>
          </div>

          {(analysis.requirements || [])
            .filter((r: Requirement) => {
              if (categoryFilter === "FUNCTIONAL")
                return r.category === "FUNCTIONAL" || r.key.startsWith("FR-");
              if (categoryFilter === "NON_FUNCTIONAL")
                return (
                  r.category === "NON_FUNCTIONAL" || r.key.startsWith("NFR-")
                );
              return true;
            })
            .map((req: Requirement) => {
              const isNfr =
                req.category === "NON_FUNCTIONAL" || req.key.startsWith("NFR-");
              return (
                <div
                  key={req.id}
                  className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-5"
                >
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-[var(--primary)]/10 text-[var(--primary)]">
                        {req.key}
                      </span>
                      <span
                        className={`text-[10px] font-medium px-2 py-0.5 rounded ${
                          isNfr
                            ? "bg-purple-500/10 text-purple-400 border border-purple-500/20"
                            : "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                        }`}
                      >
                        {isNfr ? "Non-Functional" : "Functional"}
                      </span>
                      <h3 className="font-semibold text-sm">{req.title}</h3>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge type="priority" value={req.priority} />
                      <Badge type="status" value={req.status} />
                    </div>
                  </div>

                  <p className="text-xs text-[var(--text-muted)] mb-3">
                    {req.description}
                  </p>

                  {req.acceptance_criteria &&
                    req.acceptance_criteria.length > 0 && (
                      <div className="bg-[var(--background)] rounded-lg p-3 border border-[var(--sidebar-border)] text-xs mb-2">
                        <span className="font-medium text-[var(--foreground)] block mb-1">
                          Acceptance Criteria:
                        </span>
                        <ul className="list-disc pl-4 space-y-0.5 text-[var(--text-muted)]">
                          {req.acceptance_criteria.map(
                            (c: string, i: number) => (
                              <li key={i}>{c}</li>
                            )
                          )}
                        </ul>
                      </div>
                    )}

                  {req.dependencies && req.dependencies.length > 0 && (
                    <div className="text-xs text-[var(--text-muted)]">
                      Dependencies:{" "}
                      <span className="font-mono">
                        {req.dependencies.join(", ")}
                      </span>
                    </div>
                  )}
                </div>
              );
            })}
        </div>
      )}

      {/* Tab 2: Clarification Questions */}
      {activeTab === "questions" && (
        <div className="space-y-4">
          {(analysis.questions || []).map((q: AnalysisQuestion) => (
            <div
              key={q.id}
              className={`bg-[var(--sidebar-bg)] border rounded-xl p-5 ${
                q.status === "UNRESOLVED"
                  ? "border-amber-500/40"
                  : "border-[var(--sidebar-border)]"
              }`}
            >
              <div className="flex items-center justify-between gap-2 mb-2">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold text-amber-400">
                    {q.question_key}
                  </span>
                  {q.context_topic && (
                    <span className="text-xs px-2 py-0.5 rounded bg-[var(--sidebar-border)] text-[var(--text-muted)]">
                      {q.context_topic}
                    </span>
                  )}
                </div>
                <span
                  className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    q.status === "RESOLVED"
                      ? "bg-green-500/20 text-green-300"
                      : "bg-amber-500/20 text-amber-300"
                  }`}
                >
                  {q.status}
                </span>
              </div>

              <p className="text-sm font-medium mb-1">{q.question}</p>
              {q.reason && (
                <p className="text-xs text-[var(--text-muted)] mb-3">
                  Reason: {q.reason}
                </p>
              )}

              {q.answer ? (
                <div className="bg-[var(--background)] border border-green-500/30 rounded-lg p-3 text-xs">
                  <span className="font-semibold text-green-400 block mb-0.5">
                    Developer Answer:
                  </span>
                  <p className="text-[var(--foreground)]">{q.answer}</p>
                </div>
              ) : answeringQId === q.id ? (
                <div className="mt-3 space-y-2">
                  <textarea
                    rows={2}
                    className="w-full bg-[var(--background)] border border-[var(--sidebar-border)] rounded-lg p-2 text-xs text-[var(--foreground)]"
                    placeholder="Type your answer to clarify this ambiguity..."
                    value={answerText}
                    onChange={(e) => setAnswerText(e.target.value)}
                  />
                  <div className="flex gap-2">
                    <Button
                      variant="primary"
                      onClick={() => handleAnswerQuestion(q.id)}
                      disabled={isActionLoading}
                    >
                      Save Answer
                    </Button>
                    <Button
                      variant="secondary"
                      onClick={() => setAnsweringQId(null)}
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              ) : (
                <Button
                  variant="secondary"
                  onClick={() => setAnsweringQId(q.id)}
                >
                  + Answer Question
                </Button>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Tab 3: Assumptions & Risks */}
      {activeTab === "assumptions" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="font-semibold text-sm mb-3">Recorded Assumptions</h3>
            <div className="space-y-3">
              {(analysis.assumptions || []).map(
                (asm: RequirementAssumption) => (
                  <div
                    key={asm.id}
                    className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-4 text-xs"
                  >
                    <p className="font-medium text-sm mb-1">
                      {asm.description}
                    </p>
                    {asm.reason && (
                      <p className="text-[var(--text-muted)] mb-2">
                        {asm.reason}
                      </p>
                    )}
                    <div className="flex gap-2">
                      <span className="px-2 py-0.5 rounded bg-[var(--sidebar-border)] text-[var(--text-muted)]">
                        Confidence: {asm.confidence}
                      </span>
                      <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-300">
                        {asm.status}
                      </span>
                    </div>
                  </div>
                )
              )}
            </div>
          </div>

          <div>
            <h3 className="font-semibold text-sm mb-3">Risks & Dependencies</h3>
            <div className="space-y-3">
              {(analysis.risks || []).map((rk: RequirementRisk) => (
                <div
                  key={rk.id}
                  className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-4 text-xs"
                >
                  <p className="font-medium text-sm mb-1">{rk.description}</p>
                  <div className="flex gap-2 mb-2">
                    <span className="px-2 py-0.5 rounded bg-red-500/20 text-red-300 font-medium">
                      {rk.severity} Severity
                    </span>
                    <span className="px-2 py-0.5 rounded bg-[var(--sidebar-border)] text-[var(--text-muted)]">
                      {rk.risk_type}
                    </span>
                  </div>
                  {rk.mitigation && (
                    <p className="text-[var(--text-muted)]">
                      <strong>Mitigation:</strong> {rk.mitigation}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: Bidirectional Traceability */}
      {activeTab === "traceability" && traceability && (
        <div className="space-y-6">
          <div className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-semibold">
                Implementation Progress
              </span>
              <span className="text-base font-bold text-[var(--primary)]">
                {traceability.overall_progress_percent}%
              </span>
            </div>
            <div className="w-full bg-[var(--background)] h-2 rounded-full overflow-hidden border border-[var(--sidebar-border)]">
              <div
                className="bg-green-500 h-full transition-all duration-300"
                style={{ width: `${traceability.overall_progress_percent}%` }}
              />
            </div>
            <div className="flex gap-4 text-xs text-[var(--text-muted)] mt-3">
              <span>Total Requirements: {traceability.total_requirements}</span>
              <span>Implemented: {traceability.implemented_requirements}</span>
              <span>Pending: {traceability.unimplemented_requirements}</span>
            </div>
          </div>

          <div className="space-y-3">
            {(traceability.items || []).map((item: TraceabilityItem) => (
              <div
                key={item.requirement_id}
                className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-4"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-[var(--primary)]">
                      {item.key}
                    </span>
                    <span className="font-semibold text-sm">{item.title}</span>
                  </div>
                  <Badge type="status" value={item.status} />
                </div>

                {item.linked_tasks && item.linked_tasks.length > 0 ? (
                  <div className="space-y-1 mt-2">
                    <span className="text-xs text-[var(--text-muted)] block">
                      Linked Implementation Tasks:
                    </span>
                    {item.linked_tasks.map(
                      (t: {
                        id: string;
                        title: string;
                        status: string;
                        priority: string;
                      }) => (
                        <Link
                          key={t.id}
                          href={`/tasks/${t.id}`}
                          className="flex items-center justify-between p-2 rounded bg-[var(--background)] border border-[var(--sidebar-border)] text-xs hover:border-[var(--primary)]"
                        >
                          <span>{t.title}</span>
                          <div className="flex gap-2">
                            <Badge type="status" value={t.status} />
                            <Badge type="priority" value={t.priority} />
                          </div>
                        </Link>
                      )
                    )}
                  </div>
                ) : (
                  <p className="text-xs text-amber-400 mt-1">
                    ⚠️ No tasks created for this requirement yet. Use
                    &apos;Generate Task Plan&apos; to break it down.
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Proposed Task Plan Review Modal */}
      {showPlanModal && taskPlan && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
          <div className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl max-w-2xl w-full max-h-[85vh] flex flex-col shadow-2xl">
            <div className="p-6 border-b border-[var(--sidebar-border)] flex items-center justify-between">
              <div>
                <h3 className="text-lg font-bold">
                  Review & Approve Task Plan
                </h3>
                <p className="text-xs text-[var(--text-muted)] mt-0.5">
                  Select which proposed implementation tasks to create in your
                  workspace.
                </p>
              </div>
              <button
                onClick={() => setShowPlanModal(false)}
                className="text-[var(--text-muted)] hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-3 flex-1">
              <p className="text-xs text-[var(--text-muted)] italic mb-2">
                Rationale: {taskPlan.rationale}
              </p>

              {(taskPlan.proposed_tasks || []).map(
                (t: ProposedTask, index: number) => {
                  const isChecked = selectedTaskIndices.includes(index);
                  return (
                    <div
                      key={index}
                      onClick={() => toggleTaskSelection(index)}
                      className={`border rounded-xl p-4 cursor-pointer transition-colors ${
                        isChecked
                          ? "border-[var(--primary)] bg-[var(--primary)]/5"
                          : "border-[var(--sidebar-border)] bg-[var(--background)] opacity-60"
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => {}}
                          className="mt-1"
                        />
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-semibold text-sm">
                              {t.title}
                            </span>
                            <Badge type="priority" value={t.priority} />
                          </div>
                          <p className="text-xs text-[var(--text-muted)] mb-2">
                            {t.description}
                          </p>
                          <div className="flex flex-wrap gap-2 text-xs">
                            {t.linked_requirement_keys?.map((k: string) => (
                              <span
                                key={k}
                                className="px-1.5 py-0.5 rounded bg-[var(--sidebar-border)] font-mono"
                              >
                                {k}
                              </span>
                            ))}
                            {t.estimated_effort && (
                              <span className="text-[var(--text-muted)]">
                                Effort: {t.estimated_effort}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                }
              )}
            </div>

            <div className="p-4 border-t border-[var(--sidebar-border)] flex justify-between items-center">
              <span className="text-xs text-[var(--text-muted)]">
                Selected: {selectedTaskIndices.length} of{" "}
                {taskPlan.proposed_tasks?.length || 0}
              </span>
              <div className="flex gap-3">
                <Button
                  variant="secondary"
                  onClick={() => setShowPlanModal(false)}
                >
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  onClick={handleApproveTaskPlan}
                  disabled={isCreatingTasks || selectedTaskIndices.length === 0}
                >
                  {isCreatingTasks
                    ? "Creating Tasks..."
                    : "Approve & Create Tasks"}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
