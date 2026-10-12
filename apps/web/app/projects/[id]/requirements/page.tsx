'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { apiClient, type Project, type RequirementsAnalysis } from '@/lib/api-client';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import ErrorState from '@/components/ui/ErrorState';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';

export default function ProjectRequirementsPage() {
  const { id: projectId } = useParams<{ id: string }>();
  const router = useRouter();

  const [project, setProject] = useState<Project | null>(null);
  const [analyses, setAnalyses] = useState<RequirementsAnalysis[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form states
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState('');
  const [brief, setBrief] = useState('');
  const [desiredOutcome, setDesiredOutcome] = useState('');
  const [constraints, setConstraints] = useState('');
  const [deadline, setDeadline] = useState('');

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
      setError(err instanceof Error ? err.message : 'Failed to load project requirements');
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
      alert(err instanceof Error ? err.message : 'Failed to analyze brief');
      setIsSubmitting(false);
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
          ← Back to {project?.name || 'Project'}
        </Link>
      </div>

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            Requirements Analysis: {project?.name}
          </h1>
          <p className="text-sm text-[var(--text-muted)] mt-1">
            Transform client briefs into reviewable functional requirements and actionable tasks.
          </p>
        </div>
        <Button
          variant={showForm ? 'secondary' : 'primary'}
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? 'Cancel' : '+ New Brief Submission'}
        </Button>
      </div>

      {showForm && (
        <div className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-6 mb-8 shadow-sm">
          <h2 className="text-lg font-semibold mb-4">Submit Client Brief for AI Analysis</h2>
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
                {isSubmitting ? 'Analyzing Brief with AI...' : 'Analyze Brief'}
              </Button>
            </div>
          </form>
        </div>
      )}

      {/* Existing Sessions List */}
      <h2 className="text-lg font-semibold mb-4">Saved Requirements Sessions</h2>
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
                  <span>Requirements: {a.total_requirements || a.requirements?.length || 0}</span>
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

