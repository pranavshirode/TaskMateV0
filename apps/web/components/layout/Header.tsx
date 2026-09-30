"use client";

import { useAuth } from "@/lib/auth-context";

export default function Header() {
  const { user } = useAuth();

  return (
    <header className="h-14 border-b border-[var(--sidebar-border)] bg-[var(--background)] flex items-center justify-between px-6">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 bg-[var(--primary)] rounded-lg flex items-center justify-center">
          <span className="text-white font-bold text-sm">TM</span>
        </div>
        <h1 className="text-lg font-semibold">TaskMate</h1>
      </div>
      <div className="flex items-center gap-4">
        {user ? (
          <span className="text-sm font-medium">{user.name}</span>
        ) : (
          <span className="text-sm text-[var(--text-muted)]">Developer Workspace</span>
        )}
      </div>
    </header>
  );
}
