"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { apiClient } from "@/lib/api-client";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";

export default function SettingsPage() {
  const { user, logout } = useAuth();
  const [name, setName] = useState(user?.name || "");
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState("");

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setIsSaving(true);
    setMessage("");
    try {
      await apiClient.updateMe({ name: name.trim() });
      setMessage("Profile updated successfully.");
    } catch (err: unknown) {
      setMessage(
        `Error: ${err instanceof Error ? err.message : "Unknown error"}`
      );
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto pb-12">
      <h1 className="text-2xl font-bold mb-6">Settings</h1>

      <div className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Profile</h2>
        <form onSubmit={handleSave} className="space-y-4">
          {message && (
            <div
              className={`text-sm rounded-lg p-3 ${message.startsWith("Error") ? "bg-red-500/10 text-red-500 border border-red-500/30" : "bg-green-500/10 text-green-500 border border-green-500/30"}`}
            >
              {message}
            </div>
          )}
          <Input
            label="Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          <Input label="Email" value={user?.email || ""} disabled />
          <Button type="submit" disabled={isSaving}>
            {isSaving ? "Saving..." : "Save Changes"}
          </Button>
        </form>
      </div>

      <div className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-6 mb-6">
        <h2 className="text-lg font-semibold mb-2">Integrations</h2>
        <p className="text-sm text-[var(--text-muted)] mb-4">
          Connect external services like GitHub to enable automated repositories
          and agent features.
        </p>
        <a href="/settings/integrations" className="inline-block">
          <Button variant="secondary">Manage Integrations →</Button>
        </a>
      </div>

      <div className="bg-[var(--sidebar-bg)] border border-[var(--sidebar-border)] rounded-xl p-6">
        <h2 className="text-lg font-semibold mb-4">Account</h2>
        <Button variant="danger" onClick={logout}>
          Sign Out
        </Button>
      </div>
    </div>
  );
}
