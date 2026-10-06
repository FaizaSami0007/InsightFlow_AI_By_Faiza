"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";

import {
  Bot,
  Send,
  Sparkles,
  ArrowRight,
  AlertCircle,
  CheckCircle2,
  RefreshCw,
  Cpu,
  ChevronDown,
  ChevronUp,
  Plus,
  MessageSquare,
  Trash2,
  Database,
  Layers,
  HelpCircle,
  FileText,
  Network,
  ShieldCheck,
  X,
  Activity,
} from "lucide-react";
import { api } from "@/lib/api-client";
import {
  Dataset,
  AIChatResponse,
  AIConversationSummary,
  AIConversationDetail,
  AIMessageItem,
  VisualizationSpec,
  AnalysisResponse,
  AITaskResponse,
  AgentMetadataResponse,
} from "@/types";
import { Select } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { VisualizationRenderer } from "@/components/visualization/visualization-renderer";
import { useAuthStore } from "@/stores/use-auth-store";


interface AIAnalystViewProps {
  initialDatasetId?: string;
  initialVersionId?: string;
}

interface MessageBubble {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  toolCalls?: Array<{ id?: string; name: string; arguments: Record<string, unknown> }>;
  toolResults?: Array<{ analysis_id?: string; name: string; row_count?: number; columns?: string[]; summary?: Record<string, unknown>; execution_time_ms?: number }>;
  analysisIds?: string[];
  suggestedQuestions?: string[];
  evidence?: {
    dataset_id: string;
    dataset_name: string;
    dataset_version_id: string;
    version_number: number;
    analysis_ids: string[];
    tool_operations: string[];
    provenance: Record<string, unknown>[];
  } | null;
  visualization?: VisualizationSpec | null;
  createdAt: string;
}

function MessageVisualizationCard({ spec }: { spec: VisualizationSpec }) {
  const [data, setData] = useState<Record<string, unknown>[]>([]);
  const [columns, setColumns] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const analysisId = spec.provenance?.analysis_id;

  useEffect(() => {
    if (!analysisId) return;
    let isMounted = true;
    setLoading(true);
    api
      .get<AnalysisResponse>(`/api/v1/analytics/${analysisId}`)
      .then((res) => {
        if (isMounted) {
          setData(res.rows || []);
          setColumns(res.columns || []);
        }
      })
      .catch((err) => {
        console.warn("Could not load full analysis rows for chart:", err);
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [analysisId]);

  if (loading && data.length === 0 && spec.chart_type !== "kpi" && spec.chart_type !== "boxplot") {
    return (
      <div className="flex items-center gap-2 p-3 text-xs text-slate bg-cloud/50 rounded-xl border border-border my-2">
        <RefreshCw className="w-3.5 h-3.5 animate-spin text-teal" />
        <span>Loading chart visualization data...</span>
      </div>
    );
  }

  return <VisualizationRenderer spec={spec} data={data} columns={columns} />;
}

export function AIAnalystView({ initialDatasetId, initialVersionId }: AIAnalystViewProps) {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>(initialDatasetId || "");
  const [selectedVersionId, setSelectedVersionId] = useState<string>(initialVersionId || "");
  const [conversations, setConversations] = useState<AIConversationSummary[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<MessageBubble[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [conversationToDelete, setConversationToDelete] = useState<string | null>(null);
  const [starterQuestions, setStarterQuestions] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [expandedTools, setExpandedTools] = useState<Record<string, boolean>>({});
  const [tasks, setTasks] = useState<AITaskResponse[]>([]);
  const [registeredAgents, setRegisteredAgents] = useState<AgentMetadataResponse[]>([]);
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [loadingTasks, setLoadingTasks] = useState(false);

  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const token = useAuthStore((s) => s.token);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load registered agents metadata
  useEffect(() => {
    async function loadAgents() {
      if (!isAuthenticated && !token) return;
      try {
        const res = await api.get<AgentMetadataResponse[]>("/api/v1/ai/agents");
        setRegisteredAgents(res || []);
      } catch (e) {
        console.warn("Could not load agent registry metadata:", e);
      }
    }
    loadAgents();
  }, [isAuthenticated, token]);

  // Load tasks for active conversation
  const loadConversationTasks = useCallback(async (convId: string) => {
    if (!convId || (!isAuthenticated && !token)) {
      setTasks([]);
      return;
    }
    setLoadingTasks(true);
    try {
      const res = await api.get<AITaskResponse[]>(`/api/v1/ai/conversations/${convId}/tasks`);
      setTasks(res || []);
    } catch (e) {
      console.warn("Could not load conversation tasks:", e);
    } finally {
      setLoadingTasks(false);
    }
  }, [isAuthenticated, token]);


  // 1. Load User Datasets
  useEffect(() => {
    async function loadDatasets() {
      if (!isAuthenticated && !token) {
        setDatasets([]);
        return;
      }
      try {
        const res = await api.get<{ items: Dataset[] }>("/api/v1/datasets");
        setDatasets(res.items || []);
        if (!selectedDatasetId && res.items && res.items.length > 0) {
          const firstDs = res.items[0];
          setSelectedDatasetId(firstDs.id);
          if (firstDs.latest_version) {
            setSelectedVersionId(firstDs.latest_version.id);
          } else if (firstDs.versions && firstDs.versions.length > 0) {
            setSelectedVersionId(firstDs.versions[0].id);
          }
        }
      } catch {
        // Silently handle unauthenticated or failed dataset fetches
      }
    }
    loadDatasets();
  }, [selectedDatasetId, isAuthenticated, token]);

  // 2. Load Conversations for Selected Dataset
  const loadConversations = useCallback(async (dsId: string) => {
    if (!dsId || (!isAuthenticated && !token)) return;
    try {
      const list = await api.get<AIConversationSummary[]>(`/api/v1/ai/conversations?dataset_id=${dsId}`);
      setConversations(list || []);
    } catch {
      // Silently handle
    }
  }, [isAuthenticated, token]);

  // 3. Load Dynamic Starter Questions for Dataset Version
  const loadStarterQuestions = useCallback(async (dsId: string, verId: string) => {
    if (!dsId || !verId) return;
    try {
      const starters = await api.get<string[]>(`/api/v1/ai/datasets/${dsId}/versions/${verId}/starters`);
      setStarterQuestions(starters || []);
    } catch (err) {
      setStarterQuestions([
        "What region has the highest revenue?",
        "Show summary statistics for numeric metrics",
        "Calculate the correlation between numeric columns",
        "Show sales grouped by category",
      ]);
    }
  }, []);

  useEffect(() => {
    if (selectedDatasetId) {
      loadConversations(selectedDatasetId);
      if (selectedVersionId) {
        loadStarterQuestions(selectedDatasetId, selectedVersionId);
      }
    }
  }, [selectedDatasetId, selectedVersionId, loadConversations, loadStarterQuestions]);

  // 4. Select / Switch Conversation
  const selectConversation = async (convId: string) => {
    setActiveConversationId(convId);
    setError(null);
    setIsLoading(true);
    loadConversationTasks(convId);
    try {
      const detail = await api.get<AIConversationDetail>(`/api/v1/ai/conversations/${convId}`);
      const mappedMessages: MessageBubble[] = (detail.messages || []).map((m: AIMessageItem) => ({
        id: m.id,
        role: m.role as "user" | "assistant",
        content: m.content,
        toolCalls: m.tool_calls || undefined,
        toolResults: m.tool_results as any,
        analysisIds: m.analysis_ids || undefined,
        visualization: m.visualization || null,
        createdAt: m.created_at,
      }));
      setMessages(mappedMessages);
    } catch (err) {
      setError((err as Error).message || "Failed to load conversation history.");
    } finally {
      setIsLoading(false);
    }
  };

  // 5. Start a New Conversation
  const handleNewConversation = () => {
    setActiveConversationId(null);
    setMessages([]);
    setTasks([]);
    setError(null);
    setInputValue("");
  };

  // 6. Delete Conversation
  const handleDeleteConversation = async (convId: string) => {
    setIsDeleting(true);
    try {
      await api.delete(`/api/v1/ai/conversations/${convId}`);
      setConversations((prev) => prev.filter((c) => c.id !== convId));
      if (activeConversationId === convId) {
        handleNewConversation();
      }
      setConversationToDelete(null);
    } catch (err) {
      setError((err as Error).message || "Failed to delete conversation.");
    } finally {
      setIsDeleting(false);
    }
  };

  // Dataset switch handler
  const handleDatasetChange = (dsId: string) => {
    setSelectedDatasetId(dsId);
    handleNewConversation();
    const found = datasets.find((d) => d.id === dsId);
    if (found?.latest_version) {
      setSelectedVersionId(found.latest_version.id);
    } else if (found?.versions && found.versions.length > 0) {
      setSelectedVersionId(found.versions[0].id);
    } else {
      setSelectedVersionId("");
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const toggleToolExpand = (id: string) => {
    setExpandedTools((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  // 7. Send Message Flow
  const handleSendMessage = async (customPrompt?: string) => {
    const textToSend = customPrompt || inputValue.trim();
    if (!textToSend || isLoading) return;

    setError(null);
    const userMsg: MessageBubble = {
      id: `user-${Date.now()}`,
      role: "user",
      content: textToSend,
      createdAt: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!customPrompt) setInputValue("");
    setIsLoading(true);

    try {
      const payload = {
        dataset_id: selectedDatasetId || null,
        dataset_version_id: selectedVersionId || null,
        conversation_id: activeConversationId,
        message: textToSend,
      };

      const res = await api.post<AIChatResponse>("/api/v1/ai/chat", payload);

      if (!activeConversationId) {
        setActiveConversationId(res.conversation_id);
        if (selectedDatasetId) {
          loadConversations(selectedDatasetId);
        }
      }

      loadConversationTasks(res.conversation_id);

      const assistantMsg: MessageBubble = {
        id: res.message_id || `asst-${Date.now()}`,
        role: "assistant",
        content: res.message,
        toolCalls: res.tool_calls,
        toolResults: res.tool_results as any,
        analysisIds: res.analysis_ids,
        suggestedQuestions: res.suggested_questions,
        evidence: res.evidence,
        visualization: res.visualization || null,
        createdAt: res.created_at || new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setError((err as Error).message || "Failed to communicate with AI Analyst.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const selectedDataset = datasets.find((d) => d.id === selectedDatasetId);
  const versionOptions = (selectedDataset?.versions || []).map((v) => ({
    value: v.id,
    label: `v${v.version_number} — ${v.file_name}`,
  }));

  const activeSuggestions =
    messages.length > 0 && messages[messages.length - 1].role === "assistant"
      ? messages[messages.length - 1].suggestedQuestions || []
      : [];

  return (
    <div className="flex h-[calc(100vh-7.5rem)] max-w-7xl mx-auto rounded-2xl border border-border bg-surface overflow-hidden shadow-soft">
      {/* ─── LEFT SIDEBAR: CONVERSATION SESSIONS ─── */}
      <aside className="w-72 border-r border-border bg-cloud/40 flex flex-col shrink-0 hidden md:flex">
        {/* New Session Button */}
        <div className="p-3 border-b border-border">
          <Button
            onClick={handleNewConversation}
            className="w-full flex items-center justify-center gap-2 rounded-xl text-xs py-2"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>New Analysis Session</span>
          </Button>
        </div>

        {/* Conversation List */}
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          <p className="px-2 py-1 text-[10px] font-semibold text-slate uppercase tracking-wider">
            Past Conversations
          </p>
          {conversations.length === 0 ? (
            <div className="p-4 text-center text-xs text-slate">
              No conversations yet for this dataset.
            </div>
          ) : (
            conversations.map((conv) => {
              const isActive = activeConversationId === conv.id;
              return (
                <div
                  key={conv.id}
                  onClick={() => selectConversation(conv.id)}
                  className={`group relative flex items-center justify-between p-2.5 rounded-xl text-xs cursor-pointer transition-all ${
                    isActive
                      ? "bg-teal-soft text-teal-dark font-medium border border-teal-border"
                      : "text-ink hover:bg-cloud border border-transparent"
                  }`}
                >
                  <div className="flex items-center gap-2 overflow-hidden flex-1">
                    <MessageSquare className="h-3.5 w-3.5 shrink-0 text-slate" />
                    <span className="truncate text-xs">{conv.title || "Untitled Session"}</span>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setConversationToDelete(conv.id);
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1 rounded-lg text-slate hover:text-danger hover:bg-danger-soft transition-all"
                    title="Delete Conversation"
                    aria-label="Delete conversation"
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </div>
              );
            })
          )}
        </div>
      </aside>

      {/* ─── MAIN ANALYST CHAT WORKSPACE ─── */}
      <div className="flex-1 flex flex-col h-full overflow-hidden bg-surface">
        {/* Header Bar: Dataset & Version Selector */}
        <header className="flex flex-wrap items-center justify-between gap-3 px-6 py-3.5 border-b border-border bg-cloud/30">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-teal text-white shadow-soft">
              <Sparkles className="h-4 w-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-ink">Conversational AI Analyst</h2>
                <Badge variant="teal">Phase 15 Multi-Agent</Badge>
              </div>
              <p className="text-[11px] text-slate">
                Governed 9-agent DAG orchestrator with deterministic tools &amp; Critic validation
              </p>
            </div>
          </div>

          {/* Dataset & Version Selectors + Task Graph Trigger */}
          <div className="flex items-center gap-2">
            {activeConversationId && (
              <Button
                variant="outline"
                onClick={() => {
                  loadConversationTasks(activeConversationId);
                  setShowTaskModal(true);
                }}
                className="text-xs h-8 px-2.5 flex items-center gap-1.5 border-teal-border text-teal-dark bg-teal-soft/40 hover:bg-teal-soft"
                title="View Multi-Agent Task Execution Graph"
              >
                <Network className="h-3.5 w-3.5 text-teal" />
                <span>Agent Graph ({tasks.length})</span>
              </Button>
            )}

            <div className="w-44">
              <Select
                options={datasets.map((d) => ({ value: d.id, label: d.name }))}
                value={selectedDatasetId}
                onChange={(e) => handleDatasetChange(e.target.value)}
                className="text-xs"
              />
            </div>
            {versionOptions.length > 0 && (
              <div className="w-40">
                <Select
                  options={versionOptions}
                  value={selectedVersionId}
                  onChange={(e) => setSelectedVersionId(e.target.value)}
                  className="text-xs"
                />
              </div>
            )}
          </div>
        </header>

        {/* Chat History Messages */}
        <main className="flex-1 overflow-y-auto p-6 space-y-6" aria-label="Conversation Messages">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center max-w-lg mx-auto py-8">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-teal-soft text-teal mb-3">
                <Bot className="h-6 w-6" />
              </div>
              <h3 className="text-base font-bold text-ink mb-1">
                Ask anything about {selectedDataset?.name || "your dataset"}
              </h3>
              <p className="text-xs text-slate mb-6 leading-relaxed">
                InsightFlow AI constructs safe analytical queries, executes DuckDB operations, and provides fully grounded answers with verifiable evidence.
              </p>

              {/* Dynamic Starter Questions */}
              {starterQuestions.length > 0 && (
                <div className="w-full space-y-2">
                  <p className="text-[10px] font-semibold text-slate uppercase tracking-wider text-left">
                    Suggested analytical questions:
                  </p>
                  {starterQuestions.map((q, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSendMessage(q)}
                      className="w-full flex items-center justify-between p-2.5 rounded-xl border border-border bg-surface text-left text-xs text-ink hover:bg-cloud hover:border-teal-border transition-all shadow-soft"
                    >
                      <span className="font-medium">{q}</span>
                      <ArrowRight className="h-3.5 w-3.5 text-slate shrink-0 ml-2" />
                    </button>
                  ))}
                </div>
              )}
            </div>
          ) : (
            messages.map((msg) => (
              <article
                key={msg.id}
                role="article"
                aria-label={`${msg.role === "user" ? "User question" : "Analyst answer"}`}
                className={`flex flex-col ${
                  msg.role === "user" ? "items-end" : "items-start"
                }`}
              >
                <div
                  className={`max-w-3xl rounded-2xl p-4 text-xs leading-relaxed ${
                    msg.role === "user"
                      ? "bg-teal text-white rounded-br-none shadow-soft font-medium"
                      : "bg-cloud text-ink rounded-bl-none border border-border"
                  }`}
                >
                  {/* Tool Execution Details */}
                  {msg.toolCalls && msg.toolCalls.length > 0 && (
                    <div className="mb-3 space-y-2 border-b border-border/40 pb-3">
                      <div className="flex items-center justify-between text-[11px] font-semibold text-teal-dark">
                        <div className="flex items-center gap-1.5">
                          <Cpu className="h-3.5 w-3.5" />
                          <span>Executed Deterministic Analytics ({msg.toolCalls.length} tool)</span>
                        </div>
                        <button
                          onClick={() => toggleToolExpand(msg.id)}
                          className="flex items-center gap-1 text-[10px] text-slate hover:text-ink font-normal"
                        >
                          {expandedTools[msg.id] ? (
                            <>
                              <span>Hide Details</span>
                              <ChevronUp className="h-3 w-3" />
                            </>
                          ) : (
                            <>
                              <span>View Tool Execution</span>
                              <ChevronDown className="h-3 w-3" />
                            </>
                          )}
                        </button>
                      </div>

                      {expandedTools[msg.id] && (
                        <div className="space-y-2 mt-2">
                          {msg.toolCalls.map((tc, i) => {
                            const result = msg.toolResults?.find(
                              (r) => r.name === tc.name
                            );
                            return (
                              <div
                                key={i}
                                className="rounded-xl border border-border bg-surface p-2.5 text-[11px] font-mono text-slate space-y-1"
                              >
                                <div className="flex items-center justify-between text-ink font-semibold">
                                  <span className="text-teal font-medium">Tool: {tc.name}</span>
                                  <Badge variant="teal">Executed</Badge>
                                </div>
                                <div>
                                  <span className="text-slate text-[10px]">Parameters:</span>
                                  <pre className="text-[10px] overflow-x-auto bg-cloud p-1 rounded mt-0.5">
                                    {JSON.stringify(tc.arguments, null, 2)}
                                  </pre>
                                </div>
                                {result && (
                                  <div>
                                    <span className="text-slate text-[10px]">Result summary:</span>
                                    <pre className="text-[10px] overflow-x-auto bg-cloud p-1 rounded mt-0.5">
                                      {JSON.stringify(result.summary || result, null, 2)}
                                    </pre>
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Message Body */}
                  <div className="whitespace-pre-wrap">{msg.content}</div>

                  {/* Grounded Interactive Visualization */}
                  {msg.visualization && (
                    <MessageVisualizationCard spec={msg.visualization} />
                  )}

                  {/* Evidence & Provenance Section */}
                  {msg.evidence && (
                    <div className="mt-3 pt-2.5 border-t border-border/30 space-y-1.5">
                      <p className="text-[10px] font-semibold uppercase tracking-wider text-slate">
                        Analytical Evidence & Lineage:
                      </p>
                      <div className="flex flex-wrap items-center gap-1.5">
                        <span className="inline-flex items-center gap-1 rounded-md bg-teal-soft/80 px-2 py-0.5 text-[10px] font-semibold text-teal-dark">
                          <Database className="h-3 w-3" />
                          {msg.evidence.dataset_name} (v{msg.evidence.version_number})
                        </span>
                        {msg.evidence.tool_operations.map((op, idx) => (
                          <span
                            key={idx}
                            className="inline-flex items-center gap-1 rounded-md bg-cloud px-2 py-0.5 text-[10px] font-medium text-slate border border-border"
                          >
                            <FileText className="h-3 w-3" />
                            Tool: {op}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
                <time className="text-[10px] text-slate mt-1 px-1">
                  {new Date(msg.createdAt).toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </time>
              </article>
            ))
          )}

          {/* Real-Time Multi-Agent Processing Status Pill */}
          {isLoading && (
            <div className="flex items-start gap-2" aria-live="polite">
              <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-teal-soft text-teal">
                <Bot className="h-4 w-4" />
              </div>
              <div className="rounded-2xl rounded-bl-none border border-border bg-cloud p-3.5 text-xs text-slate space-y-2">
                <div className="flex items-center gap-2 font-medium text-ink">
                  <RefreshCw className="h-3.5 w-3.5 animate-spin text-teal" />
                  <span>Multi-Agent Orchestrator Executing Task DAG...</span>
                </div>
                <div className="flex flex-wrap items-center gap-2 text-[10px] text-slate font-mono">
                  <span className="flex items-center gap-1 bg-surface px-2 py-0.5 rounded border border-border">
                    <Activity className="h-2.5 w-2.5 text-teal" />
                    Supervisor Planning
                  </span>
                  <span className="text-slate">→</span>
                  <span className="flex items-center gap-1 bg-surface px-2 py-0.5 rounded border border-border">
                    <Cpu className="h-2.5 w-2.5 text-blue-500" />
                    Data Analyst / Engine
                  </span>
                  <span className="text-slate">→</span>
                  <span className="flex items-center gap-1 bg-surface px-2 py-0.5 rounded border border-border">
                    <ShieldCheck className="h-2.5 w-2.5 text-emerald-500" />
                    Critic Validation
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Error Banner */}
          {error && (
            <div className="flex items-center gap-2 rounded-xl border border-danger-border bg-danger-soft p-3 text-xs text-danger">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span className="flex-1">{error}</span>
              <Button
                variant="outline"
                onClick={() => handleSendMessage()}
                className="text-[10px] h-7 px-2"
              >
                Retry
              </Button>
            </div>
          )}

          <div ref={messagesEndRef} />
        </main>

        {/* ─── SUGGESTED FOLLOW-UP QUESTION CHIPS ─── */}
        {activeSuggestions.length > 0 && !isLoading && (
          <div className="px-6 py-2 border-t border-border/40 bg-cloud/20 flex flex-wrap items-center gap-1.5">
            <span className="text-[10px] font-semibold text-slate uppercase tracking-wider mr-1">
              Suggested next:
            </span>
            {activeSuggestions.map((s, idx) => (
              <button
                key={idx}
                onClick={() => handleSendMessage(s)}
                className="inline-flex items-center gap-1 rounded-lg border border-border bg-surface px-2.5 py-1 text-[11px] text-ink hover:bg-teal-soft hover:border-teal-border hover:text-teal-dark transition-all"
              >
                <span>{s}</span>
                <ArrowRight className="h-2.5 w-2.5 text-slate" />
              </button>
            ))}
          </div>
        )}

        {/* ─── INPUT AREA ─── */}
        <footer className="p-4 border-t border-border bg-surface">
          <div className="flex items-end gap-2">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={`Ask anything about ${selectedDataset?.name || "the dataset"} (e.g. "What region has highest revenue?")`}
              rows={2}
              className="flex-1 resize-none rounded-xl border border-border bg-cloud px-3 py-2 text-xs text-ink placeholder:text-slate focus:border-teal focus:outline-none focus:ring-1 focus:ring-teal"
              aria-label="Analytical query input"
            />
            <Button
              onClick={() => handleSendMessage()}
              disabled={!inputValue.trim() || isLoading}
              className="h-10 px-4 rounded-xl flex items-center gap-1.5"
            >
              <Send className="h-3.5 w-3.5" />
              <span>Send</span>
            </Button>
          </div>
        </footer>
      </div>

      {/* ─── MULTI-AGENT EXECUTION GRAPH MODAL ─── */}
      {showTaskModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <div className="bg-surface rounded-2xl border border-border p-6 max-w-3xl w-full max-h-[85vh] flex flex-col shadow-soft-lg space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div className="flex items-center gap-2">
                <Network className="h-5 w-5 text-teal" />
                <div>
                  <h3 className="text-sm font-bold text-ink">Multi-Agent Task Execution Graph</h3>
                  <p className="text-[11px] text-slate">
                    Topologically sorted execution DAG and validation audit trace
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowTaskModal(false)}
                className="p-1.5 rounded-lg text-slate hover:text-ink hover:bg-cloud"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Task List / DAG view */}
            <div className="flex-1 overflow-y-auto space-y-3 pr-1">
              {loadingTasks ? (
                <div className="flex items-center justify-center py-12 gap-2 text-xs text-slate">
                  <RefreshCw className="h-4 w-4 animate-spin text-teal" />
                  <span>Loading task execution graph...</span>
                </div>
              ) : tasks.length === 0 ? (
                <div className="text-center py-12 text-xs text-slate">
                  No multi-agent tasks recorded for this session yet. Ask a question to trigger the orchestrator.
                </div>
              ) : (
                tasks.map((t, idx) => {
                  const agentDef = registeredAgents.find((a) => a.agent_id === t.agent_id);
                  return (
                    <div
                      key={t.id || idx}
                      className="rounded-xl border border-border bg-cloud/30 p-3.5 space-y-2 text-xs"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-teal text-white text-[10px] font-bold">
                            {t.execution_order + 1}
                          </span>
                          <span className="font-semibold text-ink">
                            {agentDef?.name || t.agent_id}
                          </span>
                          <Badge
                            variant={
                              t.status === "COMPLETED"
                                ? "teal"
                                : t.status === "FAILED"
                                ? "danger"
                                : "blue"
                            }
                          >
                            {t.status}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-2 text-[10px] text-slate font-mono">
                          {t.duration_ms !== null && t.duration_ms !== undefined && (
                            <span>{t.duration_ms.toFixed(1)}ms</span>
                          )}
                          {t.tokens_used !== null && t.tokens_used !== undefined && (
                            <span>• {t.tokens_used} tokens</span>
                          )}
                        </div>
                      </div>

                      {t.objective && (
                        <p className="text-[11px] text-slate">
                          <span className="font-medium text-ink">Objective:</span> {t.objective}
                        </p>
                      )}

                      {t.depends_on_task_ids && t.depends_on_task_ids.length > 0 && (
                        <div className="flex items-center gap-1 text-[10px] text-slate">
                          <span>Depends on:</span>
                          {t.depends_on_task_ids.map((depId, dIdx) => (
                            <span key={dIdx} className="bg-surface px-1.5 py-0.5 rounded border border-border font-mono">
                              {depId}
                            </span>
                          ))}
                        </div>
                      )}

                      {t.validation_report && (
                        <div className="mt-2 p-2 rounded-lg bg-surface border border-border/80 text-[11px] space-y-1">
                          <div className="flex items-center justify-between font-semibold">
                            <span className="text-emerald-600 flex items-center gap-1">
                              <ShieldCheck className="h-3 w-3" />
                              Critic Validation: {t.validation_report.overall_status}
                            </span>
                            <span className="text-[10px] text-slate">
                              {t.validation_report.verified_claims_count} Verified /{" "}
                              {t.validation_report.contradicted_claims_count} Contradicted
                            </span>
                          </div>
                          <p className="text-[10px] text-slate">{t.validation_report.summary}</p>
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>

            <div className="flex items-center justify-between border-t border-border pt-3">
              <div className="flex items-center gap-1 text-[10px] text-slate">
                <span>Total Active Agents: {registeredAgents.length || 9}</span>
              </div>
              <Button
                variant="outline"
                onClick={() => setShowTaskModal(false)}
                className="text-xs"
              >
                Close
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* ─── CONFIRM DELETE MODAL ─── */}
      {conversationToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-surface rounded-2xl border border-border p-6 max-w-sm w-full space-y-4 shadow-soft-lg">
            <div className="flex items-center gap-2 text-danger">
              <AlertCircle className="h-5 w-5" />
              <h4 className="text-sm font-bold text-ink">Delete Conversation</h4>
            </div>
            <p className="text-xs text-slate">
              Are you sure you want to delete this analysis session? This action cannot be undone.
            </p>
            <div className="flex items-center justify-end gap-2 pt-2">
              <Button
                variant="outline"
                onClick={() => setConversationToDelete(null)}
                className="text-xs"
              >
                Cancel
              </Button>
              <Button
                variant="danger"
                disabled={isDeleting}
                onClick={() => handleDeleteConversation(conversationToDelete)}
                className="text-xs"
              >
                {isDeleting ? "Deleting..." : "Delete Session"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

