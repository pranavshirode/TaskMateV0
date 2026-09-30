'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import ErrorState from '@/components/ui/ErrorState';
import EmptyState from '@/components/ui/EmptyState';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import Pagination from '@/components/ui/Pagination';

const STATUSES = ['', 'BACKLOG', 'TODO', 'IN_PROGRESS', 'BLOCKED', 'REVIEW', 'COMPLETED'];
const PRIORITIES = ['', 'LOW', 'MEDIUM', 'HIGH', 'URGENT'];

export default function TasksPage() {
  const router = useRouter();
  const [tasks, setTasks] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');
  const pageSize = 20;

  const fetchTasks = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const params: Record<string, string> = { page: String(page), page_size: String(pageSize), sort_by: sortBy, sort_order: sortOrder };
      if (search) params.search = search;
      if (statusFilter) params.status = statusFilter;
      if (priorityFilter) params.priority = priorityFilter;
      const res = await apiClient.listTasks(params);
      setTasks(res.items);
      setTotal(res.total);
    } catch (err: any) {
      setError(err.message || 'Failed to load tasks');
    } finally {
      setIsLoading(false);
    }
  }, [page, search, statusFilter, priorityFilter, sortBy, sortOrder]);

  useEffect(() => { fetchTasks(); }, [fetchTasks]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchTasks();
  };

  return (
    <div className="max-w-5xl mx-auto pb-12">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Tasks</h1>
        <Button onClick={() => router.push('/tasks/new')}>+ New Task</Button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-6">
        <form onSubmit={handleSearch} className="flex-1 min-w-[200px]">
          <input
            type="text"
            placeholder="Search tasks..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--sidebar-border)] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[var(--primary)] text-[var(--foreground)] placeholder:text-[var(--text-muted)]"
          />
        </form>
        <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }} className="px-3 py-2 bg-[var(--background)] border border-[var(--sidebar-border)] rounded-lg text-sm text-[var(--foreground)]">
          <option value="">All Statuses</option>
          {STATUSES.filter(Boolean).map(s => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
        </select>
        <select value={priorityFilter} onChange={(e) => { setPriorityFilter(e.target.value); setPage(1); }} className="px-3 py-2 bg-[var(--background)] border border-[var(--sidebar-border)] rounded-lg text-sm text-[var(--foreground)]">
          <option value="">All Priorities</option>
          {PRIORITIES.filter(Boolean).map(p => <option key={p} value={p}>{p}</option>)}
        </select>
        <select value={`${sortBy}:${sortOrder}`} onChange={(e) => { const [sb, so] = e.target.value.split(':'); setSortBy(sb); setSortOrder(so); setPage(1); }} className="px-3 py-2 bg-[var(--background)] border border-[var(--sidebar-border)] rounded-lg text-sm text-[var(--foreground)]">
          <option value="created_at:desc">Newest</option>
          <option value="created_at:asc">Oldest</option>
          <option value="due_date:asc">Due Date ↑</option>
          <option value="due_date:desc">Due Date ↓</option>
          <option value="priority:asc">Priority ↑</option>
          <option value="priority:desc">Priority ↓</option>
          <option value="updated_at:desc">Recently Updated</option>
        </select>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12"><LoadingSpinner /></div>
      ) : error ? (
        <ErrorState message={error} onRetry={fetchTasks} />
      ) : tasks.length === 0 ? (
        <EmptyState
          title="No tasks yet"
          description="Create your first task to get started."
          actionLabel="Create Task"
          onAction={() => router.push('/tasks/new')}
        />
      ) : (
        <>
          <div className="border border-[var(--sidebar-border)] rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-[var(--sidebar-bg)]">
                <tr className="text-left text-[var(--text-muted)]">
                  <th className="px-4 py-3 font-medium">Title</th>
                  <th className="px-4 py-3 font-medium hidden md:table-cell">Status</th>
                  <th className="px-4 py-3 font-medium hidden md:table-cell">Priority</th>
                  <th className="px-4 py-3 font-medium hidden lg:table-cell">Due Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--sidebar-border)]">
                {tasks.map((task) => (
                  <tr key={task.id} className="hover:bg-[var(--sidebar-bg)] cursor-pointer transition-colors" onClick={() => router.push(`/tasks/${task.id}`)}>
                    <td className="px-4 py-3">
                      <div className="font-medium">{task.title}</div>
                      <div className="flex gap-1 mt-1 md:hidden">
                        <Badge type="status" value={task.status} />
                        <Badge type="priority" value={task.priority} />
                      </div>
                    </td>
                    <td className="px-4 py-3 hidden md:table-cell"><Badge type="status" value={task.status} /></td>
                    <td className="px-4 py-3 hidden md:table-cell"><Badge type="priority" value={task.priority} /></td>
                    <td className="px-4 py-3 hidden lg:table-cell text-[var(--text-muted)]">{task.due_date || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {total > pageSize && (
            <div className="mt-4">
              <Pagination page={page} pageSize={pageSize} total={total} onPageChange={setPage} />
            </div>
          )}
        </>
      )}
    </div>
  );
}
