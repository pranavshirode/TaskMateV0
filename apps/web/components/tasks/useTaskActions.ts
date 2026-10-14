"use client";

import { useCallback } from "react";
import { apiClient, type Task } from "@/lib/api-client";
import { errorMessage, humanize } from "@/lib/format";
import { useFeedback } from "@/components/ui/Feedback";

/**
 * Status changes with optimistic UI and an "Undo" toast.
 * `onChange` receives the task with its new status (or the reverted one on failure/undo).
 */
export function useTaskActions(onChange: (task: Task) => void) {
  const { toast } = useFeedback();

  const setStatus = useCallback(
    async (task: Task, status: string) => {
      if (task.status === status) return;
      const previous = task.status;
      onChange({ ...task, status });
      try {
        const updated = await apiClient.changeTaskStatus(task.id, status);
        onChange({ ...task, ...updated });
        toast(
          status === "COMPLETED"
            ? `Completed "${task.title}"`
            : `Moved "${task.title}" to ${humanize(status)}`,
          "success",
          {
            label: "Undo",
            onClick: async () => {
              onChange({ ...task, status: previous });
              try {
                await apiClient.changeTaskStatus(task.id, previous);
              } catch (err) {
                toast(errorMessage(err, "Undo failed"), "error");
              }
            },
          }
        );
      } catch (err) {
        onChange({ ...task, status: previous });
        toast(errorMessage(err, "Could not update the task"), "error");
      }
    },
    [onChange, toast]
  );

  const toggleComplete = useCallback(
    (task: Task) =>
      setStatus(task, task.status === "COMPLETED" ? "TODO" : "COMPLETED"),
    [setStatus]
  );

  return { setStatus, toggleComplete };
}
