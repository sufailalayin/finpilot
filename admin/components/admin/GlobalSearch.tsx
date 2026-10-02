"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { fetchAdminUsers, fetchBillingPlans } from "../../lib/api";
import { Modal } from "./Modal";

interface SearchResult {
  id: string;
  type: "user" | "plan" | "page";
  title: string;
  subtitle: string;
  url: string;
}

const STATIC_PAGES: SearchResult[] = [
  { id: "p1", type: "page", title: "Overview Dashboard", subtitle: "KPIs, revenue, users, charts", url: "/" },
  { id: "p2", type: "page", title: "Customer Management", subtitle: "Search, filter, view 360", url: "/users" },
  { id: "p3", type: "page", title: "Subscriptions", subtitle: "Plan conversion and distribution", url: "/subscriptions" },
  { id: "p4", type: "page", title: "Billing Plans", subtitle: "Create and configure plans", url: "/plans" },
  { id: "p5", type: "page", title: "Payments", subtitle: "Accounting, receipts, voiding", url: "/payments" },
  { id: "p6", type: "page", title: "AI Usage", subtitle: "Token and query analytics", url: "/ai" },
  { id: "p7", type: "page", title: "App Releases", subtitle: "OTA and Play Store updates", url: "/release" },
  { id: "p8", type: "page", title: "Security Events", subtitle: "Logins, IP addresses, failures", url: "/security" },
  { id: "p9", type: "page", title: "Admin Audit Logs", subtitle: "Immutable historical changes", url: "/logs" },
  { id: "p10", type: "page", title: "System Health", subtitle: "Readiness checks and test email", url: "/system" },
];

interface GlobalSearchProps {
  isOpen: boolean;
  onClose: () => void;
}

export function GlobalSearch({ isOpen, onClose }: GlobalSearchProps) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>(STATIC_PAGES);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!isOpen) {
      setQuery("");
      setResults(STATIC_PAGES);
      return;
    }
  }, [isOpen]);

  useEffect(() => {
    if (!query.trim()) {
      setResults(STATIC_PAGES);
      return;
    }

    const term = query.toLowerCase().trim();
    const matchedPages = STATIC_PAGES.filter(
      (p) => p.title.toLowerCase().includes(term) || p.subtitle.toLowerCase().includes(term),
    );

    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const [usersRes, plansRes] = await Promise.all([
          fetchAdminUsers({ q: term, page_size: 5 }).catch(() => ({ items: [] })),
          fetchBillingPlans().catch(() => []),
        ]);

        const userResults: SearchResult[] = (usersRes.items || []).map((u) => ({
          id: `u-${u.id}`,
          type: "user",
          title: u.full_name || u.email,
          subtitle: `${u.email} · ${u.plan_code?.toUpperCase() || "FREE"} (${u.user_status})`,
          url: `/users?q=${encodeURIComponent(u.email)}`,
        }));

        const planResults: SearchResult[] = (plansRes || [])
          .filter((p) => p.name.toLowerCase().includes(term) || p.code.toLowerCase().includes(term))
          .map((p) => ({
            id: `plan-${p.id}`,
            type: "plan",
            title: p.name,
            subtitle: `${p.code} · ${p.currency} ${p.price} / ${p.billing_period}`,
            url: "/plans",
          }));

        setResults([...matchedPages, ...userResults, ...planResults]);
      } finally {
        setLoading(false);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [query]);

  function handleSelect(item: SearchResult) {
    onClose();
    router.push(item.url);
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Quick Finder"
      description="Search customers, plans, payments, and system pages"
      maxWidth="640px"
    >
      <div className="global-search-container">
        <div className="search-input-wrapper">
          <span className="search-input-icon">🔍</span>
          <input
            type="text"
            className="global-search-input"
            placeholder="Type customer email, plan name, or page (e.g. 'John', 'Pro', 'Payments')..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoFocus
          />
          {loading && <span className="search-loading-spinner" />}
        </div>

        <div className="search-results-list">
          {results.length === 0 ? (
            <div className="search-no-results">
              No matching records found for &ldquo;{query}&rdquo;
            </div>
          ) : (
            results.map((item) => (
              <div
                key={item.id}
                className="search-result-item"
                onClick={() => handleSelect(item)}
              >
                <div className="result-type-badge">
                  {item.type === "page" && "📄 Page"}
                  {item.type === "user" && "👤 Customer"}
                  {item.type === "plan" && "💳 Plan"}
                </div>
                <div className="result-content">
                  <div className="result-title">{item.title}</div>
                  <div className="result-subtitle">{item.subtitle}</div>
                </div>
                <span className="result-jump-arrow">→</span>
              </div>
            ))
          )}
        </div>
      </div>
    </Modal>
  );
}
