'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api-client';
import Input from '@/components/ui/Input';
import Button from '@/components/ui/Button';

export default function NewClientPage() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [notes, setNotes] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) { setError('Name is required'); return; }
    setError(''); setIsSubmitting(true);
    try {
      const data: Record<string, string> = { name: name.trim() };
      if (companyName.trim()) data.company_name = companyName.trim();
      if (email.trim()) data.email = email.trim();
      if (phone.trim()) data.phone = phone.trim();
      if (notes.trim()) data.notes = notes.trim();
      const client = await apiClient.createClient(data);
      router.push(`/clients/${client.id}`);
    } catch (err: unknown) { setError(err instanceof Error ? err.message : 'Failed to create client'); }
    finally { setIsSubmitting(false); }
  };

  return (
    <div className="max-w-2xl mx-auto pb-12">
      <h1 className="text-2xl font-bold mb-6">Add Client</h1>
      <form onSubmit={handleSubmit} className="space-y-5 bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-6">
        {error && <div className="bg-red-500/10 border border-red-500/30 text-red-500 text-sm rounded-lg p-3">{error}</div>}
        <Input label="Contact Name *" value={name} onChange={(e) => setName(e.target.value)} required placeholder="John Doe" />
        <Input label="Company Name" value={companyName} onChange={(e) => setCompanyName(e.target.value)} placeholder="Acme Inc." />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="john@acme.com" />
          <Input label="Phone" type="tel" value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+1 234 567 8901" />
        </div>
        <div className="flex flex-col gap-1 w-full">
          <label className="text-sm font-medium text-[var(--foreground)]">Notes</label>
          <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={3} placeholder="Any additional notes..."
            className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--sidebar-border)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--primary)] text-[var(--foreground)] placeholder:text-[var(--text-muted)]" />
        </div>
        <div className="flex gap-3 pt-2">
          <Button type="submit" disabled={isSubmitting}>{isSubmitting ? 'Creating...' : 'Add Client'}</Button>
          <Button type="button" variant="secondary" onClick={() => router.back()}>Cancel</Button>
        </div>
      </form>
    </div>
  );
}
