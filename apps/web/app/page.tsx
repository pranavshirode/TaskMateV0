"use client";

import { useState } from "react";
import Link from "next/link";

/* ─── Tiny SVG icon helpers ──────────────────────────────────────── */
function ChevronDown({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="6 9 12 15 18 9" />
    </svg>
  );
}
function CheckIcon({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}
function ArrowRight({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" />
    </svg>
  );
}
function MenuIcon() {
  return (
    <svg width={20} height={20} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="12" x2="21" y2="12" /><line x1="3" y1="18" x2="21" y2="18" />
    </svg>
  );
}
function XIcon() {
  return (
    <svg width={20} height={20} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  );
}

/* ─── Logo mark ─────────────────────────────────────────────────── */
function LogoMark({ size = 28 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 28 28" fill="none">
      <rect width="28" height="28" rx="7" fill="#8B7CFF" />
      <path d="M7 14h14M7 9.5h8M7 18.5h10" stroke="white" strokeWidth="2" strokeLinecap="round" />
      <circle cx="20" cy="9.5" r="2" fill="white" />
    </svg>
  );
}

/* ─── Nav ────────────────────────────────────────────────────────── */
const NAV_LINKS = [
  { label: "Product", href: "#product" },
  { label: "How it works", href: "#how-it-works" },
  { label: "Features", href: "#features" },
  { label: "FAQ", href: "#faq" },
];

function LandingNav() {
  const [open, setOpen] = useState(false);
  return (
    <header
      style={{
        position: "sticky",
        top: 0,
        zIndex: 50,
        borderBottom: "1px solid var(--lp-border)",
        background: "rgba(9,11,16,0.88)",
        backdropFilter: "blur(16px)",
        WebkitBackdropFilter: "blur(16px)",
      }}
    >
      <div style={{ maxWidth: 1200, margin: "0 auto", padding: "0 24px" }}>
        <div style={{ display: "flex", alignItems: "center", height: 60, gap: 32 }}>
          {/* Logo */}
          <Link href="/" style={{ display: "flex", alignItems: "center", gap: 10, textDecoration: "none" }}>
            <LogoMark size={28} />
            <span style={{ fontWeight: 700, fontSize: 17, color: "var(--lp-text)", letterSpacing: "-0.02em" }}>
              TaskMate <span style={{ color: "var(--lp-violet)" }}>AI</span>
            </span>
          </Link>

          {/* Desktop nav */}
          <nav style={{ display: "flex", gap: 4, flex: 1, justifyContent: "center" }} className="lp-desktop-nav">
            {NAV_LINKS.map((l) => (
              <a
                key={l.href}
                href={l.href}
                style={{
                  padding: "6px 14px",
                  borderRadius: 8,
                  fontSize: 14,
                  color: "var(--lp-text2)",
                  textDecoration: "none",
                  transition: "color 0.15s, background 0.15s",
                }}
                onMouseEnter={(e) => { (e.target as HTMLElement).style.color = "var(--lp-text)"; (e.target as HTMLElement).style.background = "rgba(255,255,255,0.05)"; }}
                onMouseLeave={(e) => { (e.target as HTMLElement).style.color = "var(--lp-text2)"; (e.target as HTMLElement).style.background = "transparent"; }}
              >
                {l.label}
              </a>
            ))}
          </nav>

          {/* CTA buttons */}
          <div style={{ display: "flex", gap: 8, alignItems: "center", marginLeft: "auto" }}>
            <Link
              href="/login"
              style={{
                padding: "7px 16px",
                borderRadius: 8,
                fontSize: 14,
                color: "var(--lp-text2)",
                textDecoration: "none",
                border: "1px solid var(--lp-border2)",
                transition: "color 0.15s, border-color 0.15s",
              }}
              onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.color = "var(--lp-text)"; (e.currentTarget as HTMLElement).style.borderColor = "rgba(139,124,255,0.5)"; }}
              onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.color = "var(--lp-text2)"; (e.currentTarget as HTMLElement).style.borderColor = "var(--lp-border2)"; }}
            >
              Log in
            </Link>
            <Link
              href="/register"
              style={{
                padding: "7px 16px",
                borderRadius: 8,
                fontSize: 14,
                fontWeight: 600,
                color: "#fff",
                textDecoration: "none",
                background: "linear-gradient(135deg, #8B7CFF, #66A6FF)",
                boxShadow: "0 0 20px rgba(139,124,255,0.3)",
                transition: "opacity 0.15s, box-shadow 0.15s",
              }}
              onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.opacity = "0.9"; (e.currentTarget as HTMLElement).style.boxShadow = "0 0 28px rgba(139,124,255,0.45)"; }}
              onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.opacity = "1"; (e.currentTarget as HTMLElement).style.boxShadow = "0 0 20px rgba(139,124,255,0.3)"; }}
            >
              Get Started
            </Link>
            {/* Hamburger - mobile */}
            <button
              aria-label="Toggle menu"
              onClick={() => setOpen(!open)}
              style={{ display: "none", background: "none", border: "none", color: "var(--lp-text2)", cursor: "pointer", padding: 4 }}
              className="lp-hamburger"
            >
              {open ? <XIcon /> : <MenuIcon />}
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        {open && (
          <div
            style={{
              borderTop: "1px solid var(--lp-border)",
              padding: "16px 0",
              display: "flex",
              flexDirection: "column",
              gap: 4,
            }}
            className="lp-mobile-menu"
          >
            {NAV_LINKS.map((l) => (
              <a
                key={l.href}
                href={l.href}
                onClick={() => setOpen(false)}
                style={{ padding: "10px 12px", borderRadius: 8, fontSize: 15, color: "var(--lp-text2)", textDecoration: "none" }}
              >
                {l.label}
              </a>
            ))}
            <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
              <Link href="/login" style={{ flex: 1, textAlign: "center", padding: "9px 16px", borderRadius: 8, fontSize: 14, color: "var(--lp-text2)", border: "1px solid var(--lp-border2)", textDecoration: "none" }}>
                Log in
              </Link>
              <Link href="/register" style={{ flex: 1, textAlign: "center", padding: "9px 16px", borderRadius: 8, fontSize: 14, fontWeight: 600, color: "#fff", background: "linear-gradient(135deg, #8B7CFF, #66A6FF)", textDecoration: "none" }}>
                Get Started
              </Link>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}

/* ─── Hero mockup ────────────────────────────────────────────────── */
function HeroMockup() {
  return (
    <div style={{
      borderRadius: 16,
      border: "1px solid var(--lp-border2)",
      background: "var(--lp-card)",
      overflow: "hidden",
      boxShadow: "0 32px 80px rgba(0,0,0,0.6), 0 0 0 1px rgba(139,124,255,0.12)",
    }}>
      {/* Window chrome */}
      <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "12px 16px", borderBottom: "1px solid var(--lp-border)", background: "var(--lp-bg2)" }}>
        {["#ff5f56", "#ffbd2e", "#27c93f"].map((c) => (
          <div key={c} style={{ width: 10, height: 10, borderRadius: "50%", background: c }} />
        ))}
        <div style={{ flex: 1, margin: "0 12px", height: 20, borderRadius: 6, background: "rgba(255,255,255,0.06)", display: "flex", alignItems: "center", paddingLeft: 10 }}>
          <span style={{ fontSize: 11, color: "var(--lp-text2)" }}>taskmate.ai/dashboard</span>
        </div>
      </div>

      {/* App layout */}
      <div style={{ display: "flex", height: 340 }}>
        {/* Sidebar */}
        <div style={{ width: 180, borderRight: "1px solid var(--lp-border)", background: "var(--lp-bg2)", padding: "16px 0" }}>
          <div style={{ padding: "0 12px 12px", borderBottom: "1px solid var(--lp-border)", marginBottom: 12 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <LogoMark size={20} />
              <span style={{ fontSize: 12, fontWeight: 700, color: "var(--lp-text)" }}>TaskMate AI</span>
            </div>
          </div>
          {[
            { label: "Today", active: true },
            { label: "Tasks", active: false },
            { label: "Projects", active: false },
            { label: "Clients", active: false },
            { label: "AI Assistant", active: false },
            { label: "Requirements", active: false },
          ].map((item) => (
            <div key={item.label} style={{
              padding: "7px 14px",
              fontSize: 12,
              color: item.active ? "var(--lp-violet)" : "var(--lp-text2)",
              background: item.active ? "rgba(139,124,255,0.12)" : "transparent",
              margin: "1px 8px",
              borderRadius: 6,
            }}>
              {item.label}
            </div>
          ))}
        </div>

        {/* Main content */}
        <div style={{ flex: 1, padding: 20, overflowY: "auto" }}>
          <div style={{ marginBottom: 16 }}>
            <p style={{ fontSize: 11, color: "var(--lp-text2)", marginBottom: 4 }}>Good morning</p>
            <h3 style={{ fontSize: 15, fontWeight: 700, color: "var(--lp-text)", margin: 0 }}>Your workspace</h3>
          </div>

          {/* Stat tiles */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8, marginBottom: 14 }}>
            {[{ label: "Tasks due", value: "3", c: "#8B7CFF" }, { label: "Projects", value: "5", c: "#66A6FF" }, { label: "Clients", value: "4", c: "#34d399" }].map((s) => (
              <div key={s.label} style={{ background: "var(--lp-bg2)", borderRadius: 8, border: "1px solid var(--lp-border)", padding: "10px 12px" }}>
                <div style={{ fontSize: 18, fontWeight: 700, color: s.c }}>{s.value}</div>
                <div style={{ fontSize: 10, color: "var(--lp-text2)", marginTop: 2 }}>{s.label}</div>
              </div>
            ))}
          </div>

          {/* Task list */}
          <div style={{ background: "var(--lp-bg2)", borderRadius: 8, border: "1px solid var(--lp-border)", padding: "10px 12px", marginBottom: 10 }}>
            <p style={{ fontSize: 10, fontWeight: 600, color: "var(--lp-text2)", marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.06em" }}>Due today</p>
            {[
              { task: "Set up auth flow", project: "ClientPortal v2", done: true },
              { task: "Review API schema", project: "DataSync", done: false },
              { task: "Send proposal draft", project: "MobileApp MVP", done: false },
            ].map((t) => (
              <div key={t.task} style={{ display: "flex", alignItems: "center", gap: 8, padding: "5px 0", borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
                <div style={{ width: 14, height: 14, borderRadius: 4, border: `1.5px solid ${t.done ? "var(--lp-violet)" : "var(--lp-border2)"}`, background: t.done ? "var(--lp-violet)" : "transparent", flexShrink: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
                  {t.done && <svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3"><polyline points="20 6 9 17 4 12" /></svg>}
                </div>
                <span style={{ fontSize: 11, color: t.done ? "var(--lp-text2)" : "var(--lp-text)", textDecoration: t.done ? "line-through" : "none", flex: 1 }}>{t.task}</span>
                <span style={{ fontSize: 10, color: "var(--lp-text2)", background: "rgba(139,124,255,0.1)", padding: "1px 6px", borderRadius: 4 }}>{t.project}</span>
              </div>
            ))}
          </div>

          {/* AI prompt bar */}
          <div style={{ background: "var(--lp-bg2)", borderRadius: 8, border: "1px solid rgba(139,124,255,0.3)", padding: "8px 12px", display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{ width: 16, height: 16, borderRadius: "50%", background: "linear-gradient(135deg, #8B7CFF, #66A6FF)", flexShrink: 0 }} />
            <span style={{ fontSize: 11, color: "var(--lp-text2)", fontStyle: "italic" }}>Ask TaskMate to organize your week…</span>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ─── Section wrapper ────────────────────────────────────────────── */
function Section({ id, children, style = {} }: { id?: string; children: React.ReactNode; style?: React.CSSProperties }) {
  return (
    <section id={id} style={{ padding: "96px 24px", ...style }}>
      <div style={{ maxWidth: 1120, margin: "0 auto" }}>
        {children}
      </div>
    </section>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ display: "inline-flex", alignItems: "center", gap: 6, background: "rgba(139,124,255,0.1)", border: "1px solid rgba(139,124,255,0.25)", borderRadius: 20, padding: "4px 12px", marginBottom: 20 }}>
      <div style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--lp-violet)" }} />
      <span style={{ fontSize: 12, fontWeight: 600, color: "var(--lp-violet)", letterSpacing: "0.04em", textTransform: "uppercase" }}>{children}</span>
    </div>
  );
}

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <h2 style={{ fontSize: "clamp(28px, 4vw, 44px)", fontWeight: 800, color: "var(--lp-text)", letterSpacing: "-0.03em", lineHeight: 1.15, margin: "0 0 20px" }}>
      {children}
    </h2>
  );
}

function SectionSubtitle({ children }: { children: React.ReactNode }) {
  return (
    <p style={{ fontSize: 17, color: "var(--lp-text2)", lineHeight: 1.7, maxWidth: 560, margin: "0 0 48px" }}>
      {children}
    </p>
  );
}

/* ─── Hero ───────────────────────────────────────────────────────── */
function HeroSection() {
  return (
    <section
      id="product"
      style={{
        padding: "80px 24px 96px",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Glow blobs */}
      <div style={{ position: "absolute", top: "-120px", left: "20%", width: 500, height: 500, borderRadius: "50%", background: "radial-gradient(circle, rgba(139,124,255,0.12) 0%, transparent 70%)", pointerEvents: "none" }} />
      <div style={{ position: "absolute", top: "60px", right: "10%", width: 400, height: 400, borderRadius: "50%", background: "radial-gradient(circle, rgba(102,166,255,0.1) 0%, transparent 70%)", pointerEvents: "none" }} />

      <div style={{ maxWidth: 1120, margin: "0 auto" }}>
        {/* Announce pill */}
        <div style={{ display: "flex", justifyContent: "center", marginBottom: 32 }}>
          <div style={{ display: "inline-flex", alignItems: "center", gap: 8, background: "rgba(139,124,255,0.08)", border: "1px solid rgba(139,124,255,0.2)", borderRadius: 20, padding: "6px 14px" }}>
            <span style={{ fontSize: 11, background: "linear-gradient(90deg, #8B7CFF, #66A6FF)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em" }}>Built for independent developers</span>
          </div>
        </div>

        {/* Two-column layout */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 56, alignItems: "center" }} className="lp-hero-grid">
          {/* Left: copy */}
          <div className="lp-animate-fade-up">
            <h1 style={{
              fontSize: "clamp(36px, 5vw, 60px)",
              fontWeight: 900,
              letterSpacing: "-0.04em",
              lineHeight: 1.1,
              color: "var(--lp-text)",
              margin: "0 0 24px",
            }}>
              Turn messy client briefs into{" "}
              <span style={{ background: "linear-gradient(135deg, #8B7CFF, #66A6FF)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
                structured projects
              </span>
            </h1>
            <p style={{ fontSize: 18, color: "var(--lp-text2)", lineHeight: 1.7, marginBottom: 36, maxWidth: 480 }}>
              TaskMate AI uses a multi-agent pipeline to analyze requirements, generate tasks, build proposals, and manage your freelance workflow — all in one workspace.
            </p>
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
              <Link
                href="/register"
                style={{
                  display: "inline-flex", alignItems: "center", gap: 8,
                  padding: "13px 28px", borderRadius: 10, fontSize: 15, fontWeight: 700,
                  color: "#fff", textDecoration: "none",
                  background: "linear-gradient(135deg, #8B7CFF, #66A6FF)",
                  boxShadow: "0 0 32px rgba(139,124,255,0.4)",
                  transition: "opacity 0.15s",
                }}
              >
                Start free <ArrowRight size={16} />
              </Link>
              <Link
                href="/login"
                style={{
                  display: "inline-flex", alignItems: "center", gap: 8,
                  padding: "13px 28px", borderRadius: 10, fontSize: 15, fontWeight: 600,
                  color: "var(--lp-text2)", textDecoration: "none",
                  border: "1px solid var(--lp-border2)",
                  transition: "color 0.15s, border-color 0.15s",
                }}
              >
                Log in
              </Link>
            </div>
            {/* Trust strip inline */}
            <div style={{ display: "flex", gap: 20, marginTop: 32, flexWrap: "wrap" }}>
              {["No credit card required", "SQLite-powered, privacy-first", "Open source architecture"].map((t) => (
                <div key={t} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <CheckIcon size={14} />
                  <span style={{ fontSize: 13, color: "var(--lp-text2)" }}>{t}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Right: product mockup */}
          <div className="lp-animate-fade-up" style={{ animationDelay: "0.15s" }}>
            <HeroMockup />
          </div>
        </div>
      </div>
    </section>
  );
}

/* ─── Problem / Solution ─────────────────────────────────────────── */
const PROBLEMS = [
  {
    emoji: "😵",
    title: "Client briefs are chaos",
    desc: "Requirements arrive as a wall of text, Notion dumps, or WhatsApp voice notes. No structure, no clarity.",
  },
  {
    emoji: "📊",
    title: "Estimating is painful",
    desc: "You spend hours decoding vague requirements before you can write a proposal — time you're not billing for.",
  },
  {
    emoji: "🧩",
    title: "Context switching kills flow",
    desc: "Juggling 4 clients across 6 tools, you're always forgetting something or losing the thread.",
  },
];

function ProblemSection() {
  return (
    <Section id="how-it-works" style={{ borderTop: "1px solid var(--lp-border)" }}>
      <div style={{ textAlign: "center", marginBottom: 56 }}>
        <SectionLabel>The problem</SectionLabel>
        <SectionHeading>Freelancing is great. The admin is not.</SectionHeading>
        <SectionSubtitle>
          You're great at building software. But the operational overhead of client work eats into your productive hours every day.
        </SectionSubtitle>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 20 }} className="lp-3col">
        {PROBLEMS.map((p) => (
          <div
            key={p.title}
            style={{
              background: "var(--lp-card)",
              border: "1px solid var(--lp-border)",
              borderRadius: 16,
              padding: 28,
              transition: "border-color 0.2s",
            }}
          >
            <div style={{ fontSize: 36, marginBottom: 16 }}>{p.emoji}</div>
            <h3 style={{ fontSize: 17, fontWeight: 700, color: "var(--lp-text)", margin: "0 0 10px" }}>{p.title}</h3>
            <p style={{ fontSize: 14, color: "var(--lp-text2)", lineHeight: 1.65, margin: 0 }}>{p.desc}</p>
          </div>
        ))}
      </div>
    </Section>
  );
}

/* ─── Workflow steps ─────────────────────────────────────────────── */
const WORKFLOW_STEPS = [
  {
    number: "01",
    title: "Paste the client brief",
    desc: "Drop any unstructured text — email, Notion doc, voice transcript — directly into TaskMate.",
  },
  {
    number: "02",
    title: "AI analyzes requirements",
    desc: "A specialized Requirement Analyzer agent extracts goals, assumptions, risks, ambiguities, and clarifying questions.",
  },
  {
    number: "03",
    title: "You review and approve",
    desc: "Nothing proceeds without your approval. Review structured requirements before the planner generates tasks.",
  },
  {
    number: "04",
    title: "Tasks, milestones, and proposal generated",
    desc: "A structured project plan, timeline, and client-ready proposal draft — ready for review.",
  },
];

function WorkflowSection() {
  return (
    <Section style={{
      background: "linear-gradient(180deg, var(--lp-bg) 0%, var(--lp-bg2) 100%)",
      borderTop: "1px solid var(--lp-border)",
      borderBottom: "1px solid var(--lp-border)",
    }}>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 72, alignItems: "start" }} className="lp-hero-grid">
        <div>
          <SectionLabel>How it works</SectionLabel>
          <SectionHeading>From vague brief to clear plan in minutes</SectionHeading>
          <SectionSubtitle>
            TaskMate's multi-agent pipeline handles the heavy lifting so you can focus on writing code.
          </SectionSubtitle>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          {WORKFLOW_STEPS.map((step, i) => (
            <div key={step.number} style={{ display: "flex", gap: 20, alignItems: "flex-start" }}>
              <div style={{ flexShrink: 0, width: 40, height: 40, borderRadius: 10, background: "rgba(139,124,255,0.12)", border: "1px solid rgba(139,124,255,0.25)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                <span style={{ fontSize: 12, fontWeight: 800, color: "var(--lp-violet)", fontVariantNumeric: "tabular-nums" }}>{step.number}</span>
              </div>
              <div>
                <h3 style={{ fontSize: 16, fontWeight: 700, color: "var(--lp-text)", margin: "0 0 6px" }}>{step.title}</h3>
                <p style={{ fontSize: 14, color: "var(--lp-text2)", lineHeight: 1.65, margin: 0 }}>{step.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </Section>
  );
}

/* ─── Features bento ─────────────────────────────────────────────── */
const FEATURES = [
  {
    title: "Multi-agent requirement analysis",
    desc: "Specialized AI agents extract structured requirements, risks, assumptions, and clarifying questions from any client brief. The pipeline pauses and asks you when information is missing — no hallucination.",
    accent: "#8B7CFF",
    wide: true,
  },
  {
    title: "Visual task board",
    desc: "Kanban-style board with drag-and-drop, priorities, deadlines, and dependency tracking across all projects.",
    accent: "#66A6FF",
    wide: false,
  },
  {
    title: "Milestones and dependencies",
    desc: "Structure work into milestones. Define blocking and blocked relationships between tasks.",
    accent: "#34d399",
    wide: false,
  },
  {
    title: "Proposal and estimate generation",
    desc: "Turn approved requirements into a structured client proposal with scope, deliverables, exclusions, and timeline estimates.",
    accent: "#f59e0b",
    wide: false,
  },
  {
    title: "Client and project management",
    desc: "Link projects to clients. Track communications, status, and interaction history in one place.",
    accent: "#f472b6",
    wide: false,
  },
  {
    title: "Local AI intent classifier",
    desc: "A trained TF-IDF + Logistic Regression model routes your workspace queries to the right agent — fast, offline, no API cost.",
    accent: "#8B7CFF",
    wide: true,
  },
];

function FeatureCard({ f }: { f: typeof FEATURES[0] }) {
  return (
    <div
      data-wide={f.wide ? "true" : "false"}
      style={{
        background: "var(--lp-card)",
        border: "1px solid var(--lp-border)",
        borderRadius: 16,
        padding: 28,
        gridColumn: f.wide ? "span 2" : "span 1",
        transition: "border-color 0.2s, transform 0.2s",
        position: "relative",
        overflow: "hidden",
      }}
      className="lp-feature-card"
    >
      <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 2, background: `linear-gradient(90deg, ${f.accent}66, transparent)` }} />
      <div style={{ width: 36, height: 36, borderRadius: 10, background: `${f.accent}1a`, border: `1px solid ${f.accent}33`, marginBottom: 16, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ width: 14, height: 14, borderRadius: "50%", background: f.accent }} />
      </div>
      <h3 style={{ fontSize: 16, fontWeight: 700, color: "var(--lp-text)", margin: "0 0 10px" }}>{f.title}</h3>
      <p style={{ fontSize: 14, color: "var(--lp-text2)", lineHeight: 1.7, margin: 0 }}>{f.desc}</p>
    </div>
  );
}

function FeaturesSection() {
  return (
    <Section id="features" style={{ borderTop: "1px solid var(--lp-border)" }}>
      <div style={{ textAlign: "center", marginBottom: 56 }}>
        <SectionLabel>Features</SectionLabel>
        <SectionHeading>Everything a freelance dev needs</SectionHeading>
        <SectionSubtitle>
          Built from the ground up for solo developers — not bloated enterprise PM tools.
        </SectionSubtitle>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }} className="lp-bento">
        {FEATURES.map((f) => <FeatureCard key={f.title} f={f} />)}
      </div>
    </Section>
  );
}

/* ─── Interactive preview ────────────────────────────────────────── */
const PREVIEW_TABS = [
  {
    id: "brief",
    label: "Client Brief",
    content: (
      <div style={{ padding: 20 }}>
        <p style={{ fontSize: 12, color: "var(--lp-text2)", margin: "0 0 12px", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em" }}>Input — Raw client message</p>
        <div style={{ background: "var(--lp-bg)", borderRadius: 8, border: "1px solid var(--lp-border)", padding: 16, fontSize: 13, color: "var(--lp-text2)", lineHeight: 1.75, fontFamily: "monospace" }}>
          Hey, I need a mobile app like Instagram but for pets. Should have login, profiles for pets, photo sharing, followers, DMs, stories, a marketplace for pet products, vet appointment booking, and an AI chatbot. Need it in 2 weeks. Budget is flexible but keep it cheap. Let me know!
        </div>
        <div style={{ marginTop: 16, display: "flex", gap: 8 }}>
          <div style={{ background: "rgba(139,124,255,0.1)", border: "1px solid rgba(139,124,255,0.25)", borderRadius: 6, padding: "4px 10px", fontSize: 12, color: "var(--lp-violet)", fontWeight: 600 }}>
            ⚠ 8 ambiguities detected
          </div>
          <div style={{ background: "rgba(245,158,11,0.1)", border: "1px solid rgba(245,158,11,0.25)", borderRadius: 6, padding: "4px 10px", fontSize: 12, color: "#f59e0b", fontWeight: 600 }}>
            ⏱ Timeline unrealistic
          </div>
        </div>
      </div>
    ),
  },
  {
    id: "requirements",
    label: "Requirements",
    content: (
      <div style={{ padding: 20 }}>
        <p style={{ fontSize: 12, color: "var(--lp-text2)", margin: "0 0 12px", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em" }}>Structured — After AI Analysis</p>
        {[
          { section: "Core features", items: ["User auth (email + OAuth)", "Pet profile CRUD", "Photo/video feed with likes/comments", "Follower/following system"] },
          { section: "Clarifications needed", items: ["iOS, Android, or cross-platform?", "Define 'flexible budget' — estimate needed", "2-week timeline is not feasible for full scope"] },
          { section: "Risks", items: ["Scope creep: 9 major features listed", "Marketplace requires payment integration (PCI scope)"] },
        ].map((s) => (
          <div key={s.section} style={{ marginBottom: 16 }}>
            <p style={{ fontSize: 11, fontWeight: 700, color: "var(--lp-violet)", margin: "0 0 6px", textTransform: "uppercase", letterSpacing: "0.06em" }}>{s.section}</p>
            {s.items.map((item) => (
              <div key={item} style={{ display: "flex", gap: 8, padding: "3px 0", fontSize: 13, color: "var(--lp-text2)", alignItems: "flex-start" }}>
                <span style={{ color: "var(--lp-violet)", marginTop: 1 }}>›</span>
                <span>{item}</span>
              </div>
            ))}
          </div>
        ))}
      </div>
    ),
  },
  {
    id: "tasks",
    label: "Project Plan",
    content: (
      <div style={{ padding: 20 }}>
        <p style={{ fontSize: 12, color: "var(--lp-text2)", margin: "0 0 12px", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em" }}>Generated task plan</p>
        {[
          { task: "Design DB schema — Users, Pets, Posts, Follows", priority: "P1", status: "todo", est: "3h" },
          { task: "Implement auth service (JWT + refresh tokens)", priority: "P1", status: "in-progress", est: "6h" },
          { task: "Build Pet profile CRUD API", priority: "P1", status: "todo", est: "4h" },
          { task: "Photo upload + CDN integration", priority: "P2", status: "todo", est: "5h" },
          { task: "Feed algorithm (chronological v1)", priority: "P2", status: "todo", est: "8h" },
        ].map((t) => (
          <div key={t.task} style={{ display: "flex", alignItems: "center", gap: 10, padding: "7px 0", borderBottom: "1px solid rgba(255,255,255,0.04)", fontSize: 13 }}>
            <div style={{
              width: 8, height: 8, borderRadius: "50%",
              background: t.status === "in-progress" ? "var(--lp-violet)" : "var(--lp-border2)",
              flexShrink: 0,
            }} />
            <span style={{ flex: 1, color: "var(--lp-text)" }}>{t.task}</span>
            <span style={{ fontSize: 11, color: t.priority === "P1" ? "#f59e0b" : "var(--lp-text2)", fontWeight: 600 }}>{t.priority}</span>
            <span style={{ fontSize: 11, color: "var(--lp-text2)" }}>{t.est}</span>
          </div>
        ))}
      </div>
    ),
  },
];

function InteractivePreview() {
  const [tab, setTab] = useState("brief");
  const active = PREVIEW_TABS.find((t) => t.id === tab)!;

  return (
    <Section style={{ borderTop: "1px solid var(--lp-border)" }}>
      <div style={{ textAlign: "center", marginBottom: 48 }}>
        <SectionLabel>See it in action</SectionLabel>
        <SectionHeading>From brief to plan</SectionHeading>
        <SectionSubtitle>Watch how a vague client message becomes a structured, actionable project plan.</SectionSubtitle>
      </div>
      <div style={{ background: "var(--lp-card)", border: "1px solid var(--lp-border2)", borderRadius: 16, overflow: "hidden", boxShadow: "0 20px 60px rgba(0,0,0,0.5)" }}>
        {/* Tabs */}
        <div style={{ display: "flex", borderBottom: "1px solid var(--lp-border)", background: "var(--lp-bg2)" }}>
          {PREVIEW_TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              style={{
                padding: "12px 20px",
                fontSize: 13,
                fontWeight: tab === t.id ? 700 : 400,
                color: tab === t.id ? "var(--lp-violet)" : "var(--lp-text2)",
                background: "none",
                border: "none",
                borderBottom: tab === t.id ? "2px solid var(--lp-violet)" : "2px solid transparent",
                cursor: "pointer",
                transition: "color 0.15s",
              }}
            >
              {t.label}
            </button>
          ))}
        </div>
        {/* Content */}
        <div style={{ minHeight: 280 }}>
          {active.content}
        </div>
      </div>
    </Section>
  );
}

/* ─── Who it's for ───────────────────────────────────────────────── */
const WHO = [
  {
    title: "Solo freelance developers",
    desc: "You take projects solo. TaskMate gives you a structured workflow to handle client briefs, manage tasks, and deliver proposals without an operations team.",
  },
  {
    title: "Developer-consultants",
    desc: "You advise clients and build things. TaskMate's requirement analysis and milestone tracking keep multi-phase projects accountable.",
  },
  {
    title: "Small dev shops (2–5 people)",
    desc: "A shared workspace to coordinate tasks, proposals, and client communications without heavyweight enterprise PM overhead.",
  },
];

function WhoSection() {
  return (
    <Section style={{
      background: "linear-gradient(180deg, var(--lp-bg2) 0%, var(--lp-bg) 100%)",
      borderTop: "1px solid var(--lp-border)",
      borderBottom: "1px solid var(--lp-border)",
    }}>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 64, alignItems: "center" }} className="lp-hero-grid">
        <div>
          <SectionLabel>Who it&apos;s for</SectionLabel>
          <SectionHeading>Made for developers who run their own show</SectionHeading>
          <p style={{ fontSize: 17, color: "var(--lp-text2)", lineHeight: 1.7, margin: 0 }}>
            TaskMate is opinionated. It is not built for 500-person enterprises or PMs who have never opened a terminal. It is built for developers who need to think clearly about their projects and clients.
          </p>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {WHO.map((w) => (
            <div key={w.title} style={{ background: "var(--lp-card)", border: "1px solid var(--lp-border)", borderRadius: 14, padding: 24, display: "flex", gap: 16, alignItems: "flex-start" }}>
              <div style={{ width: 32, height: 32, borderRadius: 8, background: "rgba(139,124,255,0.12)", border: "1px solid rgba(139,124,255,0.25)", flexShrink: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <CheckIcon size={14} />
              </div>
              <div>
                <h3 style={{ fontSize: 15, fontWeight: 700, color: "var(--lp-text)", margin: "0 0 6px" }}>{w.title}</h3>
                <p style={{ fontSize: 13, color: "var(--lp-text2)", lineHeight: 1.65, margin: 0 }}>{w.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </Section>
  );
}

/* ─── FAQ ────────────────────────────────────────────────────────── */
const FAQS = [
  {
    q: "Is the AI locally trained or does it call external APIs?",
    a: "TaskMate ships with a locally trained TF-IDF + Logistic Regression intent classifier for routing workspace queries. The analysis pipeline can use any OpenAI-compatible provider you configure. No data leaves your machine unless you connect an external provider.",
  },
  {
    q: "Does it require an OpenAI API key?",
    a: "No. TaskMate works with any OpenAI-compatible endpoint including local models via Ollama. The default provider is configurable in your environment file. The intent classifier runs entirely offline.",
  },
  {
    q: "Is proposal generation fully automated?",
    a: "The pipeline generates a structured proposal draft after requirements are approved by you. It includes scope, deliverables, assumptions, exclusions, and timeline estimates. You review and edit before sending.",
  },
  {
    q: "Does the AI ever make changes without my approval?",
    a: "No. Every WRITE action — creating tasks, updating project data, or sending proposals — requires explicit developer approval. Read-only queries (listing tasks, fetching project info) run without a prompt.",
  },
  {
    q: "What's the current development status?",
    a: "TaskMate V1 is complete. The core pipeline (requirement analysis → task planning → proposal generation), client management, milestones, dependencies, and the local intent classifier are all implemented and tested. This is an active project in development.",
  },
  {
    q: "Can I run it on my own machine?",
    a: "Yes. TaskMate is a full-stack app (FastAPI backend + Next.js frontend) that runs locally with SQLite. A Docker Compose setup is included for clean-machine deployment. No external database required.",
  },
];

function FAQSection() {
  const [open, setOpen] = useState<number | null>(null);
  return (
    <Section id="faq" style={{ borderTop: "1px solid var(--lp-border)" }}>
      <div style={{ maxWidth: 720, margin: "0 auto" }}>
        <div style={{ textAlign: "center", marginBottom: 48 }}>
          <SectionLabel>FAQ</SectionLabel>
          <SectionHeading>Common questions</SectionHeading>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {FAQS.map((faq, i) => (
            <div
              key={i}
              style={{
                background: "var(--lp-card)",
                border: `1px solid ${open === i ? "rgba(139,124,255,0.3)" : "var(--lp-border)"}`,
                borderRadius: 12,
                overflow: "hidden",
                transition: "border-color 0.2s",
              }}
            >
              <button
                onClick={() => setOpen(open === i ? null : i)}
                style={{
                  width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between",
                  gap: 16, padding: "18px 22px", background: "none", border: "none",
                  cursor: "pointer", textAlign: "left",
                }}
                aria-expanded={open === i}
              >
                <span style={{ fontSize: 15, fontWeight: 600, color: "var(--lp-text)" }}>{faq.q}</span>
                <span style={{ flexShrink: 0, color: "var(--lp-text2)", transform: open === i ? "rotate(180deg)" : "none", transition: "transform 0.2s" }}>
                  <ChevronDown size={18} />
                </span>
              </button>
              {open === i && (
                <div style={{ padding: "0 22px 20px", fontSize: 14, color: "var(--lp-text2)", lineHeight: 1.75 }}>
                  {faq.a}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </Section>
  );
}

/* ─── Final CTA ──────────────────────────────────────────────────── */
function FinalCTA() {
  return (
    <section style={{ padding: "80px 24px", position: "relative", overflow: "hidden" }}>
      <div style={{ position: "absolute", inset: 0, background: "radial-gradient(ellipse at 50% 0%, rgba(139,124,255,0.15) 0%, transparent 65%)", pointerEvents: "none" }} />
      <div style={{ maxWidth: 700, margin: "0 auto", textAlign: "center", position: "relative" }}>
        <SectionLabel>Get started</SectionLabel>
        <h2 style={{ fontSize: "clamp(30px, 4.5vw, 48px)", fontWeight: 900, color: "var(--lp-text)", letterSpacing: "-0.03em", lineHeight: 1.1, margin: "0 0 20px" }}>
          Stop wrestling with requirements.{" "}
          <span style={{ background: "linear-gradient(135deg, #8B7CFF, #66A6FF)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            Start shipping.
          </span>
        </h2>
        <p style={{ fontSize: 17, color: "var(--lp-text2)", lineHeight: 1.7, marginBottom: 36 }}>
          TaskMate AI is free to run locally. Set up takes about 5 minutes with Docker Compose or the development script.
        </p>
        <div style={{ display: "flex", gap: 12, justifyContent: "center", flexWrap: "wrap" }}>
          <Link
            href="/register"
            style={{
              display: "inline-flex", alignItems: "center", gap: 8,
              padding: "14px 32px", borderRadius: 10, fontSize: 16, fontWeight: 700,
              color: "#fff", textDecoration: "none",
              background: "linear-gradient(135deg, #8B7CFF, #66A6FF)",
              boxShadow: "0 0 40px rgba(139,124,255,0.4)",
            }}
          >
            Create your workspace <ArrowRight size={18} />
          </Link>
          <Link
            href="/login"
            style={{
              display: "inline-flex", alignItems: "center",
              padding: "14px 28px", borderRadius: 10, fontSize: 15, fontWeight: 600,
              color: "var(--lp-text2)", textDecoration: "none",
              border: "1px solid var(--lp-border2)",
            }}
          >
            Sign in
          </Link>
        </div>
      </div>
    </section>
  );
}

/* ─── Footer ─────────────────────────────────────────────────────── */
function LandingFooter() {
  return (
    <footer style={{ borderTop: "1px solid var(--lp-border)", padding: "40px 24px" }}>
      <div style={{ maxWidth: 1120, margin: "0 auto", display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 16 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <LogoMark size={22} />
          <span style={{ fontSize: 14, fontWeight: 700, color: "var(--lp-text)" }}>TaskMate AI</span>
          <span style={{ fontSize: 13, color: "var(--lp-text2)", marginLeft: 8 }}>— AI project assistant for freelance developers</span>
        </div>
        <div style={{ display: "flex", gap: 24 }}>
          {[
            { label: "Dashboard", href: "/dashboard" },
            { label: "Log in", href: "/login" },
            { label: "Register", href: "/register" },
          ].map((l) => (
            <Link key={l.href} href={l.href} style={{ fontSize: 13, color: "var(--lp-text2)", textDecoration: "none" }}>
              {l.label}
            </Link>
          ))}
        </div>
        <p style={{ fontSize: 12, color: "var(--lp-text2)", margin: 0 }}>
          © {new Date().getFullYear()} TaskMate AI. V1.
        </p>
      </div>
    </footer>
  );
}

/* ─── Responsive CSS ─────────────────────────────────────────────── */
function ResponsiveStyles() {
  return (
    <style>{`
      .lp-desktop-nav { display: flex; }
      .lp-hamburger { display: none; }
      .lp-mobile-menu { display: flex; }
      .lp-hero-grid { grid-template-columns: 1fr 1fr; }
      .lp-3col { grid-template-columns: repeat(3, 1fr); }
      .lp-bento { grid-template-columns: repeat(3, 1fr); }

      .lp-feature-card:hover {
        border-color: rgba(139,124,255,0.3);
        transform: translateY(-2px);
      }

      @media (max-width: 900px) {
        .lp-hero-grid { grid-template-columns: 1fr !important; }
        .lp-3col { grid-template-columns: 1fr !important; }
        .lp-bento { grid-template-columns: repeat(2, 1fr) !important; }
      }

      @media (max-width: 640px) {
        .lp-desktop-nav { display: none !important; }
        .lp-hamburger { display: flex !important; }
        .lp-bento { grid-template-columns: 1fr !important; }
        .lp-feature-card { grid-column: span 1 !important; }
      }

      @media (max-width: 900px) {
        .lp-feature-card[data-wide="true"] { grid-column: span 2; }
      }
      @media (max-width: 640px) {
        .lp-feature-card[data-wide="true"] { grid-column: span 1; }
      }
    `}</style>
  );
}

/* ─── Page ───────────────────────────────────────────────────────── */
export default function LandingPage() {
  return (
    <div
      className="landing"
      style={{ minHeight: "100vh", background: "var(--lp-bg)", color: "var(--lp-text)", fontFamily: "Inter, system-ui, -apple-system, sans-serif" }}
    >
      <ResponsiveStyles />
      <LandingNav />
      <HeroSection />
      <ProblemSection />
      <WorkflowSection />
      <FeaturesSection />
      <InteractivePreview />
      <WhoSection />
      <FAQSection />
      <FinalCTA />
      <LandingFooter />
    </div>
  );
}
