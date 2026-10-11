'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import ErrorState from '@/components/ui/ErrorState';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';

export default function RequirementsIndexPage() {
  const [projects, setProjects] = useState<any[]>([]);
  const [analyses, setAnalyses] = useState<any[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchInitialData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const projRes = await apiClient.listProjects();
      const projList = projRes.items || [];
      setProjects(projList);

      if (projList.length > 0) {
        setSelectedProjectId(projList[0].id);
        const analysisRes = await apiClient.listProjectAnalyses(projList[0].id);
        setAnalyses(analysisRes || []);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load projects');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchInitialData();
  }, []);

  const handleProjectChange = async (projectId: string) => {
    setSelectedProjectId(projectId);
    try {
      setIsLoading(true);
      const res = await apiClient.listProjectAnalyses(projectId);
      setAnalyses(res || []);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto pb-12">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Requirements Analysis</h1>
          <p className="text-sm text-[var(--text-muted)] mt-1">
            AI-assisted client brief breakdown, clarification questions, and task traceability.
          </p>
        </div>
        {selectedProjectId && (
          <Link href={`/projects/${selectedProjectId}/requirements`}>
            <Button variant="primary">+ New Analysis Session</Button>
          </Link>
        )}
      </div>

      {projects.length > 0 ? (
        <div className="mb-6 flex items-center gap-3">
          <label className="text-sm font-medium text-[var(--text-muted)]">Select Project:</label>
          <select
            value={selectedProjectId}
            onChange={(e) => handleProjectChange(e.target.value)}
            className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-lg px-3 py-1.5 text-sm"
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>
      ) : null}

      {isLoading ? (
        <div className="flex justify-center py-16">
          <LoadingSpinner />
        </div>
      ) : error ? (
        <ErrorState message={error} onRetry={fetchInitialData} />
      ) : analyses.length > 0 ? (
        <div className="grid gap-4">
          {analyses.map((a) => (
            <Link
              key={a.id}
              href={`/projects/${a.project_id}/requirements/${a.id}`}
              className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-5 hover:border-[var(--primary)] transition-colors block"
            >
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 mb-2">
                <div className="flex items-center gap-3">
                  <h3 className="font-semibold text-base">{a.title}</h3>
                  <span className="text-xs px-2 py-0.5 rounded-full border border-[var(--sidebar-border)] text-[var(--text-muted)]">
                    v{a.version}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge type="status" value={a.status} />
                </div>
              </div>
              <p className="text-sm text-[var(--text-muted)] line-clamp-2 mb-3">
                {a.brief}
              </p>
              <div className="flex flex-wrap gap-4 text-xs text-[var(--text-muted)] border-t border-[var(--sidebar-border)] pt-3">
                <span>Requirements: <strong className="text-[var(--foreground)]">{a.total_requirements}</strong></span>
                <span>Approved: <strong className="text-green-400">{a.approved_requirements}</strong></span>
                {a.unresolved_questions > 0 && (
                  <span className="text-amber-400 font-medium">
                    ⚠️ {a.unresolved_questions} Questions Unresolved
                  </span>
                )}
                <span>Created: {new Date(a.created_at).toLocaleDateString()}</span>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-12 text-center">
          <p className="text-base text-[var(--text-muted)] mb-4">
            No requirements analyses for this project yet.
          </p>
          {selectedProjectId && (
            <Link href={`/projects/${selectedProjectId}/requirements`}>
              <Button variant="primary">Create First Analysis</Button>
            </Link>
          )}
        </div>
      )}
    </div>
  );
}

