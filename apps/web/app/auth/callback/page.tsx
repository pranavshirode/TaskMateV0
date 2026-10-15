"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import Link from "next/link";
import AuthShell from "@/components/layout/AuthShell";

function CallbackHandler() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { setSessionToken } = useAuth();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = searchParams.get("token");
    const err = searchParams.get("error");

    if (err) {
      setError(err);
      return;
    }

    if (!token) {
      setError("No authentication token provided.");
      return;
    }

    let isCancelled = false;

    setSessionToken(token)
      .then(() => {
        if (!isCancelled) {
          router.replace("/dashboard");
        }
      })
      .catch((e) => {
        if (!isCancelled) {
          setError(
            e instanceof Error ? e.message : "Failed to establish session."
          );
        }
      });

    return () => {
      isCancelled = true;
    };
  }, [searchParams, router, setSessionToken]);

  if (error) {
    return (
      <AuthShell
        title="Authentication Failed"
        subtitle="We couldn't sign you in with Google."
      >
        <div className="space-y-4">
          <div
            role="alert"
            className="rounded-lg border border-[color-mix(in_srgb,var(--danger)_30%,transparent)] bg-[var(--danger-soft)] p-3 text-sm text-[var(--danger)]"
          >
            {error}
          </div>
          <div className="text-center pt-2">
            <Link
              href="/login"
              className="inline-block rounded-lg bg-[var(--primary)] px-4 py-2 text-sm font-medium text-white hover:opacity-90"
            >
              Back to Sign In
            </Link>
          </div>
        </div>
      </AuthShell>
    );
  }

  return (
    <AuthShell
      title="Completing sign-in"
      subtitle="Connecting your Google account..."
    >
      <div className="flex flex-col items-center justify-center py-8 space-y-4">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[var(--primary)] border-t-transparent" />
        <p className="text-sm text-[var(--text-muted)]">
          Redirecting to your workspace...
        </p>
      </div>
    </AuthShell>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense
      fallback={
        <AuthShell
          title="Completing sign-in"
          subtitle="Connecting your Google account..."
        >
          <div className="flex flex-col items-center justify-center py-8 space-y-4">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-[var(--primary)] border-t-transparent" />
            <p className="text-sm text-[var(--text-muted)]">Loading...</p>
          </div>
        </AuthShell>
      }
    >
      <CallbackHandler />
    </Suspense>
  );
}

