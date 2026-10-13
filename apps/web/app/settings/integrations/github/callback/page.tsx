"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { apiClient } from "@/lib/api-client";

function CallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState("Processing GitHub authorization...");

  useEffect(() => {
    const code = searchParams.get("code");
    if (!code) {
      setStatus("No authorization code found.");
      setTimeout(() => router.push("/settings/integrations"), 2000);
      return;
    }

    // In a real app, we'd exchange the code for an access token on the backend.
    // For local development without a real OAuth app, we're accepting the token directly.
    // Here we'll just simulate it or use the code as token if running locally.

    apiClient.connectGitHub({ access_token: code }).then(({ error }) => {
      if (error) {
        setStatus(`Failed to connect: ${error.message}`);
      } else {
        setStatus("Successfully connected GitHub!");
      }
      setTimeout(() => router.push("/settings/integrations"), 2000);
    });
  }, [router, searchParams]);

  return (
    <div className="flex flex-col items-center justify-center min-h-[50vh]">
      <div className="text-xl font-medium">{status}</div>
      <p className="text-[var(--text-muted)] mt-2">
        Redirecting you back to settings...
      </p>
    </div>
  );
}

export default function GitHubCallbackPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <CallbackContent />
    </Suspense>
  );
}
