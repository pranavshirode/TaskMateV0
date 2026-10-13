"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api-client";

export default function IntegrationsPage() {
  const [githubConnected, setGithubConnected] = useState<boolean>(false);
  const [githubUsername, setGithubUsername] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStatus();
  }, []);

  async function fetchStatus() {
    setLoading(true);
    const { data } = await apiClient.getGitHubStatus();
    if (data) {
      setGithubConnected(data.connected);
      setGithubUsername(data.username || null);
    }
    setLoading(false);
  }

  async function handleConnect() {
    const { data } = await apiClient.getGitHubAuthorizeUrl();
    if (data?.url) {
      window.location.href = data.url;
    } else {
      alert("Failed to get authorization URL");
    }
  }

  async function handleDisconnect() {
    if (confirm("Are you sure you want to disconnect GitHub?")) {
      await apiClient.disconnectGitHub();
      fetchStatus();
    }
  }

  return (
    <div className="max-w-2xl mx-auto py-8 px-4">
      <h1 className="text-2xl font-bold mb-6">Integrations</h1>

      <div className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-lg p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-black dark:bg-white rounded-full flex items-center justify-center text-white dark:text-black text-xl">
              <svg
                height="24"
                aria-hidden="true"
                viewBox="0 0 16 16"
                version="1.1"
                width="24"
                data-view-component="true"
                fill="currentColor"
              >
                <path d="M8 0c4.42 0 8 3.58 8 8a8.013 8.013 0 0 1-5.45 7.59c-.4.08-.55-.17-.55-.38 0-.27.01-1.13.01-2.2 0-.75-.25-1.23-.54-1.48 1.78-.2 3.65-.88 3.65-3.95 0-.88-.31-1.59-.82-2.15.08-.2.36-1.02-.08-2.12 0 0-.67-.22-2.2.82-.64-.18-1.32-.27-2-.27-.68 0-1.36.09-2 .27-1.53-1.03-2.2-.82-2.2-.82-.44 1.1-.16 1.92-.08 2.12-.51.56-.82 1.28-.82 2.15 0 3.06 1.86 3.75 3.64 3.95-.23.2-.44.55-.51 1.07-.46.21-1.61.55-2.33-.66-.15-.24-.6-.83-1.23-.82-.67.01-.27.38.01.53.34.19.73.9.82 1.13.16.45.68 1.31 2.69.94 0 .67.01 1.3.01 1.49 0 .21-.15.45-.55.38A7.995 7.995 0 0 1 0 8c0-4.42 3.58-8 8-8Z"></path>
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-semibold">GitHub</h2>
              <p className="text-sm text-[var(--text-muted)]">
                Connect to read repositories, issues, and pull requests.
              </p>
              {loading ? (
                <p className="text-sm mt-2 text-[var(--text-muted)]">
                  Checking status...
                </p>
              ) : githubConnected ? (
                <p className="text-sm mt-2 text-green-600 dark:text-green-400 font-medium">
                  Connected as {githubUsername}
                </p>
              ) : (
                <p className="text-sm mt-2 text-red-600 dark:text-red-400 font-medium">
                  Not connected
                </p>
              )}
            </div>
          </div>

          <div>
            {loading ? null : githubConnected ? (
              <button
                onClick={handleDisconnect}
                className="px-4 py-2 border border-red-200 text-red-600 rounded hover:bg-red-50 dark:border-red-900 dark:text-red-400 dark:hover:bg-red-900/30 text-sm font-medium transition-colors"
              >
                Disconnect
              </button>
            ) : (
              <button
                onClick={handleConnect}
                className="px-4 py-2 bg-[var(--primary)] text-white rounded hover:opacity-90 text-sm font-medium transition-opacity"
              >
                Connect GitHub
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
