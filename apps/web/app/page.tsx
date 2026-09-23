"use client";

import { useEffect, useState } from "react";
import { apiClient, type SystemInfoResponse } from "@/lib/api-client";

export default function Home() {
  const [systemInfo, setSystemInfo] = useState<SystemInfoResponse | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<"loading" | "connected" | "error">("loading");
  const [errorMessage, setErrorMessage] = useState<string>("");

  useEffect(() => {
    async function checkConnection() {
      const { data, error } = await apiClient.getSystemInfo();
      if (data) {
        setSystemInfo(data);
        setConnectionStatus("connected");
      } else {
        setConnectionStatus("error");
        setErrorMessage(error?.message || "Failed to connect to backend");
      }
    }
    checkConnection();
  }, []);

  return (
    <div className="max-w-3xl">
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-2">Welcome to TaskMate</h2>
        <p className="text-[var(--text-muted)]">
          Your AI-powered developer workspace for freelance projects.
        </p>
      </div>

      {/* Backend Connection Status */}
      <div className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-6 mb-6">
        <h3 className="text-sm font-semibold uppercase text-[var(--text-muted)] mb-4">
          System Status
        </h3>

        <div className="flex items-center gap-3 mb-4">
          <div
            className={`w-3 h-3 rounded-full ${
              connectionStatus === "connected"
                ? "bg-green-500"
                : connectionStatus === "error"
                  ? "bg-red-500"
                  : "bg-yellow-500 animate-pulse"
            }`}
          />
          <span className="text-sm">
            {connectionStatus === "connected"
              ? "Backend Connected"
              : connectionStatus === "error"
                ? "Backend Disconnected"
                : "Checking connection..."}
          </span>
        </div>

        {systemInfo && (
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-[var(--text-muted)]">Service</p>
              <p className="font-medium">{systemInfo.name}</p>
            </div>
            <div>
              <p className="text-[var(--text-muted)]">Version</p>
              <p className="font-medium">{systemInfo.version}</p>
            </div>
            <div>
              <p className="text-[var(--text-muted)]">Environment</p>
              <p className="font-medium">{systemInfo.environment}</p>
            </div>
          </div>
        )}

        {connectionStatus === "error" && (
          <p className="text-sm text-red-500 mt-2">{errorMessage}</p>
        )}
      </div>

      {/* Quick Info Cards */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-5">
          <h3 className="font-semibold mb-2">🚀 Sprint 0</h3>
          <p className="text-sm text-[var(--text-muted)]">
            Engineering foundation established. Full-stack environment with
            FastAPI, Next.js, and PostgreSQL.
          </p>
        </div>
        <div className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-5">
          <h3 className="font-semibold mb-2">🎯 Coming Next</h3>
          <p className="text-sm text-[var(--text-muted)]">
            Task management, project organization, AI agent integration,
            and GitHub connectivity.
          </p>
        </div>
      </div>
    </div>
  );
}
