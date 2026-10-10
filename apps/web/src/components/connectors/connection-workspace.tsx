"use client";

import React, { useState, useEffect } from "react";
import {
  Database,
  Globe,
  HardDrive,
  FileSpreadsheet,
  Plus,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Clock,
  Eye,
  ArrowRight,
  Shield,
  Activity,
  Layers,
  ChevronRight,
  Search,
  Check,
  Play,
  KeyRound,
  ExternalLink,
} from "lucide-react";
import {
  ConnectorType,
  ConnectorCatalogItem,
  DataConnection,
  ConnectionTestResult,
  ResourceSpec,
  ResourcePreviewResponse,
  DataConnectionSyncJob,
  ConnectionHealthResponse,
} from "@/types";
import { Button } from "@/components/ui/button";
import { PageHero } from "@/components/ui/page-hero";

export function ConnectionWorkspace() {
  const [activeTab, setActiveTab] = useState<"connections" | "catalog" | "sync_history">("connections");
  const [connections, setConnections] = useState<DataConnection[]>([]);
  const [catalog, setCatalog] = useState<ConnectorCatalogItem[]>([]);
  const [selectedConnection, setSelectedConnection] = useState<DataConnection | null>(null);
  const [connectionHealth, setConnectionHealth] = useState<ConnectionHealthResponse | null>(null);
  const [discoveredSchema, setDiscoveredSchema] = useState<ResourceSpec[]>([]);
  const [selectedResource, setSelectedResource] = useState<string | null>(null);
  const [previewData, setPreviewData] = useState<ResourcePreviewResponse | null>(null);
  const [syncJobs, setSyncJobs] = useState<DataConnectionSyncJob[]>([]);

  // Wizard state
  const [isWizardOpen, setIsWizardOpen] = useState(false);
  const [wizardStep, setWizardStep] = useState<number>(1);
  const [selectedConnectorType, setSelectedConnectorType] = useState<ConnectorType>("POSTGRESQL");
  const [connName, setConnName] = useState("");
  const [connDescription, setConnDescription] = useState("");
  const [configFields, setConfigFields] = useState<Record<string, any>>({
    host: "localhost",
    port: 5432,
    database: "analytics",
    username: "postgres",
  });
  const [credFields, setCredFields] = useState<Record<string, any>>({
    password: "",
  });
  const [syncSchedule, setSyncSchedule] = useState("0 */6 * * *");
  const [testResult, setTestResult] = useState<ConnectionTestResult | null>(null);
  const [isTesting, setIsTesting] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  // Demo / Initial state initialization
  useEffect(() => {
    // Default catalog
    const initialCatalog: ConnectorCatalogItem[] = [
      {
        connector_type: "POSTGRESQL",
        name: "PostgreSQL",
        category: "Database",
        description: "Enterprise relational database with read-only query safety and schema discovery.",
        supported_auth: ["PASSWORD", "SSL_CERT", "IAM"],
        capabilities: ["FULL_SYNC", "INCREMENTAL_SYNC", "SCHEMA_DISCOVERY", "PREVIEW"],
        required_config: ["host", "port", "database", "username"],
        is_available: true,
      },
      {
        connector_type: "MYSQL",
        name: "MySQL",
        category: "Database",
        description: "High-performance relational storage with binary-safe streaming synchronization.",
        supported_auth: ["PASSWORD", "SSL_CERT"],
        capabilities: ["FULL_SYNC", "INCREMENTAL_SYNC", "SCHEMA_DISCOVERY", "PREVIEW"],
        required_config: ["host", "port", "database", "username"],
        is_available: true,
      },
      {
        connector_type: "SQLITE",
        name: "SQLite",
        category: "Database",
        description: "File-backed or embedded SQLite databases with immutable table introspection.",
        supported_auth: ["NONE", "FILE_PERMISSIONS"],
        capabilities: ["FULL_SYNC", "INCREMENTAL_SYNC", "SCHEMA_DISCOVERY", "PREVIEW"],
        required_config: ["database_path"],
        is_available: true,
      },
      {
        connector_type: "REST_API",
        name: "REST API / Webhook",
        category: "API",
        description: "Generic HTTP/REST endpoints with SSRF protection, pagination, and JSON normalization.",
        supported_auth: ["API_KEY", "BEARER_TOKEN", "BASIC_AUTH", "OAUTH2"],
        capabilities: ["FULL_SYNC", "INCREMENTAL_SYNC", "SCHEMA_DISCOVERY", "PREVIEW"],
        required_config: ["base_url"],
        is_available: true,
      },
      {
        connector_type: "OBJECT_STORAGE",
        name: "Cloud Object Storage (S3/GCS/Azure)",
        category: "Storage",
        description: "Parquet, CSV, and JSON datasets in AWS S3, Google Cloud Storage, or Azure Blob.",
        supported_auth: ["ACCESS_KEY", "IAM_ROLE", "SAS_TOKEN"],
        capabilities: ["FULL_SYNC", "INCREMENTAL_SYNC", "SCHEMA_DISCOVERY", "PREVIEW"],
        required_config: ["bucket_name"],
        is_available: true,
      },
      {
        connector_type: "GOOGLE_SHEETS",
        name: "Google Sheets",
        category: "Spreadsheet",
        description: "Cloud spreadsheets with named worksheet range synchronization and live drift tracking.",
        supported_auth: ["OAUTH2", "SERVICE_ACCOUNT"],
        capabilities: ["FULL_SYNC", "SCHEMA_DISCOVERY", "PREVIEW"],
        required_config: ["spreadsheet_id"],
        is_available: true,
      },
    ];
    setCatalog(initialCatalog);

    // Initial default active connections
    const initialConnections: DataConnection[] = [
      {
        id: "conn-prod-pg-01",
        user_id: "user-admin",
        name: "Production Analytics Replica",
        description: "Postgres read-replica for real-time sales & billing aggregation.",
        connector_type: "POSTGRESQL",
        status: "ACTIVE",
        configuration: { host: "aurora.prod.internal", port: 5432, database: "commerce_db", username: "analyst_ro" },
        health_status: "HEALTHY",
        health_details: { latency_ms: 18.4, last_message: "Connection verified" },
        sync_schedule: "0 */6 * * *",
        is_active: true,
        last_tested_at: new Date(Date.now() - 3600000).toISOString(),
        last_sync_at: new Date(Date.now() - 7200000).toISOString(),
        created_at: new Date(Date.now() - 86400000 * 7).toISOString(),
        updated_at: new Date(Date.now() - 3600000).toISOString(),
      },
      {
        id: "conn-stripe-api-02",
        user_id: "user-admin",
        name: "Stripe Billing REST API",
        description: "Payment gateway event ingestion for churn & MRR predictive modeling.",
        connector_type: "REST_API",
        status: "ACTIVE",
        configuration: { base_url: "https://api.stripe.com/v1" },
        health_status: "HEALTHY",
        health_details: { latency_ms: 45.2, status_code: 200 },
        sync_schedule: "0 0 * * *",
        is_active: true,
        last_tested_at: new Date(Date.now() - 7200000).toISOString(),
        last_sync_at: new Date(Date.now() - 14400000).toISOString(),
        created_at: new Date(Date.now() - 86400000 * 14).toISOString(),
        updated_at: new Date(Date.now() - 7200000).toISOString(),
      },
      {
        id: "conn-s3-lake-03",
        user_id: "user-admin",
        name: "AWS S3 Data Lake (Parquet)",
        description: "Daily partitioned telemetry and clickstream event exports.",
        connector_type: "OBJECT_STORAGE",
        status: "ACTIVE",
        configuration: { bucket_name: "insightflow-lake-production", prefix: "events/v2/" },
        health_status: "HEALTHY",
        health_details: { latency_ms: 62.0 },
        sync_schedule: "0 */12 * * *",
        is_active: true,
        last_tested_at: new Date(Date.now() - 1800000).toISOString(),
        last_sync_at: new Date(Date.now() - 3600000).toISOString(),
        created_at: new Date(Date.now() - 86400000 * 30).toISOString(),
        updated_at: new Date(Date.now() - 1800000).toISOString(),
      },
    ];
    setConnections(initialConnections);
    setSelectedConnection(initialConnections[0]);
  }, []);

  // Update schema & health when connection changes
  useEffect(() => {
    if (!selectedConnection) return;

    if (selectedConnection.connector_type === "POSTGRESQL") {
      setDiscoveredSchema([
        {
          resource_id: "customers",
          name: "customers",
          resource_type: "TABLE",
          estimated_rows: 14250,
          columns: [
            { name: "customer_id", data_type: "UUID", nullable: false, is_primary_key: true },
            { name: "company_name", data_type: "VARCHAR", nullable: false, is_primary_key: false },
            { name: "annual_revenue", data_type: "NUMERIC", nullable: true, is_primary_key: false },
            { name: "churn_risk_score", data_type: "FLOAT", nullable: true, is_primary_key: false },
            { name: "created_at", data_type: "TIMESTAMP", nullable: false, is_primary_key: false },
          ],
        },
        {
          resource_id: "orders",
          name: "orders",
          resource_type: "TABLE",
          estimated_rows: 98400,
          columns: [
            { name: "order_id", data_type: "BIGINT", nullable: false, is_primary_key: true },
            { name: "customer_id", data_type: "UUID", nullable: false, is_primary_key: false },
            { name: "amount", data_type: "NUMERIC", nullable: false, is_primary_key: false },
            { name: "status", data_type: "VARCHAR", nullable: false, is_primary_key: false },
            { name: "order_date", data_type: "TIMESTAMP", nullable: false, is_primary_key: false },
          ],
        },
      ]);
      setSelectedResource("customers");
      setPreviewData({
        resource_id: "customers",
        columns: ["customer_id", "company_name", "annual_revenue", "churn_risk_score", "created_at"],
        data_types: {
          customer_id: "UUID",
          company_name: "VARCHAR",
          annual_revenue: "NUMERIC",
          churn_risk_score: "FLOAT",
          created_at: "TIMESTAMP",
        },
        total_preview_rows: 5,
        estimated_total_rows: 14250,
        rows: [
          { customer_id: "e4a2...01", company_name: "Acme Corp", annual_revenue: 1250000.0, churn_risk_score: 0.12, created_at: "2026-01-15 08:30:00" },
          { customer_id: "e4a2...02", company_name: "Apex Retail", annual_revenue: 430000.0, churn_risk_score: 0.45, created_at: "2026-02-01 11:15:00" },
          { customer_id: "e4a2...03", company_name: "Nexus Global", annual_revenue: 8900000.0, churn_risk_score: 0.04, created_at: "2026-02-14 14:00:00" },
          { customer_id: "e4a2...04", company_name: "Vanguard AI", annual_revenue: 2100000.0, churn_risk_score: 0.28, created_at: "2026-03-01 09:45:00" },
          { customer_id: "e4a2...05", company_name: "Horizon Logistics", annual_revenue: 670000.0, churn_risk_score: 0.81, created_at: "2026-03-10 16:20:00" },
        ],
      });
    }

    setConnectionHealth({
      connection_id: selectedConnection.id,
      health_status: selectedConnection.health_status,
      health_score: 96.5,
      last_successful_sync: selectedConnection.last_sync_at,
      freshness: {
        freshness_status: "FRESH",
        hours_since_sync: 2.0,
        is_stale: false,
        message: "Data is fresh and strictly synchronized with upstream cadence.",
      },
      drift_status: {
        has_drift: false,
        added_columns: [],
        removed_columns: [],
        type_changes: {},
        severity: "NONE",
        recommendation: "NO_ACTION",
      },
      recommendations: ["Connection is healthy and synchronized within scheduled parameters."],
    });

    setSyncJobs([
      {
        id: "job-sync-01",
        connection_id: selectedConnection.id,
        dataset_id: "ds-warehouse-01",
        dataset_version_id: "v-3",
        source_resource: "customers",
        sync_type: "FULL_SYNC",
        status: "COMPLETED",
        started_at: new Date(Date.now() - 7200000).toISOString(),
        completed_at: new Date(Date.now() - 7185000).toISOString(),
        rows_processed: 14250,
        rows_added: 14250,
        rows_updated: 0,
        rows_rejected: 0,
        sync_metadata: { duration_seconds: 15, bytes_ingested: 1845000 },
        created_at: new Date(Date.now() - 7200000).toISOString(),
      },
      {
        id: "job-sync-02",
        connection_id: selectedConnection.id,
        dataset_id: "ds-warehouse-01",
        dataset_version_id: "v-2",
        source_resource: "customers",
        sync_type: "FULL_SYNC",
        status: "COMPLETED",
        started_at: new Date(Date.now() - 28800000).toISOString(),
        completed_at: new Date(Date.now() - 28785000).toISOString(),
        rows_processed: 14120,
        rows_added: 14120,
        rows_updated: 0,
        rows_rejected: 0,
        sync_metadata: { duration_seconds: 14, bytes_ingested: 1832000 },
        created_at: new Date(Date.now() - 28800000).toISOString(),
      },
    ]);
  }, [selectedConnection]);

  // Handle direct connection testing
  const handleTestConnection = async () => {
    setIsTesting(true);
    setTestResult(null);
    try {
      // Simulate live network ping
      await new Promise((r) => setTimeout(r, 800));
      setTestResult({
        success: true,
        status: "SUCCESS",
        message: "Successfully validated read-only handshake and discovered remote schemas.",
        latency_ms: 22.4,
        discovered_resources_count: 4,
        tested_at: new Date().toISOString(),
      });
    } catch {
      setTestResult({
        success: false,
        status: "NETWORK_ERROR",
        message: "Failed to connect to target data source.",
        latency_ms: 120.0,
        discovered_resources_count: 0,
        tested_at: new Date().toISOString(),
      });
    } finally {
      setIsTesting(false);
    }
  };

  // Handle saving new connection
  const handleSaveConnection = async () => {
    setIsSaving(true);
    try {
      await new Promise((r) => setTimeout(r, 600));
      const newConn: DataConnection = {
        id: `conn-${Date.now()}`,
        user_id: "user-admin",
        name: connName || `${selectedConnectorType} Source`,
        description: connDescription || "Enterprise connector source.",
        connector_type: selectedConnectorType,
        status: "ACTIVE",
        configuration: configFields,
        health_status: "HEALTHY",
        health_details: { latency_ms: 22.4 },
        sync_schedule: syncSchedule,
        is_active: true,
        last_tested_at: new Date().toISOString(),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      setConnections([newConn, ...connections]);
      setSelectedConnection(newConn);
      setIsWizardOpen(false);
      setWizardStep(1);
    } finally {
      setIsSaving(false);
    }
  };

  // Handle on-demand sync trigger
  const handleTriggerSync = async () => {
    if (!selectedConnection || !selectedResource) return;
    setIsSyncing(true);
    try {
      await new Promise((r) => setTimeout(r, 1200));
      const newJob: DataConnectionSyncJob = {
        id: `job-sync-${Date.now()}`,
        connection_id: selectedConnection.id,
        dataset_id: "ds-warehouse-live",
        dataset_version_id: `v-${syncJobs.length + 1}`,
        source_resource: selectedResource,
        sync_type: "FULL_SYNC",
        status: "COMPLETED",
        started_at: new Date().toISOString(),
        completed_at: new Date().toISOString(),
        rows_processed: 14250,
        rows_added: 14250,
        rows_updated: 0,
        rows_rejected: 0,
        sync_metadata: { duration_seconds: 1.2, bytes_ingested: 1845000 },
        created_at: new Date().toISOString(),
      };
      setSyncJobs([newJob, ...syncJobs]);
      setSelectedConnection({
        ...selectedConnection,
        last_sync_at: new Date().toISOString(),
      });
    } finally {
      setIsSyncing(false);
    }
  };

  const getConnectorIcon = (type: ConnectorType) => {
    switch (type) {
      case "POSTGRESQL":
      case "MYSQL":
      case "SQLITE":
        return <Database className="h-5 w-5 text-teal" />;
      case "REST_API":
        return <Globe className="h-5 w-5 text-indigo" />;
      case "OBJECT_STORAGE":
        return <HardDrive className="h-5 w-5 text-amber" />;
      case "GOOGLE_SHEETS":
        return <FileSpreadsheet className="h-5 w-5 text-emerald" />;
      default:
        return <Layers className="h-5 w-5 text-muted-foreground" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header & Actions via Shared PageHero */}
      <PageHero
        icon={<Shield className="h-6 w-6" />}
        iconVariant="teal"
        title="Enterprise Data Connectors"
        description="Secure, encrypted real-world integrations for SQL databases, REST APIs, cloud object storage, and spreadsheets."
        actions={
          <>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setActiveTab(activeTab === "catalog" ? "connections" : "catalog")}
              className="border-border text-foreground hover:bg-muted text-xs whitespace-nowrap"
            >
              {activeTab === "catalog" ? "View Active Connections" : "Browse Connector Catalog"}
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => {
                setIsWizardOpen(true);
                setWizardStep(1);
              }}
              className="bg-teal text-white hover:bg-teal-hover shadow-soft flex items-center gap-1.5 text-xs whitespace-nowrap"
            >
              <Plus className="h-4 w-4 shrink-0" />
              <span>New Connection</span>
            </Button>
          </>
        }
      />

      {/* Main Workspace Layout */}
      {activeTab === "catalog" ? (
        /* Catalog Grid */
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-ink">Available Connector Catalog</h2>
            <div className="relative w-72">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate" />
              <input
                type="text"
                placeholder="Search connector types..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-xl border border-border bg-white pl-9 pr-3 py-1.5 text-xs text-ink placeholder:text-slate focus:outline-none focus:ring-2 focus:ring-teal"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {catalog
              .filter(
                (c) =>
                  c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                  c.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
                  c.category.toLowerCase().includes(searchQuery.toLowerCase())
              )
              .map((item) => (
                <div
                  key={item.connector_type}
                  className="rounded-2xl border border-border bg-white p-5 shadow-soft hover:shadow-soft-lg transition-all duration-200 flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <div className="p-2.5 rounded-xl bg-teal-soft border border-teal-border text-teal">
                        {getConnectorIcon(item.connector_type)}
                      </div>
                      <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-cloud text-slate">
                        {item.category}
                      </span>
                    </div>
                    <h3 className="text-sm font-bold text-ink">{item.name}</h3>
                    <p className="text-xs text-slate mt-1 line-clamp-2">{item.description}</p>

                    <div className="mt-4 space-y-2">
                      <div className="text-[11px] font-medium text-slate">Capabilities:</div>
                      <div className="flex flex-wrap gap-1.5">
                        {item.capabilities.map((cap) => (
                          <span
                            key={cap}
                            className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-teal-soft/60 text-teal border border-teal-border"
                          >
                            {cap}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="mt-5 pt-4 border-t border-border flex items-center justify-between">
                    <span className="text-xs text-teal flex items-center gap-1 font-semibold">
                      <CheckCircle2 className="h-3.5 w-3.5" /> Production Ready
                    </span>
                    <Button
                      variant="outline"
                      onClick={() => {
                        setSelectedConnectorType(item.connector_type);
                        setIsWizardOpen(true);
                        setWizardStep(2);
                      }}
                      className="text-xs py-1 h-8"
                    >
                      Connect <ArrowRight className="h-3.5 w-3.5 ml-1" />
                    </Button>
                  </div>
                </div>
              ))}
          </div>
        </div>
      ) : (
        /* Active Connections & Live Detail Split View */
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Connection List (4 cols) */}
          <div className="lg:col-span-4 space-y-3">
            <div className="flex items-center justify-between px-1">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate">
                Connected Sources ({connections.length})
              </span>
            </div>

            <div className="space-y-2">
              {connections.map((conn) => {
                const isSelected = selectedConnection?.id === conn.id;
                return (
                  <button
                    key={conn.id}
                    onClick={() => setSelectedConnection(conn)}
                    className={`w-full text-left p-4 rounded-2xl border transition-all duration-200 ${
                      isSelected
                        ? "border-teal bg-teal-soft/40 shadow-soft ring-1 ring-teal/30"
                        : "border-border bg-white hover:border-teal/50 hover:bg-cloud"
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-xl bg-cloud border border-border">
                          {getConnectorIcon(conn.connector_type)}
                        </div>
                        <div>
                          <div className="font-semibold text-xs text-ink">{conn.name}</div>
                          <div className="text-xs text-slate flex items-center gap-1.5 mt-0.5">
                            <span className="font-mono text-[11px] uppercase">{conn.connector_type}</span>
                            <span>•</span>
                            <span className="flex items-center gap-1 text-teal font-medium">
                              <span className="h-1.5 w-1.5 rounded-full bg-teal"></span> Active
                            </span>
                          </div>
                        </div>
                      </div>
                      <ChevronRight className={`h-4 w-4 mt-1 transition-transform ${isSelected ? "text-teal rotate-90" : "text-slate"}`} />
                    </div>

                    <div className="mt-3 flex items-center justify-between text-[11px] text-slate pt-2 border-t border-border">
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {conn.last_sync_at ? "Synced 2h ago" : "Not synced"}
                      </span>
                      <span className="font-mono text-[10px] bg-cloud px-1.5 py-0.5 rounded border border-border">
                        {conn.sync_schedule || "Manual"}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Right Live Inspection & Resource Browser (8 cols) */}
          <div className="lg:col-span-8 space-y-6">
            {selectedConnection ? (
              <div className="space-y-6">
                {/* Connection Header & Health Summary Card */}
                <div className="rounded-2xl border border-border bg-white p-6 shadow-soft">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                    <div className="flex items-center gap-3.5">
                      <div className="p-3 rounded-2xl bg-teal-soft border border-teal-border text-teal">
                        {getConnectorIcon(selectedConnection.connector_type)}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h2 className="text-lg font-bold text-ink">{selectedConnection.name}</h2>
                          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-teal-soft text-teal border border-teal-border">
                            {selectedConnection.health_status}
                          </span>
                        </div>
                        <p className="text-xs text-slate mt-0.5">{selectedConnection.description}</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        onClick={handleTriggerSync}
                        disabled={isSyncing}
                        className="text-xs h-9 flex items-center gap-1.5 border-teal/40 text-teal hover:bg-teal-soft"
                      >
                        <RefreshCw className={`h-3.5 w-3.5 ${isSyncing ? "animate-spin" : ""}`} />
                        {isSyncing ? "Syncing..." : "Sync Now"}
                      </Button>
                    </div>
                  </div>

                  {/* Health & Freshness Indicators */}
                  <div className="mt-5 grid grid-cols-1 sm:grid-cols-3 gap-3 pt-4 border-t border-border">
                    <div className="p-3 rounded-xl bg-cloud border border-border flex items-center gap-3">
                      <Activity className="h-5 w-5 text-teal shrink-0" />
                      <div>
                        <div className="text-[11px] text-slate">Health Score</div>
                        <div className="text-sm font-bold text-ink">
                          {connectionHealth?.health_score || 95.0} / 100
                        </div>
                      </div>
                    </div>
                    <div className="p-3 rounded-xl bg-cloud border border-border flex items-center gap-3">
                      <Clock className="h-5 w-5 text-blue shrink-0" />
                      <div>
                        <div className="text-[11px] text-slate">Freshness Status</div>
                        <div className="text-sm font-bold text-teal">
                          {connectionHealth?.freshness.freshness_status || "FRESH"}
                        </div>
                      </div>
                    </div>
                    <div className="p-3 rounded-xl bg-cloud border border-border flex items-center gap-3">
                      <Shield className="h-5 w-5 text-teal shrink-0" />
                      <div>
                        <div className="text-[11px] text-slate">Security Guard</div>
                        <div className="text-sm font-bold text-ink">SSRF & Read-Only Safe</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Resource Browser & Live Table Preview */}
                <div className="rounded-2xl border border-border bg-white p-6 shadow-soft space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-base font-bold text-ink flex items-center gap-2">
                        <Layers className="h-4 w-4 text-teal" /> Discovered Resources
                      </h3>
                      <p className="text-xs text-slate mt-0.5">
                        Schema discovered via safe introspection with zero remote mutations.
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      {discoveredSchema.map((res) => (
                        <button
                          key={res.resource_id}
                          onClick={() => setSelectedResource(res.resource_id)}
                          className={`px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all ${
                            selectedResource === res.resource_id
                              ? "border-teal bg-teal-soft text-teal"
                              : "border-border bg-cloud text-slate hover:bg-white"
                          }`}
                        >
                          {res.name} ({res.estimated_rows?.toLocaleString()} rows)
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Schema Columns & Data Preview Tabs */}
                  {previewData && (
                    <div className="space-y-3">
                      <div className="text-xs font-semibold text-slate uppercase tracking-wider">
                        Live Preview ({previewData.total_preview_rows} rows sampled)
                      </div>
                      <div className="overflow-x-auto rounded-xl border border-border bg-cloud">
                        <table className="w-full text-left text-xs border-collapse">
                          <thead>
                            <tr className="border-b border-border bg-white text-slate font-semibold">
                              {previewData.columns.map((col) => (
                                <th key={col} className="px-3 py-2.5 font-medium whitespace-nowrap">
                                  <div className="flex items-center gap-1.5">
                                    <span className="text-ink font-semibold">{col}</span>
                                    <span className="text-[10px] font-mono text-teal font-normal">
                                      {previewData.data_types[col] || "TEXT"}
                                    </span>
                                  </div>
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-border bg-white">
                            {previewData.rows.map((row, idx) => (
                              <tr key={idx} className="hover:bg-cloud transition-colors">
                                {previewData.columns.map((col) => (
                                  <td key={col} className="px-3 py-2 text-ink font-mono text-[11px] whitespace-nowrap">
                                    {String(row[col] ?? "")}
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>

                {/* Synchronization Job History */}
                <div className="rounded-2xl border border-border bg-white p-6 shadow-soft space-y-3">
                  <h3 className="text-base font-bold text-ink flex items-center gap-2">
                    <RefreshCw className="h-4 w-4 text-teal" /> Synchronization Audit History
                  </h3>
                  <div className="space-y-2">
                    {syncJobs.map((job) => (
                      <div
                        key={job.id}
                        className="p-3.5 rounded-xl border border-border bg-cloud flex items-center justify-between text-xs"
                      >
                        <div className="flex items-center gap-3">
                          <CheckCircle2 className="h-4 w-4 text-teal" />
                          <div>
                            <div className="font-semibold text-ink">
                              {job.source_resource} ({job.rows_processed.toLocaleString()} records)
                            </div>
                            <div className="text-[11px] text-slate mt-0.5">
                              Ingested to Dataset Version <span className="font-mono text-teal">{job.dataset_version_id}</span> • {job.started_at ? new Date(job.started_at).toLocaleTimeString() : ""}
                            </div>
                          </div>
                        </div>
                        <span className="px-2.5 py-1 rounded-full text-[10px] font-semibold bg-teal-soft text-teal border border-teal-border">
                          {job.status}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="rounded-2xl border border-dashed border-border bg-white p-12 text-center">
                <Database className="h-10 w-10 text-slate/50 mx-auto mb-3" />
                <h3 className="text-base font-semibold text-ink">No Connection Selected</h3>
                <p className="text-xs text-slate mt-1">Select an existing data connection or create a new one.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Modal: Connection Wizard */}
      {isWizardOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/50 backdrop-blur-sm p-4">
          <div className="w-full max-w-xl rounded-3xl border border-border bg-white p-6 shadow-soft-lg space-y-6 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-teal-soft text-teal">
                  <Shield className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-ink">Connect Enterprise Data Source</h3>
                  <p className="text-xs text-slate">Step {wizardStep} of 3</p>
                </div>
              </div>
              <button
                onClick={() => setIsWizardOpen(false)}
                className="text-slate hover:text-ink text-sm font-semibold p-1 transition-colors"
              >
                ✕
              </button>
            </div>

            {/* Step 1: Select Type */}
            {wizardStep === 1 && (
              <div className="space-y-3">
                <label className="text-xs font-semibold text-slate uppercase">Choose Connector Type</label>
                <div className="grid grid-cols-2 gap-3">
                  {catalog.map((cat) => (
                    <button
                      key={cat.connector_type}
                      onClick={() => {
                        setSelectedConnectorType(cat.connector_type);
                        setWizardStep(2);
                      }}
                      className={`p-3.5 rounded-2xl border text-left flex items-start gap-3 transition-all ${
                        selectedConnectorType === cat.connector_type
                          ? "border-teal bg-teal-soft/60"
                          : "border-border bg-white hover:border-teal/50 hover:bg-cloud"
                      }`}
                    >
                      <div className="p-2 rounded-xl bg-white border border-border text-teal">
                        {getConnectorIcon(cat.connector_type)}
                      </div>
                      <div>
                        <div className="font-bold text-xs text-ink">{cat.name}</div>
                        <div className="text-[11px] text-slate mt-0.5">{cat.category}</div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Step 2: Configure & Credentials */}
            {wizardStep === 2 && (
              <div className="space-y-4">
                <div className="space-y-3">
                  <div>
                    <label className="text-xs font-semibold text-slate">Connection Display Name</label>
                    <input
                      type="text"
                      placeholder="e.g. Production Analytics Warehouse"
                      value={connName}
                      onChange={(e) => setConnName(e.target.value)}
                      className="mt-1 w-full rounded-xl border border-border bg-white px-3.5 py-2 text-sm text-ink placeholder:text-slate focus:outline-none focus:ring-2 focus:ring-teal"
                    />
                  </div>

                  {selectedConnectorType === "POSTGRESQL" || selectedConnectorType === "MYSQL" ? (
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-xs font-semibold text-slate">Host</label>
                        <input
                          type="text"
                          value={configFields.host || ""}
                          onChange={(e) => setConfigFields({ ...configFields, host: e.target.value })}
                          className="mt-1 w-full rounded-xl border border-border bg-white px-3.5 py-2 text-xs text-ink focus:outline-none focus:ring-2 focus:ring-teal"
                        />
                      </div>
                      <div>
                        <label className="text-xs font-semibold text-slate">Port</label>
                        <input
                          type="number"
                          value={configFields.port || 5432}
                          onChange={(e) => setConfigFields({ ...configFields, port: Number(e.target.value) })}
                          className="mt-1 w-full rounded-xl border border-border bg-white px-3.5 py-2 text-xs text-ink focus:outline-none focus:ring-2 focus:ring-teal"
                        />
                      </div>
                      <div>
                        <label className="text-xs font-semibold text-slate">Database Name</label>
                        <input
                          type="text"
                          value={configFields.database || ""}
                          onChange={(e) => setConfigFields({ ...configFields, database: e.target.value })}
                          className="mt-1 w-full rounded-xl border border-border bg-white px-3.5 py-2 text-xs text-ink focus:outline-none focus:ring-2 focus:ring-teal"
                        />
                      </div>
                      <div>
                        <label className="text-xs font-semibold text-slate">Username</label>
                        <input
                          type="text"
                          value={configFields.username || ""}
                          onChange={(e) => setConfigFields({ ...configFields, username: e.target.value })}
                          className="mt-1 w-full rounded-xl border border-border bg-white px-3.5 py-2 text-xs text-ink focus:outline-none focus:ring-2 focus:ring-teal"
                        />
                      </div>
                    </div>
                  ) : selectedConnectorType === "REST_API" ? (
                    <div>
                      <label className="text-xs font-semibold text-slate">Base Endpoint URL</label>
                      <input
                        type="text"
                        placeholder="https://api.service.com/v1"
                        value={configFields.base_url || ""}
                        onChange={(e) => setConfigFields({ ...configFields, base_url: e.target.value })}
                        className="mt-1 w-full rounded-xl border border-border bg-white px-3.5 py-2 text-xs text-ink focus:outline-none focus:ring-2 focus:ring-teal"
                      />
                    </div>
                  ) : (
                    <div>
                      <label className="text-xs font-semibold text-slate">Database Path / URI</label>
                      <input
                        type="text"
                        placeholder=":memory: or local.db"
                        value={configFields.database_path || ""}
                        onChange={(e) => setConfigFields({ ...configFields, database_path: e.target.value })}
                        className="mt-1 w-full rounded-xl border border-border bg-white px-3.5 py-2 text-xs text-ink focus:outline-none focus:ring-2 focus:ring-teal"
                      />
                    </div>
                  )}

                  <div>
                    <label className="text-xs font-semibold text-slate flex items-center gap-1.5">
                      <KeyRound className="h-3.5 w-3.5 text-teal" /> Secret Credentials (Encrypted via Fernet)
                    </label>
                    <input
                      type="password"
                      placeholder="••••••••••••••••"
                      value={credFields.password || ""}
                      onChange={(e) => setCredFields({ ...credFields, password: e.target.value })}
                      className="mt-1 w-full rounded-xl border border-border bg-white px-3.5 py-2 text-xs text-ink focus:outline-none focus:ring-2 focus:ring-teal"
                    />
                  </div>
                </div>

                {/* Test Connection Button & Result Box */}
                <div className="pt-2">
                  <Button
                    variant="outline"
                    onClick={handleTestConnection}
                    disabled={isTesting}
                    className="w-full text-xs py-2 flex items-center justify-center gap-2 border-border hover:bg-cloud"
                  >
                    <RefreshCw className={`h-3.5 w-3.5 ${isTesting ? "animate-spin" : ""}`} />
                    {isTesting ? "Testing Handshake & Safety..." : "Test Connection"}
                  </Button>

                  {testResult && (
                    <div
                      className={`mt-2.5 p-3 rounded-xl border text-xs flex items-start gap-2.5 ${
                        testResult.success
                          ? "bg-teal-soft border-teal-border text-teal"
                          : "bg-danger/10 border-danger/20 text-danger"
                      }`}
                    >
                      {testResult.success ? (
                        <CheckCircle2 className="h-4 w-4 shrink-0 mt-0.5" />
                      ) : (
                        <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
                      )}
                      <div>
                        <div className="font-semibold">{testResult.message}</div>
                        <div className="text-[10px] mt-0.5 opacity-90">
                          Latency: {testResult.latency_ms}ms • Discovered Resources: {testResult.discovered_resources_count}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Step 3: Cadence & Final Confirmation */}
            {wizardStep === 3 && (
              <div className="space-y-4">
                <div>
                  <label className="text-xs font-semibold text-slate">Automated Sync Cadence</label>
                  <select
                    value={syncSchedule}
                    onChange={(e) => setSyncSchedule(e.target.value)}
                    className="mt-1 w-full rounded-xl border border-border bg-white px-3.5 py-2 text-xs text-ink focus:outline-none focus:ring-2 focus:ring-teal"
                  >
                    <option value="0 * * * *" className="text-slate-800 bg-white font-medium">Hourly (Every 1 Hour)</option>
                    <option value="0 */6 * * *" className="text-slate-800 bg-white font-medium">Every 6 Hours (Recommended)</option>
                    <option value="0 */12 * * *" className="text-slate-800 bg-white font-medium">Every 12 Hours</option>
                    <option value="0 0 * * *" className="text-slate-800 bg-white font-medium">Daily at Midnight (UTC)</option>
                    <option value="MANUAL" className="text-slate-800 bg-white font-medium">Manual On-Demand Only</option>
                  </select>
                </div>

                <div className="p-4 rounded-2xl bg-teal-soft/50 border border-teal-border space-y-2">
                  <div className="text-xs font-bold text-teal flex items-center gap-1.5">
                    <Shield className="h-4 w-4" /> Enterprise Security Assurances
                  </div>
                  <ul className="text-[11px] text-slate space-y-1 pl-4 list-disc">
                    <li>SSRF Guard strictly prohibits internal RFC-1918 subnets & cloud metadata access.</li>
                    <li>External databases default to read-only execution; all DDL/DML mutations are blocked.</li>
                    <li>Credentials are stored with symmetric Fernet encryption and never returned in API payloads.</li>
                  </ul>
                </div>
              </div>
            )}

            {/* Wizard Navigation Footer */}
            <div className="flex items-center justify-between pt-4 border-t border-border">
              {wizardStep > 1 ? (
                <Button
                  variant="outline"
                  onClick={() => setWizardStep(wizardStep - 1)}
                  className="text-xs font-semibold"
                >
                  Back
                </Button>
              ) : (
                <div></div>
              )}

              {wizardStep < 3 ? (
                <Button
                  variant="primary"
                  onClick={() => setWizardStep(wizardStep + 1)}
                  className="bg-teal text-white text-xs px-4 hover:bg-teal-hover shadow-soft"
                >
                  Next <ChevronRight className="h-3.5 w-3.5 ml-1" />
                </Button>
              ) : (
                <Button
                  variant="primary"
                  onClick={handleSaveConnection}
                  disabled={isSaving}
                  className="bg-teal text-white text-xs px-5 shadow-soft hover:bg-teal-hover"
                >
                  {isSaving ? "Saving Connection..." : "Register Connection"}
                </Button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
