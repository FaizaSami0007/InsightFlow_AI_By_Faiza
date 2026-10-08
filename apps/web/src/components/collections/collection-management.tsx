"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Layers,
  Plus,
  GitBranch,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Database,
  ArrowRight,
  RefreshCw,
  Trash2,
  Play,
  Activity,
  Sliders,
  Sparkles,
  Info,
  ChevronRight,
} from "lucide-react";
import {
  Dataset,
  DatasetCollection,
  DatasetRelationship,
  DiscoveredRelationshipCandidate,
  RelationshipStatus,
} from "@/types";
import { api } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { PageHero } from "@/components/ui/page-hero";

export function CollectionManagement() {
  const [collections, setCollections] = useState<DatasetCollection[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedCollection, setSelectedCollection] = useState<DatasetCollection | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // New Collection Modal State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newColName, setNewColName] = useState("");
  const [newColDesc, setNewColDesc] = useState("");
  const [selectedDatasetIds, setSelectedDatasetIds] = useState<string[]>([]);

  // Discovery Candidates State
  const [candidates, setCandidates] = useState<DiscoveredRelationshipCandidate[]>([]);
  const [discovering, setDiscovering] = useState(false);

  // Add Dataset to Collection Modal State
  const [showAddDatasetModal, setShowAddDatasetModal] = useState(false);
  const [datasetToAdd, setDatasetToAdd] = useState("");

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [colRes, dataRes] = await Promise.all([
        api.get<DatasetCollection[] | { items: DatasetCollection[]; total: number }>("/api/v1/collections"),
        api.get<{ items: Dataset[] } | Dataset[]>("/api/v1/datasets"),
      ]);
      const collectionList: DatasetCollection[] = Array.isArray(colRes)
        ? colRes
        : (colRes && typeof colRes === "object" && "items" in colRes && Array.isArray((colRes as { items: DatasetCollection[] }).items))
        ? (colRes as { items: DatasetCollection[] }).items
        : [];
      const datasetList: Dataset[] = Array.isArray(dataRes)
        ? dataRes
        : (dataRes && typeof dataRes === "object" && "items" in dataRes && Array.isArray((dataRes as { items: Dataset[] }).items))
        ? (dataRes as { items: Dataset[] }).items
        : [];
      setCollections(collectionList);
      setDatasets(datasetList);
      if (collectionList.length > 0 && !selectedCollection) {
        setSelectedCollection(collectionList[0]);
      } else if (selectedCollection) {
        const updated = collectionList.find((c: DatasetCollection) => c.id === selectedCollection.id);
        setSelectedCollection(updated || (collectionList[0] ?? null));
      }
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load collections");
    } finally {
      setLoading(false);
    }
  }, [selectedCollection]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleCreateCollection = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newColName.trim()) return;
    try {
      setActionLoading(true);
      const res = await api.post<DatasetCollection>("/api/v1/collections", {
        name: newColName.trim(),
        description: newColDesc.trim() || undefined,
        dataset_ids: selectedDatasetIds,
      });
      setShowCreateModal(false);
      setNewColName("");
      setNewColDesc("");
      setSelectedDatasetIds([]);
      setSuccessMsg(`Collection "${res.name}" created successfully.`);
      await fetchData();
      setSelectedCollection(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create collection");
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeleteCollection = async (colId: string) => {
    if (!confirm("Are you sure you want to delete this dataset collection?")) return;
    try {
      setActionLoading(true);
      await api.delete(`/api/v1/collections/${colId}`);
      setSuccessMsg("Collection deleted successfully.");
      if (selectedCollection?.id === colId) {
        setSelectedCollection(null);
      }
      await fetchData();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to delete collection");
    } finally {
      setActionLoading(false);
    }
  };

  const handleAddDataset = async () => {
    if (!selectedCollection || !datasetToAdd) return;
    try {
      setActionLoading(true);
      const updated = await api.post<DatasetCollection>(
        `/api/v1/collections/${selectedCollection.id}/datasets/${datasetToAdd}`,
        {}
      );
      setSelectedCollection(updated);
      setShowAddDatasetModal(false);
      setDatasetToAdd("");
      setSuccessMsg("Dataset added to collection.");
      await fetchData();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to add dataset");
    } finally {
      setActionLoading(false);
    }
  };

  const handleRemoveDataset = async (datasetId: string) => {
    if (!selectedCollection) return;
    try {
      setActionLoading(true);
      const updated = await api.delete<DatasetCollection>(
        `/api/v1/collections/${selectedCollection.id}/datasets/${datasetId}`
      );
      setSelectedCollection(updated);
      setSuccessMsg("Dataset removed from collection.");
      await fetchData();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to remove dataset");
    } finally {
      setActionLoading(false);
    }
  };

  const handleDiscoverRelationships = async () => {
    if (!selectedCollection) return;
    try {
      setDiscovering(true);
      const res = await api.post<{ candidates: DiscoveredRelationshipCandidate[]; total: number }>(
        `/api/v1/collections/${selectedCollection.id}/discover-relationships`,
        {}
      );
      setCandidates(res.candidates || []);
      if ((res.candidates || []).length === 0) {
        setSuccessMsg("No new candidate relationships discovered in this collection.");
      } else {
        setSuccessMsg(`Discovered ${res.candidates.length} candidate relationship(s).`);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to discover relationships");
    } finally {
      setDiscovering(false);
    }
  };

  const handleApproveCandidate = async (cand: DiscoveredRelationshipCandidate) => {
    if (!selectedCollection) return;
    try {
      setActionLoading(true);
      // Resolve latest version IDs
      const sDataset = datasets.find((d) => d.id === cand.source_dataset_id);
      const tDataset = datasets.find((d) => d.id === cand.target_dataset_id);
      if (!sDataset?.latest_version || !tDataset?.latest_version) {
        throw new Error("Unable to resolve dataset versions for join candidate.");
      }

      await api.post<DatasetRelationship>("/api/v1/relationships", {
        collection_id: selectedCollection.id,
        source_dataset_id: cand.source_dataset_id,
        source_version_id: sDataset.latest_version.id,
        source_field: cand.source_field,
        target_dataset_id: cand.target_dataset_id,
        target_version_id: tDataset.latest_version.id,
        target_field: cand.target_field,
        relationship_type: cand.inferred_type,
      });

      // Remove approved candidate from candidate list
      setCandidates((prev) =>
        prev.filter(
          (c) =>
            !(
              c.source_dataset_id === cand.source_dataset_id &&
              c.target_dataset_id === cand.target_dataset_id &&
              c.source_field === cand.source_field &&
              c.target_field === cand.target_field
            )
        )
      );

      setSuccessMsg(
        `Relationship ${cand.source_field} ↔ ${cand.target_field} proposed & validated.`
      );
      await fetchData();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to approve relationship");
    } finally {
      setActionLoading(false);
    }
  };

  const handleUpdateRelStatus = async (relId: string, newStatus: RelationshipStatus) => {
    try {
      setActionLoading(true);
      await api.patch<DatasetRelationship>(`/api/v1/relationships/${relId}/status`, {
        status: newStatus,
      });
      setSuccessMsg(`Relationship status updated to ${newStatus}.`);
      await fetchData();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to update relationship status");
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeleteRel = async (relId: string) => {
    if (!confirm("Are you sure you want to delete this relationship?")) return;
    try {
      setActionLoading(true);
      await api.delete(`/api/v1/relationships/${relId}`);
      setSuccessMsg("Relationship deleted.");
      await fetchData();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to delete relationship");
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header via PageHero */}
      <PageHero
        icon={<Layers className="h-6 w-6" />}
        iconVariant="teal"
        title="Dataset Collections & Federation"
        description="Group datasets logically and define validated referential relationships for cross-dataset AI analytics."
        actions={
          <Button
            variant="primary"
            size="sm"
            onClick={() => setShowCreateModal(true)}
            className="whitespace-nowrap"
            leftIcon={<Plus className="h-4 w-4" />}
          >
            New Collection
          </Button>
        }
      />

      {/* Alerts */}
      {error && (
        <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-xs font-semibold hover:underline">
            Dismiss
          </button>
        </div>
      )}

      {successMsg && (
        <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-sm flex items-center justify-between">
          <span>{successMsg}</span>
          <button onClick={() => setSuccessMsg(null)} className="text-xs font-semibold hover:underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Main Grid: Collections List & Detail View */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Collections Sidebar */}
        <div className="lg:col-span-4 space-y-4">
          <div className="bg-card border border-border/60 rounded-xl p-4 shadow-xs">
            <div className="flex items-center justify-between mb-3 pb-2 border-b border-border/40">
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Workspaces ({collections.length})
              </span>
              <button
                onClick={fetchData}
                disabled={loading}
                className="p-1 rounded text-muted-foreground hover:text-foreground transition-colors"
                title="Refresh collections"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
              </button>
            </div>

            {loading && collections.length === 0 ? (
              <div className="py-8 text-center text-xs text-muted-foreground">
                Loading collections…
              </div>
            ) : collections.length === 0 ? (
              <div className="py-8 text-center space-y-2">
                <Database className="h-8 w-8 text-muted-foreground/40 mx-auto" />
                <p className="text-xs text-muted-foreground">No collections created yet.</p>
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="text-xs text-primary font-medium hover:underline"
                >
                  Create your first collection
                </button>
              </div>
            ) : (
              <div className="space-y-2">
                {collections.map((col) => {
                  const isSelected = selectedCollection?.id === col.id;
                  const validatedCount = (col.relationships || []).filter(
                    (r) => r.status === "VALIDATED"
                  ).length;

                  return (
                    <div
                      key={col.id}
                      onClick={() => setSelectedCollection(col)}
                      className={`p-3 rounded-lg border text-left cursor-pointer transition-all ${
                        isSelected
                          ? "bg-primary/5 border-primary/40 shadow-xs"
                          : "border-border/40 hover:bg-muted/40 hover:border-border"
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="space-y-1">
                          <h2 className="text-sm font-medium text-foreground">{col.name}</h2>
                          {col.description && (
                            <p className="text-xs text-muted-foreground line-clamp-1">
                              {col.description}
                            </p>
                          )}
                        </div>
                        <ChevronRight
                          className={`h-4 w-4 transition-transform ${
                            isSelected ? "text-primary translate-x-0.5" : "text-muted-foreground/40"
                          }`}
                        />
                      </div>

                      <div className="flex items-center gap-3 mt-3 pt-2 border-t border-border/30 text-[11px] text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Database className="h-3 w-3" />
                          {col.items?.length || 0} datasets
                        </span>
                        <span className="flex items-center gap-1">
                          <GitBranch className="h-3 w-3" />
                          {validatedCount} validated joins
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Right: Selected Collection Detail */}
        <div className="lg:col-span-8 space-y-6">
          {selectedCollection ? (
            <div className="space-y-6">
              {/* Collection Header */}
              <div className="bg-card border border-border/60 rounded-xl p-5 shadow-xs space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <h2 className="text-lg font-semibold text-foreground">
                        {selectedCollection.name}
                      </h2>
                      <span className="px-2 py-0.5 text-[10px] font-medium bg-primary/10 text-primary rounded-full">
                        Logical Workspace
                      </span>
                    </div>
                    {selectedCollection.description && (
                      <p className="text-xs text-muted-foreground mt-1">
                        {selectedCollection.description}
                      </p>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    <a
                      href={`/analyst?collection_id=${selectedCollection.id}`}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors shadow-xs"
                    >
                      <Sparkles className="h-3.5 w-3.5" />
                      Analyze in AI Workspace
                    </a>
                    <button
                      onClick={() => handleDeleteCollection(selectedCollection.id)}
                      disabled={actionLoading}
                      className="p-2 rounded-lg text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
                      title="Delete collection"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>

              {/* Datasets in Collection Section */}
              <div className="bg-card border border-border/60 rounded-xl p-5 shadow-xs space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Database className="h-4 w-4 text-primary" />
                    <h3 className="text-sm font-semibold text-foreground">
                      Member Datasets ({selectedCollection.items?.length || 0})
                    </h3>
                  </div>
                  <button
                    onClick={() => setShowAddDatasetModal(true)}
                    className="inline-flex items-center gap-1 text-xs font-medium text-primary hover:underline"
                  >
                    <Plus className="h-3.5 w-3.5" />
                    Add Dataset
                  </button>
                </div>

                {(!selectedCollection.items || selectedCollection.items.length === 0) ? (
                  <div className="py-6 text-center text-xs text-muted-foreground border border-dashed border-border/60 rounded-lg">
                    No datasets added to this collection yet.
                  </div>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {selectedCollection.items.map((item) => {
                      const dObj = datasets.find((d) => d.id === item.dataset_id);
                      return (
                        <div
                          key={item.id}
                          className="flex items-center justify-between p-3 rounded-lg border border-border/50 bg-background/50 hover:bg-muted/20 transition-colors"
                        >
                          <div className="space-y-0.5">
                            <span className="text-xs font-medium text-foreground">
                              {dObj?.name || item.dataset_id}
                            </span>
                            <div className="text-[10px] text-muted-foreground flex items-center gap-2">
                              <span>Format: {dObj?.latest_version?.file_format || "CSV"}</span>
                              <span>•</span>
                              <span>Rows: {dObj?.latest_version?.row_count?.toLocaleString() || "—"}</span>
                            </div>
                          </div>
                          <button
                            onClick={() => handleRemoveDataset(item.dataset_id)}
                            className="p-1 text-muted-foreground hover:text-destructive transition-colors"
                            title="Remove from collection"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Candidate Relationships Discovery Section */}
              <div className="bg-card border border-border/60 rounded-xl p-5 shadow-xs space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-amber-500" />
                    <div>
                      <h3 className="text-sm font-semibold text-foreground">
                        Relationship Discovery
                      </h3>
                      <p className="text-[11px] text-muted-foreground">
                        Inspect statistical column overlaps and semantic keys to suggest join candidates.
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={handleDiscoverRelationships}
                    disabled={discovering || (selectedCollection.items?.length || 0) < 2}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-secondary text-secondary-foreground hover:bg-secondary/80 disabled:opacity-50 transition-colors"
                  >
                    <RefreshCw className={`h-3.5 w-3.5 ${discovering ? "animate-spin" : ""}`} />
                    {discovering ? "Discovering…" : "Discover Relationships"}
                  </button>
                </div>

                {candidates.length > 0 && (
                  <div className="space-y-2 mt-3 pt-3 border-t border-border/40">
                    <span className="text-xs font-semibold text-foreground">
                      Suggested Candidates ({candidates.length})
                    </span>
                    <div className="space-y-2">
                      {candidates.map((cand, idx) => (
                        <div
                          key={idx}
                          className="flex flex-col sm:flex-row sm:items-center justify-between p-3 rounded-lg border border-amber-500/30 bg-amber-500/5 gap-3"
                        >
                          <div className="space-y-1">
                            <div className="flex items-center gap-2 text-xs font-medium text-foreground">
                              <span className="text-primary font-semibold">
                                {cand.source_dataset_name}.{cand.source_field}
                              </span>
                              <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />
                              <span className="text-primary font-semibold">
                                {cand.target_dataset_name}.{cand.target_field}
                              </span>
                              <span className="px-1.5 py-0.5 text-[10px] rounded bg-background border border-border text-muted-foreground">
                                {cand.inferred_type}
                              </span>
                            </div>
                            <p className="text-[11px] text-muted-foreground">
                              Confidence: {Math.round(cand.confidence * 100)}% • {cand.reason}
                            </p>
                          </div>

                          <div className="flex items-center gap-2 shrink-0">
                            <button
                              onClick={() => handleApproveCandidate(cand)}
                              disabled={actionLoading}
                              className="px-2.5 py-1 text-xs font-medium rounded bg-emerald-600 text-white hover:bg-emerald-700 transition-colors"
                            >
                              Approve & Validate
                            </button>
                            <button
                              onClick={() =>
                                setCandidates((prev) => prev.filter((_, i) => i !== idx))
                              }
                              className="px-2.5 py-1 text-xs font-medium rounded border border-border text-muted-foreground hover:bg-muted transition-colors"
                            >
                              Dismiss
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Validated & Configured Relationships Table */}
              <div className="bg-card border border-border/60 rounded-xl p-5 shadow-xs space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <GitBranch className="h-4 w-4 text-primary" />
                    <h3 className="text-sm font-semibold text-foreground">
                      Relationships & Referential Integrity
                    </h3>
                  </div>
                </div>

                {(!selectedCollection.relationships ||
                  selectedCollection.relationships.length === 0) ? (
                  <div className="py-8 text-center space-y-1 text-xs text-muted-foreground border border-dashed border-border/60 rounded-lg">
                    <GitBranch className="h-6 w-6 text-muted-foreground/40 mx-auto mb-2" />
                    <p>No relationships configured in this collection yet.</p>
                    <p className="text-[11px]">
                      Click &ldquo;Discover Relationships&rdquo; above to find join keys automatically.
                    </p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead>
                        <tr className="border-b border-border/50 text-muted-foreground">
                          <th className="py-2.5 px-3 font-medium">Join Fields</th>
                          <th className="py-2.5 px-3 font-medium">Cardinality</th>
                          <th className="py-2.5 px-3 font-medium">Referential Coverage</th>
                          <th className="py-2.5 px-3 font-medium">Quality Score</th>
                          <th className="py-2.5 px-3 font-medium">Status</th>
                          <th className="py-2.5 px-3 font-medium text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border/30">
                        {selectedCollection.relationships.map((rel) => {
                          const sData = datasets.find((d) => d.id === rel.source_dataset_id);
                          const tData = datasets.find((d) => d.id === rel.target_dataset_id);

                          const statusColors = {
                            VALIDATED: "bg-emerald-500/10 text-emerald-600 border-emerald-500/20",
                            PROPOSED: "bg-amber-500/10 text-amber-600 border-amber-500/20",
                            DISABLED: "bg-muted text-muted-foreground border-border",
                            REJECTED: "bg-destructive/10 text-destructive border-destructive/20",
                          };

                          return (
                            <tr key={rel.id} className="hover:bg-muted/20 transition-colors">
                              <td className="py-3 px-3 font-medium text-foreground">
                                <div className="flex items-center gap-1.5">
                                  <span>
                                    {sData?.name || "Source"}.{rel.source_field}
                                  </span>
                                  <ArrowRight className="h-3 w-3 text-muted-foreground" />
                                  <span>
                                    {tData?.name || "Target"}.{rel.target_field}
                                  </span>
                                </div>
                              </td>

                              <td className="py-3 px-3 text-muted-foreground">
                                <span className="px-1.5 py-0.5 rounded bg-background border border-border text-[10px]">
                                  {rel.relationship_type}
                                </span>
                              </td>

                              <td className="py-3 px-3">
                                <div className="flex items-center gap-2">
                                  <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
                                    <div
                                      className="h-full bg-primary rounded-full"
                                      style={{ width: `${Math.min(rel.coverage_ratio * 100, 100)}%` }}
                                    />
                                  </div>
                                  <span className="text-[11px] text-foreground font-mono">
                                    {(rel.coverage_ratio * 100).toFixed(1)}%
                                  </span>
                                </div>
                              </td>

                              <td className="py-3 px-3 text-foreground font-mono">
                                {rel.quality_score.toFixed(1)} / 100
                              </td>

                              <td className="py-3 px-3">
                                <span
                                  className={`px-2 py-0.5 text-[10px] font-medium border rounded-full ${
                                    statusColors[rel.status] || statusColors.PROPOSED
                                  }`}
                                >
                                  {rel.status}
                                </span>
                              </td>

                              <td className="py-3 px-3 text-right">
                                <div className="flex items-center justify-end gap-1.5">
                                  {rel.status === "VALIDATED" ? (
                                    <button
                                      onClick={() => handleUpdateRelStatus(rel.id, "DISABLED")}
                                      className="px-2 py-0.5 text-[10px] rounded border border-border text-muted-foreground hover:bg-muted transition-colors"
                                    >
                                      Disable
                                    </button>
                                  ) : (
                                    <button
                                      onClick={() => handleUpdateRelStatus(rel.id, "VALIDATED")}
                                      className="px-2 py-0.5 text-[10px] rounded bg-emerald-600/10 text-emerald-600 border border-emerald-600/20 hover:bg-emerald-600/20 transition-colors"
                                    >
                                      Activate
                                    </button>
                                  )}
                                  <button
                                    onClick={() => handleDeleteRel(rel.id)}
                                    className="p-1 text-muted-foreground hover:text-destructive transition-colors"
                                    title="Delete relationship"
                                  >
                                    <Trash2 className="h-3 w-3" />
                                  </button>
                                </div>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="bg-card border border-border/60 rounded-xl p-12 text-center space-y-3 shadow-xs">
              <Layers className="h-10 w-10 text-muted-foreground/30 mx-auto" />
              <h2 className="text-base font-semibold text-foreground">
                Select or Create a Collection
              </h2>
              <p className="text-xs text-muted-foreground max-w-sm mx-auto">
                Dataset collections group your related tables (e.g. Customers, Orders, Products) to enable multi-dataset federated queries without physically merging files.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Create Collection Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-xl shadow-xl max-w-md w-full p-6 space-y-4 animate-in fade-in zoom-in-95">
            <h3 className="text-base font-semibold text-foreground">
              Create New Dataset Collection
            </h3>

            <form onSubmit={handleCreateCollection} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-foreground">Collection Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Sales Intelligence"
                  value={newColName}
                  onChange={(e) => setNewColName(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-lg border border-border bg-background focus:outline-hidden focus:ring-2 focus:ring-primary/20"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-medium text-foreground">Description (optional)</label>
                <textarea
                  rows={2}
                  placeholder="e.g. Federated context for customers, orders and products"
                  value={newColDesc}
                  onChange={(e) => setNewColDesc(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-lg border border-border bg-background focus:outline-hidden focus:ring-2 focus:ring-primary/20"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-medium text-foreground">
                  Include Datasets ({selectedDatasetIds.length} selected)
                </label>
                <div className="max-h-40 overflow-y-auto space-y-1.5 p-2 rounded-lg border border-border/60 bg-muted/20">
                  {datasets.map((d) => (
                    <label
                      key={d.id}
                      className="flex items-center gap-2 p-1.5 rounded hover:bg-muted/40 cursor-pointer text-xs"
                    >
                      <input
                        type="checkbox"
                        checked={selectedDatasetIds.includes(d.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedDatasetIds([...selectedDatasetIds, d.id]);
                          } else {
                            setSelectedDatasetIds(selectedDatasetIds.filter((id) => id !== d.id));
                          }
                        }}
                        className="rounded border-border"
                      />
                      <span className="text-foreground">{d.name}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-border/40">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-3 py-1.5 text-xs font-medium rounded-lg border border-border text-muted-foreground hover:bg-muted transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading || !newColName.trim()}
                  className="px-4 py-1.5 text-xs font-medium rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
                >
                  {actionLoading ? "Creating…" : "Create Collection"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Dataset Modal */}
      {showAddDatasetModal && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-xl shadow-xl max-w-sm w-full p-5 space-y-4">
            <h3 className="text-sm font-semibold text-foreground">
              Add Dataset to Collection
            </h3>

            <div className="space-y-2">
              <label className="text-xs text-muted-foreground">Select Dataset</label>
              <select
                value={datasetToAdd}
                onChange={(e) => setDatasetToAdd(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-lg border border-border bg-background focus:outline-hidden focus:ring-2 focus:ring-primary/20"
              >
                <option value="">-- Choose a dataset --</option>
                {datasets
                  .filter(
                    (d) =>
                      !selectedCollection?.items?.some((item) => item.dataset_id === d.id)
                  )
                  .map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name}
                    </option>
                  ))}
              </select>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-border/40">
              <button
                type="button"
                onClick={() => setShowAddDatasetModal(false)}
                className="px-3 py-1.5 text-xs font-medium rounded-lg border border-border text-muted-foreground hover:bg-muted"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleAddDataset}
                disabled={actionLoading || !datasetToAdd}
                className="px-4 py-1.5 text-xs font-medium rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              >
                Add Dataset
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
