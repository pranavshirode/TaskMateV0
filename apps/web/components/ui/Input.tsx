import React from "react";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
}

export default function Input({
  label,
  error,
  hint,
  className = "",
  id,
  ...props
}: InputProps) {
  const inputId =
    id ||
    (label ? `input-${label.replace(/\W+/g, "-").toLowerCase()}` : undefined);
  return (
    <div className="flex flex-col gap-1.5 w-full">
      {label && (
        <label
          htmlFor={inputId}
          className="text-sm font-medium text-[var(--foreground)]"
        >
          {label}
        </label>
      )}
      <input
        id={inputId}
        className={`field ${error ? "!border-[var(--danger)]" : ""} ${className}`}
        {...props}
      />
      {error ? (
        <span className="text-xs text-[var(--danger)]">{error}</span>
      ) : (
        hint && <span className="text-xs text-[var(--text-muted)]">{hint}</span>
      )}
    </div>
  );
}
