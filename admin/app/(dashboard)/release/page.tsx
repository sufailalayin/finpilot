"use client";

import React, { useEffect, useState } from "react";
import { fetchAppRelease, updateAppRelease } from "../../../lib/api";
import { formatDateTime } from "../../../lib/format";
import type { AppRelease } from "../../../lib/types/admin";
import { useToast } from "../../../components/admin/Toast";

export default function AppReleasePage() {
  const { showToast } = useToast();
  const [release, setRelease] = useState<AppRelease | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Form fields
  const [latestVersion, setLatestVersion] = useState("");
  const [latestBuild, setLatestBuild] = useState("");
  const [minVersion, setMinVersion] = useState("");
  const [minBuild, setMinBuild] = useState("");
  const [updateUrl, setUpdateUrl] = useState("");
  const [distribution, setDistribution] = useState<"apk" | "play_store">("apk");
  const [isUpdateEnabled, setIsUpdateEnabled] = useState(false);
  const [releaseNotes, setReleaseNotes] = useState("");

  async function loadRelease() {
    setLoading(true);
    try {
      const data = await fetchAppRelease();
      setRelease(data);
      setLatestVersion(data.latest_version);
      setLatestBuild(String(data.latest_build_number));
      setMinVersion(data.minimum_version);
      setMinBuild(String(data.minimum_build_number));
      setUpdateUrl(data.update_url || "");
      setDistribution(data.distribution);
      setIsUpdateEnabled(data.is_update_enabled);
      setReleaseNotes(data.release_notes || "");
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to load release info", "error");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadRelease();
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const updated = await updateAppRelease({
        latest_version: latestVersion.trim(),
        latest_build_number: parseInt(latestBuild, 10) || 1,
        minimum_version: minVersion.trim(),
        minimum_build_number: parseInt(minBuild, 10) || 1,
        update_url: updateUrl.trim() || null,
        distribution,
        is_update_enabled: isUpdateEnabled,
        release_notes: releaseNotes.trim() || null,
      });
      setRelease(updated);
      showToast("Mobile app release parameters updated successfully", "success");
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Failed to update release configuration", "error");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="dashboard-content">
      <div className="page-header-row">
        <div>
          <h2>App Release & OTA Updates</h2>
          <p className="text-muted">
            Configure client update prompts, minimum required versions, and release notes for the FinPilot Android app.
          </p>
        </div>
      </div>

      <div className="charts-grid-2">
        {/* Form Card */}
        <div className="card panel">
          <div className="section-header">
            <div>
              <h4>Release Parameters</h4>
              <p className="text-muted text-sm">
                Values delivered to mobile clients on launch to determine update enforcement
              </p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="admin-form">
            <div className="form-grid-2">
              <div className="form-group">
                <label>Latest Version</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 1.2.0"
                  value={latestVersion}
                  onChange={(e) => setLatestVersion(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label>Latest Build Number</label>
                <input
                  type="number"
                  required
                  placeholder="e.g. 8"
                  value={latestBuild}
                  onChange={(e) => setLatestBuild(e.target.value)}
                />
              </div>
            </div>

            <div className="form-grid-2">
              <div className="form-group">
                <label>Minimum Required Version</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 1.2.0"
                  value={minVersion}
                  onChange={(e) => setMinVersion(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label>Minimum Required Build</label>
                <input
                  type="number"
                  required
                  placeholder="e.g. 8"
                  value={minBuild}
                  onChange={(e) => setMinBuild(e.target.value)}
                />
              </div>
            </div>

            <div className="form-grid-2">
              <div className="form-group">
                <label>Distribution Channel</label>
                <select
                  value={distribution}
                  onChange={(e) => setDistribution(e.target.value as "apk" | "play_store")}
                >
                  <option value="apk">Direct APK Download</option>
                  <option value="play_store">Google Play Store</option>
                </select>
              </div>

              <div className="form-group">
                <label>Update Download URL</label>
                <input
                  type="url"
                  placeholder="https://github.com/.../FinPilot-1.2.0-build8-production.apk"
                  value={updateUrl}
                  onChange={(e) => setUpdateUrl(e.target.value)}
                />
              </div>
            </div>

            <div className="form-group">
              <label>Release Notes (Shown to mobile users)</label>
              <textarea
                rows={4}
                placeholder="What's new in this release..."
                value={releaseNotes}
                onChange={(e) => setReleaseNotes(e.target.value)}
              />
            </div>

            <div className="form-group-checkbox">
              <label>
                <input
                  type="checkbox"
                  checked={isUpdateEnabled}
                  onChange={(e) => setIsUpdateEnabled(e.target.checked)}
                />
                <span>
                  <strong>Enforce Update Prompt:</strong> Notify or block users if running below minimum build
                </span>
              </label>
            </div>

            <div style={{ marginTop: "18px" }}>
              <button type="submit" className="btn btn-primary" disabled={saving}>
                {saving ? "Saving Changes..." : "Publish Release Settings"}
              </button>
            </div>
          </form>
        </div>

        {/* Live Status Card */}
        <div className="card panel">
          <div className="section-header">
            <div>
              <h4>Current Client Configuration</h4>
              <p className="text-muted text-sm">Active settings currently queried by the app</p>
            </div>
          </div>

          <div className="c-info-list" style={{ marginTop: "14px" }}>
            <div className="c-info-row">
              <span className="c-label">Latest Published:</span>
              <span className="c-val">
                <strong>FinPilot v{release?.latest_version}</strong> (Build {release?.latest_build_number})
              </span>
            </div>

            <div className="c-info-row">
              <span className="c-label">Minimum Requirement:</span>
              <span className="c-val">
                v{release?.minimum_version} (Build {release?.minimum_build_number})
              </span>
            </div>

            <div className="c-info-row">
              <span className="c-label">Distribution:</span>
              <span className="c-val font-mono">{release?.distribution.toUpperCase()}</span>
            </div>

            <div className="c-info-row">
              <span className="c-label">Update Enforcement:</span>
              <span className="c-val">
                <span
                  className={`status-pill ${
                    release?.is_update_enabled ? "pill-warning" : "pill-neutral"
                  }`}
                >
                  <span className="pill-dot" />
                  <span className="pill-text">
                    {release?.is_update_enabled ? "ENFORCED" : "OPTIONAL / DISABLED"}
                  </span>
                </span>
              </span>
            </div>

            <div className="c-info-row">
              <span className="c-label">Update URL:</span>
              <span className="c-val font-mono text-sm" style={{ wordBreak: "break-all" }}>
                {release?.update_url || "Not specified"}
              </span>
            </div>

            <div className="c-info-row">
              <span className="c-label">Last Configuration Change:</span>
              <span className="c-val">{formatDateTime(release?.updated_at)}</span>
            </div>
          </div>

          {release?.release_notes && (
            <div style={{ marginTop: "20px" }}>
              <span className="c-label" style={{ display: "block", marginBottom: "6px" }}>
                Release Notes Preview:
              </span>
              <div className="release-notes-box">
                <pre>{release.release_notes}</pre>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
