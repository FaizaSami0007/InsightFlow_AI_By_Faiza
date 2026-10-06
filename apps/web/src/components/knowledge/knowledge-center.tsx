"use client";

import React, { useState, useEffect } from "react";
import {
  KnowledgeCollectionResponse,
  KnowledgeDocumentResponse,
  KnowledgeDocumentVersionResponse,
  KnowledgeChunkResponse,
  DatasetKnowledgeLinkResponse,
  KnowledgeType,
  DocumentProcessingStatus,
  KnowledgeCitation,
  KnowledgeSearchResultItem,
  Dataset,
} from "@/types";
import {
  BookOpen,
  FolderPlus,
  FileText,
  Search,
  Upload,
  Layers,
  Link2,
  Trash2,
  CheckCircle2,
  AlertCircle,
  Clock,
  ExternalLink,
  Sparkles,
  ShieldCheck,
  Tag,
  Filter,
  RefreshCw,
  Eye,
  FileCode,
  FileSpreadsheet,
  FileCheck,
} from "lucide-react";

interface KnowledgeCenterProps {
  token?: string;
  initialDatasets?: Dataset[];
}

export const KnowledgeCenter: React.FC<KnowledgeCenterProps> = ({
  token,
  initialDatasets = [],
}) => {
  // State
  const [activeTab, setActiveTab] = useState<"documents" | "collections" | "links" | "search">("documents");
  const [collections, setCollections] = useState<KnowledgeCollectionResponse[]>([]);
  const [documents, setDocuments] = useState<KnowledgeDocumentResponse[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>(initialDatasets);
  const [links, setLinks] = useState<DatasetKnowledgeLinkResponse[]>([]);
  const [selectedCollectionId, setSelectedCollectionId] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [searchResults, setSearchResults] = useState<{
    results: KnowledgeSearchResultItem[];
    citations: KnowledgeCitation[];
    has_sufficient_evidence: boolean;
    notice?: string | null;
  } | null>(null);
  const [isSearching, setIsSearching] = useState<boolean>(false);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadStatus, setUploadStatus] = useState<string>("");

  // Modal state for chunk inspection
  const [inspectingDoc, setInspectingDoc] = useState<KnowledgeDocumentResponse | null>(null);
  const [inspectingChunks, setInspectingChunks] = useState<KnowledgeChunkResponse[]>([]);
  const [inspectingVersions, setInspectingVersions] = useState<KnowledgeDocumentVersionResponse[]>([]);
  const [isDetailLoading, setIsDetailLoading] = useState<boolean>(false);

  // Form states
  const [newCollectionName, setNewCollectionName] = useState<string>("");
  const [newCollectionDesc, setNewCollectionDesc] = useState<string>("");
  const [uploadCollectionId, setUploadCollectionId] = useState<string>("");
  const [uploadKnowledgeType, setUploadKnowledgeType] = useState<KnowledgeType>("BUSINESS_RULE");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Link form
  const [linkDatasetId, setLinkDatasetId] = useState<string>("");
  const [linkDocumentId, setLinkDocumentId] = useState<string>("");

  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // Fetch initial data
  const fetchData = React.useCallback(async () => {
    try {
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;

      // Fetch collections
      const colRes = await fetch(`${apiBase}/api/v1/knowledge/collections`, { headers });
      if (colRes.ok) {
        const colData = await colRes.json();
        setCollections(colData);
      }

      // Fetch documents
      const docRes = await fetch(`${apiBase}/api/v1/knowledge/documents`, { headers });
      if (docRes.ok) {
        const docData = await docRes.json();
        setDocuments(docData.items || docData.documents || []);
      }

      // Fetch datasets if empty
      if (datasets.length === 0) {
        const dsRes = await fetch(`${apiBase}/api/v1/datasets`, { headers });
        if (dsRes.ok) {
          const dsData = await dsRes.json();
          setDatasets(dsData.datasets || dsData || []);
        }
      }
    } catch (err) {
      console.error("Failed to load knowledge data", err);
    }
  }, [apiBase, token, datasets.length]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Create Collection
  const handleCreateCollection = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCollectionName.trim()) return;

    try {
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch(`${apiBase}/api/v1/knowledge/collections`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          name: newCollectionName.trim(),
          description: newCollectionDesc.trim() || undefined,
        }),
      });

      if (res.ok) {
        setNewCollectionName("");
        setNewCollectionDesc("");
        fetchData();
      }
    } catch (err) {
      console.error("Create collection error", err);
    }
  };

  // Upload Document
  const handleUploadDocument = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    setIsUploading(true);
    setUploadStatus("Uploading & extracting structure...");

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      if (uploadCollectionId) formData.append("collection_id", uploadCollectionId);
      if (uploadKnowledgeType) formData.append("knowledge_type", uploadKnowledgeType);

      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch(`${apiBase}/api/v1/knowledge/documents`, {
        method: "POST",
        headers,
        body: formData,
      });

      if (res.ok) {
        setUploadStatus("Document indexed successfully!");
        setSelectedFile(null);
        setTimeout(() => setUploadStatus(""), 3000);
        fetchData();
      } else {
        const errorData = await res.json();
        setUploadStatus(`Upload failed: ${errorData.detail || "Server error"}`);
      }
    } catch (err) {
      console.error("Upload error", err);
      setUploadStatus("Upload failed due to network error");
    } finally {
      setIsUploading(false);
    }
  };

  // Inspect Document Chunks & Versions
  const handleInspectDocument = async (doc: KnowledgeDocumentResponse) => {
    setInspectingDoc(doc);
    setIsDetailLoading(true);
    try {
      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const [chunksRes, verRes] = await Promise.all([
        fetch(`${apiBase}/api/v1/knowledge/documents/${doc.id}/chunks`, { headers }),
        fetch(`${apiBase}/api/v1/knowledge/documents/${doc.id}/versions`, { headers }),
      ]);

      if (chunksRes.ok) {
        const chunkData = await chunksRes.json();
        setInspectingChunks(chunkData.chunks || chunkData || []);
      }
      if (verRes.ok) {
        const verData = await verRes.json();
        setInspectingVersions(verData || []);
      }
    } catch (err) {
      console.error("Failed to inspect document", err);
    } finally {
      setIsDetailLoading(false);
    }
  };

  // Perform Hybrid Search
  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    try {
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch(`${apiBase}/api/v1/knowledge/search`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          query: searchQuery.trim(),
          collection_id: selectedCollectionId !== "all" ? selectedCollectionId : undefined,
          top_k: 5,
          min_similarity: 0.15,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setSearchResults(data);
      }
    } catch (err) {
      console.error("Search error", err);
    } finally {
      setIsSearching(false);
    }
  };

  // Link Document to Dataset
  const handleLinkDataset = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!linkDatasetId || !linkDocumentId) return;

    try {
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch(`${apiBase}/api/v1/knowledge/links`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          dataset_id: linkDatasetId,
          document_id: linkDocumentId,
          relationship_nature: "context_provider",
        }),
      });

      if (res.ok) {
        const newLink = await res.json();
        setLinks((prev) => [newLink, ...prev]);
        setLinkDocumentId("");
      }
    } catch (err) {
      console.error("Link error", err);
    }
  };

  const getStatusBadge = (status: DocumentProcessingStatus) => {
    switch (status) {
      case "READY":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3 h-3 text-emerald-500" />
            READY
          </span>
        );
      case "EXTRACTING":
      case "CHUNKED":
      case "EMBEDDED":
      case "INDEXED":
      case "UPLOADED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-teal-50 text-teal-700 border border-teal-200 animate-pulse">
            <RefreshCw className="w-3 h-3 text-teal animate-spin" />
            {status}
          </span>
        );
      case "FAILED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-50 text-rose-700 border border-rose-200">
            <AlertCircle className="w-3 h-3 text-rose-500" />
            FAILED
          </span>
        );
      case "STALE":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200">
            <Clock className="w-3 h-3 text-amber-500" />
            STALE
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700">
            {status}
          </span>
        );
    }
  };

  const filteredDocuments = selectedCollectionId === "all"
    ? documents
    : documents.filter((d) => d.collection_id === selectedCollectionId);

  return (
    <div className="space-y-6 max-w-7xl mx-auto p-4 md:p-6 text-ink">
      {/* Header Banner */}
      <div className="rounded-2xl bg-gradient-to-r from-teal-900 via-teal-800 to-slate-900 text-white p-6 shadow-soft-lg flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full bg-teal-500/20 text-teal-300 text-xs font-semibold uppercase tracking-wider border border-teal-400/30">
              Phase 14 Active
            </span>
            <span className="text-xs text-teal-200/80">Deterministic Hybrid RAG</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white mt-1">
            Knowledge Intelligence & Context-Aware RAG
          </h1>
          <p className="text-sm text-slate-300 max-w-2xl mt-1">
            Ingest, extract, chunk, embed, and cite enterprise business knowledge. Provides grounded domain context to analytical AI without hallucinations.
          </p>
        </div>
        <div className="flex items-center gap-3 self-start md:self-auto">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white/10 backdrop-blur border border-white/15 text-xs text-teal-100">
            <ShieldCheck className="w-4 h-4 text-teal-300" />
            <span>Passive Untrusted Data Policy</span>
          </div>
        </div>
      </div>

      {/* Metrics Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-surface rounded-xl p-4 border border-border shadow-soft flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-teal-soft text-teal">
            <BookOpen className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs text-slate font-medium">Documents</p>
            <p className="text-lg font-bold text-ink">{documents.length}</p>
          </div>
        </div>
        <div className="bg-surface rounded-xl p-4 border border-border shadow-soft flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-indigo-50 text-indigo-600">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs text-slate font-medium">Collections</p>
            <p className="text-lg font-bold text-ink">{collections.length}</p>
          </div>
        </div>
        <div className="bg-surface rounded-xl p-4 border border-border shadow-soft flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-emerald-50 text-emerald-600">
            <FileCode className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs text-slate font-medium">Total Chunks</p>
            <p className="text-lg font-bold text-ink">
              {documents.reduce((acc, d) => acc + (d.chunk_count || 0), 0)}
            </p>
          </div>
        </div>
        <div className="bg-surface rounded-xl p-4 border border-border shadow-soft flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-amber-50 text-amber-600">
            <Link2 className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs text-slate font-medium">Dataset Links</p>
            <p className="text-lg font-bold text-ink">{links.length}</p>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-border space-x-4">
        <button
          onClick={() => setActiveTab("documents")}
          className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === "documents"
              ? "border-teal text-teal"
              : "border-transparent text-slate hover:text-ink"
          }`}
        >
          <FileText className="w-4 h-4" />
          Documents & Ingestion
        </button>
        <button
          onClick={() => setActiveTab("collections")}
          className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === "collections"
              ? "border-teal text-teal"
              : "border-transparent text-slate hover:text-ink"
          }`}
        >
          <Layers className="w-4 h-4" />
          Collections ({collections.length})
        </button>
        <button
          onClick={() => setActiveTab("links")}
          className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === "links"
              ? "border-teal text-teal"
              : "border-transparent text-slate hover:text-ink"
          }`}
        >
          <Link2 className="w-4 h-4" />
          Dataset ↔ Knowledge
        </button>
        <button
          onClick={() => setActiveTab("search")}
          className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === "search"
              ? "border-teal text-teal"
              : "border-transparent text-slate hover:text-ink"
          }`}
        >
          <Search className="w-4 h-4" />
          Hybrid Search & Citations
        </button>
      </div>

      {/* Tab 1: Documents & Ingestion */}
      {activeTab === "documents" && (
        <div className="space-y-6">
          {/* Upload Card */}
          <div className="bg-surface rounded-2xl p-6 border border-border shadow-soft">
            <h2 className="text-base font-semibold text-ink flex items-center gap-2">
              <Upload className="w-4 h-4 text-teal" />
              Ingest Business Document
            </h2>
            <p className="text-xs text-slate mt-0.5">
              Securely upload PDF, DOCX, TXT, Markdown, or reference CSV files. Files are parsed, chunked, and embedded into deterministic vector storage.
            </p>

            <form onSubmit={handleUploadDocument} className="mt-4 grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
              <div className="md:col-span-1">
                <label className="block text-xs font-medium text-slate mb-1">Knowledge Collection</label>
                <select
                  value={uploadCollectionId}
                  onChange={(e) => setUploadCollectionId(e.target.value)}
                  className="w-full text-xs rounded-xl border border-border bg-background px-3 py-2 text-ink focus:outline-none focus:ring-2 focus:ring-teal"
                >
                  <option value="">(No collection - Root)</option>
                  {collections.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="md:col-span-1">
                <label className="block text-xs font-medium text-slate mb-1">Knowledge Type</label>
                <select
                  value={uploadKnowledgeType}
                  onChange={(e) => setUploadKnowledgeType(e.target.value as KnowledgeType)}
                  className="w-full text-xs rounded-xl border border-border bg-background px-3 py-2 text-ink focus:outline-none focus:ring-2 focus:ring-teal"
                >
                  <option value="BUSINESS_RULE">Business Rule</option>
                  <option value="KPI_DEFINITION">KPI Definition</option>
                  <option value="METRIC_FORMULA">Metric Formula</option>
                  <option value="POLICY">Policy / Standard</option>
                  <option value="GLOSSARY">Glossary Term</option>
                  <option value="DOMAIN_GUIDE">Domain Guide</option>
                  <option value="SOP">SOP / Process</option>
                </select>
              </div>

              <div className="md:col-span-1">
                <label className="block text-xs font-medium text-slate mb-1">Document File</label>
                <input
                  type="file"
                  accept=".pdf,.docx,.doc,.txt,.md,.markdown,.json,.csv"
                  onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                  className="w-full text-xs text-slate file:mr-2 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-teal-soft file:text-teal hover:file:bg-teal/20"
                />
              </div>

              <div className="md:col-span-1 flex items-center gap-2">
                <button
                  type="submit"
                  disabled={!selectedFile || isUploading}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-xl bg-teal text-white text-xs font-semibold hover:bg-teal-dark disabled:opacity-50 transition-colors shadow-soft"
                >
                  {isUploading ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <Upload className="w-3.5 h-3.5" />
                      Upload & Ingest
                    </>
                  )}
                </button>
              </div>
            </form>

            {uploadStatus && (
              <div className="mt-3 p-3 rounded-xl bg-cloud text-xs font-medium text-ink flex items-center gap-2">
                <FileCheck className="w-4 h-4 text-teal" />
                {uploadStatus}
              </div>
            )}
          </div>

          {/* Collection Filter Bar */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-slate" />
              <span className="text-xs font-medium text-slate">Filter by Collection:</span>
              <select
                value={selectedCollectionId}
                onChange={(e) => setSelectedCollectionId(e.target.value)}
                className="text-xs rounded-lg border border-border bg-surface px-2.5 py-1 text-ink focus:outline-none focus:ring-1 focus:ring-teal"
              >
                <option value="all">All Documents ({documents.length})</option>
                {collections.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} ({documents.filter((d) => d.collection_id === c.id).length})
                  </option>
                ))}
              </select>
            </div>
            <button
              onClick={fetchData}
              className="text-xs text-slate hover:text-ink flex items-center gap-1 transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Refresh
            </button>
          </div>

          {/* Documents Table */}
          <div className="bg-surface rounded-2xl border border-border shadow-soft overflow-hidden">
            {filteredDocuments.length === 0 ? (
              <div className="p-12 text-center text-slate">
                <BookOpen className="w-10 h-10 mx-auto text-slate-300 mb-2" />
                <p className="text-sm font-semibold text-ink">No documents found</p>
                <p className="text-xs text-slate mt-1">
                  Upload PDF, DOCX, TXT or Markdown files above to start populating your business knowledge base.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-ink">
                  <thead className="bg-cloud text-slate uppercase text-[10px] tracking-wider border-b border-border">
                    <tr>
                      <th className="py-3 px-4">Document Title</th>
                      <th className="py-3 px-4">Type</th>
                      <th className="py-3 px-4">Knowledge Class</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4">Version</th>
                      <th className="py-3 px-4">Chunks</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {filteredDocuments.map((doc) => (
                      <tr key={doc.id} className="hover:bg-cloud/50 transition-colors">
                        <td className="py-3 px-4 font-semibold text-ink flex items-center gap-2">
                          <FileText className="w-4 h-4 text-teal shrink-0" />
                          <div>
                            <span className="block truncate max-w-xs">{doc.title}</span>
                            <span className="text-[10px] text-slate font-normal">{doc.filename}</span>
                          </div>
                        </td>
                        <td className="py-3 px-4 uppercase text-slate font-medium">{doc.file_type}</td>
                        <td className="py-3 px-4">
                          <span className="px-2 py-0.5 rounded-md bg-cloud text-slate text-[11px] font-medium capitalize">
                            {doc.knowledge_type?.replace("_", " ") || "General"}
                          </span>
                        </td>
                        <td className="py-3 px-4">{getStatusBadge(doc.status)}</td>
                        <td className="py-3 px-4 text-slate">v{doc.current_version_num || 1}</td>
                        <td className="py-3 px-4 font-medium text-ink">{doc.chunk_count || 0}</td>
                        <td className="py-3 px-4 text-right">
                          <button
                            onClick={() => handleInspectDocument(doc)}
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-teal-soft text-teal hover:bg-teal/20 text-xs font-semibold transition-colors"
                          >
                            <Eye className="w-3.5 h-3.5" />
                            Inspect Chunks
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 2: Collections */}
      {activeTab === "collections" && (
        <div className="space-y-6">
          {/* Create Collection Card */}
          <div className="bg-surface rounded-2xl p-6 border border-border shadow-soft">
            <h2 className="text-base font-semibold text-ink flex items-center gap-2">
              <FolderPlus className="w-4 h-4 text-teal" />
              Create Knowledge Collection
            </h2>
            <p className="text-xs text-slate mt-0.5">
              Organize documents by business domain (e.g. Policies, Pricing Rules, KPI Definitions, SOPs).
            </p>

            <form onSubmit={handleCreateCollection} className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
              <div>
                <label className="block text-xs font-medium text-slate mb-1">Collection Name</label>
                <input
                  type="text"
                  placeholder="e.g. Sales & Pricing Policies"
                  value={newCollectionName}
                  onChange={(e) => setNewCollectionName(e.target.value)}
                  className="w-full text-xs rounded-xl border border-border bg-background px-3 py-2 text-ink focus:outline-none focus:ring-2 focus:ring-teal"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate mb-1">Description (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g. Global sales discount thresholds and SLA definitions"
                  value={newCollectionDesc}
                  onChange={(e) => setNewCollectionDesc(e.target.value)}
                  className="w-full text-xs rounded-xl border border-border bg-background px-3 py-2 text-ink focus:outline-none focus:ring-2 focus:ring-teal"
                />
              </div>
              <div>
                <button
                  type="submit"
                  disabled={!newCollectionName.trim()}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-xl bg-teal text-white text-xs font-semibold hover:bg-teal-dark disabled:opacity-50 transition-colors shadow-soft"
                >
                  <FolderPlus className="w-3.5 h-3.5" />
                  Create Collection
                </button>
              </div>
            </form>
          </div>

          {/* Collections Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {collections.map((col) => {
              const docCount = documents.filter((d) => d.collection_id === col.id).length;
              return (
                <div
                  key={col.id}
                  className="bg-surface rounded-2xl p-5 border border-border shadow-soft flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <div className="p-2 rounded-xl bg-teal-soft text-teal">
                        <Layers className="w-4 h-4" />
                      </div>
                      <span className="text-xs font-semibold text-slate bg-cloud px-2 py-0.5 rounded-md">
                        {docCount} {docCount === 1 ? "document" : "documents"}
                      </span>
                    </div>
                    <h3 className="text-sm font-bold text-ink">{col.name}</h3>
                    {col.description && (
                      <p className="text-xs text-slate mt-1 line-clamp-2">{col.description}</p>
                    )}
                  </div>
                  <div className="mt-4 pt-3 border-t border-border flex items-center justify-between text-xs text-slate">
                    <span>ID: {col.id.slice(0, 8)}...</span>
                    <button
                      onClick={() => {
                        setSelectedCollectionId(col.id);
                        setActiveTab("documents");
                      }}
                      className="text-teal font-semibold hover:underline flex items-center gap-1"
                    >
                      View Docs <ExternalLink className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Tab 3: Dataset ↔ Knowledge Linking */}
      {activeTab === "links" && (
        <div className="space-y-6">
          {/* Link Form */}
          <div className="bg-surface rounded-2xl p-6 border border-border shadow-soft">
            <h2 className="text-base font-semibold text-ink flex items-center gap-2">
              <Link2 className="w-4 h-4 text-teal" />
              Link Business Document to Dataset
            </h2>
            <p className="text-xs text-slate mt-0.5">
              Bind contextual knowledge to quantitative datasets. When conversational queries target a linked dataset, relevant business documents will be prioritized for evidence retrieval.
            </p>

            <form onSubmit={handleLinkDataset} className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
              <div>
                <label className="block text-xs font-medium text-slate mb-1">Select Dataset</label>
                <select
                  value={linkDatasetId}
                  onChange={(e) => setLinkDatasetId(e.target.value)}
                  className="w-full text-xs rounded-xl border border-border bg-background px-3 py-2 text-ink focus:outline-none focus:ring-2 focus:ring-teal"
                >
                  <option value="">-- Choose Dataset --</option>
                  {datasets.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name || d.id}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate mb-1">Select Business Document</label>
                <select
                  value={linkDocumentId}
                  onChange={(e) => setLinkDocumentId(e.target.value)}
                  className="w-full text-xs rounded-xl border border-border bg-background px-3 py-2 text-ink focus:outline-none focus:ring-2 focus:ring-teal"
                >
                  <option value="">-- Choose Document --</option>
                  {documents.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.title} (v{d.current_version_num})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <button
                  type="submit"
                  disabled={!linkDatasetId || !linkDocumentId}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-xl bg-teal text-white text-xs font-semibold hover:bg-teal-dark disabled:opacity-50 transition-colors shadow-soft"
                >
                  <Link2 className="w-3.5 h-3.5" />
                  Establish Association
                </button>
              </div>
            </form>
          </div>

          {/* Links View */}
          <div className="bg-surface rounded-2xl border border-border shadow-soft p-6">
            <h3 className="text-sm font-semibold text-ink mb-3">Active Dataset-Knowledge Associations</h3>
            {links.length === 0 ? (
              <p className="text-xs text-slate">No manual dataset associations defined yet. Create one above.</p>
            ) : (
              <div className="space-y-2">
                {links.map((link) => (
                  <div
                    key={link.id}
                    className="p-3 rounded-xl bg-cloud flex items-center justify-between text-xs"
                  >
                    <div className="flex items-center gap-3">
                      <FileSpreadsheet className="w-4 h-4 text-indigo-500" />
                      <span className="font-semibold text-ink">Dataset {link.dataset_id.slice(0, 8)}...</span>
                      <span className="text-slate">↔</span>
                      <BookOpen className="w-4 h-4 text-teal" />
                      <span className="font-semibold text-ink">Document {link.document_id?.slice(0, 8)}...</span>
                    </div>
                    <span className="text-[10px] bg-teal-soft text-teal px-2 py-0.5 rounded font-medium">
                      Context Provider
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 4: Hybrid Search & Citation Explorer */}
      {activeTab === "search" && (
        <div className="space-y-6">
          <div className="bg-surface rounded-2xl p-6 border border-border shadow-soft">
            <h2 className="text-base font-semibold text-ink flex items-center gap-2">
              <Search className="w-4 h-4 text-teal" />
              Grounded Hybrid Knowledge Search
            </h2>
            <p className="text-xs text-slate mt-0.5">
              Test semantic vector retrieval combined with keyword BM25 scoring. Inspect generated citations and evidence sufficiency.
            </p>

            <form onSubmit={handleSearch} className="mt-4 flex gap-3">
              <input
                type="text"
                placeholder="e.g. What is our refund duration policy? or What is the definition of churn?"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="flex-1 text-xs rounded-xl border border-border bg-background px-4 py-2.5 text-ink focus:outline-none focus:ring-2 focus:ring-teal"
              />
              <button
                type="submit"
                disabled={!searchQuery.trim() || isSearching}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-teal text-white text-xs font-semibold hover:bg-teal-dark disabled:opacity-50 transition-colors shadow-soft"
              >
                {isSearching ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                Search
              </button>
            </form>
          </div>

          {/* Search Results */}
          {searchResults && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate">
                  Retrieved {searchResults.results.length} candidate chunks
                </span>
                <span
                  className={`text-xs px-2.5 py-0.5 rounded-full font-semibold ${
                    searchResults.has_sufficient_evidence
                      ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                      : "bg-rose-50 text-rose-700 border border-rose-200"
                  }`}
                >
                  {searchResults.has_sufficient_evidence
                    ? "✓ Sufficient Evidence Grounding"
                    : "⚠ Insufficient Evidence (Refusal Required)"}
                </span>
              </div>

              {/* Citations Preview */}
              {searchResults.citations.length > 0 && (
                <div className="bg-surface rounded-2xl p-4 border border-teal-200 bg-teal-soft/30 shadow-soft">
                  <h4 className="text-xs font-bold text-teal flex items-center gap-1.5 mb-2">
                    <Sparkles className="w-3.5 h-3.5" />
                    Formal Citations Generated
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {searchResults.citations.map((c, idx) => (
                      <div
                        key={idx}
                        className="px-3 py-1.5 rounded-xl bg-white border border-teal-200 text-xs font-medium text-ink shadow-sm"
                      >
                        <span className="font-bold text-teal mr-1">[{idx + 1}]</span>
                        {c.document_title}
                        {c.page_number ? `, p. ${c.page_number}` : ""} (v{c.version_number})
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Chunks List */}
              <div className="space-y-3">
                {searchResults.results.map((item, idx) => (
                  <div
                    key={item.chunk_id || idx}
                    className="bg-surface rounded-2xl p-4 border border-border shadow-soft space-y-2"
                  >
                    <div className="flex items-center justify-between text-xs text-slate">
                      <div className="flex items-center gap-2">
                        <Tag className="w-3.5 h-3.5 text-teal" />
                        <span className="font-semibold text-ink">
                          {item.section_heading || "General Section"}
                        </span>
                        {item.page_number && (
                          <span className="bg-cloud px-1.5 py-0.5 rounded text-[10px]">
                            Page {item.page_number}
                          </span>
                        )}
                      </div>
                      <span className="text-[11px] text-teal font-medium">Chunk #{item.chunk_index}</span>
                    </div>
                    <p className="text-xs text-ink/90 leading-relaxed font-mono bg-cloud/50 p-3 rounded-xl">
                      {item.content}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Inspect Document Modal */}
      {inspectingDoc && (
        <div className="fixed inset-0 z-50 bg-ink/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-surface rounded-2xl border border-border shadow-soft-lg max-w-3xl w-full max-h-[85vh] flex flex-col overflow-hidden">
            <div className="p-5 border-b border-border flex items-center justify-between bg-cloud">
              <div>
                <h3 className="text-sm font-bold text-ink flex items-center gap-2">
                  <FileText className="w-4 h-4 text-teal" />
                  {inspectingDoc.title}
                </h3>
                <p className="text-[11px] text-slate mt-0.5">
                  Type: {inspectingDoc.file_type} | Version: v{inspectingDoc.current_version_num} | ID: {inspectingDoc.id}
                </p>
              </div>
              <button
                onClick={() => setInspectingDoc(null)}
                className="text-slate hover:text-ink text-xs font-semibold px-2.5 py-1 rounded-lg hover:bg-cloud"
              >
                Close
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-4 flex-1">
              {isDetailLoading ? (
                <div className="p-12 text-center text-slate">
                  <RefreshCw className="w-6 h-6 mx-auto animate-spin text-teal mb-2" />
                  <p className="text-xs font-medium">Loading document chunks and versions...</p>
                </div>
              ) : (
                <>
                  <div>
                    <h4 className="text-xs font-bold uppercase text-slate tracking-wider mb-2">
                      Indexed Semantic Chunks ({inspectingChunks.length})
                    </h4>
                    <div className="space-y-2">
                      {inspectingChunks.map((chunk) => (
                        <div
                          key={chunk.id}
                          className="p-3 rounded-xl border border-border bg-background text-xs space-y-1.5"
                        >
                          <div className="flex items-center justify-between text-slate text-[11px]">
                            <span className="font-semibold text-teal">
                              {chunk.section_heading || "Untitled Section"}
                            </span>
                            <span>
                              {chunk.page_number ? `p. ${chunk.page_number} | ` : ""}
                              {chunk.token_count || 0} tokens
                            </span>
                          </div>
                          <p className="text-ink leading-relaxed font-mono text-[11px] bg-cloud/40 p-2.5 rounded-lg">
                            {chunk.content}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
