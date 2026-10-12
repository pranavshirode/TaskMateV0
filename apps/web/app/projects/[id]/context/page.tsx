'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { apiClient, type Project, type ProjectContextNote } from '@/lib/api-client';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import ErrorState from '@/components/ui/ErrorState';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';

export default function ProjectContextPage() {
  const { id: projectId } = useParams<{ id: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [notes, setNotes] = useState<ProjectContextNote[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // New note form
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [category, setCategory] = useState('DECISION');
  const [isConfirmed, setIsConfirmed] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const [projRes, notesRes] = await Promise.all([
        apiClient.getProject(projectId),
        apiClient.listProjectContextNotes(projectId, false),
      ]);
      setProject(projRes);
      setNotes(notesRes || []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load project context');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [projectId]);

  const handleCreateNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) return;

    try {
      setIsSubmitting(true);
      await apiClient.createProjectContextNote(projectId, {
        title: title.trim(),
        content: content.trim(),
        category,
        is_confirmed: isConfirmed,
      });
      setTitle('');
      setContent('');
      setShowForm(false);
      fetchData();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to create note');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteNote = async (noteId: string) => {
    if (!confirm('Delete this project context note?')) return;
    try {
      await apiClient.deleteProjectContextNote(noteId);
      fetchData();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to delete note');
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
            Project Memory & Decisions: {project?.name}
          </h1>
          <p className="text-sm text-[var(--text-muted)] mt-1">
            Explicitly recorded architectural decisions, constraints, and client preferences remembered across AI sessions.
          </p>
        </div>
        <Button variant={showForm ? 'secondary' : 'primary'} onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Cancel' : '+ Add Memory Note'}
        </Button>
      </div>

      {showForm && (
        <div className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-6 mb-8">
          <h2 className="text-base font-semibold mb-4">Record New Project Memory Note</h2>
          <form onSubmit={handleCreateNote} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-[var(--text-muted)] mb-1">
                Note Title *
              </label>
              <Input
                placeholder="e.g. Database Choice & Sharding Strategy"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-[var(--text-muted)] mb-1">
                  Category
                </label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full bg-[var(--background)] border border-[var(--sidebar-border)] rounded-lg p-2 text-sm text-[var(--foreground)]"
                >
                  <option value="DECISION">Architectural Decision</option>
                  <option value="CONSTRAINT">Technical Constraint</option>
                  <option value="CLIENT_PREFERENCE">Client Preference</option>
                  <option value="ARCHITECTURAL_NOTE">General Note</option>
                </select>
              </div>

              <div className="flex items-center gap-2 pt-6">
                <input
                  type="checkbox"
                  id="confirmed_check"
                  checked={isConfirmed}
                  onChange={(e) => setIsConfirmed(e.target.checked)}
                />
                <label htmlFor="confirmed_check" className="text-xs font-medium text-[var(--foreground)]">
                  Explicitly Confirmed Fact (Unchecked = Unconfirmed Assumption)
                </label>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-[var(--text-muted)] mb-1">
                Content & Rationale *
              </label>
              <textarea
                rows={4}
                className="w-full bg-[var(--background)] border border-[var(--sidebar-border)] rounded-lg p-3 text-sm text-[var(--foreground)]"
                placeholder="Details of the decision, trade-offs evaluated, and instructions for future AI prompts..."
                value={content}
                onChange={(e) => setContent(e.target.value)}
                required
              />
            </div>

            <div className="flex justify-end gap-3">
              <Button type="button" variant="secondary" onClick={() => setShowForm(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" disabled={isSubmitting}>
                {isSubmitting ? 'Saving...' : 'Save Decision'}
              </Button>
            </div>
          </form>
        </div>
      )}

      {notes.length > 0 ? (
        <div className="space-y-4">
          {notes.map((n) => (
            <div
              key={n.id}
              className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-5"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-sm">{n.title}</h3>
                  <span className="text-xs px-2 py-0.5 rounded bg-[var(--sidebar-border)] text-[var(--text-muted)] font-mono">
                    {n.category}
                  </span>
                  <span
                    className={`text-xs px-2 py-0.5 rounded font-medium ${
                      n.is_confirmed ? 'bg-green-500/20 text-green-300' : 'bg-amber-500/20 text-amber-300'
                    }`}
                  >
                    {n.is_confirmed ? '✓ Confirmed' : '⚠️ Unconfirmed'}
                  </span>
                </div>
                <button
                  onClick={() => handleDeleteNote(n.id)}
                  className="text-xs text-red-400 hover:underline"
                >
                  Delete
                </button>
              </div>
              <p className="text-sm text-[var(--text-muted)] whitespace-pre-wrap">{n.content}</p>
              <span className="text-xs text-[var(--text-muted)] block mt-3">
                Recorded {new Date(n.created_at).toLocaleDateString()}
              </span>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-10 text-center">
          <p className="text-sm text-[var(--text-muted)] mb-3">
            No persistent context notes recorded for this project yet.
          </p>
          <Button variant="primary" onClick={() => setShowForm(true)}>
            Record First Project Decision
          </Button>
        </div>
      )}
    </div>
  );
}

