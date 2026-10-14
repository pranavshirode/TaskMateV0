"use client";

import Link from "next/link";
import Icon from "@/components/ui/Icon";
import { useWorkspaceUI } from "./WorkspaceUI";

export default function Header({ onOpenMenu }: { onOpenMenu?: () => void }) {
  const { openPalette, openQuickAdd } = useWorkspaceUI();

  return (
    <header className="flex h-14 shrink-0 items-center gap-3 border-b border-[var(--sidebar-border)] bg-[var(--sidebar-bg)] px-4 md:px-6">
      <button
        onClick={onOpenMenu}
        aria-label="Open menu"
        className="rounded-md p-1.5 text-[var(--text-muted)] hover:bg-[var(--surface-hover)] md:hidden"
      >
        <Icon name="menu" />
      </button>

      <button
        onClick={openPalette}
        className="flex h-9 w-full max-w-md items-center gap-2 rounded-lg border border-[var(--sidebar-border)] bg-[var(--background)] px-3 text-sm text-[var(--text-muted)] transition-colors hover:border-[color-mix(in_srgb,var(--primary)_40%,transparent)]"
      >
        <Icon name="search" size={16} />
        <span className="flex-1 truncate text-left">Search or jump to...</span>
        <span className="kbd hidden sm:inline-flex">Ctrl K</span>
      </button>

      <div className="ml-auto flex items-center gap-2">
        <Link
          href="/ai"
          className="hidden items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium text-[var(--foreground)] hover:bg-[var(--surface-hover)] sm:inline-flex"
        >
          <Icon name="sparkles" size={16} className="text-[var(--primary)]" />
          Ask AI
        </Link>
        <button
          onClick={() => openQuickAdd()}
          title="New task (C)"
          className="inline-flex items-center gap-1.5 rounded-lg bg-[var(--primary)] px-3 py-2 text-sm font-medium text-white shadow-sm hover:bg-[var(--primary-hover)]"
        >
          <Icon name="plus" size={16} />
          <span className="hidden sm:inline">New task</span>
        </button>
      </div>
    </header>
  );
}
