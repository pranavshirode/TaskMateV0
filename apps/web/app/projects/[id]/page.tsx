'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import ErrorState from '@/components/ui/ErrorState';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [project, setProject] = useState<any>(null);
  const [repos, setRepos] = useState<any[]>([]);
  const [tasks, setTasks] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showRepoForm, setShowRepoForm] = useState(false);
  const [repoName, setRepoName] = useState('');
  const [repoUrl, setRepoUrl] = useState('');

  const fetchData = async () => {
    try {
      setIsLoading(true); setError(null);
      const [proj, repoList, taskList] = await Promise.all([
        apiClient.getProject(id),
        apiClient.listProjectRepos(id),
        apiClient.listTasks({ project_id: id, page_size: '10', sort_by: 'updated_at', sort_order: 'desc' }),
      ]);
      setProject(proj); setRepos(repoList || []); setTasks(taskList.items || []);
    } catch (err: any) { setError(err.message); }
    finally { setIsLoading(false); }
  };

  useEffect(() => { fetchData(); }, [id]);

  const handleAddRepo = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoName.trim() || !repoUrl.trim()) return;
    try {
      await apiClient.createRepo(id, { name: repoName.trim(), url: repoUrl.trim(), provider: 'GITHUB', default_branch: 'main' });
      setRepoName(''); setRepoUrl(''); setShowRepoForm(false);
      fetchData();
    } catch (err: any) { alert(err.message); }
  };

  const handleArchive = async () => {
    if (!confirm('Archive this project?')) return;
    try { await apiClient.archiveProject(id); router.push('/projects'); }
    catch (err: any) { alert(err.message); }
  };

  if (isLoading) return <div className="flex justify-center py-12"><LoadingSpinner /></div>;
  if (error) return <ErrorState message={error} onRetry={fetchData} />;
  if (!project) return null;

  const ts = project.task_summary || {};

  return (
    <div className="max-w-3xl mx-auto pb-12">
      <div className="mb-4">
        <Link href="/projects" className="text-sm text-[var(--text-muted)] hover:text-[var(--foreground)]">← Back to Projects</Link>
      </div>

      <div className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-6 mb-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-xl font-bold">{project.name}</h1>
            <Badge type="status" value={project.status} />
          </div>
          <Button variant="danger" onClick={handleArchive}>Archive</Button>
        </div>
        {project.description && <p className="text-[var(--text-muted)] mb-4">{project.description}</p>}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div><span className="text-xs text-[var(--text-muted)] block">Client</span>{project.client_id ? <Link href={`/clients/${project.client_id}`} className="text-[var(--primary)] hover:underline">{project.client_id.substring(0,8)}...</Link> : '—'}</div>
          <div><span className="text-xs text-[var(--text-muted)] block">Start Date</span>{project.start_date || '—'}</div>
          <div><span className="text-xs text-[var(--text-muted)] block">Deadline</span>{project.deadline || '—'}</div>
          <div><span className="text-xs text-[var(--text-muted)] block">Created</span>{new Date(project.created_at).toLocaleDateString()}</div>
        </div>
      </div>

      {/* Task Summary */}
      <div className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Task Summary</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-3 border border-[var(--sidebar-border)] rounded-lg">
            <div className="text-2xl font-bold">{ts.total ?? 0}</div><div className="text-xs text-[var(--text-muted)]">Total</div>
          </div>
          <div className="text-center p-3 border border-green-500/30 rounded-lg">
            <div className="text-2xl font-bold text-green-400">{ts.completed ?? 0}</div><div className="text-xs text-[var(--text-muted)]">Completed</div>
          </div>
          <div className="text-center p-3 border border-yellow-500/30 rounded-lg">
            <div className="text-2xl font-bold text-yellow-400">{ts.in_progress ?? 0}</div><div className="text-xs text-[var(--text-muted)]">In Progress</div>
          </div>
          <div className="text-center p-3 border border-red-500/30 rounded-lg">
            <div className="text-2xl font-bold text-red-400">{ts.overdue ?? 0}</div><div className="text-xs text-[var(--text-muted)]">Overdue</div>
          </div>
        </div>
      </div>

      {/* Repositories */}
      <div className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Repositories</h2>
          <Button variant="secondary" onClick={() => setShowRepoForm(!showRepoForm)}>{showRepoForm ? 'Cancel' : '+ Add Repo'}</Button>
        </div>
        {showRepoForm && (
          <form onSubmit={handleAddRepo} className="flex gap-3 mb-4">
            <Input placeholder="Repo name" value={repoName} onChange={(e) => setRepoName(e.target.value)} required />
            <Input placeholder="https://github.com/..." value={repoUrl} onChange={(e) => setRepoUrl(e.target.value)} required />
            <Button type="submit">Add</Button>
          </form>
        )}
        {repos.length > 0 ? (
          <div className="space-y-2">
            {repos.map((r: any) => (
              <div key={r.id} className="flex items-center justify-between p-3 border border-[var(--sidebar-border)] rounded-lg">
                <div><div className="font-medium text-sm">{r.name}</div><a href={r.url} target="_blank" rel="noreferrer" className="text-xs text-[var(--primary)] hover:underline">{r.url}</a></div>
                <span className="text-xs text-[var(--text-muted)]">{r.default_branch}</span>
              </div>
            ))}
          </div>
        ) : <p className="text-sm text-[var(--text-muted)]">No repositories linked yet.</p>}
      </div>

      {/* Recent Tasks */}
      <div className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-6">
        <h2 className="text-lg font-semibold mb-4">Recent Tasks</h2>
        {tasks.length > 0 ? (
          <div className="space-y-2">
            {tasks.map((task: any) => (
              <Link key={task.id} href={`/tasks/${task.id}`} className="flex items-center justify-between p-3 border border-[var(--sidebar-border)] rounded-lg hover:border-[var(--primary)] transition-colors">
                <span className="font-medium text-sm">{task.title}</span>
                <div className="flex gap-2"><Badge type="status" value={task.status} /><Badge type="priority" value={task.priority} /></div>
              </Link>
            ))}
          </div>
        ) : <p className="text-sm text-[var(--text-muted)]">No tasks for this project yet.</p>}
      </div>
    </div>
  );
}
