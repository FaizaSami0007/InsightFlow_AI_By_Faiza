"use client";

import * as React from "react";
import {
  Share2,
  Copy,
  Check,
  Trash2,
  Shield,
  Eye,
  Calendar,
  AlertTriangle,
  Loader2,
  Lock,
  Camera,
  Radio,
} from "lucide-react";
import { Dialog } from "@/components/ui/dialog";
import {
  Dashboard,
  ShareResponse,
  ShareListResponse,
  ShareCreateRequest,
} from "@/types";
import { api, ApiError } from "@/lib/api-client";
import { cn } from "@/lib/utils";

interface DashboardShareModalProps {
  isOpen: boolean;
  onClose: () => void;
  dashboard: Dashboard;
}

export function DashboardShareModal({
  isOpen,
  onClose,
  dashboard,
}: DashboardShareModalProps) {
  const [shares, setShares] = React.useState<ShareResponse[]>([]);
  const [isLoading, setIsLoading] = React.useState(false);
  const [isCreating, setIsCreating] = React.useState(false);
  const [copiedToken, setCopiedToken] = React.useState<string | null>(null);
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);

  // Form states
  const [expiresInDays, setExpiresInDays] = React.useState<number | "none">(7);
  const [isSnapshot, setIsSnapshot] = React.useState(false);
  const [selectedFilters, setSelectedFilters] = React.useState<string[]>(
    dashboard.filters.map((f) => f.column_name)
  );

  const fetchShares = React.useCallback(async () => {
    if (!dashboard.id) return;
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const res = await api.get<ShareListResponse>(
        `/api/v1/dashboards/${dashboard.id}/shares`
      );
      setShares(res.items || []);
    } catch {
      // ignore
    } finally {
      setIsLoading(false);
    }
  }, [dashboard.id]);

  React.useEffect(() => {
    if (isOpen) {
      fetchShares();
      setSelectedFilters(dashboard.filters.map((f) => f.column_name));
    }
  }, [isOpen, fetchShares, dashboard.filters]);

  const handleCreateShare = async () => {
    setIsCreating(true);
    setErrorMessage(null);
    try {
      const payload: ShareCreateRequest = {
        expires_in_days: expiresInDays === "none" ? null : expiresInDays,
        is_snapshot: isSnapshot,
        allowed_filters: selectedFilters,
      };

      const newShare = await api.post<ShareResponse>(
        `/api/v1/dashboards/${dashboard.id}/shares`,
        payload
      );

      setShares((prev) => [newShare, ...prev]);

      // Copy automatically
      const fullUrl = `${window.location.origin}/shared/${newShare.share_token}`;
      await navigator.clipboard.writeText(fullUrl);
      setCopiedToken(newShare.share_token);
      setTimeout(() => setCopiedToken(null), 3000);
    } catch (err) {
      setErrorMessage(
        err instanceof ApiError ? err.message : "Failed to generate share link."
      );
    } finally {
      setIsCreating(false);
    }
  };

  const handleCopy = async (token: string) => {
    const fullUrl = `${window.location.origin}/shared/${token}`;
    await navigator.clipboard.writeText(fullUrl);
    setCopiedToken(token);
    setTimeout(() => setCopiedToken(null), 3000);
  };

  const handleRevoke = async (shareId: string) => {
    try {
      await api.delete(`/api/v1/shares/${shareId}`);
      setShares((prev) =>
        prev.map((s) => (s.id === shareId ? { ...s, is_active: false } : s))
      );
    } catch {
      setErrorMessage("Failed to revoke share link.");
    }
  };

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title="Share Dashboard"
      description="Generate secure, tokenized read-only links for external viewers."
      className="max-w-xl"
    >
      <div className="space-y-6">
        {/* Create Share Section */}

        <div className="space-y-4 rounded-xl border border-border bg-cloud-subtle/30 p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-ink">New Share Link</span>
            <div className="flex items-center gap-1.5 text-[11px] text-slate">
              <Lock className="h-3 w-3 text-teal" />
              <span>Read-Only & Token Protected</span>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {/* Expiration Setting */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-ink flex items-center gap-1.5">
                <Calendar className="h-3.5 w-3.5 text-slate" />
                <span>Link Expiration</span>
              </label>
              <select
                value={expiresInDays}
                onChange={(e) =>
                  setExpiresInDays(
                    e.target.value === "none" ? "none" : Number(e.target.value)
                  )
                }
                className="w-full rounded-xl border border-border bg-surface px-3 py-2 text-xs text-ink focus:border-teal focus:outline-none focus:ring-2 focus:ring-teal/20"
              >
                <option value={1} className="text-slate-800 bg-white font-medium">Expires in 1 Day</option>
                <option value={7} className="text-slate-800 bg-white font-medium">Expires in 7 Days (Default)</option>
                <option value={30} className="text-slate-800 bg-white font-medium">Expires in 30 Days</option>
                <option value={90} className="text-slate-800 bg-white font-medium">Expires in 90 Days</option>
                <option value="none" className="text-slate-800 bg-white font-medium">No Expiration (Indefinite)</option>
              </select>
            </div>

            {/* Mode: Snapshot vs Live */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-ink flex items-center gap-1.5">
                {isSnapshot ? (
                  <Camera className="h-3.5 w-3.5 text-teal" />
                ) : (
                  <Radio className="h-3.5 w-3.5 text-teal" />
                )}
                <span>Data Mode</span>
              </label>
              <select
                value={isSnapshot ? "snapshot" : "live"}
                onChange={(e) => setIsSnapshot(e.target.value === "snapshot")}
                className="w-full rounded-xl border border-border bg-surface px-3 py-2 text-xs text-ink focus:border-teal focus:outline-none focus:ring-2 focus:ring-teal/20"
              >
                <option value="live" className="text-slate-800 bg-white font-medium">Live Analytical Queries</option>
                <option value="snapshot" className="text-slate-800 bg-white font-medium">Frozen Static Snapshot</option>
              </select>
            </div>
          </div>

          {/* Allowed Interactive Filters */}
          {dashboard.filters.length > 0 && (
            <div className="space-y-1.5 pt-1">
              <label className="text-xs font-medium text-ink">
                Allow Viewers to Filter By:
              </label>
              <div className="flex flex-wrap gap-2">
                {dashboard.filters.map((filter) => {
                  const isChecked = selectedFilters.includes(filter.column_name);
                  return (
                    <button
                      key={filter.id}
                      type="button"
                      onClick={() => {
                        setSelectedFilters((prev) =>
                          isChecked
                            ? prev.filter((c) => c !== filter.column_name)
                            : [...prev, filter.column_name]
                        );
                      }}
                      className={cn(
                        "flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-[11px] font-medium transition-colors",
                        isChecked
                          ? "border-teal bg-teal-soft/50 text-teal"
                          : "border-border bg-surface text-slate hover:bg-cloud"
                      )}
                    >
                      {isChecked && <Check className="h-3 w-3" />}
                      <span>{filter.display_name}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Security Advisory Callout */}
          <div className="flex items-start gap-2 rounded-xl bg-amber-500/10 border border-amber-500/20 p-2.5 text-[11px] text-amber-900">
            <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5 text-amber-600" />
            <p>
              Anyone with this share link can view the dashboard specification and
              filtered analytical results. Viewer interactions will NOT alter your
              original dashboard.
            </p>
          </div>

          <button
            type="button"
            onClick={handleCreateShare}
            disabled={isCreating}
            className="flex items-center justify-center gap-2 w-full rounded-xl bg-teal py-2.5 text-xs font-semibold text-white shadow-soft hover:bg-teal-hover transition-colors disabled:opacity-50"
          >
            {isCreating ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Creating Secure Link...</span>
              </>
            ) : (
              <>
                <Share2 className="h-4 w-4" />
                <span>Generate & Copy Share Link</span>
              </>
            )}
          </button>
        </div>

        {/* Existing Share Links List */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate">
              Active Share Links ({shares.filter((s) => s.is_active).length})
            </span>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-6">
              <Loader2 className="h-5 w-5 animate-spin text-teal" />
            </div>
          ) : shares.length === 0 ? (
            <p className="text-xs text-slate py-3 text-center">
              No active share links. Create one above to share this dashboard.
            </p>
          ) : (
            <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
              {shares.map((share) => {
                const isCopied = copiedToken === share.share_token;
                const isRevoked = !share.is_active;

                return (
                  <div
                    key={share.id}
                    className={cn(
                      "flex items-center justify-between rounded-xl border p-3 text-xs transition-all",
                      isRevoked
                        ? "border-border/60 bg-cloud-subtle/40 opacity-60"
                        : "border-border bg-surface hover:border-slate/40 shadow-soft-sm"
                    )}
                  >
                    <div className="space-y-1 max-w-[65%]">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-[11px] font-semibold text-ink">
                          ...{share.share_token.slice(-12)}
                        </span>
                        {share.is_snapshot ? (
                          <span className="rounded bg-sky-100 text-sky-800 px-1.5 py-0.2 text-[10px] font-semibold">
                            Snapshot
                          </span>
                        ) : (
                          <span className="rounded bg-teal-soft text-teal px-1.5 py-0.2 text-[10px] font-semibold">
                            Live
                          </span>
                        )}
                        {isRevoked && (
                          <span className="rounded bg-rose/10 text-rose px-1.5 py-0.2 text-[10px] font-semibold">
                            Revoked
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-3 text-[10px] text-slate">
                        <span className="flex items-center gap-1">
                          <Eye className="h-3 w-3" />
                          {share.view_count} views
                        </span>
                        <span>
                          {share.expires_at
                            ? `Expires: ${new Date(share.expires_at).toLocaleDateString()}`
                            : "No Expiration"}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-1.5">
                      {!isRevoked && (
                        <>
                          <button
                            type="button"
                            onClick={() => handleCopy(share.share_token)}
                            className={cn(
                              "flex items-center gap-1 rounded-lg border px-2.5 py-1.5 text-xs font-semibold transition-colors",
                              isCopied
                                ? "border-teal bg-teal text-white"
                                : "border-border bg-cloud-subtle text-ink hover:bg-cloud"
                            )}
                            title="Copy share link"
                          >
                            {isCopied ? (
                              <>
                                <Check className="h-3.5 w-3.5" />
                                <span>Copied</span>
                              </>
                            ) : (
                              <>
                                <Copy className="h-3.5 w-3.5 text-teal" />
                                <span>Copy</span>
                              </>
                            )}
                          </button>
                          <button
                            type="button"
                            onClick={() => handleRevoke(share.id)}
                            className="flex items-center rounded-lg border border-border p-1.5 text-slate hover:border-rose/30 hover:bg-rose/10 hover:text-rose transition-colors"
                            title="Revoke access immediately"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Error Feedback */}
        {errorMessage && (
          <div className="rounded-xl bg-rose/10 border border-rose/20 p-2.5 text-xs text-rose">
            {errorMessage}
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-border pt-4">
          <div className="flex items-center gap-1.5 text-[11px] text-slate">
            <Shield className="h-3.5 w-3.5 text-teal" />
            <span>Encrypted token generation with strict IDOR isolation</span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl border border-border bg-surface px-4 py-2 text-xs font-semibold text-slate hover:bg-cloud transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </Dialog>
  );
}
