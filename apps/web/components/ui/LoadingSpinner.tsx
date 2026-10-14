export default function LoadingSpinner({ size = 24 }: { size?: number }) {
  return (
    <div
      className="inline-block animate-spin rounded-full border-2 border-[var(--sidebar-border)] border-t-[var(--primary)] motion-reduce:animate-[spin_1.5s_linear_infinite]"
      style={{ width: size, height: size }}
      role="status"
    >
      <span className="sr-only">Loading...</span>
    </div>
  );
}
