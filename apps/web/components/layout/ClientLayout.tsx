"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import AuthGuard from "@/components/layout/AuthGuard";
import { WorkspaceUIProvider } from "@/components/layout/WorkspaceUI";
import { FeedbackProvider } from "@/components/ui/Feedback";

export default function ClientLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => setMenuOpen(false), [pathname]);

  const isAuthPage =
    pathname === "/login" ||
    pathname === "/register" ||
    pathname.startsWith("/auth/");
  const isLandingPage = pathname === "/";
  // Chat pages manage their own full-height scrolling.
  const isFullBleed =
    pathname.startsWith("/ai") || pathname.startsWith("/assistant");

  if (isAuthPage || isLandingPage) {
    return (
      <FeedbackProvider>
        <main className="flex-1 overflow-y-auto">{children}</main>
      </FeedbackProvider>
    );
  }

  return (
    <FeedbackProvider>
      <AuthGuard>
        <WorkspaceUIProvider>
          <div className="flex h-screen overflow-hidden">
            <Sidebar className="hidden md:flex" />

            {menuOpen && (
              <div className="fixed inset-0 z-40 md:hidden">
                <div
                  className="absolute inset-0 bg-black/40"
                  onClick={() => setMenuOpen(false)}
                />
                <Sidebar
                  className="animate-pop relative h-full"
                  onNavigate={() => setMenuOpen(false)}
                />
              </div>
            )}

            <div className="flex min-w-0 flex-1 flex-col">
              <Header onOpenMenu={() => setMenuOpen(true)} />
              <main
                className={`flex-1 ${isFullBleed ? "overflow-hidden" : "overflow-y-auto px-4 py-6 md:px-8 md:py-8"}`}
              >
                {children}
              </main>
            </div>
          </div>
        </WorkspaceUIProvider>
      </AuthGuard>
    </FeedbackProvider>
  );
}
