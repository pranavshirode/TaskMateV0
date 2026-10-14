import React from "react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger" | "ghost";
}

export default function Button({
  variant = "primary",
  className = "",
  children,
  ...props
}: ButtonProps) {
  const baseClasses =
    "px-4 py-2 rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed";

  const variants = {
    primary:
      "bg-[var(--primary)] hover:bg-[var(--primary-hover)] text-white focus:ring-[var(--primary)]",
    secondary:
      "bg-[var(--sidebar-bg)] hover:bg-[var(--sidebar-border)] text-[var(--foreground)] border border-[var(--sidebar-border)] focus:ring-[var(--sidebar-border)]",
    danger: "bg-red-600 hover:bg-red-700 text-white focus:ring-red-500",
    ghost:
      "bg-transparent hover:bg-[var(--sidebar-border)] text-[var(--foreground)] focus:ring-[var(--sidebar-border)]",
  };

  return (
    <button
      className={`${baseClasses} ${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
