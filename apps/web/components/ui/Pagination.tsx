import React from "react";
import Button from "./Button";

interface PaginationProps {
  page?: number;
  currentPage?: number;
  pageSize?: number;
  total?: number;
  totalPages?: number;
  onPageChange: (page: number) => void;
}

export default function Pagination({
  page,
  currentPage,
  pageSize,
  total,
  totalPages: totalPagesProp,
  onPageChange,
}: PaginationProps) {
  const current = page ?? currentPage ?? 1;
  const pages =
    totalPagesProp ?? (total && pageSize ? Math.ceil(total / pageSize) : 1);

  if (pages <= 1) return null;

  return (
    <div className="flex items-center justify-center gap-2 mt-6">
      <Button
        variant="secondary"
        onClick={() => onPageChange(current - 1)}
        disabled={current === 1}
      >
        Previous
      </Button>
      <span className="text-sm text-[var(--text-muted)]">
        Page {current} of {pages}
      </span>
      <Button
        variant="secondary"
        onClick={() => onPageChange(current + 1)}
        disabled={current === pages}
      >
        Next
      </Button>
    </div>
  );
}
