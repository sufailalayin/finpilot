import React from "react";

interface StatusBadgeProps {
  status: string | null | undefined;
  variant?: "user" | "entitlement" | "payment" | "plan" | "system" | "default";
}

export function StatusBadge({ status, variant = "default" }: StatusBadgeProps) {
  if (!status) {
    return <span className="badge badge-neutral">—</span>;
  }

  const norm = status.toLowerCase();
  let type = "neutral";

  if (["active", "pro", "received", "healthy", "ready", "pass", "ok"].includes(norm)) {
    type = "success";
  } else if (["trial", "free", "pending", "warn", "degraded"].includes(norm)) {
    type = "warning";
  } else if (
    ["suspended", "deleted", "expired", "cancelled", "failed", "voided", "refunded", "error", "inactive"].includes(
      norm,
    )
  ) {
    type = "danger";
  }

  return (
    <span className={`status-pill pill-${type} pill-${variant}`}>
      <span className="pill-dot" />
      <span className="pill-text">{status.toUpperCase()}</span>
    </span>
  );
}
