'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api-client';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import ErrorState from '@/components/ui/ErrorState';
import EmptyState from '@/components/ui/EmptyState';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import Pagination from '@/components/ui/Pagination';

const PROJECT_STATUSES = ['', 'PLANNING', 'ACTIVE', 'ON_HOLD', 'COMPLETED', 'ARCHIVED'];

export default function ProjectsPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const pageSize = 20;

  const fetchProjects = useCallback(async () => {
    try {
      setIsLoading(true); setError(null);
      const params: Record<string, string> = { page: String(page), page_size: String(pageSize) };
      if (search) params.search = search;
      if (statusFilter) params.status = statusFilter;
      const res = await apiClient.listProjects(params);
      setProjects(res.items); setTotal(res.total);
    } catch (err: any) { setError(err.message); }
    finally { setIsLoading(false); }
  }, [page, search, statusFilter]);

  useEffect(() => { fetchProjects(); }, [fetchProjects]);

  return (
    <div className="max-w-5xl mx-auto pb-12">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Projects</h1>
        <Button onClick={() => router.push('/projects/new')}>+ New Project</Button>
      </div>

      <div className="flex flex-wrap gap-3 mb-6">
        <input type="text" placeholder="Search projects..." value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          className="flex-1 min-w-[200px] px-3 py-2 bg-[var(--background)] border border-[var(--sidebar-border)] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[var(--primary)] text-[var(--foreground)] placeholder:text-[var(--text-muted)]" />
        <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          className="px-3 py-2 bg-[var(--background)] border border-[var(--sidebar-border)] rounded-lg text-sm text-[var(--foreground)]">
          <option value="">All Statuses</option>
          {PROJECT_STATUSES.filter(Boolean).map(s => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
        </select>
      </div>

      {isLoading ? <div className="flex justify-center py-12"><LoadingSpinner /></div>
       : error ? <ErrorState message={error} onRetry={fetchProjects} />
       : projects.length === 0 ? <EmptyState title="No projects yet" description="Create your first project to get started." actionLabel="Create Project" onAction={() => router.push('/projects/new')} />
       : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {projects.map((project) => (
              <div key={project.id} onClick={() => router.push(`/projects/${project.id}`)}
                className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-5 cursor-pointer hover:border-[var(--primary)] transition-colors">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-semibold">{project.name}</h3>
                  <Badge type="status" value={project.status} />
                </div>
                {project.description && <p className="text-sm text-[var(--text-muted)] line-clamp-2 mb-2">{project.description}</p>}
                <div className="flex gap-4 text-xs text-[var(--text-muted)]">
                  {project.deadline && <span>Deadline: {project.deadline}</span>}
                  <span>Created: {new Date(project.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>
          {total > pageSize && <div className="mt-4"><Pagination page={page} pageSize={pageSize} total={total} onPageChange={setPage} /></div>}
        </>
      )}
    </div>
  );
}
