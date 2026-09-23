"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

interface NavItem {
  name: string;
  href: string;
  icon: string;
  disabled?: boolean;
}

const navigation: NavItem[] = [
  { name: "Today", href: "/", icon: "📅" },
  { name: "Tasks", href: "/tasks", icon: "✅" },
  { name: "Projects", href: "/projects", icon: "📁" },
  { name: "Clients", href: "/clients", icon: "👥" },
  { name: "Agent", href: "/agent", icon: "🤖", disabled: true },
  { name: "Settings", href: "/settings", icon: "⚙️" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 border-r border-[var(--sidebar-border)] bg-[var(--sidebar-bg)] flex flex-col">
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.disabled ? "#" : item.href}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive
                  ? "bg-[var(--primary)] text-white"
                  : item.disabled
                    ? "text-[var(--text-muted)] opacity-50 cursor-not-allowed"
                    : "text-[var(--foreground)] hover:bg-[var(--sidebar-border)]"
              }`}
              onClick={item.disabled ? (e) => e.preventDefault() : undefined}
            >
              <span>{item.icon}</span>
              <span>{item.name}</span>
              {item.disabled && (
                <span className="ml-auto text-xs bg-[var(--sidebar-border)] px-1.5 py-0.5 rounded">
                  Soon
                </span>
              )}
            </Link>
          );
        })}
      </nav>
      <div className="p-4 border-t border-[var(--sidebar-border)]">
        <p className="text-xs text-[var(--text-muted)]">
          TaskMate AI v0.1.0
        </p>
      </div>
    </aside>
  );
}
