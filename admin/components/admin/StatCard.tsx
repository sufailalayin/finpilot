import React from "react";

interface StatCardProps {
  title: string;
  value: string | number;
  subtext?: string;
  trend?: {
    value: string;
    isPositive?: boolean;
    isNeutral?: boolean;
  };
  icon?: React.ReactNode;
  onClick?: () => void;
  className?: string;
}

export function StatCard({
  title,
  value,
  subtext,
  trend,
  icon,
  onClick,
  className = "",
}: StatCardProps) {
  return (
    <div
      className={`stat-card ${onClick ? "stat-card-clickable" : ""} ${className}`}
      onClick={onClick}
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      <div className="stat-card-header">
        <span className="stat-card-title">{title}</span>
        {icon && <div className="stat-card-icon">{icon}</div>}
      </div>

      <div className="stat-card-body">
        <span className="stat-card-value">{value}</span>
      </div>

      {(subtext || trend) && (
        <div className="stat-card-footer">
          {trend && (
            <span
              className={`stat-card-trend ${
                trend.isNeutral
                  ? "trend-neutral"
                  : trend.isPositive
                    ? "trend-positive"
                    : "trend-negative"
              }`}
            >
              {trend.isPositive ? "↑ " : trend.isNeutral ? "• " : "↓ "}
              {trend.value}
            </span>
          )}
          {subtext && <span className="stat-card-subtext">{subtext}</span>}
        </div>
      )}
    </div>
  );
}
