"use client";

import React, {
  createContext,
  useCallback,
  useContext,
  useRef,
  useState,
} from "react";
import Icon from "./Icon";
import Modal from "./Modal";
import Button from "./Button";

// In-app replacement for window.alert / window.confirm: non-blocking toasts and
// a promise-based confirm dialog.

type ToastTone = "success" | "error" | "info";

interface Toast {
  id: number;
  message: string;
  tone: ToastTone;
  action?: { label: string; onClick: () => void };
}

interface ConfirmOptions {
  title: string;
  message?: string;
  confirmLabel?: string;
  danger?: boolean;
}

interface FeedbackContextType {
  toast: (message: string, tone?: ToastTone, action?: Toast["action"]) => void;
  confirm: (options: ConfirmOptions) => Promise<boolean>;
}

const noop: FeedbackContextType = {
  toast: () => {},
  confirm: async () => true,
};

const FeedbackContext = createContext<FeedbackContextType>(noop);

export function FeedbackProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [confirmState, setConfirmState] = useState<ConfirmOptions | null>(null);
  const resolver = useRef<((ok: boolean) => void) | null>(null);
  const nextId = useRef(1);

  const dismiss = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const toast = useCallback<FeedbackContextType["toast"]>(
    (message, tone = "success", action) => {
      const id = nextId.current++;
      setToasts((prev) => [...prev.slice(-3), { id, message, tone, action }]);
      setTimeout(() => dismiss(id), tone === "error" ? 6000 : 4000);
    },
    [dismiss]
  );

  const confirm = useCallback((options: ConfirmOptions) => {
    setConfirmState(options);
    return new Promise<boolean>((resolve) => {
      resolver.current = resolve;
    });
  }, []);

  const settle = (ok: boolean) => {
    resolver.current?.(ok);
    resolver.current = null;
    setConfirmState(null);
  };

  const toneStyles: Record<ToastTone, string> = {
    success: "text-[var(--success)]",
    error: "text-[var(--danger)]",
    info: "text-[var(--primary)]",
  };

  return (
    <FeedbackContext.Provider value={{ toast, confirm }}>
      {children}

      <div
        aria-live="polite"
        className="pointer-events-none fixed bottom-4 right-4 z-[60] flex w-[calc(100%-2rem)] max-w-sm flex-col gap-2"
      >
        {toasts.map((t) => (
          <div
            key={t.id}
            className="animate-pop pointer-events-auto flex items-start gap-3 rounded-lg border border-[var(--sidebar-border)] bg-[var(--sidebar-bg)] px-4 py-3 text-sm"
            style={{ boxShadow: "var(--shadow-lg)" }}
          >
            <Icon
              name={
                t.tone === "error"
                  ? "alert"
                  : t.tone === "info"
                    ? "sparkles"
                    : "check"
              }
              size={16}
              className={`mt-0.5 ${toneStyles[t.tone]}`}
            />
            <span className="flex-1 whitespace-pre-wrap">{t.message}</span>
            {t.action && (
              <button
                className="font-medium text-[var(--primary)] hover:underline"
                onClick={() => {
                  t.action?.onClick();
                  dismiss(t.id);
                }}
              >
                {t.action.label}
              </button>
            )}
            <button
              aria-label="Dismiss"
              onClick={() => dismiss(t.id)}
              className="text-[var(--text-muted)] hover:text-[var(--foreground)]"
            >
              <Icon name="x" size={14} />
            </button>
          </div>
        ))}
      </div>

      <Modal
        isOpen={!!confirmState}
        onClose={() => settle(false)}
        title={confirmState?.title || ""}
      >
        {confirmState?.message && (
          <p className="mb-5 text-sm text-[var(--text-muted)]">
            {confirmState.message}
          </p>
        )}
        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={() => settle(false)}>
            Cancel
          </Button>
          <Button
            autoFocus
            variant={confirmState?.danger ? "danger" : "primary"}
            className={
              confirmState?.danger ? "!bg-[var(--danger)] !text-white" : ""
            }
            onClick={() => settle(true)}
          >
            {confirmState?.confirmLabel || "Confirm"}
          </Button>
        </div>
      </Modal>
    </FeedbackContext.Provider>
  );
}

export function useFeedback() {
  return useContext(FeedbackContext);
}
