"use client";

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import CommandPalette from "./CommandPalette";
import QuickAddTask, { type QuickAddDefaults } from "./QuickAddTask";

// Workspace-wide UI state: the command palette, the quick-add task dialog, and a
// `dataVersion` counter pages can depend on to refetch after a global action
// (e.g. a task created from the header) changes data they are showing.

interface WorkspaceUIContextType {
  openPalette: () => void;
  openQuickAdd: (defaults?: QuickAddDefaults) => void;
  dataVersion: number;
  notifyDataChanged: () => void;
}

const WorkspaceUIContext = createContext<WorkspaceUIContextType>({
  openPalette: () => {},
  openQuickAdd: () => {},
  dataVersion: 0,
  notifyDataChanged: () => {},
});

function isTypingTarget(target: EventTarget | null) {
  if (!(target instanceof HTMLElement)) return false;
  return (
    target.isContentEditable ||
    ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName)
  );
}

export function WorkspaceUIProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [quickAdd, setQuickAdd] = useState<QuickAddDefaults | null>(null);
  const [dataVersion, setDataVersion] = useState(0);

  const openPalette = useCallback(() => setPaletteOpen(true), []);
  const openQuickAdd = useCallback(
    (defaults?: QuickAddDefaults) => setQuickAdd(defaults || {}),
    []
  );
  const notifyDataChanged = useCallback(() => setDataVersion((v) => v + 1), []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPaletteOpen((open) => !open);
        return;
      }
      if (e.metaKey || e.ctrlKey || e.altKey || isTypingTarget(e.target))
        return;
      if (paletteOpen || quickAdd) return;
      if (e.key === "c") {
        e.preventDefault();
        setQuickAdd({});
      } else if (e.key === "/") {
        e.preventDefault();
        setPaletteOpen(true);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [paletteOpen, quickAdd]);

  return (
    <WorkspaceUIContext.Provider
      value={{ openPalette, openQuickAdd, dataVersion, notifyDataChanged }}
    >
      {children}
      {paletteOpen && (
        <CommandPalette
          onClose={() => setPaletteOpen(false)}
          onQuickAdd={(defaults) => {
            setPaletteOpen(false);
            setQuickAdd(defaults);
          }}
        />
      )}
      {quickAdd && (
        <QuickAddTask
          defaults={quickAdd}
          onClose={() => setQuickAdd(null)}
          onCreated={notifyDataChanged}
        />
      )}
    </WorkspaceUIContext.Provider>
  );
}

export function useWorkspaceUI() {
  return useContext(WorkspaceUIContext);
}
