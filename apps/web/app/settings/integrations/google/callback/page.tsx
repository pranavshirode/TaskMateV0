"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { apiClient } from "@/lib/api-client";
import LoadingSpinner from "@/components/ui/LoadingSpinner";

function CallbackContent() {
  const router = useRouter();
  const params = useSearchParams();
  const [status, setStatus] = useState("Connecting your Google account...");
  const [failed, setFailed] = useState(false);
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return; // the code is single-use; avoid double submission in dev
    started.current = true;
    const code = params.get("code");
    const state = params.get("state");
    const denied = params.get("error");
    if (denied || !code || !state) {
      setFailed(true);
      setStatus(
        denied === "access_denied"
          ? "Google access was not granted."
          : "Google did not return an authorization code."
      );
      return;
    }
    apiClient
      .connectGoogle(code, state)
      .then((res) => {
        setStatus(`Connected ${res.email}. Redirecting...`);
        setTimeout(() => router.replace("/settings/integrations"), 1200);
      })
      .catch((err: unknown) => {
        setFailed(true);
        setStatus(
          err instanceof Error ? err.message : "Could not connect Google."
        );
      });
  }, [params, router]);

  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4 text-center">
      {!failed && <LoadingSpinner />}
      <p
        className={`text-base font-medium ${failed ? "text-[var(--danger)]" : ""}`}
      >
        {status}
      </p>
      {failed && (
        <button
          onClick={() => router.replace("/settings/integrations")}
          className="text-sm text-[var(--primary)] hover:underline"
        >
          Back to Integrations
        </button>
      )}
    </div>
  );
}

export default function GoogleCallbackPage() {
  return (
    <Suspense fallback={null}>
      <CallbackContent />
    </Suspense>
  );
}
