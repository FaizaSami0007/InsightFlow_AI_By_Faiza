"use client";

import * as React from "react";
import {
  Activity,
  CheckCircle2,
  Database,
  FileSpreadsheet,
  Layers,
  LineChart,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Terminal,
} from "lucide-react";
import { AppShell } from "@/components/shell/app-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Tabs, TabList, TabTrigger, TabContent } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog } from "@/components/ui/dialog";
import { LoadingState } from "@/components/states/loading-state";
import { EmptyState } from "@/components/states/empty-state";
import { ErrorState } from "@/components/states/error-state";
import { SuccessState } from "@/components/states/success-state";
import { ProcessingState } from "@/components/states/processing-state";
import { api } from "@/lib/api-client";
import { ApiHealthResponse, ApiReadinessResponse } from "@/types";

export default function Home() {
  const [activeTab, setActiveTab] = React.useState("overview");
  const [selectedUxState, setSelectedUxState] = React.useState<"loading" | "empty" | "error" | "success" | "processing">("loading");
  const [isDialogOpen, setIsDialogOpen] = React.useState(false);
  const [healthStatus, setHealthStatus] = React.useState<ApiHealthResponse | null>(null);
  const [readinessStatus, setReadinessStatus] = React.useState<ApiReadinessResponse | null>(null);
  const [isCheckingHealth, setIsCheckingHealth] = React.useState(false);
  const [apiError, setApiError] = React.useState<string | null>(null);

  const fetchHealth = React.useCallback(async () => {
    setIsCheckingHealth(true);
    setApiError(null);
    try {
      const health = await api.get<ApiHealthResponse>("/api/v1/health");
      setHealthStatus(health);
      try {
        const readiness = await api.get<ApiReadinessResponse>("/api/v1/health/ready");
        setReadinessStatus(readiness);
      } catch {
        // Readiness can be degraded without failing overall liveness
      }
    } catch (err) {
      setApiError((err as Error).message || "Could not reach FastAPI backend");
    } finally {
      setIsCheckingHealth(false);
    }
  }, []);

  React.useEffect(() => {
    fetchHealth();
  }, [fetchHealth]);

  return (
    <AppShell>
      <div className="space-y-6">
        {/* Header Hero Banner */}
        <div className="rounded-2xl border border-border bg-surface p-6 sm:p-8 shadow-soft">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="max-w-2xl space-y-2">
              <div className="inline-flex items-center gap-2 rounded-lg bg-teal-soft px-2.5 py-1 text-xs font-semibold text-teal border border-teal-border">
                <Sparkles className="h-3.5 w-3.5" />
                Phase 1 Foundation Ready
              </div>
              <h1 className="text-lg sm:text-xl lg:text-2xl font-bold tracking-tight text-ink">
                InsightFlow AI Analytics Platform
              </h1>
              <p className="text-xs sm:text-sm text-slate leading-relaxed">
                Automated data analysis and context-aware dashboard generation. The LLM reasons over analytical plans;
                deterministic tools calculate truth with complete provenance.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <Button
                variant="outline"
                size="sm"
                onClick={fetchHealth}
                isLoading={isCheckingHealth}
                leftIcon={<RefreshCw className="h-3.5 w-3.5" />}
              >
                Check API Health
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={() => setIsDialogOpen(true)}
                leftIcon={<Layers className="h-3.5 w-3.5" />}
              >
                Explore Primitives
              </Button>
            </div>
          </div>

          {/* System Status Pill Summary */}
          <div className="mt-6 flex flex-wrap items-center gap-3 border-t border-border pt-4 text-xs text-slate">
            <span className="font-semibold text-ink">Runtime Status:</span>
            {healthStatus ? (
              <Badge variant="teal" dot>
                FastAPI: {healthStatus.status} (v{healthStatus.version})
              </Badge>
            ) : apiError ? (
              <Badge variant="danger" dot>
                API Offline: {apiError}
              </Badge>
            ) : (
              <Badge variant="outline">Connecting to API...</Badge>
            )}

            {readinessStatus && (
              <Badge variant={readinessStatus.status === "ready" ? "teal" : "amber"} dot>
                Database: {readinessStatus.checks.database}
              </Badge>
            )}

            <Badge variant="blue">Environment: {healthStatus?.environment || "development"}</Badge>
            <Badge variant="outline">Architecture: Modular Monolith</Badge>
          </div>
        </div>

        {/* Main Interactive Tabbed Experience */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabList className="w-full justify-start overflow-x-auto">
            <TabTrigger value="overview">Architecture Overview</TabTrigger>
            <TabTrigger value="components">Design System & UI Primitives</TabTrigger>
            <TabTrigger value="states">Global UX States</TabTrigger>
            <TabTrigger value="diagnostics">Health & Diagnostics</TabTrigger>
          </TabList>

          {/* TAB 1: ARCHITECTURE OVERVIEW */}
          <TabContent value="overview">
            <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-4">
              <Card>
                <CardHeader>
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-teal-soft text-teal mb-1">
                    <Database className="h-4 w-4" />
                  </div>
                  <CardTitle>Data Ingestion & Lineage</CardTitle>
                  <CardDescription>Phase 2 Foundation</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-xs text-slate leading-relaxed">
                    Strict MIME validation, schema inference, dataset versioning, and column-level provenance tracking.
                  </p>
                  <div className="mt-4 flex items-center gap-2">
                    <Badge variant="teal">PostgreSQL + Parquet</Badge>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-soft text-blue mb-1">
                    <LineChart className="h-4 w-4" />
                  </div>
                  <CardTitle>Deterministic Analytics</CardTitle>
                  <CardDescription>Phase 4 Engine</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-xs text-slate leading-relaxed">
                    Embedded DuckDB analytical query execution. Fast aggregations, correlations, and read-only sandboxes.
                  </p>
                  <div className="mt-4 flex items-center gap-2">
                    <Badge variant="blue">DuckDB + Polars</Badge>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-soft text-amber mb-1">
                    <ShieldCheck className="h-4 w-4" />
                  </div>
                  <CardTitle>AI Tool Allowlisting</CardTitle>
                  <CardDescription>Phase 5 Orchestrator</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-xs text-slate leading-relaxed">
                    Structured analysis plans with strict JSON schemas. Never execute unvalidated model code.
                  </p>
                  <div className="mt-4 flex items-center gap-2">
                    <Badge variant="amber">Strict Schemas</Badge>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-cloud text-ink mb-1">
                    <FileSpreadsheet className="h-4 w-4" />
                  </div>
                  <CardTitle>Context-Aware Dashboards</CardTitle>
                  <CardDescription>Phase 7 Visualizer</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-xs text-slate leading-relaxed">
                    Declarative JSON dashboard layouts with responsive reflow, chart recommendations, and NL editing.
                  </p>
                  <div className="mt-4 flex items-center gap-2">
                    <Badge variant="default">Next.js + SVG/Canvas</Badge>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Architecture Invariants Card */}
            <Card className="mt-6">
              <CardHeader>
                <CardTitle>Core Architectural Invariants</CardTitle>
                <CardDescription>Non-negotiable system rules defined in ADRs</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="flex items-start gap-3 rounded-xl border border-border bg-cloud p-3.5">
                    <CheckCircle2 className="h-4 w-4 shrink-0 text-teal mt-0.5" />
                    <div>
                      <h4 className="text-xs font-semibold text-ink">Deterministic Calculation</h4>
                      <p className="text-[11px] text-slate mt-0.5">The model reasons; deterministic tools calculate. Numerical truth is never LLM hallucinated.</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3 rounded-xl border border-border bg-cloud p-3.5">
                    <CheckCircle2 className="h-4 w-4 shrink-0 text-teal mt-0.5" />
                    <div>
                      <h4 className="text-xs font-semibold text-ink">Zero-Trust LLM Output</h4>
                      <p className="text-[11px] text-slate mt-0.5">All tool invocations and analysis plans undergo strict schema validation before execution.</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3 rounded-xl border border-border bg-cloud p-3.5">
                    <CheckCircle2 className="h-4 w-4 shrink-0 text-teal mt-0.5" />
                    <div>
                      <h4 className="text-xs font-semibold text-ink">Institutional Soft UI</h4>
                      <p className="text-[11px] text-slate mt-0.5">Restrained color palette (Ink, Slate, Cloud, Surface, Teal) with clear focus rings and zero decorative clutter.</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3 rounded-xl border border-border bg-cloud p-3.5">
                    <CheckCircle2 className="h-4 w-4 shrink-0 text-teal mt-0.5" />
                    <div>
                      <h4 className="text-xs font-semibold text-ink">WCAG Accessibility</h4>
                      <p className="text-[11px] text-slate mt-0.5">Complete keyboard navigation, semantic hierarchy, ARIA announcements, and screen-reader skip links.</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabContent>

          {/* TAB 2: DESIGN SYSTEM & PRIMITIVES */}
          <TabContent value="components">
            <div className="space-y-6">
              {/* Buttons & Badges */}
              <Card>
                <CardHeader>
                  <CardTitle>Buttons & Badges</CardTitle>
                  <CardDescription>Interactive soft UI controls with keyboard focus rings</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex flex-wrap items-center gap-3">
                    <Button variant="primary">Primary Action</Button>
                    <Button variant="secondary">Secondary Soft</Button>
                    <Button variant="outline">Outline Surface</Button>
                    <Button variant="ghost">Ghost Action</Button>
                    <Button variant="danger">Destructive</Button>
                    <Button variant="primary" isLoading>Loading</Button>
                  </div>
                  <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-border">
                    <Badge variant="default">Neutral</Badge>
                    <Badge variant="teal" dot>Teal Active</Badge>
                    <Badge variant="blue" dot>Info Blue</Badge>
                    <Badge variant="amber" dot>Warning Amber</Badge>
                    <Badge variant="danger" dot>Error Danger</Badge>
                    <Badge variant="outline">Outline</Badge>
                  </div>
                </CardContent>
              </Card>

              {/* Form Controls */}
              <Card>
                <CardHeader>
                  <CardTitle>Form Controls</CardTitle>
                  <CardDescription>Accessible inputs and selection menus with validation states</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-4 sm:grid-cols-3">
                    <Input
                      label="Dataset Name"
                      placeholder="e.g. Q4 Financials"
                      helperText="Must be unique within workspace"
                    />
                    <Select
                      label="Analysis Engine"
                      options={[
                        { value: "duckdb", label: "DuckDB (In-Memory Engine)" },
                        { value: "polars", label: "Polars (Vectorized)" },
                        { value: "postgres", label: "PostgreSQL Standard" },
                      ]}
                      helperText="Analytical calculation backend"
                    />
                    <Input
                      label="Invalid Input Sample"
                      defaultValue="bad_dataset_name#$$"
                      error="Dataset name contains invalid characters"
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Alerts */}
              <div className="grid gap-4 sm:grid-cols-2">
                <Alert variant="info">
                  <AlertTitle>Context-Aware Execution</AlertTitle>
                  <AlertDescription>
                    Deterministic query plans will validate column types before DuckDB execution.
                  </AlertDescription>
                </Alert>

                <Alert variant="warning">
                  <AlertTitle>Phase 1 Constraint</AlertTitle>
                  <AlertDescription>
                    Live dataset upload and LLM integration will be unlocked in Phase 2 and Phase 5.
                  </AlertDescription>
                </Alert>
              </div>

              {/* Data Table Primitive */}
              <Card>
                <CardHeader>
                  <CardTitle>Dense Data Table Primitive</CardTitle>
                  <CardDescription>Institutional layout designed for high scanability</CardDescription>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Dataset Name</TableHead>
                        <TableHead>Rows</TableHead>
                        <TableHead>Columns</TableHead>
                        <TableHead>Quality Score</TableHead>
                        <TableHead>Status</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      <TableRow>
                        <TableCell className="font-semibold text-ink">ecommerce_transactions_2025.csv</TableCell>
                        <TableCell>145,200</TableCell>
                        <TableCell>18</TableCell>
                        <TableCell>
                          <span className="font-semibold text-teal">98.4%</span>
                        </TableCell>
                        <TableCell>
                          <Badge variant="teal" dot>Ready</Badge>
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell className="font-semibold text-ink">saas_customer_churn_q3.csv</TableCell>
                        <TableCell>42,150</TableCell>
                        <TableCell>12</TableCell>
                        <TableCell>
                          <span className="font-semibold text-amber">91.2%</span>
                        </TableCell>
                        <TableCell>
                          <Badge variant="teal" dot>Ready</Badge>
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell className="font-semibold text-ink">marketing_campaign_attribution.csv</TableCell>
                        <TableCell>8,900</TableCell>
                        <TableCell>9</TableCell>
                        <TableCell>
                          <span className="font-semibold text-danger">74.0%</span>
                        </TableCell>
                        <TableCell>
                          <Badge variant="amber" dot>Needs Review</Badge>
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </div>
          </TabContent>

          {/* TAB 3: GLOBAL UX STATES */}
          <TabContent value="states">
            <Card>
              <CardHeader>
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                  <div>
                    <CardTitle>Global UX State Handlers</CardTitle>
                    <CardDescription>Consistent feedback patterns preventing blank screen antipatterns</CardDescription>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {(["loading", "empty", "error", "success", "processing"] as const).map((stateKey) => (
                      <Button
                        key={stateKey}
                        variant={selectedUxState === stateKey ? "primary" : "outline"}
                        size="sm"
                        onClick={() => setSelectedUxState(stateKey)}
                        className="capitalize"
                      >
                        {stateKey}
                      </Button>
                    ))}
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-2">
                {selectedUxState === "loading" && (
                  <LoadingState
                    title="Profiling Dataset Schema"
                    description="Analyzing column distributions, null ratios, and data types..."
                  />
                )}
                {selectedUxState === "empty" && (
                  <EmptyState
                    title="No datasets uploaded yet"
                    description="Upload a CSV or Parquet file to begin profiling and natural-language analysis."
                    action={<Button variant="primary" size="sm">Upload First Dataset</Button>}
                  />
                )}
                {selectedUxState === "error" && (
                  <ErrorState
                    title="DuckDB Query Execution Timeout"
                    message="The analytical query exceeded the 30-second budget. Consider narrowing your date filters."
                    onRetry={() => setSelectedUxState("processing")}
                  />
                )}
                {selectedUxState === "success" && (
                  <SuccessState
                    title="Analysis Plan Validated & Saved"
                    message="Calculations completed with verified provenance. Result hash: 8f7e2a9b."
                    action={<Button variant="outline" size="sm">View Provenance Log</Button>}
                  />
                )}
                {selectedUxState === "processing" && (
                  <ProcessingState
                    title="Executing Deterministic Analysis"
                    stage="Aggregating Revenue by Region"
                    progressPercent={65}
                    description="Step 2 of 3: Computing monthly descriptive statistics."
                  />
                )}
              </CardContent>
            </Card>
          </TabContent>

          {/* TAB 4: DIAGNOSTICS & API HEALTH */}
          <TabContent value="diagnostics">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Backend & Environment Diagnostics</CardTitle>
                    <CardDescription>Live health checks against FastAPI and database layers</CardDescription>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={fetchHealth}
                    isLoading={isCheckingHealth}
                    leftIcon={<RefreshCw className="h-3.5 w-3.5" />}
                  >
                    Refresh
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-3 sm:grid-cols-3">
                  <div className="rounded-xl border border-border bg-cloud p-4">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-slate">Liveness Probe</span>
                      <Activity className="h-4 w-4 text-teal" />
                    </div>
                    <div className="mt-2 text-lg font-bold text-ink">
                      {healthStatus?.status === "healthy" ? "Healthy (200)" : "Unreachable"}
                    </div>
                    <p className="mt-1 text-[11px] text-slate font-mono">GET /api/v1/health</p>
                  </div>

                  <div className="rounded-xl border border-border bg-cloud p-4">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-slate">Readiness Probe</span>
                      <Database className="h-4 w-4 text-teal" />
                    </div>
                    <div className="mt-2 text-lg font-bold text-ink">
                      {readinessStatus?.status || "Degraded"}
                    </div>
                    <p className="mt-1 text-[11px] text-slate font-mono">GET /api/v1/health/ready</p>
                  </div>

                  <div className="rounded-xl border border-border bg-cloud p-4">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-slate">Security Context</span>
                      <ShieldCheck className="h-4 w-4 text-teal" />
                    </div>
                    <div className="mt-2 text-lg font-bold text-ink">Active</div>
                    <p className="mt-1 text-[11px] text-slate">CORS & OWASP Headers</p>
                  </div>
                </div>

                {/* Raw API Response Display */}
                <div className="rounded-xl border border-border bg-surface p-4">
                  <div className="flex items-center gap-2 mb-2 text-xs font-semibold text-ink">
                    <Terminal className="h-4 w-4 text-slate" />
                    <span>Live Health Check Payload</span>
                  </div>
                  <pre className="overflow-x-auto rounded-lg bg-ink p-3 text-[11px] text-cloud font-mono">
                    {JSON.stringify(
                      {
                        health: healthStatus || { error: apiError },
                        readiness: readinessStatus || { status: "offline" },
                      },
                      null,
                      2
                    )}
                  </pre>
                </div>
              </CardContent>
            </Card>
          </TabContent>
        </Tabs>

        {/* Modal Dialog Primitive Demonstration */}
        <Dialog
          isOpen={isDialogOpen}
          onClose={() => setIsDialogOpen(false)}
          title="InsightFlow Architecture Primitives"
          description="Phase 1 Foundation establishes clean boundaries before data engineering."
        >
          <div className="space-y-4 text-xs text-slate">
            <p className="leading-relaxed">
              Every future analytical feature builds upon this modular monolith foundation. The Next.js client
              communicates with FastAPI through centralized, typed, error-normalized API contracts.
            </p>
            <div className="rounded-xl bg-cloud p-3 space-y-1">
              <div className="font-semibold text-ink">Phase 1 Verification Checklist:</div>
              <ul className="list-disc list-inside space-y-0.5 text-slate text-[11px]">
                <li>FastAPI liveness and readiness endpoints</li>
                <li>Pydantic settings with environment validation</li>
                <li>Structured logging with sensitive key scrubbing</li>
                <li>Accessible application shell & responsive navigation</li>
                <li>Soft UI design tokens & reusable primitives</li>
              </ul>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" size="sm" onClick={() => setIsDialogOpen(false)}>
                Close
              </Button>
              <Button variant="primary" size="sm" onClick={() => setIsDialogOpen(false)}>
                Acknowledged
              </Button>
            </div>
          </div>
        </Dialog>
      </div>
    </AppShell>
  );
}
