"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import AuthShell from "@/components/layout/AuthShell";

// Seeded by scripts/seed.py; offered only in local development.
const DEMO_ACCOUNT = { email: "alex@taskmate.dev", password: "password123" };

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const signIn = async (credentials: { email: string; password: string }) => {
    setError("");
    setIsSubmitting(true);
    try {
      await login(credentials);
      router.push("/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AuthShell
      title="Welcome back"
      subtitle="Sign in to your TaskMate workspace."
    >
      <form
        onSubmit={(e) => {
          e.preventDefault();
          signIn({ email, password });
        }}
        className="space-y-4"
      >
        {error && (
          <div
            role="alert"
            className="rounded-lg border border-[color-mix(in_srgb,var(--danger)_30%,transparent)] bg-[var(--danger-soft)] p-3 text-sm text-[var(--danger)]"
          >
            {error}
          </div>
        )}
        <Input
          label="Email"
          type="email"
          autoComplete="email"
          autoFocus
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          placeholder="you@example.com"
        />
        <Input
          label="Password"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          placeholder="••••••••"
        />
        <Button type="submit" disabled={isSubmitting} className="w-full">
          {isSubmitting ? "Signing in..." : "Sign in"}
        </Button>
        {process.env.NODE_ENV === "development" && (
          <Button
            type="button"
            variant="secondary"
            disabled={isSubmitting}
            className="w-full"
            onClick={() => signIn(DEMO_ACCOUNT)}
          >
            Use demo account
          </Button>
        )}
      </form>
      <p className="mt-6 text-center text-sm text-[var(--text-muted)]">
        New to TaskMate?{" "}
        <Link
          href="/register"
          className="font-medium text-[var(--primary)] hover:underline"
        >
          Create an account
        </Link>
      </p>
    </AuthShell>
  );
}
