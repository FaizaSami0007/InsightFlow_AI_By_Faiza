"use client";

import React, { useState, useEffect, useRef } from "react";
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
} from "lucide-react";
import { api } from "@/lib/api-client";
import { Dataset, AIChatResponse } from "@/types";
import { Select } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface AIAnalystViewProps {
  initialDatasetId?: string;
  initialVersionId?: string;
}

interface MessageBubble {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  toolCalls?: Array<{ id: string; name: string; arguments: Record<string, unknown> }>;
  toolResults?: Array<{ tool_call_id: string; name: string; result: Record<string, unknown>; error?: string | null }>;
  citations?: string[];
  executionSteps?: string[];
  createdAt: string;
}

export function AIAnalystView({ initialDatasetId, initialVersionId }: AIAnalystViewProps) {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>(initialDatasetId || "");
  const [selectedVersionId, setSelectedVersionId] = useState<string>(initialVersionId || "");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<MessageBubble[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedTools, setExpandedTools] = useState<Record<string, boolean>>({});

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load user datasets
  useEffect(() => {
    async function loadDatasets() {
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
      } catch (err) {
        console.error("Failed to load datasets:", err);
      }
    }
    loadDatasets();
  }, [selectedDatasetId]);

  // Update version when selected dataset changes
  const handleDatasetChange = (dsId: string) => {
    setSelectedDatasetId(dsId);
    setConversationId(null);
    setMessages([]);
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
        conversation_id: conversationId,
        message: textToSend,
      };

      const res = await api.post<AIChatResponse>("/api/v1/ai/chat", payload);

      setConversationId(res.conversation_id);

      const assistantMsg: MessageBubble = {
        id: `asst-${Date.now()}`,
        role: "assistant",
        content: res.message,
        toolCalls: res.tool_calls,
        toolResults: res.tool_results,
        citations: res.citations,
        executionSteps: res.execution_steps,
        createdAt: new Date().toISOString(),
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

  const samplePrompts = [
    "What region has the highest revenue?",
    "Show summary statistics for numeric metrics",
    "Calculate the correlation between numeric columns",
    "Show sales grouped by category",
  ];

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] max-w-6xl mx-auto rounded-2xl border border-border bg-surface overflow-hidden shadow-soft">
      {/* Header Context Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-6 py-4 border-b border-border bg-cloud/50">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-teal text-white shadow-soft">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-ink">AI Data Analyst</h2>
              <Badge variant="teal">Phase 5 Orchestrator</Badge>
            </div>
            <p className="text-xs text-slate">
              Grounded analytical reasoning with safe deterministic tool calling
            </p>
          </div>
        </div>

        {/* Dataset & Version Pickers */}
        <div className="flex items-center gap-2">
          <div className="w-48">
            <Select
              options={datasets.map((d) => ({ value: d.id, label: d.name }))}
              value={selectedDatasetId}
              onChange={(e) => handleDatasetChange(e.target.value)}
              className="text-xs"
            />
          </div>
          {versionOptions.length > 0 && (
            <div className="w-44">
              <Select
                options={versionOptions}
                value={selectedVersionId}
                onChange={(e) => setSelectedVersionId(e.target.value)}
                className="text-xs"
              />
            </div>
          )}
        </div>
      </div>

      {/* Chat History Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center max-w-md mx-auto py-12">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-teal-soft text-teal mb-4">
              <Bot className="h-8 w-8" />
            </div>
            <h3 className="text-lg font-bold text-ink mb-1">
              Ask questions about your data
            </h3>
            <p className="text-xs text-slate mb-6">
              The AI Analyst plans structured queries, executes deterministic analytics via DuckDB tools, and guarantees 100% numerical grounding.
            </p>

            {/* Quick Prompts */}
            <div className="w-full space-y-2">
              <p className="text-[11px] font-semibold text-slate uppercase tracking-wider text-left">
                Suggested questions:
              </p>
              {samplePrompts.map((p, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSendMessage(p)}
                  className="w-full flex items-center justify-between p-2.5 rounded-xl border border-border bg-surface text-left text-xs text-ink hover:bg-cloud hover:border-teal-border transition-all"
                >
                  <span>{p}</span>
                  <ArrowRight className="h-3.5 w-3.5 text-slate shrink-0 ml-2" />
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex flex-col ${
                msg.role === "user" ? "items-end" : "items-start"
              }`}
            >
              <div
                className={`max-w-3xl rounded-2xl p-4 text-xs leading-relaxed ${
                  msg.role === "user"
                    ? "bg-teal text-white rounded-br-none shadow-soft"
                    : "bg-cloud text-ink rounded-bl-none border border-border"
                }`}
              >
                {/* Tool Execution Steps & Trace */}
                {msg.toolCalls && msg.toolCalls.length > 0 && (
                  <div className="mb-3 space-y-2 border-b border-border/40 pb-3">
                    <div className="flex items-center justify-between text-[11px] font-semibold text-teal-dark">
                      <div className="flex items-center gap-1.5">
                        <Cpu className="h-3.5 w-3.5" />
                        <span>Deterministic Tool Pipeline ({msg.toolCalls.length} tool called)</span>
                      </div>
                      <button
                        onClick={() => toggleToolExpand(msg.id)}
                        className="flex items-center gap-1 text-[10px] text-slate hover:text-ink"
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

                    {/* Collapsible Details */}
                    {expandedTools[msg.id] && (
                      <div className="space-y-2 mt-2">
                        {msg.toolCalls.map((tc, i) => {
                          const result = msg.toolResults?.find(
                            (r) => r.tool_call_id === tc.id || r.name === tc.name
                          );
                          return (
                            <div
                              key={i}
                              className="rounded-xl border border-border bg-surface p-2.5 text-[11px] font-mono text-slate space-y-1"
                            >
                              <div className="flex items-center justify-between text-ink font-semibold">
                                <span className="text-teal font-medium">Tool: {tc.name}</span>
                                {result?.error ? (
                                  <Badge variant="danger">Failed</Badge>
                                ) : (
                                  <Badge variant="teal">Executed</Badge>
                                )}
                              </div>
                              <div>
                                <span className="text-slate text-[10px]">Arguments:</span>
                                <pre className="text-[10px] overflow-x-auto bg-cloud p-1 rounded mt-0.5">
                                  {JSON.stringify(tc.arguments, null, 2)}
                                </pre>
                              </div>
                              {result && (
                                <div>
                                  <span className="text-slate text-[10px]">Result:</span>
                                  <pre className="text-[10px] overflow-x-auto bg-cloud p-1 rounded mt-0.5">
                                    {JSON.stringify(result.result, null, 2)}
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

                {/* Message Content */}
                <div className="whitespace-pre-wrap">{msg.content}</div>

                {/* Citations & Lineage */}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="mt-3 pt-2 border-t border-border/30 flex flex-wrap gap-1.5">
                    {msg.citations.map((c, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center gap-1 rounded-md bg-teal-soft/70 px-2 py-0.5 text-[10px] font-semibold text-teal-dark"
                      >
                        <CheckCircle2 className="h-3 w-3" />
                        {c}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              <span className="text-[10px] text-slate mt-1 px-1">
                {new Date(msg.createdAt).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </span>
            </div>
          ))
        )}

        {/* Loading Indicator */}
        {isLoading && (
          <div className="flex items-start gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-teal-soft text-teal">
              <Bot className="h-4 w-4" />
            </div>
            <div className="rounded-2xl rounded-bl-none border border-border bg-cloud p-3.5 text-xs text-slate flex items-center gap-2">
              <RefreshCw className="h-3.5 w-3.5 animate-spin text-teal" />
              <span>Analyzing dataset, calling deterministic tools, and synthesizing grounded answer...</span>
            </div>
          </div>
        )}

        {/* Error Notification */}
        {error && (
          <div className="flex items-center gap-2 rounded-xl border border-destructive/30 bg-destructive/10 p-3 text-xs text-destructive">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span className="flex-1">{error}</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-border bg-surface">
        <div className="flex items-end gap-2">
          <textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about this dataset (e.g., 'What region has the highest revenue?')"
            rows={2}
            className="flex-1 resize-none rounded-xl border border-border bg-cloud px-3 py-2 text-xs text-ink placeholder:text-slate focus:border-teal focus:outline-none focus:ring-1 focus:ring-teal"
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
      </div>
    </div>
  );
}
