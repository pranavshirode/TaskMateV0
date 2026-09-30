'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api-client';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import Button from '@/components/ui/Button';

const STATUS_OPTIONS = [
  { value: 'BACKLOG', label: 'Backlog' },
  { value: 'TODO', label: 'To Do' },
  { value: 'IN_PROGRESS', label: 'In Progress' },
  { value: 'REVIEW', label: 'Review' },
];

const PRIORITY_OPTIONS = [
  { value: 'LOW', label: 'Low' },
  { value: 'MEDIUM', label: 'Medium' },
  { value: 'HIGH', label: 'High' },
  { value: 'URGENT', label: 'Urgent' },
];

export default function NewTaskPage() {
  const router = useRouter();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [projectId, setProjectId] = useState('');
  const [clientId, setClientId] = useState('');
  const [status, setStatus] = useState('TODO');
  const [priority, setPriority] = useState('MEDIUM');
  const [dueDate, setDueDate] = useState('');
  const [estimatedMinutes, setEstimatedMinutes] = useState('');
  const [labelsInput, setLabelsInput] = useState('');
  const [projects, setProjects] = useState<any[]>([]);
  const [clients, setClients] = useState<any[]>([]);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const [projRes, clientRes] = await Promise.all([
          apiClient.listProjects({ page_size: '100' }),
          apiClient.listClients({ page_size: '100' }),
        ]);
        setProjects(projRes.items || []);
        setClients(clientRes.items || []);
      } catch (e) { /* ignore */ }
    };
    load();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) { setError('Title is required'); return; }
    setError('');
    setIsSubmitting(true);
    try {
      const data: any = { title: title.trim(), status, priority };
      if (description.trim()) data.description = description.trim();
      if (projectId) data.project_id = projectId;
      if (clientId) data.client_id = clientId;
      if (dueDate) data.due_date = dueDate;
      if (estimatedMinutes) data.estimated_minutes = parseInt(estimatedMinutes, 10);
      if (labelsInput.trim()) data.labels = labelsInput.split(',').map((l: string) => l.trim()).filter(Boolean);

      const task = await apiClient.createTask(data);
      router.push(`/tasks/${task.id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to create task');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto pb-12">
      <h1 className="text-2xl font-bold mb-6">Create Task</h1>
      <form onSubmit={handleSubmit} className="space-y-5 bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-6">
        {error && <div className="bg-red-500/10 border border-red-500/30 text-red-500 text-sm rounded-lg p-3">{error}</div>}

        <Input label="Title *" value={title} onChange={(e) => setTitle(e.target.value)} required placeholder="What needs to be done?" />

        <div className="flex flex-col gap-1 w-full">
          <label className="text-sm font-medium text-[var(--foreground)]">Description</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            placeholder="Add details..."
            className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--sidebar-border)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--primary)] text-[var(--foreground)] placeholder:text-[var(--text-muted)]"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Select label="Project" value={projectId} onChange={(e) => setProjectId(e.target.value)} options={[{ value: '', label: 'None' }, ...projects.map(p => ({ value: p.id, label: p.name }))]} />
          <Select label="Client" value={clientId} onChange={(e) => setClientId(e.target.value)} options={[{ value: '', label: 'None' }, ...clients.map(c => ({ value: c.id, label: c.name }))]} />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Select label="Status" value={status} onChange={(e) => setStatus(e.target.value)} options={STATUS_OPTIONS} />
          <Select label="Priority" value={priority} onChange={(e) => setPriority(e.target.value)} options={PRIORITY_OPTIONS} />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input label="Due Date" type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
          <Input label="Estimated Effort (minutes)" type="number" min="0" value={estimatedMinutes} onChange={(e) => setEstimatedMinutes(e.target.value)} placeholder="e.g. 120" />
        </div>

        <Input label="Labels" value={labelsInput} onChange={(e) => setLabelsInput(e.target.value)} placeholder="bug, frontend, urgent (comma-separated)" />

        <div className="flex gap-3 pt-2">
          <Button type="submit" disabled={isSubmitting}>{isSubmitting ? 'Creating...' : 'Create Task'}</Button>
          <Button type="button" variant="secondary" onClick={() => router.back()}>Cancel</Button>
        </div>
      </form>
    </div>
  );
}
