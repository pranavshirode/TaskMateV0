'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient, type Client } from '@/lib/api-client';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import ErrorState from '@/components/ui/ErrorState';
import EmptyState from '@/components/ui/EmptyState';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import Pagination from '@/components/ui/Pagination';

export default function ClientsPage() {
  const router = useRouter();
  const [clients, setClients] = useState<Client[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const pageSize = 20;

  const fetchClients = useCallback(async () => {
    try {
      setIsLoading(true); setError(null);
      const params: Record<string, string> = { page: String(page), page_size: String(pageSize) };
      if (search) params.search = search;
      if (statusFilter) params.status = statusFilter;
      const res = await apiClient.listClients(params);
      setClients(res.items); setTotal(res.total);
    } catch (err: unknown) { setError(err instanceof Error ? err.message : 'Unknown error'); }
    finally { setIsLoading(false); }
  }, [page, search, statusFilter]);

  useEffect(() => { fetchClients(); }, [fetchClients]);

  return (
    <div className="max-w-5xl mx-auto pb-12">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Clients</h1>
        <Button onClick={() => router.push('/clients/new')}>+ New Client</Button>
      </div>

      <div className="flex flex-wrap gap-3 mb-6">
        <input type="text" placeholder="Search clients..." value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          className="flex-1 min-w-[200px] px-3 py-2 bg-[var(--background)] border border-[var(--sidebar-border)] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[var(--primary)] text-[var(--foreground)] placeholder:text-[var(--text-muted)]" />
        <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          className="px-3 py-2 bg-[var(--background)] border border-[var(--sidebar-border)] rounded-lg text-sm text-[var(--foreground)]">
          <option value="">All</option>
          <option value="ACTIVE">Active</option>
          <option value="ARCHIVED">Archived</option>
        </select>
      </div>

      {isLoading ? <div className="flex justify-center py-12"><LoadingSpinner /></div>
       : error ? <ErrorState message={error} onRetry={fetchClients} />
       : clients.length === 0 ? <EmptyState title="No clients yet" description="Add your first client to start tracking projects." actionLabel="Add Client" onAction={() => router.push('/clients/new')} />
       : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {clients.map((client) => (
              <div key={client.id} onClick={() => router.push(`/clients/${client.id}`)}
                className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-5 cursor-pointer hover:border-[var(--primary)] transition-colors">
                <div className="flex items-start justify-between mb-1">
                  <h3 className="font-semibold">{client.name}</h3>
                  <Badge type="status" value={client.status} />
                </div>
                {client.company_name && <p className="text-sm text-[var(--text-muted)]">{client.company_name}</p>}
                {client.email && <p className="text-xs text-[var(--text-muted)] mt-1">{client.email}</p>}
              </div>
            ))}
          </div>
          {total > pageSize && <div className="mt-4"><Pagination page={page} pageSize={pageSize} total={total} onPageChange={setPage} /></div>}
        </>
      )}
    </div>
  );
}
