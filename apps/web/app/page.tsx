'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/lib/auth-context';
import { apiClient, type DashboardToday, type Task, type Project } from '@/lib/api-client';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import ErrorState from '@/components/ui/ErrorState';
import Badge from '@/components/ui/Badge';
import Link from 'next/link';

export default function DashboardPage() {
  const { user } = useAuth();
  const [data, setData] = useState<DashboardToday | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const res = await apiClient.getDashboardToday();
      setData(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-full">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchDashboard} />;
  }

  if (!data) {
    return null;
  }

  const TaskCard = ({ task }: { task: Task }) => (
    <Link
      href={`/tasks/${task.id}`}
      className="block p-3 border border-[var(--sidebar-border)] rounded-lg hover:border-[var(--primary)] transition-colors"
    >
      <div className="font-medium mb-1 text-sm">{task.title}</div>
      <div className="flex gap-2 flex-wrap">
        <Badge type="status" value={task.status} />
        <Badge type="priority" value={task.priority} />
        {task.due_date && (
          <span className="text-xs text-[var(--text-muted)]">Due: {task.due_date}</span>
        )}
      </div>
    </Link>
  );

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-12">
      <header className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight mb-2">
          {getGreeting()}, {user?.name || 'Developer'}
        </h1>
        <p className="text-[var(--text-muted)]">
          Here&apos;s what needs your attention today.
        </p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Due Today */}
        <section className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <span>📅</span> Due Today
            {(data.due_today?.length || 0) > 0 && (
              <span className="text-xs bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded-full">{data.due_today.length}</span>
            )}
          </h2>
          {(data.due_today?.length || 0) > 0 ? (
            <div className="space-y-3">
              {data.due_today.map((task: Task) => (
                <TaskCard key={task.id} task={task} />
              ))}
            </div>
          ) : (
            <p className="text-sm text-[var(--text-muted)]">No tasks due today. Enjoy your day!</p>
          )}
        </section>

        {/* Overdue */}
        <section className="bg-[var(--sidebar-bg)] border border-red-500/30 rounded-xl p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2 text-red-400">
            <span>⚠️</span> Overdue
            {(data.overdue?.length || 0) > 0 && (
              <span className="text-xs bg-red-500/20 text-red-400 px-2 py-0.5 rounded-full">{data.overdue.length}</span>
            )}
          </h2>
          {(data.overdue?.length || 0) > 0 ? (
            <div className="space-y-3">
              {data.overdue.map((task: Task) => (
                <TaskCard key={task.id} task={task} />
              ))}
            </div>
          ) : (
            <p className="text-sm text-[var(--text-muted)]">No overdue tasks. Great job!</p>
          )}
        </section>

        {/* High Priority */}
        <section className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2 text-orange-400">
            <span>🔥</span> High Priority
            {(data.high_priority?.length || 0) > 0 && (
              <span className="text-xs bg-orange-500/20 text-orange-400 px-2 py-0.5 rounded-full">{data.high_priority.length}</span>
            )}
          </h2>
          {(data.high_priority?.length || 0) > 0 ? (
            <div className="space-y-3">
              {data.high_priority.map((task: Task) => (
                <TaskCard key={task.id} task={task} />
              ))}
            </div>
          ) : (
            <p className="text-sm text-[var(--text-muted)]">No urgent or high priority tasks.</p>
          )}
        </section>

        {/* Active Projects */}
        <section className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <span>📁</span> Active Projects
          </h2>
          {(data.active_projects?.length || 0) > 0 ? (
            <div className="space-y-3">
              {data.active_projects.map((project: Project) => (
                <Link
                  key={project.id}
                  href={`/projects/${project.id}`}
                  className="block p-3 border border-[var(--sidebar-border)] rounded-lg hover:border-[var(--primary)] transition-colors"
                >
                  <div className="font-medium text-sm">{project.name}</div>
                  {project.deadline && (
                    <div className="text-xs text-[var(--text-muted)] mt-1">Deadline: {project.deadline}</div>
                  )}
                </Link>
              ))}
            </div>
          ) : (
            <p className="text-sm text-[var(--text-muted)]">No active projects yet.</p>
          )}
        </section>
      </div>

      {/* Recently Updated */}
      <section className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <span>🕐</span> Recently Updated
        </h2>
        {(data.recently_updated?.length || 0) > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {data.recently_updated.slice(0, 6).map((task: Task) => (
              <TaskCard key={task.id} task={task} />
            ))}
          </div>
        ) : (
          <p className="text-sm text-[var(--text-muted)]">No recent activity.</p>
        )}
      </section>

      {/* Sprint 4 Requirements & Workspace Intelligence */}
      <section className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <span>📋</span> Requirements & Workspace Intelligence
          </h2>
          <Link href="/requirements" className="text-xs text-[var(--primary)] hover:underline">
            View All Requirements →
          </Link>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link href="/requirements" className="p-4 rounded-lg border border-[var(--sidebar-border)] hover:border-[var(--primary)] transition-colors">
            <div className="font-semibold text-sm mb-1">Requirements Analysis</div>
            <p className="text-xs text-[var(--text-muted)]">Analyze client briefs, answer clarifying questions, and trace tasks.</p>
          </Link>
          <Link href="/projects" className="p-4 rounded-lg border border-[var(--sidebar-border)] hover:border-[var(--primary)] transition-colors">
            <div className="font-semibold text-sm mb-1">Project Decisions & Memory</div>
            <p className="text-xs text-[var(--text-muted)]">Persist confirmed architectural decisions and constraints across AI sessions.</p>
          </Link>
          <Link href="/projects" className="p-4 rounded-lg border border-[var(--sidebar-border)] hover:border-[var(--primary)] transition-colors">
            <div className="font-semibold text-sm mb-1">Client Requests & Scope Impact</div>
            <p className="text-xs text-[var(--text-muted)]">Assess incoming client requests against approved requirements.</p>
          </Link>
        </div>
      </section>
    </div>
  );
}
