import React from "react";

interface TaskEvent {
  id: string;
  event_type: string;
  created_at: string;
  old_value?: string;
  new_value?: string;
  user_name?: string;
}

interface ActivityTimelineProps {
  events: TaskEvent[];
}

export default function ActivityTimeline({ events }: ActivityTimelineProps) {
  if (!events || events.length === 0) {
    return (
      <div className="text-sm text-[var(--text-muted)]">
        No activity recorded yet.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {events.map((event) => (
        <div key={event.id} className="flex gap-4">
          <div className="mt-1">
            <div className="w-2 h-2 rounded-full bg-[var(--primary)]" />
          </div>
          <div>
            <div className="text-sm font-medium">
              {event.user_name || "System"}{" "}
              {event.event_type.replace("_", " ").toLowerCase()}
            </div>
            {event.old_value && event.new_value && (
              <div className="text-xs text-[var(--text-muted)] mt-1">
                Changed from{" "}
                <span className="line-through">{event.old_value}</span> to{" "}
                <span>{event.new_value}</span>
              </div>
            )}
            <div className="text-xs text-[var(--text-muted)] mt-1">
              {new Date(event.created_at).toLocaleString()}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
