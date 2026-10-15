"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { initials } from "@/lib/format";
import Icon from "@/components/ui/Icon";
import { NAV_SECTIONS, isNavActive } from "./nav";

export default function Sidebar({
  onNavigate,
  className = "",
}: {
  onNavigate?: () => void;
  className?: string;
}) {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside
      className={`flex w-60 flex-col border-r border-[var(--sidebar-border)] bg-[var(--nav-bg)] ${className}`}
    >
      <Link
        href="/dashboard"
        onClick={onNavigate}
        className="flex h-14 items-center gap-2.5 border-b border-[var(--sidebar-border)] px-5"
      >
        <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-[var(--primary)] text-white">
          <Icon name="check" size={16} strokeWidth={2.5} />
        </span>
        <span className="text-[15px] font-semibold tracking-tight">
          TaskMate
        </span>
      </Link>

      <nav className="flex-1 overflow-y-auto px-3 py-4" aria-label="Main">
        {NAV_SECTIONS.map((section) => (
          <div key={section.title} className="mb-5">
            <p className="mb-1.5 px-3 text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
              {section.title}
            </p>
            <div className="space-y-0.5">
              {section.items.map((item) => {
                const isActive = isNavActive(pathname, item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={onNavigate}
                    aria-current={isActive ? "page" : undefined}
                    className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                      isActive
                        ? "bg-[var(--primary-soft)] font-medium text-[var(--primary)]"
                        : "text-[color-mix(in_srgb,var(--foreground)_80%,transparent)] hover:bg-[var(--surface-hover)] hover:text-[var(--foreground)]"
                    }`}
                  >
                    <Icon
                      name={item.icon}
                      size={17}
                      className={isActive ? "" : "text-[var(--text-muted)]"}
                    />
                    <span>{item.name}</span>
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      <div className="border-t border-[var(--sidebar-border)] p-3">
        {user && (
          <div className="flex items-center gap-3 rounded-lg px-2 py-2">
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--primary-soft)] text-xs font-semibold text-[var(--primary)]">
              {initials(user.name)}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">{user.name}</p>
              <p className="truncate text-xs text-[var(--text-muted)]">
                {user.email}
              </p>
            </div>
            <button
              onClick={logout}
              title="Log out"
              aria-label="Log out"
              className="rounded-md p-1.5 text-[var(--text-muted)] hover:bg-[var(--surface-hover)] hover:text-[var(--foreground)]"
            >
              <Icon name="logout" size={16} />
            </button>
          </div>
        )}
        <p className="px-2 pt-1 text-[11px] text-[var(--text-muted)]">
          TaskMate AI v1.0.0
        </p>
      </div>
    </aside>
  );
}
