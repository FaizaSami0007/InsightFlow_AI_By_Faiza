"use client";

import * as React from "react";
import Link from "next/link";
import {
  Clock,
  Download,
  FileSpreadsheet,
  History,
  Lock,
  Plus,
  RefreshCw,
  Upload,
  UploadCloud,
  X,
} from "lucide-react";
import { AppShell } from "@/components/shell/app-shell";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { EmptyState } from "@/components/states/empty-state";
import { ErrorState } from "@/components/states/error-state";
import { LoadingState } from "@/components/states/loading-state";
import { api, ApiError } from "@/lib/api-client";
import { useAuthStore } from "@/stores/use-auth-store";
import { Dataset, DatasetListResponse, DatasetVersion } from "@/types";

export default function DatasetsPage() {
  const { isAuthenticated, isInitializing } = useAuthStore();

  const [datasets, setDatasets] = React.useState<Dataset[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);
  const [fetchError, setFetchError] = React.useState<string | null>(null);

  // Upload Modal State
  const [isUploadOpen, setIsUploadOpen] = React.useState(false);
  const [targetDatasetForVersion, setTargetDatasetForVersion] = React.useState<Dataset | null>(null);
  const [datasetName, setDatasetName] = React.useState("");
  const [datasetDescription, setDatasetDescription] = React.useState("");
  const [selectedFile, setSelectedFile] = React.useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = React.useState<number>(0);
  const [uploadStage, setUploadStage] = React.useState<"idle" | "uploading" | "validating" | "success" | "error">("idle");
  const [uploadError, setUploadError] = React.useState<string | null>(null);
  const [isDragging, setIsDragging] = React.useState(false);

  // Version History Modal State
  const [historyDataset, setHistoryDataset] = React.useState<Dataset | null>(null);
  const [versions, setVersions] = React.useState<DatasetVersion[]>([]);
  const [isLoadingVersions, setIsLoadingVersions] = React.useState(false);

  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const fetchDatasets = React.useCallback(async () => {
    if (!isAuthenticated) return;
    setIsLoading(true);
    setFetchError(null);
    try {
      const response = await api.get<DatasetListResponse>("/api/v1/datasets?page=1&page_size=50");
      setDatasets(response.items);
    } catch (err) {
      setFetchError(err instanceof ApiError ? err.message : "Failed to load datasets.");
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated]);

  React.useEffect(() => {
    if (isAuthenticated) {
      fetchDatasets();
    } else if (!isInitializing) {
      setIsLoading(false);
    }
  }, [isAuthenticated, isInitializing, fetchDatasets]);

  // Open Version History
  const handleOpenHistory = async (dataset: Dataset) => {
    setHistoryDataset(dataset);
    setIsLoadingVersions(true);
    try {
      const res = await api.get<DatasetVersion[]>(`/api/v1/datasets/${dataset.id}/versions`);
      setVersions(res);
    } catch {
      setVersions([]);
    } finally {
      setIsLoadingVersions(false);
    }
  };

  // Open Upload for new Dataset
  const handleOpenUploadNew = () => {
    setTargetDatasetForVersion(null);
    setDatasetName("");
    setDatasetDescription("");
    setSelectedFile(null);
    setUploadStage("idle");
    setUploadError(null);
    setIsUploadOpen(true);
  };

  // Open Upload for next Version
  const handleOpenUploadVersion = (dataset: Dataset) => {
    setTargetDatasetForVersion(dataset);
    setDatasetName(dataset.name);
    setDatasetDescription(dataset.description || "");
    setSelectedFile(null);
    setUploadStage("idle");
    setUploadError(null);
    setIsUploadOpen(true);
  };

  // Handle File Selection with Pre-Validation
  const handleFileChange = (file: File | null) => {
    setUploadError(null);
    if (!file) {
      setSelectedFile(null);
      return;
    }

    const ext = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
    if (ext !== ".csv" && ext !== ".parquet") {
      setUploadError(`Unsupported file format '${ext}'. Please select a .csv or .parquet file.`);
      setSelectedFile(null);
      return;
    }

    const maxBytes = 50 * 1024 * 1024;
    if (file.size > maxBytes) {
      setUploadError(`File exceeds maximum size limit of 50 MB (${(file.size / (1024 * 1024)).toFixed(1)} MB).`);
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
    if (!targetDatasetForVersion && !datasetName) {
      // Auto-populate clean dataset name from filename
      const baseName = file.name.substring(0, file.name.lastIndexOf(".")) || file.name;
      const formatted = baseName.replace(/[-_]+/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
      setDatasetName(formatted);
    }
  };

  // Submit Upload
  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setUploadError("Please select a file to upload.");
      return;
    }

    if (!targetDatasetForVersion && !datasetName.trim()) {
      setUploadError("Dataset name is required.");
      return;
    }

    setUploadStage("uploading");
    setUploadProgress(30);

    const formData = new FormData();
    formData.append("file", selectedFile);
    if (!targetDatasetForVersion) {
      formData.append("name", datasetName.trim());
      if (datasetDescription.trim()) {
        formData.append("description", datasetDescription.trim());
      }
    }

    try {
      setTimeout(() => {
        setUploadProgress(75);
        setUploadStage("validating");
      }, 400);

      if (targetDatasetForVersion) {
        await api.upload(`/api/v1/datasets/${targetDatasetForVersion.id}/versions`, formData);
      } else {
        await api.upload("/api/v1/datasets", formData);
      }

      setUploadProgress(100);
      setUploadStage("success");
      await fetchDatasets();
      setTimeout(() => {
        setIsUploadOpen(false);
      }, 1200);
    } catch (err) {
      setUploadStage("error");
      setUploadError(err instanceof ApiError ? err.message : "Failed to process dataset file.");
    }
  };

  // Download Handler
  const handleDownload = async (dataset: Dataset, versionNumber?: number) => {
    const filename = `${dataset.name.toLowerCase().replace(/\s+/g, "_")}_v${versionNumber || dataset.version_count}.${dataset.latest_version?.file_format.toLowerCase() || "csv"}`;
    const url = `/api/v1/datasets/${dataset.id}/download${versionNumber ? `?version=${versionNumber}` : ""}`;
    try {
      await api.download(url, filename);
    } catch (err) {
      alert(`Download failed: ${err instanceof Error ? err.message : "Unknown error"}`);
    }
  };

  const formatBytes = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  if (isInitializing) {
    return (
      <AppShell>
        <LoadingState title="Initializing Session" description="Verifying authentication..." />
      </AppShell>
    );
  }

  if (!isAuthenticated) {
    return (
      <AppShell>
        <Card className="max-w-xl mx-auto my-12 border-border shadow-soft-md">
          <CardHeader className="text-center pb-2">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-teal-soft text-teal mb-2">
              <Lock className="h-6 w-6" />
            </div>
            <CardTitle>Authentication Required</CardTitle>
            <CardDescription>
              Please sign in to your InsightFlow account to upload, version, and manage your datasets.
            </CardDescription>
          </CardHeader>
          <CardFooter className="flex justify-center gap-3 pt-4">
            <Link href="/login">
              <Button variant="primary">Sign In</Button>
            </Link>
            <Link href="/register">
              <Button variant="outline">Create Account</Button>
            </Link>
          </CardFooter>
        </Card>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="space-y-6">
        {/* Top Header & Actions Bar */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-ink">Datasets & Versioning</h1>
            <p className="text-xs text-slate mt-0.5">
              Manage uploaded structured datasets, inspect version lineage, and prepare files for deterministic analytics.
            </p>
          </div>
          <div className="flex items-center gap-2.5">
            <Button
              variant="outline"
              size="sm"
              onClick={fetchDatasets}
              isLoading={isLoading}
              leftIcon={<RefreshCw className="h-3.5 w-3.5" />}
              aria-label="Refresh datasets list"
            >
              Refresh
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleOpenUploadNew}
              leftIcon={<Plus className="h-4 w-4" />}
            >
              Upload Dataset
            </Button>
          </div>
        </div>

        {/* Content Area with Global States */}
        {isLoading && datasets.length === 0 ? (
          <LoadingState title="Loading Datasets" description="Retrieving your uploaded data files..." />
        ) : fetchError ? (
          <ErrorState message={fetchError} onRetry={fetchDatasets} />
        ) : datasets.length === 0 ? (
          <EmptyState
            icon={<FileSpreadsheet className="h-10 w-10 text-slate" />}
            title="No datasets uploaded yet"
            description="Upload your first CSV or Parquet tabular file to begin automated data profiling, quality checks, and grounded AI analysis."
            action={
              <Button variant="primary" size="sm" onClick={handleOpenUploadNew} leftIcon={<Upload className="h-3.5 w-3.5" />}>
                Upload First Dataset
              </Button>
            }
          />
        ) : (
          <Card className="shadow-soft">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Your Datasets ({datasets.length})</CardTitle>
                  <CardDescription>Server-side ownership verified and versioned</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Dataset Name</TableHead>
                    <TableHead>Format</TableHead>
                    <TableHead>Dimensions</TableHead>
                    <TableHead>Active Version</TableHead>
                    <TableHead>File Size</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Updated</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {datasets.map((dataset) => {
                    const latest = dataset.latest_version;
                    return (
                      <TableRow key={dataset.id}>
                        <TableCell>
                          <div className="flex flex-col">
                            <span className="font-semibold text-ink text-xs">{dataset.name}</span>
                            {dataset.description && (
                              <span className="text-[11px] text-slate truncate max-w-xs">
                                {dataset.description}
                              </span>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant={latest?.file_format === "PARQUET" ? "blue" : "default"}>
                            {latest?.file_format || "CSV"}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <span className="font-mono text-[11px] text-slate">
                            {latest?.row_count !== null ? `${latest?.row_count?.toLocaleString()} rows × ${latest?.column_count} cols` : "—"}
                          </span>
                        </TableCell>
                        <TableCell>
                          <Badge variant="teal" dot>
                            v{dataset.version_count}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-slate font-mono text-[11px]">
                          {latest ? formatBytes(latest.file_size) : "—"}
                        </TableCell>
                        <TableCell>
                          <Badge variant={dataset.status === "READY" ? "teal" : "amber"}>
                            {dataset.status}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-slate text-[11px]">
                          {new Date(dataset.updated_at).toLocaleDateString(undefined, {
                            month: "short",
                            day: "numeric",
                            year: "numeric",
                          })}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDownload(dataset)}
                              title="Download dataset file"
                              aria-label={`Download ${dataset.name}`}
                              leftIcon={<Download className="h-3.5 w-3.5" />}
                            >
                              Download
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleOpenHistory(dataset)}
                              title="View version history"
                              aria-label={`Version history for ${dataset.name}`}
                              leftIcon={<History className="h-3.5 w-3.5" />}
                            >
                              Versions
                            </Button>
                            <Button
                              variant="secondary"
                              size="sm"
                              onClick={() => handleOpenUploadVersion(dataset)}
                              title="Upload updated file version"
                              aria-label={`Upload new version for ${dataset.name}`}
                              leftIcon={<Upload className="h-3.5 w-3.5" />}
                            >
                              New Version
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        )}

        {/* Upload Dataset Modal Dialog */}
        <Dialog
          isOpen={isUploadOpen}
          onClose={() => {
            if (uploadStage !== "uploading") setIsUploadOpen(false);
          }}
          title={targetDatasetForVersion ? `Upload Version for "${targetDatasetForVersion.name}"` : "Upload New Dataset"}
          description={
            targetDatasetForVersion
              ? `Incrementing version to v${targetDatasetForVersion.version_count + 1}`
              : "Upload a structured tabular CSV or Parquet file (up to 50 MB)"
          }
        >
          <form onSubmit={handleUploadSubmit} className="space-y-4">
            {uploadError && (
              <Alert variant="danger">
                <AlertTitle>Upload Error</AlertTitle>
                <AlertDescription>{uploadError}</AlertDescription>
              </Alert>
            )}

            {!targetDatasetForVersion && (
              <>
                <Input
                  label="Dataset Name"
                  placeholder="e.g. Q4 Regional Sales"
                  value={datasetName}
                  onChange={(e) => setDatasetName(e.target.value)}
                  required
                />
                <Input
                  label="Description (Optional)"
                  placeholder="Brief explanation of data origin and contents"
                  value={datasetDescription}
                  onChange={(e) => setDatasetDescription(e.target.value)}
                />
              </>
            )}

            {/* Drag and Drop Zone + File Picker Alternative */}
            <div className="space-y-1.5">
              <label className="block text-xs font-medium text-slate">
                Tabular File (.csv or .parquet)
              </label>
              <div
                onDragOver={(e) => {
                  e.preventDefault();
                  setIsDragging(true);
                }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={(e) => {
                  e.preventDefault();
                  setIsDragging(false);
                  if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                    handleFileChange(e.dataTransfer.files[0]);
                  }
                }}
                className={`flex min-h-[140px] cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-6 text-center transition-all ${
                  isDragging
                    ? "border-teal bg-teal-soft/40"
                    : selectedFile
                    ? "border-teal-border bg-teal-soft/20"
                    : "border-border hover:border-border-strong bg-cloud/50"
                }`}
                onClick={() => fileInputRef.current?.click()}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    fileInputRef.current?.click();
                  }
                }}
                aria-label="Upload dataset drop area. Press enter to open file picker."
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv,.parquet"
                  className="hidden"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      handleFileChange(e.target.files[0]);
                    }
                  }}
                />

                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-surface shadow-soft text-teal mb-2">
                  <UploadCloud className="h-5 w-5" />
                </div>

                {selectedFile ? (
                  <div className="space-y-1">
                    <p className="text-xs font-semibold text-teal">{selectedFile.name}</p>
                    <p className="text-[11px] text-slate">{formatBytes(selectedFile.size)}</p>
                  </div>
                ) : (
                  <div className="space-y-1">
                    <p className="text-xs font-medium text-ink">
                      Drag and drop your file here, or <span className="font-semibold text-teal underline">browse</span>
                    </p>
                    <p className="text-[11px] text-slate">Supports CSV & Parquet up to 50 MB</p>
                  </div>
                )}
              </div>
            </div>

            {/* Upload Stage Progress Bar */}
            {uploadStage === "uploading" && (
              <div className="space-y-2 rounded-xl bg-cloud p-3 text-xs">
                <div className="flex items-center justify-between text-slate">
                  <span className="font-medium">Uploading file to server...</span>
                  <span className="font-mono font-semibold text-teal">{uploadProgress}%</span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-cloud-subtle">
                  <div
                    className="h-full bg-teal transition-all duration-300 rounded-full"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}

            {uploadStage === "validating" && (
              <div className="flex items-center gap-2 rounded-xl bg-teal-soft p-3 text-xs text-teal font-medium">
                <span className="h-2 w-2 rounded-full bg-teal animate-ping" />
                <span>Validating table schema and computing SHA-256 checksum...</span>
              </div>
            )}

            {uploadStage === "success" && (
              <Alert variant="success">
                <AlertTitle>Success</AlertTitle>
                <AlertDescription>Dataset uploaded and validated successfully!</AlertDescription>
              </Alert>
            )}

            <div className="flex justify-end gap-2 pt-3 border-t border-border">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setIsUploadOpen(false)}
                disabled={uploadStage === "uploading" || uploadStage === "validating"}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                size="sm"
                disabled={!selectedFile || uploadStage === "uploading" || uploadStage === "validating"}
                isLoading={uploadStage === "uploading" || uploadStage === "validating"}
              >
                {targetDatasetForVersion ? "Upload Version" : "Upload Dataset"}
              </Button>
            </div>
          </form>
        </Dialog>

        {/* Version History Modal Dialog */}
        <Dialog
          isOpen={!!historyDataset}
          onClose={() => setHistoryDataset(null)}
          title={`Version History — ${historyDataset?.name || ""}`}
          description="Immutable record of all uploaded dataset versions"
          className="max-w-2xl"
        >
          <div className="space-y-4">
            {isLoadingVersions ? (
              <LoadingState title="Loading Versions" description="Retrieving history records..." />
            ) : versions.length === 0 ? (
              <p className="text-xs text-slate py-4 text-center">No versions recorded.</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Version</TableHead>
                    <TableHead>File Name</TableHead>
                    <TableHead>Format</TableHead>
                    <TableHead>Dimensions</TableHead>
                    <TableHead>Size</TableHead>
                    <TableHead>Checksum (SHA-256)</TableHead>
                    <TableHead>Uploaded</TableHead>
                    <TableHead className="text-right">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {versions.map((ver) => (
                    <TableRow key={ver.id}>
                      <TableCell>
                        <Badge variant="teal" dot>
                          v{ver.version_number}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-semibold text-xs text-ink">{ver.file_name}</TableCell>
                      <TableCell>
                        <Badge variant={ver.file_format === "PARQUET" ? "blue" : "default"}>
                          {ver.file_format}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-slate font-mono text-[11px]">
                        {ver.row_count !== null ? `${ver.row_count?.toLocaleString()} × ${ver.column_count}` : "—"}
                      </TableCell>
                      <TableCell className="text-slate font-mono text-[11px]">
                        {formatBytes(ver.file_size)}
                      </TableCell>
                      <TableCell className="text-slate font-mono text-[10px]" title={ver.checksum}>
                        {ver.checksum.slice(0, 8)}...
                      </TableCell>
                      <TableCell className="text-slate text-[11px]">
                        <span className="inline-flex items-center gap-1">
                          <Clock className="h-3 w-3 text-slate/70" />
                          {new Date(ver.created_at).toLocaleDateString()}
                        </span>
                      </TableCell>
                      <TableCell className="text-right">
                        {historyDataset && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDownload(historyDataset, ver.version_number)}
                            title="Download this version"
                            aria-label={`Download version ${ver.version_number}`}
                            leftIcon={<Download className="h-3.5 w-3.5" />}
                          >
                            Get
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}

            <div className="flex justify-end pt-2">
              <Button variant="outline" size="sm" onClick={() => setHistoryDataset(null)}>
                Close
              </Button>
            </div>
          </div>
        </Dialog>
      </div>
    </AppShell>
  );
}
