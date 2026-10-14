"use client";

import AssistantChat from "@/components/ai/AssistantChat";

// Kept for existing links; this is the same assistant as /ai, opened in Agent mode.
export default function AssistantPage() {
  return <AssistantChat defaultMode="agent" />;
}
