"use client";

import React, { useState } from "react";
import { Header } from "../../components/admin/Header";
import { Sidebar } from "../../components/admin/Sidebar";
import { ToastProvider } from "../../components/admin/Toast";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <ToastProvider>
      <div className={`admin-app-shell ${isCollapsed ? "shell-collapsed" : ""}`}>
        <Sidebar
          isMobileOpen={isMobileOpen}
          onMobileClose={() => setIsMobileOpen(false)}
          isCollapsed={isCollapsed}
          onToggleCollapse={() => setIsCollapsed(!isCollapsed)}
        />

        <div className="admin-main-viewport">
          <Header
            onMobileMenuClick={() => setIsMobileOpen(true)}
          />

          <main className="admin-page-content">{children}</main>
        </div>
      </div>
    </ToastProvider>
  );
}
