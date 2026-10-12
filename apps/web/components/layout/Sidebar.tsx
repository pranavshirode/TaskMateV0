"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

interface NavItem {
  name: string;
  href: string;
  icon: string;
}

const navigation: NavItem[] = [
  { name: "Today", href: "/", icon: "📅" },
  { name: "AI Assistant", href: "/ai", icon: "✨" },
  { name: "Tasks", href: "/tasks", icon: "✅" },
  { name: "Requirements", href: "/requirements", icon: "📋" },
  { name: "Projects", href: "/projects", icon: "📁" },
  { name: "Clients", href: "/clients", icon: "👥" },
  { name: "Repositories", href: "/repositories", icon: "📦" },
  { name: "Settings", href: "/settings", icon: "⚙️" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside className="w-56 border-r border-[var(--sidebar-border)] bg-[var(--sidebar-bg)] flex flex-col">
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navigation.map((item) => {
          const isActive = pathname === item.href || (pathname.startsWith(item.href) && item.href !== '/');
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive
                  ? "bg-[var(--primary)] text-white"
                  : "text-[var(--foreground)] hover:bg-[var(--sidebar-border)]"
              }`}
            >
              <span>{item.icon}</span>
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>
      <div className="p-4 border-t border-[var(--sidebar-border)] flex flex-col gap-2">
        {user && (
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">{user.name}</span>
            <button onClick={logout} className="text-xs text-[var(--text-muted)] hover:text-[var(--foreground)]">Logout</button>
          </div>
        )}
        <p className="text-xs text-[var(--text-muted)]">
          TaskMate AI v1.0.0
        </p>
      </div>
    </aside>
  );
}
