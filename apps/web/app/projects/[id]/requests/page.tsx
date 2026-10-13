"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  apiClient,
  type Project,
  type ClientRequest,
  type ImpactSummary,
} from "@/lib/api-client";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import ErrorState from "@/components/ui/ErrorState";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";

export default function ProjectClientRequestsPage() {
  const { id: projectId } = useParams<{ id: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [requests, setRequests] = useState<ClientRequest[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // New request form
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [requestType, setRequestType] = useState("CHANGE_REQUEST");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Impact analysis modal
  const [analyzingReqId, setAnalyzingReqId] = useState<string | null>(null);
  const [activeImpact, setActiveImpact] = useState<ImpactSummary | null>(null);

  const fetchData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const [projRes, reqRes] = await Promise.all([
        apiClient.getProject(projectId),
        apiClient.listProjectClientRequests(projectId),
      ]);
      setProject(projRes);
      setRequests(reqRes || []);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to load client requests"
      );
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [projectId]);

  const handleCreateRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) return;

    try {
      setIsSubmitting(true);
      await apiClient.createClientRequest(projectId, {
        title: title.trim(),
        content: content.trim(),
        request_type: requestType,
      });
      setTitle("");
      setContent("");
      setShowForm(false);
      fetchData();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to create request");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAnalyzeImpact = async (requestId: string) => {
    try {
      setAnalyzingReqId(requestId);
      const impact = await apiClient.analyzeClientRequestImpact(requestId);
      setActiveImpact(
        (impact.impact_summary || impact) as unknown as ImpactSummary
      );
      fetchData();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to analyze impact");
    } finally {
      setAnalyzingReqId(null);
    }
  };

  const handleApproveRequest = async (requestId: string) => {
    try {
      await apiClient.approveClientRequest(requestId);
      setActiveImpact(null);
      fetchData();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to approve request");
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
            Client Requests: {project?.name}
          </h1>
          <p className="text-sm text-[var(--text-muted)] mt-1">
            Capture incoming emails, messages, or meeting requests and assess
            scope impact against approved requirements.
          </p>
        </div>
        <Button
          variant={showForm ? "secondary" : "primary"}
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? "Cancel" : "+ Record Client Request"}
        </Button>
      </div>

      {showForm && (
        <div className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-6 mb-8">
          <h2 className="text-base font-semibold mb-4">
            Record New Client Request / Message
          </h2>
          <form onSubmit={handleCreateRequest} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-[var(--text-muted)] mb-1">
                Request Subject / Title *
              </label>
              <Input
                placeholder="e.g. Client requested dark mode toggle in navbar"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-[var(--text-muted)] mb-1">
                Classification Type
              </label>
              <select
                value={requestType}
                onChange={(e) => setRequestType(e.target.value)}
                className="w-full bg-[var(--background)] border border-[var(--sidebar-border)] rounded-lg p-2 text-sm text-[var(--foreground)]"
              >
                <option value="CHANGE_REQUEST">Change Request</option>
                <option value="NEW_FEATURE">New Feature</option>
                <option value="BUG_REPORT">Bug Report</option>
                <option value="CLARIFICATION">Clarification</option>
                <option value="OUT_OF_SCOPE">Out of Scope</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-[var(--text-muted)] mb-1">
                Client Message or Meeting Note *
              </label>
              <textarea
                rows={4}
                className="w-full bg-[var(--background)] border border-[var(--sidebar-border)] rounded-lg p-3 text-sm text-[var(--foreground)]"
                placeholder="Paste the client's email, message, or meeting transcript..."
                value={content}
                onChange={(e) => setContent(e.target.value)}
                required
              />
            </div>

            <div className="flex justify-end gap-3">
              <Button
                type="button"
                variant="secondary"
                onClick={() => setShowForm(false)}
              >
                Cancel
              </Button>
              <Button type="submit" variant="primary" disabled={isSubmitting}>
                {isSubmitting ? "Recording..." : "Record Request"}
              </Button>
            </div>
          </form>
        </div>
      )}

      {requests.length > 0 ? (
        <div className="space-y-4">
          {requests.map((r) => (
            <div
              key={r.id}
              className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-5"
            >
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 mb-2">
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-sm">{r.title}</h3>
                  <span className="text-xs px-2 py-0.5 rounded bg-[var(--sidebar-border)] text-[var(--text-muted)] font-mono">
                    {r.request_type}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge type="status" value={r.status} />
                  <Button
                    variant="secondary"
                    onClick={() => handleAnalyzeImpact(r.id)}
                    disabled={analyzingReqId === r.id}
                  >
                    {analyzingReqId === r.id
                      ? "Analyzing..."
                      : "⚡ Assess Impact"}
                  </Button>
                  {r.status !== "APPROVED" && (
                    <Button
                      variant="primary"
                      onClick={() => handleApproveRequest(r.id)}
                    >
                      ✓ Approve
                    </Button>
                  )}
                </div>
              </div>

              <p className="text-xs text-[var(--text-muted)] whitespace-pre-wrap mb-3">
                {r.content}
              </p>

              {r.impact_summary && (
                <div className="bg-[var(--background)] border border-[var(--sidebar-border)] rounded-lg p-3 text-xs">
                  <span className="font-semibold text-amber-400 block mb-1">
                    AI Impact Assessment (
                    {String(r.impact_summary.request_type || "")}):
                  </span>
                  <p className="text-[var(--text-muted)] mb-2">
                    {String(
                      r.impact_summary.scope_change_summary ||
                        r.impact_summary.classification_explanation ||
                        ""
                    )}
                  </p>
                  {(r.impact_summary.recommended_actions?.length || 0) > 0 && (
                    <div>
                      <span className="font-medium text-[var(--foreground)] block">
                        Recommended Actions:
                      </span>
                      <ul className="list-disc pl-4 space-y-0.5 text-[var(--text-muted)]">
                        {r.impact_summary.recommended_actions?.map(
                          (act: string, i: number) => (
                            <li key={i}>{act}</li>
                          )
                        )}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-10 text-center">
          <p className="text-sm text-[var(--text-muted)] mb-3">
            No client requests logged for this project yet.
          </p>
          <Button variant="primary" onClick={() => setShowForm(true)}>
            Record First Request
          </Button>
        </div>
      )}

      {/* Impact Modal */}
      {activeImpact && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
          <div className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl max-w-lg w-full p-6 shadow-2xl">
            <h3 className="text-base font-bold mb-2">
              Change Impact Assessment
            </h3>
            <p className="text-xs text-[var(--text-muted)] mb-4">
              {String(activeImpact.classification_explanation || "")}
            </p>

            <div className="space-y-3 text-xs mb-6">
              <div>
                <span className="font-semibold text-[var(--foreground)] block">
                  Scope Change Summary:
                </span>
                <p className="text-[var(--text-muted)]">
                  {String(activeImpact.scope_change_summary || "")}
                </p>
              </div>

              {(activeImpact.recommended_actions?.length || 0) > 0 && (
                <div>
                  <span className="font-semibold text-[var(--foreground)] block">
                    Recommended Actions:
                  </span>
                  <ul className="list-disc pl-4 space-y-0.5 text-[var(--text-muted)]">
                    {activeImpact.recommended_actions?.map(
                      (act: string, i: number) => (
                        <li key={i}>{act}</li>
                      )
                    )}
                  </ul>
                </div>
              )}
            </div>

            <div className="flex justify-end gap-3">
              <Button variant="secondary" onClick={() => setActiveImpact(null)}>
                Close
              </Button>
              <Button
                variant="primary"
                onClick={() =>
                  handleApproveRequest(String(activeImpact.request_id || ""))
                }
              >
                Approve Change
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
