"use client";

import React, { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { fetchSystemReadiness } from "../../lib/api";
import { GlobalSearch } from "./GlobalSearch";

interface HeaderProps {
  onMobileMenuClick: () => void;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

const PAGE_TITLES: Record<string, { title: string; subtitle: string }> = {
  "/": {
    title: "Executive Overview",
    subtitle: "Real-time key performance indicators, revenue, and active subscriptions",
  },
  "/users": {
    title: "Customer Management",
    subtitle: "Search, filter, view 360 customer profiles and manage user access",
  },
  "/subscriptions": {
    title: "Subscriptions",
    subtitle: "Distribution, conversion metrics, and plan assignments",
  },
  "/plans": {
    title: "Billing Plans",
    subtitle: "Create, price, and maintain FinPilot billing tiers",
  },
  "/payments": {
    title: "Payment Records",
    subtitle: "Audit recorded revenue, payment methods, and void transactions safely",
  },
  "/ai": {
    title: "AI Consumption",
    subtitle: "Request volumes, prompt and response character trends, and top users",
  },
  "/release": {
    title: "App Releases",
    subtitle: "Manage mobile application versions and enforce critical upgrades",
  },
  "/security": {
    title: "Security & Sessions",
    subtitle: "Monitor authentication events, device logins, and active sessions",
  },
  "/logs": {
    title: "Audit History",
    subtitle: "Immutable record of all administrative mutations and security actions",
  },
  "/system": {
    title: "System Health & Config",
    subtitle: "Production readiness checks, email testing, and infrastructure status",
  },
};

export function Header({
  onMobileMenuClick,
  onRefresh,
  isRefreshing = false,
}: HeaderProps) {
  const pathname = usePathname();
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [readinessStatus, setReadinessStatus] = useState<string>("checking");

  useEffect(() => {
    fetchSystemReadiness()
      .then((res) => {
        setReadinessStatus(res.status || "healthy");
      })
      .catch(() => {
        setReadinessStatus("degraded");
      });
  }, []);

  // Keyboard shortcut Cmd+K or Ctrl+K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setIsSearchOpen(true);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const meta = PAGE_TITLES[pathname] || {
    title: "Admin Console",
    subtitle: "FinPilot Management Portal",
  };

  return (
    <>
      <header className="admin-header">
        <div className="header-left">
          <button
            className="mobile-hamburger-btn"
            onClick={onMobileMenuClick}
            aria-label="Open mobile navigation"
          >
            ☰
          </button>
          <div className="header-titles">
            <h1 className="header-page-title">{meta.title}</h1>
            <p className="header-page-subtitle">{meta.subtitle}</p>
          </div>
        </div>

        <div className="header-right">
          {/* Global search trigger */}
          <button
            className="header-search-btn"
            onClick={() => setIsSearchOpen(true)}
            title="Search (Ctrl + K)"
          >
            <span className="search-icon">🔍</span>
            <span className="search-text">Search...</span>
            <kbd className="search-shortcut">⌘K</kbd>
          </button>

          {/* System readiness pill */}
          <div
            className={`header-status-pill status-${
              readinessStatus === "healthy" || readinessStatus === "ready"
                ? "good"
                : readinessStatus === "checking"
                  ? "warn"
                  : "bad"
            }`}
          >
            <span className="status-dot" />
            <span className="status-label">
              {readinessStatus === "checking"
                ? "Checking System"
                : readinessStatus === "healthy" || readinessStatus === "ready"
                  ? "Systems Healthy"
                  : "Service Degraded"}
            </span>
          </div>

          {/* Refresh button */}
          {onRefresh && (
            <button
              className="header-action-btn"
              onClick={onRefresh}
              disabled={isRefreshing}
              title="Refresh Data"
            >
              <span className={`refresh-icon ${isRefreshing ? "spin" : ""}`}>
                ↻
              </span>
              <span className="btn-label">Refresh</span>
            </button>
          )}

          {/* Admin badge */}
          <div className="admin-profile-pill">
            <div className="admin-avatar">A</div>
            <div className="admin-details">
              <span className="admin-role">ADMIN</span>
              <span className="admin-org">FinPilot</span>
            </div>
          </div>
        </div>
      </header>

      <GlobalSearch
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
      />
    </>
  );
}
