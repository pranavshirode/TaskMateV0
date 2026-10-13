"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { apiClient, type Client, type Project } from "@/lib/api-client";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import ErrorState from "@/components/ui/ErrorState";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";

export default function ClientDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [client, setClient] = useState<Client | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const [clientData, projData] = await Promise.all([
        apiClient.getClient(id),
        apiClient.listProjects({ client_id: id, page_size: "50" }),
      ]);
      setClient(clientData);
      setProjects(projData.items || []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [id]);

  const handleArchive = async () => {
    if (!confirm("Archive this client?")) return;
    try {
      await apiClient.archiveClient(id);
      router.push("/clients");
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to archive client");
    }
  };

  if (isLoading)
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner />
      </div>
    );
  if (error) return <ErrorState message={error} onRetry={fetchData} />;
  if (!client) return null;

  return (
    <div className="max-w-3xl mx-auto pb-12">
      <div className="mb-4">
        <Link
          href="/clients"
          className="text-sm text-[var(--text-muted)] hover:text-[var(--foreground)]"
        >
          ← Back to Clients
        </Link>
      </div>

      <div className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-6 mb-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-xl font-bold">{client.name}</h1>
            <Badge type="status" value={client.status} />
          </div>
          <Button variant="danger" onClick={handleArchive}>
            Archive
          </Button>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm mt-4">
          <div>
            <span className="text-xs text-[var(--text-muted)] block">
              Company
            </span>
            {client.company_name || "—"}
          </div>
          <div>
            <span className="text-xs text-[var(--text-muted)] block">
              Email
            </span>
            {client.email ? (
              <a
                href={`mailto:${client.email}`}
                className="text-[var(--primary)] hover:underline"
              >
                {client.email}
              </a>
            ) : (
              "—"
            )}
          </div>
          <div>
            <span className="text-xs text-[var(--text-muted)] block">
              Phone
            </span>
            {client.phone || "—"}
          </div>
        </div>
        {client.notes && (
          <div className="mt-4 pt-4 border-t border-[var(--sidebar-border)]">
            <span className="text-xs text-[var(--text-muted)] block mb-1">
              Notes
            </span>
            <p className="text-sm">{client.notes}</p>
          </div>
        )}
      </div>

      {/* Projects */}
      <div className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">
            Projects ({projects.length})
          </h2>
          <Button
            variant="secondary"
            onClick={() => router.push("/projects/new")}
          >
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
                <Badge type="status" value={p.status} />
              </Link>
            ))}
          </div>
        ) : (
          <p className="text-sm text-[var(--text-muted)]">
            No projects for this client yet.
          </p>
        )}
      </div>
    </div>
  );
}
