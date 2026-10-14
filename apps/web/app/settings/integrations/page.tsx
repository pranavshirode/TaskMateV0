"use client";

import { useCallback, useEffect, useState } from "react";
import {
  apiClient,
  type GitHubStatus,
  type GoogleStatus,
  type MCPServerStatus,
} from "@/lib/api-client";
import { useFeedback } from "@/components/ui/Feedback";
import PageHeader from "@/components/ui/PageHeader";
import Button from "@/components/ui/Button";
import Icon from "@/components/ui/Icon";
import LoadingSpinner from "@/components/ui/LoadingSpinner";

const GITHUB_TOKEN_URL =
  "https://github.com/settings/personal-access-tokens/new";

export default function IntegrationsPage() {
  const { toast, confirm } = useFeedback();
  const [github, setGithub] = useState<GitHubStatus | null>(null);
  const [google, setGoogle] = useState<GoogleStatus | null>(null);
  const [mcp, setMcp] = useState<MCPServerStatus[] | null>(null);
  const [mcpLoading, setMcpLoading] = useState(true);
  const [token, setToken] = useState("");
  const [busy, setBusy] = useState<string | null>(null);

  const loadMcp = useCallback(async () => {
    setMcpLoading(true);
    try {
      setMcp(await apiClient.getMCPStatus());
    } catch {
      setMcp(null);
    } finally {
      setMcpLoading(false);
    }
  }, []);

  const load = useCallback(async () => {
    const [gh, gg] = await Promise.all([
      apiClient.getGitHubStatus(),
      apiClient.getGoogleStatus().catch(() => null),
    ]);
    setGithub(gh.data);
    setGoogle(gg);
    loadMcp();
  }, [loadMcp]);

  useEffect(() => {
    load();
  }, [load]);

  const connectGitHubToken = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token.trim()) return;
    setBusy("github");
    const { data, error } = await apiClient.connectGitHub({
      access_token: token.trim(),
    });
    setBusy(null);
    if (error) {
      toast(error.message, "error");
      return;
    }
    setToken("");
    toast(`GitHub connected${data?.username ? ` as ${data.username}` : ""}`);
    load();
  };

  const signInWithGitHub = async () => {
    const { data, error } = await apiClient.getGitHubAuthorizeUrl();
    if (data?.url) window.location.href = data.url;
    else toast(error?.message || "GitHub sign-in is not configured", "error");
  };

  const connectGoogle = async () => {
    setBusy("google");
    try {
      const { url } = await apiClient.getGoogleAuthorizeUrl();
      window.location.href = url;
    } catch (err) {
      setBusy(null);
      toast(
        err instanceof Error ? err.message : "Could not start Google sign-in",
        "error"
      );
    }
  };

  const disconnect = async (which: "github" | "google") => {
    const label = which === "github" ? "GitHub" : "Google";
    const ok = await confirm({
      title: `Disconnect ${label}?`,
      message: `The AI agent will no longer be able to use your ${label} account. Stored tokens are deleted.`,
      confirmLabel: "Disconnect",
      danger: true,
    });
    if (!ok) return;
    try {
      if (which === "github") await apiClient.disconnectGitHub();
      else await apiClient.disconnectGoogle();
      toast(`${label} disconnected`);
    } catch (err) {
      toast(err instanceof Error ? err.message : "Disconnect failed", "error");
    }
    load();
  };

  return (
    <div className="mx-auto max-w-3xl pb-12">
      <PageHeader
        title="Integrations"
        description="Connect your accounts so the AI agent can work with them through MCP. Anything that sends, creates or changes something asks for your approval first."
      />

      <div className="space-y-4">
        {/* GitHub */}
        <section className="card p-5">
          <div className="flex items-start gap-4">
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[var(--foreground)] text-[var(--background)]">
              <Icon name="github" size={20} />
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h2 className="font-semibold">GitHub</h2>
                <StatusPill
                  loading={github === null}
                  connected={!!github?.connected}
                  label={
                    github?.username
                      ? `Connected as ${github.username}`
                      : undefined
                  }
                />
              </div>
              <p className="mt-0.5 text-sm text-[var(--text-muted)]">
                Repositories, issues and pull requests, through GitHub&apos;s
                official MCP server.
              </p>

              {github?.connected ? (
                <Button
                  variant="secondary"
                  size="sm"
                  className="mt-4"
                  onClick={() => disconnect("github")}
                >
                  Disconnect
                </Button>
              ) : github ? (
                <div className="mt-4 space-y-3">
                  <form
                    onSubmit={connectGitHubToken}
                    className="flex flex-col gap-2 sm:flex-row"
                  >
                    <input
                      type="password"
                      autoComplete="off"
                      value={token}
                      onChange={(e) => setToken(e.target.value)}
                      placeholder="Paste a GitHub personal access token"
                      aria-label="GitHub personal access token"
                      className="field flex-1 font-mono"
                    />
                    <Button
                      type="submit"
                      disabled={!token.trim() || busy === "github"}
                    >
                      {busy === "github" ? "Checking..." : "Connect"}
                    </Button>
                  </form>
                  <p className="text-xs text-[var(--text-muted)]">
                    Create a{" "}
                    <a
                      href={GITHUB_TOKEN_URL}
                      target="_blank"
                      rel="noreferrer"
                      className="text-[var(--primary)] hover:underline"
                    >
                      fine-grained token
                    </a>{" "}
                    with access to your repositories and permissions{" "}
                    <strong>
                      Contents, Issues, Pull requests: Read and write
                    </strong>
                    . It is stored encrypted and never shown to the AI.
                  </p>
                  {github.oauth_available && (
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={signInWithGitHub}
                    >
                      <Icon name="github" size={14} /> Or sign in with GitHub
                    </Button>
                  )}
                </div>
              ) : null}
            </div>
          </div>
        </section>

        {/* Google */}
        <section className="card p-5">
          <div className="flex items-start gap-4">
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-[var(--sidebar-border)] bg-white text-lg font-bold text-[#4285F4]">
              G
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h2 className="font-semibold">Google Workspace</h2>
                <StatusPill
                  loading={google === null}
                  connected={!!google?.connected}
                  label={
                    google?.email ? `Connected as ${google.email}` : undefined
                  }
                />
              </div>
              <p className="mt-0.5 text-sm text-[var(--text-muted)]">
                Gmail, Drive, Docs, Sheets, Slides and Calendar, through the
                Google Workspace MCP server.
              </p>

              {google && !google.configured ? (
                <p className="mt-4 rounded-lg border border-[color-mix(in_srgb,var(--warning)_35%,transparent)] bg-[var(--warning-soft)] p-3 text-xs text-[var(--foreground)]">
                  Google isn&apos;t set up on this server yet. The developer
                  needs to add{" "}
                  <code className="font-mono">GOOGLE_OAUTH_CLIENT_ID</code> and{" "}
                  <code className="font-mono">GOOGLE_OAUTH_CLIENT_SECRET</code>{" "}
                  to <code className="font-mono">apps/api/.env</code> (see the
                  Google setup steps in DEMO.md).
                </p>
              ) : google?.connected ? (
                <Button
                  variant="secondary"
                  size="sm"
                  className="mt-4"
                  onClick={() => disconnect("google")}
                >
                  Disconnect
                </Button>
              ) : google ? (
                <Button
                  size="sm"
                  className="mt-4"
                  onClick={connectGoogle}
                  disabled={busy === "google"}
                >
                  {busy === "google" ? "Opening Google..." : "Connect Google"}
                </Button>
              ) : null}
            </div>
          </div>
        </section>

        {/* What the agent can use */}
        <section className="card p-5">
          <div className="mb-3 flex items-center justify-between gap-2">
            <div>
              <h2 className="flex items-center gap-2 font-semibold">
                <Icon name="bot" size={16} className="text-[var(--primary)]" />{" "}
                Agent tools (MCP)
              </h2>
              <p className="mt-0.5 text-sm text-[var(--text-muted)]">
                What the AI agent can use for you right now. Use Agent mode in
                the AI Assistant.
              </p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={loadMcp}
              disabled={mcpLoading}
            >
              {mcpLoading ? "Checking..." : "Refresh"}
            </Button>
          </div>

          {mcpLoading && !mcp ? (
            <div className="flex justify-center py-6">
              <LoadingSpinner />
            </div>
          ) : !mcp ? (
            <p className="text-sm text-[var(--danger)]">
              Could not load MCP status.
            </p>
          ) : (
            <div className="divide-y divide-[var(--sidebar-border)]">
              {mcp.map((server) => (
                <MCPServerRow key={server.key} server={server} />
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

function StatusPill({
  loading,
  connected,
  label,
}: {
  loading: boolean;
  connected: boolean;
  label?: string;
}) {
  if (loading)
    return (
      <span className="text-xs text-[var(--text-muted)]">Checking...</span>
    );
  return connected ? (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-[var(--success-soft)] px-2.5 py-0.5 text-xs font-medium text-[var(--success)]">
      <Icon name="check" size={12} /> {label || "Connected"}
    </span>
  ) : (
    <span className="rounded-full bg-[var(--surface-hover)] px-2.5 py-0.5 text-xs font-medium text-[var(--text-muted)]">
      Not connected
    </span>
  );
}

function MCPServerRow({ server }: { server: MCPServerStatus }) {
  const [open, setOpen] = useState(false);
  const read = server.tools.filter((t) => t.permission === "READ");
  const gated = server.tools.filter((t) => t.permission !== "READ");
  const short = (name: string) =>
    name.split(".").slice(2).join(".").replace(/_/g, " ");

  let state: { text: string; tone: string };
  if (!server.configured)
    state = {
      text: "Not configured on this server",
      tone: "text-[var(--text-muted)]",
    };
  else if (!server.connected)
    state = {
      text: "Connect the account above to enable",
      tone: "text-[var(--text-muted)]",
    };
  else if (server.error)
    state = {
      text: `Unavailable: ${server.error}`,
      tone: "text-[var(--danger)]",
    };
  else
    state = {
      text: `Ready · ${server.tool_count} tools`,
      tone: "text-[var(--success)]",
    };

  return (
    <div className="py-3">
      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-medium">{server.label}</p>
          <p className={`text-xs ${state.tone}`}>{state.text}</p>
        </div>
        {server.tools.length > 0 && (
          <button
            onClick={() => setOpen((o) => !o)}
            className="inline-flex shrink-0 items-center gap-1 text-xs text-[var(--text-muted)] hover:text-[var(--foreground)]"
            aria-expanded={open}
          >
            {open ? "Hide tools" : "Show tools"}
            <Icon
              name="chevronDown"
              size={14}
              className={open ? "rotate-180" : ""}
            />
          </button>
        )}
      </div>
      {open && (
        <div className="mt-3 grid gap-3 sm:grid-cols-2">
          <ToolList
            title="Runs directly (read-only)"
            tools={read.map((t) => short(t.name))}
          />
          <ToolList
            title="Asks for your approval"
            tools={gated.map((t) => short(t.name))}
          />
        </div>
      )}
    </div>
  );
}

function ToolList({ title, tools }: { title: string; tools: string[] }) {
  return (
    <div className="rounded-lg border border-[var(--sidebar-border)] p-3">
      <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-[var(--text-muted)]">
        {title} ({tools.length})
      </p>
      {tools.length === 0 ? (
        <p className="text-xs text-[var(--text-muted)]">None</p>
      ) : (
        <ul className="space-y-0.5 text-xs">
          {tools.map((t) => (
            <li key={t} className="truncate">
              {t}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
