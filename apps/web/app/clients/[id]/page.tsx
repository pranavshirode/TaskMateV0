"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  apiClient,
  type Client,
  type ClientCommunication,
  type Project,
} from "@/lib/api-client";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import ErrorState from "@/components/ui/ErrorState";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import Modal from "@/components/ui/Modal";
import Input from "@/components/ui/Input";
import Select from "@/components/ui/Select";
import Icon from "@/components/ui/Icon";
import { useFeedback } from "@/components/ui/Feedback";

function errorMessage(err: unknown, fallback: string): string {
  return err instanceof Error ? err.message : fallback;
}

export default function ClientDetailPage() {
  const { toast, confirm } = useFeedback();
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  const [client, setClient] = useState<Client | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [communications, setCommunications] = useState<ClientCommunication[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modals & form state
  const [showDraftModal, setShowDraftModal] = useState(false);
  const [showAIDraftModal, setShowAIDraftModal] = useState(false);
  const [viewingComm, setViewingComm] = useState<ClientCommunication | null>(null);

  // Manual Draft fields
  const [draftSubject, setDraftSubject] = useState("");
  const [draftContent, setDraftContent] = useState("");
  const [draftChannel, setDraftChannel] = useState("EMAIL");
  const [draftType, setDraftType] = useState("FOLLOW_UP");
  const [draftProjectId, setDraftProjectId] = useState<string>("");
  const [draftNotes, setDraftNotes] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // AI Draft fields
  const [aiType, setAiType] = useState("FOLLOW_UP");
  const [aiTone, setAiTone] = useState("professional");
  const [aiProjectId, setAiProjectId] = useState<string>("");
  const [aiNotes, setAiNotes] = useState("");
  const [isDraftingAI, setIsDraftingAI] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const [clientData, projData, commsData] = await Promise.all([
        apiClient.getClient(id),
        apiClient.listProjects({ client_id: id, page_size: "50" }),
        apiClient.listClientCommunications(id),
      ]);
      setClient(clientData);
      setProjects(projData.items || []);
      setCommunications(commsData || []);
    } catch (err: unknown) {
      setError(errorMessage(err, "Failed to load client details"));
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleArchive = async () => {
    if (!(await confirm({ title: "Archive this client?" }))) return;
    try {
      await apiClient.archiveClient(id);
      router.push("/clients");
    } catch (err: unknown) {
      toast(errorMessage(err, "Failed to archive client"), "error");
    }
  };

  const handleCreateDraft = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!draftSubject.trim() || !draftContent.trim()) {
      toast("Subject and content are required.", "error");
      return;
    }
    try {
      setIsSubmitting(true);
      await apiClient.createClientCommunication({
        client_id: id,
        project_id: draftProjectId || undefined,
        subject: draftSubject.trim(),
        content: draftContent.trim(),
        channel: draftChannel,
        communication_type: draftType,
        notes: draftNotes.trim() || undefined,
      });
      toast("Communication draft created.", "success");
      setShowDraftModal(false);
      setDraftSubject("");
      setDraftContent("");
      setDraftNotes("");
      await fetchData();
    } catch (err: unknown) {
      toast(errorMessage(err, "Failed to create draft"), "error");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAIDraft = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setIsDraftingAI(true);
      await apiClient.aiDraftCommunication({
        client_id: id,
        project_id: aiProjectId || undefined,
        communication_type: aiType,
        tone: aiTone,
        context_notes: aiNotes.trim() || undefined,
      });
      toast("AI generated communication draft.", "success");
      setShowAIDraftModal(false);
      setAiNotes("");
      await fetchData();
    } catch (err: unknown) {
      toast(errorMessage(err, "Failed to generate AI draft"), "error");
    } finally {
      setIsDraftingAI(false);
    }
  };

  const handleSubmitForApproval = async (commId: string) => {
    try {
      await apiClient.transitionCommunicationStatus(commId, "PENDING_APPROVAL", "Submitted for review");
      toast("Submitted for approval.", "success");
      await fetchData();
    } catch (err: unknown) {
      toast(errorMessage(err, "Failed to submit for approval"), "error");
    }
  };

  const handleApprove = async (commId: string) => {
    try {
      await apiClient.approveClientCommunication(commId);
      toast("Communication approved for sending.", "success");
      await fetchData();
    } catch (err: unknown) {
      toast(errorMessage(err, "Failed to approve communication"), "error");
    }
  };

  const handleSend = async (comm: ClientCommunication) => {
    const confirmed = await confirm({
      title: "Send this communication?",
      message: `Dispatch "${comm.subject}" via ${comm.channel} to ${client?.name}?`,
      confirmLabel: "Send Message",
    });
    if (!confirmed) return;

    try {
      await apiClient.sendClientCommunication(comm.id);
      toast("Communication dispatched.", "success");
      await fetchData();
    } catch (err: unknown) {
      toast(errorMessage(err, "Failed to send communication"), "error");
    }
  };

  const handleDelete = async (commId: string) => {
    const confirmed = await confirm({
      title: "Delete this communication draft?",
      message: "This action cannot be undone.",
      confirmLabel: "Delete Draft",
      danger: true,
    });
    if (!confirmed) return;

    try {
      await apiClient.deleteClientCommunication(commId);
      toast("Draft deleted.", "success");
      await fetchData();
    } catch (err: unknown) {
      toast(errorMessage(err, "Failed to delete draft"), "error");
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) return <ErrorState message={error} onRetry={fetchData} />;
  if (!client) return null;

  return (
    <div className="max-w-4xl mx-auto pb-16 space-y-6">
      <div>
        <Link
          href="/clients"
          className="text-sm text-[var(--text-muted)] hover:text-[var(--foreground)] transition-colors"
        >
          ← Back to Clients
        </Link>
      </div>

      {/* Client Summary Card */}
      <div className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">{client.name}</h1>
            <div className="mt-1">
              <Badge type="status" value={client.status || "ACTIVE"} />
            </div>
          </div>
          <Button variant="danger" onClick={handleArchive}>
            Archive
          </Button>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm mt-4">
          <div>
            <span className="text-xs text-[var(--text-muted)] block">Company</span>
            {client.company_name || "—"}
          </div>
          <div>
            <span className="text-xs text-[var(--text-muted)] block">Email</span>
            {client.email ? (
              <a href={`mailto:${client.email}`} className="text-[var(--primary)] hover:underline">
                {client.email}
              </a>
            ) : (
              "—"
            )}
          </div>
          <div>
            <span className="text-xs text-[var(--text-muted)] block">Phone</span>
            {client.phone || "—"}
          </div>
        </div>
        {client.notes && (
          <div className="mt-4 pt-4 border-t border-[var(--sidebar-border)]">
            <span className="text-xs text-[var(--text-muted)] block mb-1">Notes</span>
            <p className="text-sm text-[var(--text-muted)]">{client.notes}</p>
          </div>
        )}
      </div>

      {/* Projects Card */}
      <div className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Projects ({projects.length})</h2>
          <Button variant="secondary" onClick={() => router.push("/projects/new")}>
            + New Project
          </Button>
        </div>
        {projects.length > 0 ? (
          <div className="space-y-2">
            {projects.map((p: Project) => (
              <Link
                key={p.id}
                href={`/projects/${p.id}`}
                className="flex items-center justify-between p-3 border border-[var(--sidebar-border)] rounded-lg hover:border-[var(--primary)] transition-colors"
              >
                <span className="font-medium text-sm">{p.name}</span>
                <Badge type="status" value={p.status || "ACTIVE"} />
              </Link>
            ))}
          </div>
        ) : (
          <p className="text-sm text-[var(--text-muted)]">No projects for this client yet.</p>
        )}
      </div>

      {/* Communications & Follow-ups Card */}
      <div className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
          <div>
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Icon name="mail" size={20} className="text-[var(--primary)]" />
              Communications & Follow-ups ({communications.length})
            </h2>
            <p className="text-xs text-[var(--text-muted)] mt-0.5">
              Draft messages, request developer approval, and track client delivery follow-ups.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              onClick={() => setShowAIDraftModal(true)}
              className="flex items-center gap-1.5 text-xs"
            >
              <Icon name="sparkles" size={14} />
              AI Draft
            </Button>
            <Button
              variant="primary"
              onClick={() => setShowDraftModal(true)}
              className="flex items-center gap-1.5 text-xs"
            >
              <Icon name="plus" size={14} />
              New Draft
            </Button>
          </div>
        </div>

        {communications.length > 0 ? (
          <div className="space-y-3">
            {communications.map((comm) => (
              <div
                key={comm.id}
                className="p-4 border border-[var(--sidebar-border)] rounded-lg bg-[var(--surface)] hover:border-[var(--primary)]/40 transition-colors"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-medium text-sm text-[var(--foreground)]">{comm.subject}</span>
                    <span className="text-xs px-2 py-0.5 rounded font-medium bg-[var(--surface-hover)] border border-[var(--sidebar-border)] text-[var(--text-muted)]">
                      {comm.channel}
                    </span>
                    <span className="text-xs px-2 py-0.5 rounded font-medium bg-[var(--surface-hover)] border border-[var(--sidebar-border)] text-[var(--text-muted)]">
                      {comm.communication_type.replace(/_/g, " ")}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-xs px-2.5 py-0.5 rounded-full font-semibold ${
                        comm.status === "SENT"
                          ? "bg-purple-500/10 text-purple-400 border border-purple-500/20"
                          : comm.status === "APPROVED"
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : comm.status === "PENDING_APPROVAL"
                          ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                          : "bg-gray-500/10 text-gray-400 border border-gray-500/20"
                      }`}
                    >
                      {comm.status.replace(/_/g, " ")}
                    </span>
                  </div>
                </div>

                <p className="text-xs text-[var(--text-muted)] line-clamp-2 mb-3 whitespace-pre-line font-mono bg-[var(--sidebar-bg)] p-2 rounded border border-[var(--sidebar-border)]">
                  {comm.content}
                </p>

                <div className="flex flex-col sm:flex-row sm:items-center justify-between text-xs text-[var(--text-muted)] gap-2 border-t border-[var(--sidebar-border)] pt-2.5">
                  <div className="flex items-center gap-3 flex-wrap">
                    <span>Created: {new Date(comm.created_at).toLocaleDateString()}</span>
                    {comm.approved_at && (
                      <span className="text-emerald-400">
                        Approved: {new Date(comm.approved_at).toLocaleDateString()}
                      </span>
                    )}
                    {comm.sent_at && (
                      <span className="text-purple-400">
                        Sent: {new Date(comm.sent_at).toLocaleDateString()}
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setViewingComm(comm)}
                      className="text-xs py-1 px-2.5"
                    >
                      View Full
                    </Button>

                    {comm.status === "DRAFT" && (
                      <>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => handleSubmitForApproval(comm.id)}
                          className="text-xs py-1 px-2.5 text-amber-400 border-amber-500/30 hover:bg-amber-500/10"
                        >
                          Submit Approval
                        </Button>
                        <Button
                          variant="danger"
                          size="sm"
                          onClick={() => handleDelete(comm.id)}
                          className="text-xs py-1 px-2"
                        >
                          Delete
                        </Button>
                      </>
                    )}

                    {comm.status === "PENDING_APPROVAL" && (
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => handleApprove(comm.id)}
                        className="text-xs py-1 px-2.5 bg-emerald-600 hover:bg-emerald-500"
                      >
                        Approve
                      </Button>
                    )}

                    {comm.status === "APPROVED" && (
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => handleSend(comm)}
                        className="text-xs py-1 px-2.5 bg-purple-600 hover:bg-purple-500 flex items-center gap-1"
                      >
                        <Icon name="check" size={12} />
                        Send Message
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 border border-dashed border-[var(--sidebar-border)] rounded-lg">
            <Icon name="mail" size={28} className="mx-auto text-[var(--text-muted)] mb-2 opacity-50" />
            <p className="text-sm font-medium text-[var(--foreground)]">No communications logged yet</p>
            <p className="text-xs text-[var(--text-muted)] mt-1 max-w-sm mx-auto">
              Draft a follow-up, status check-in, or delivery update, or generate one with the AI assistant.
            </p>
          </div>
        )}
      </div>

      {/* Modal: View Communication Details */}
      {viewingComm && (
        <Modal
          isOpen={true}
          onClose={() => setViewingComm(null)}
          title={viewingComm.subject}
          size="lg"
        >
          <div className="space-y-4 text-sm">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs px-2 py-0.5 rounded bg-[var(--surface-hover)] border border-[var(--sidebar-border)]">
                Channel: {viewingComm.channel}
              </span>
              <span className="text-xs px-2 py-0.5 rounded bg-[var(--surface-hover)] border border-[var(--sidebar-border)]">
                Type: {viewingComm.communication_type.replace(/_/g, " ")}
              </span>
              <span className="text-xs px-2 py-0.5 rounded bg-[var(--surface-hover)] border border-[var(--sidebar-border)]">
                Status: {viewingComm.status}
              </span>
            </div>

            <div className="p-4 rounded-lg bg-[var(--surface)] border border-[var(--sidebar-border)] whitespace-pre-wrap font-sans text-[var(--foreground)] leading-relaxed">
              {viewingComm.content}
            </div>

            {viewingComm.notes && (
              <div className="text-xs text-[var(--text-muted)]">
                <span className="font-semibold block mb-0.5">Internal Notes:</span>
                {viewingComm.notes}
              </div>
            )}

            <div className="flex justify-end pt-2 border-t border-[var(--sidebar-border)]">
              <Button variant="secondary" onClick={() => setViewingComm(null)}>
                Close
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* Modal: New Manual Draft */}
      <Modal
        isOpen={showDraftModal}
        onClose={() => setShowDraftModal(false)}
        title="Draft Client Communication"
        size="lg"
      >
        <form onSubmit={handleCreateDraft} className="space-y-4">
          <Input
            label="Subject"
            value={draftSubject}
            onChange={(e) => setDraftSubject(e.target.value)}
            placeholder="e.g. Sprint 2 Progress Update & Milestone Review"
            required
          />

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <Select
              label="Channel"
              value={draftChannel}
              onChange={(e) => setDraftChannel(e.target.value)}
              options={[
                { value: "EMAIL", label: "Email" },
                { value: "SLACK", label: "Slack" },
                { value: "WHATSAPP", label: "WhatsApp" },
                { value: "NOTE", label: "Internal Note" },
              ]}
            />

            <Select
              label="Type"
              value={draftType}
              onChange={(e) => setDraftType(e.target.value)}
              options={[
                { value: "FOLLOW_UP", label: "Follow-up" },
                { value: "STATUS_UPDATE", label: "Status Update" },
                { value: "MILESTONE_DELIVERY", label: "Milestone Delivery" },
                { value: "PROPOSAL_OUTREACH", label: "Proposal Outreach" },
                { value: "CHECK_IN", label: "Check-in" },
              ]}
            />

            <Select
              label="Project (optional)"
              value={draftProjectId}
              onChange={(e) => setDraftProjectId(e.target.value)}
              options={[
                { value: "", label: "No Project" },
                ...projects.map((p) => ({ value: p.id, label: p.name })),
              ]}
            />
          </div>

          <div>
            <label className="text-xs font-medium text-[var(--text-muted)] block mb-1">
              Message Content <span className="text-red-400">*</span>
            </label>
            <textarea
              rows={6}
              value={draftContent}
              onChange={(e) => setDraftContent(e.target.value)}
              placeholder="Draft your message here..."
              required
              className="w-full text-sm p-3 rounded-lg border border-[var(--sidebar-border)] bg-[var(--surface)] text-[var(--foreground)] focus:outline-none focus:border-[var(--primary)]"
            />
          </div>

          <Input
            label="Internal Notes (optional)"
            value={draftNotes}
            onChange={(e) => setDraftNotes(e.target.value)}
            placeholder="Context or internal reminders"
          />

          <div className="flex justify-end gap-2 pt-2 border-t border-[var(--sidebar-border)]">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setShowDraftModal(false)}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" disabled={isSubmitting}>
              {isSubmitting ? "Creating..." : "Save Draft"}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Modal: AI Draft Assistant */}
      <Modal
        isOpen={showAIDraftModal}
        onClose={() => setShowAIDraftModal(false)}
        title="AI Communication Drafter"
        size="md"
      >
        <form onSubmit={handleAIDraft} className="space-y-4">
          <p className="text-xs text-[var(--text-muted)]">
            TaskMate AI will compose a polite, contextual outreach draft using project status and client details. Drafts require your approval before sending.
          </p>

          <Select
            label="Communication Type"
            value={aiType}
            onChange={(e) => setAiType(e.target.value)}
            options={[
              { value: "FOLLOW_UP", label: "Follow-up" },
              { value: "STATUS_UPDATE", label: "Status Update" },
              { value: "MILESTONE_DELIVERY", label: "Milestone Delivery" },
              { value: "PROPOSAL_OUTREACH", label: "Proposal Outreach" },
              { value: "CHECK_IN", label: "Periodic Check-in" },
            ]}
          />

          <Select
            label="Tone"
            value={aiTone}
            onChange={(e) => setAiTone(e.target.value)}
            options={[
              { value: "professional", label: "Professional & Direct" },
              { value: "friendly", label: "Warm & Friendly" },
              { value: "urgent", label: "Urgent Action Required" },
              { value: "concise", label: "Brief & Bulleted" },
            ]}
          />

          <Select
            label="Context Project"
            value={aiProjectId}
            onChange={(e) => setAiProjectId(e.target.value)}
            options={[
              { value: "", label: "General Client Context" },
              ...projects.map((p) => ({ value: p.id, label: p.name })),
            ]}
          />

          <div>
            <label className="text-xs font-medium text-[var(--text-muted)] block mb-1">
              Specific details or instructions (optional)
            </label>
            <textarea
              rows={3}
              value={aiNotes}
              onChange={(e) => setAiNotes(e.target.value)}
              placeholder="e.g. Phase 1 testing completed. Ready for review on staging server. Next invoice will follow."
              className="w-full text-sm p-2.5 rounded-lg border border-[var(--sidebar-border)] bg-[var(--surface)] text-[var(--foreground)] focus:outline-none focus:border-[var(--primary)]"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-[var(--sidebar-border)]">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setShowAIDraftModal(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              disabled={isDraftingAI}
              className="flex items-center gap-1.5"
            >
              <Icon name="sparkles" size={14} />
              {isDraftingAI ? "Drafting..." : "Generate Draft"}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
