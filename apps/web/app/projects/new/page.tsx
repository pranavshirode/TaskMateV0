'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient, type Client } from '@/lib/api-client';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import Button from '@/components/ui/Button';

const STATUS_OPTIONS = [
  { value: 'PLANNING', label: 'Planning' },
  { value: 'ACTIVE', label: 'Active' },
  { value: 'ON_HOLD', label: 'On Hold' },
];

export default function NewProjectPage() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [clientId, setClientId] = useState('');
  const [description, setDescription] = useState('');
  const [status, setStatus] = useState('PLANNING');
  const [startDate, setStartDate] = useState('');
  const [deadline, setDeadline] = useState('');
  const [clients, setClients] = useState<Client[]>([]);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    apiClient.listClients({ page_size: '100' }).then(res => setClients(res.items || [])).catch(() => {});
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) { setError('Name is required'); return; }
    setError(''); setIsSubmitting(true);
    try {
      const data: Record<string, string> = { name: name.trim(), status };
      if (clientId) data.client_id = clientId;
      if (description.trim()) data.description = description.trim();
      if (startDate) data.start_date = startDate;
      if (deadline) data.deadline = deadline;
      const project = await apiClient.createProject(data);
      router.push(`/projects/${project.id}`);
    } catch (err: unknown) { setError(err instanceof Error ? err.message : 'Failed to create project'); }
    finally { setIsSubmitting(false); }
  };

  return (
    <div className="max-w-2xl mx-auto pb-12">
      <h1 className="text-2xl font-bold mb-6">Create Project</h1>
      <form onSubmit={handleSubmit} className="space-y-5 bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-6">
        {error && <div className="bg-red-500/10 border border-red-500/30 text-red-500 text-sm rounded-lg p-3">{error}</div>}
        <Input label="Project Name *" value={name} onChange={(e) => setName(e.target.value)} required placeholder="My Project" />
        <Select label="Client" value={clientId} onChange={(e) => setClientId(e.target.value)} options={[{ value: '', label: 'None' }, ...clients.map(c => ({ value: c.id, label: c.name }))]} />
        <div className="flex flex-col gap-1 w-full">
          <label className="text-sm font-medium text-[var(--foreground)]">Description</label>
          <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={3} placeholder="Project details..."
            className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--sidebar-border)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--primary)] text-[var(--foreground)] placeholder:text-[var(--text-muted)]" />
        </div>
        <Select label="Status" value={status} onChange={(e) => setStatus(e.target.value)} options={STATUS_OPTIONS} />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input label="Start Date" type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
          <Input label="Deadline" type="date" value={deadline} onChange={(e) => setDeadline(e.target.value)} />
        </div>
        <div className="flex gap-3 pt-2">
          <Button type="submit" disabled={isSubmitting}>{isSubmitting ? 'Creating...' : 'Create Project'}</Button>
          <Button type="button" variant="secondary" onClick={() => router.back()}>Cancel</Button>
        </div>
      </form>
    </div>
  );
}
