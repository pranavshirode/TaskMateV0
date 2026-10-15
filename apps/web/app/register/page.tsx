"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import AuthShell from "@/components/layout/AuthShell";
import GoogleSignInButton from "@/components/ui/GoogleSignInButton";

export default function RegisterPage() {
  const { register, login } = useAuth();
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    setIsSubmitting(true);
    try {
      await register({ name, email, password });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Registration failed");
      setIsSubmitting(false);
      return;
    }
    // Sign straight in so new users land in their workspace, not back on a login form.
    try {
      await login({ email, password });
      router.push("/dashboard");
    } catch {
      router.push("/login");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AuthShell
      title="Create your workspace"
      subtitle="Free for solo developers. Takes 30 seconds."
    >
      <div className="space-y-4">
        {error && (
          <div
            role="alert"
            className="rounded-lg border border-[color-mix(in_srgb,var(--danger)_30%,transparent)] bg-[var(--danger-soft)] p-3 text-sm text-[var(--danger)]"
          >
            {error}
          </div>
        )}

        <GoogleSignInButton text="Sign up with Google" />

        <div className="relative my-4 flex items-center justify-center">
          <div className="w-full border-t border-[var(--sidebar-border)]" />
          <span className="absolute bg-[var(--background)] px-3 text-xs uppercase tracking-wider text-[var(--text-muted)]">
            or register with email
          </span>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Name"
          autoComplete="name"
          autoFocus
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          placeholder="Alex Developer"
        />
        <Input
          label="Email"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          placeholder="you@example.com"
        />
        <Input
          label="Password"
          type="password"
          autoComplete="new-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          placeholder="••••••••"
          hint="At least 8 characters"
        />
        <Button type="submit" disabled={isSubmitting} className="w-full">
          {isSubmitting ? "Creating workspace..." : "Create account"}
        </Button>
      </form>
      </div>
      <p className="mt-6 text-center text-sm text-[var(--text-muted)]">
        Already have an account?{" "}
        <Link
          href="/login"
          className="font-medium text-[var(--primary)] hover:underline"
        >
          Sign in
        </Link>
      </p>
    </AuthShell>
  );
}
