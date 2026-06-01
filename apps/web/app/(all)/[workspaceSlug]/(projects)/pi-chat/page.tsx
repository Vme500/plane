/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useState, useCallback } from "react";
import { observer } from "mobx-react";
import { useParams } from "next/navigation";
// plane imports
import { Button } from "@plane/propel/button";
// components
import { PageHead } from "@/components/core/page-title";
// hooks
import { useInstance } from "@/hooks/store/use-instance";
// services
import { AIService } from "@/services/ai.service";

const aiService = new AIService();

type ChatMode = "standard" | "mcp";

type MCPPreviewItem = {
  type: string;
  title: string;
  subtitle: string;
  metadata?: Record<string, unknown>;
};

type ProposedAction = {
  action_id: string;
  workspace_slug: string;
  actor_id: string;
  action_type: string;
  target_type: string;
  target_id: string | null;
  target_display: string | null;
  current_value: string | null;
  proposed_value: string | null;
  risk_level: string;
  summary: string;
  requires_confirmation: boolean;
  expires_at: string;
  execution_enabled: boolean;
};

type MCPPreview = {
  mode: string;
  adapter: string;
  tool: { name: string; status: string; readonly: boolean };
  summary: string;
  items: MCPPreviewItem[];
  safety?: { raw_result_returned: boolean; write_operation: boolean; permission_filtered: boolean };
  proposed_action?: ProposedAction | null;
};

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt: string;
  mode?: ChatMode;
  mcpPreview?: MCPPreview;
};

let messageIdCounter = 0;
const generateId = () => `msg_${Date.now()}_${++messageIdCounter}`;

function extractAIResponse(res: unknown): string {
  if (!res) return "No response content returned.";
  if (typeof res === "string") return res;
  if (typeof res === "object" && res !== null) {
    const obj = res as Record<string, unknown>;
    if (typeof obj.response_html === "string" && obj.response_html) return obj.response_html;
    if (typeof obj.response === "string" && obj.response) return obj.response;
    if (typeof obj.message === "string" && obj.message) return obj.message;
    if (typeof obj.result === "string" && obj.result) return obj.result;
    if (typeof obj.text === "string" && obj.text) return obj.text;
    if (typeof obj.content === "string" && obj.content) return obj.content;
  }
  return "No response content returned.";
}

function extractMCPPreview(res: unknown): MCPPreview | undefined {
  if (!res || typeof res !== "object") return undefined;
  const obj = res as Record<string, unknown>;
  return obj.mcp_preview as MCPPreview | undefined;
}

function PiChatPage() {
  const { workspaceSlug } = useParams();
  const { config } = useInstance();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [chatMode, setChatMode] = useState<ChatMode>("standard");

  const enableAiAssistant = config?.enable_ai_assistant ?? false;
  const hasLlmConfigured = config?.has_llm_configured ?? false;
  const enableAiMcpRuntime = config?.enable_ai_mcp_runtime ?? false;

  const handleSend = useCallback(async () => {
    const prompt = input.trim();
    if (!prompt || !workspaceSlug) return;

    const currentMode = chatMode;
    const userMessage: ChatMessage = {
      id: generateId(),
      role: "user",
      content: prompt,
      createdAt: new Date().toISOString(),
      mode: currentMode,
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const payload: { prompt: string; task: string; mode?: string } = {
        prompt,
        task: "chat",
      };

      // Add mode for MCP requests
      if (currentMode === "mcp") {
        payload.mode = "mcp";
      }

      const res = await aiService.createGptTask(workspaceSlug.toString(), payload);

      // Extract response
      const responseContent = extractAIResponse(res);
      const mcpPreview = currentMode === "mcp" ? extractMCPPreview(res) : undefined;

      const assistantMessage: ChatMessage = {
        id: generateId(),
        role: "assistant",
        content: responseContent,
        createdAt: new Date().toISOString(),
        mode: currentMode,
        mcpPreview,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: unknown) {
      let errorMessage = "Failed to get AI response. Please try again.";
      if (err && typeof err === "object") {
        const errObj = err as Record<string, unknown>;
        if (errObj.status === 429) {
          errorMessage = "Rate limit exceeded. Please try again later.";
        } else if (errObj.data && typeof errObj.data === "object") {
          const data = errObj.data as Record<string, unknown>;
          if (typeof data.error === "string") errorMessage = data.error;
        }
      }
      const errorAssistantMessage: ChatMessage = {
        id: generateId(),
        role: "assistant",
        content: `Error: ${errorMessage}`,
        createdAt: new Date().toISOString(),
        mode: currentMode,
      };
      setMessages((prev) => [...prev, errorAssistantMessage]);
    } finally {
      setIsLoading(false);
    }
  }, [input, workspaceSlug, chatMode]);

  // Feature flag: AI Assistant disabled
  if (!enableAiAssistant) {
    return (
      <>
        <PageHead title="Plane AI" />
        <div className="flex h-full items-center justify-center p-4">
          <div className="border-custom-border-200 bg-custom-background-80 text-sm text-custom-text-200 max-w-md rounded-lg border px-6 py-4 text-center">
            AI Assistant is disabled. Please set{" "}
            <code className="bg-custom-background-100 rounded px-1">ENABLE_AI_ASSISTANT=1</code> to enable it.
          </div>
        </div>
      </>
    );
  }

  // LLM not configured
  if (!hasLlmConfigured) {
    return (
      <>
        <PageHead title="Plane AI" />
        <div className="flex h-full items-center justify-center p-4">
          <div className="border-yellow-500/30 bg-yellow-500/10 text-sm text-yellow-700 max-w-md rounded-lg border px-6 py-4 text-center">
            LLM is not configured. Please configure <code className="bg-yellow-500/20 rounded px-1">LLM_API_KEY</code>{" "}
            before using AI Assistant.
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <PageHead title="Plane AI" />
      <div className="flex h-full flex-col overflow-hidden">
        {/* Chat area */}
        <div className="flex flex-1 flex-col overflow-hidden">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4">
            {messages.length === 0 && (
              <div className="text-sm text-custom-text-300 flex h-full items-center justify-center">
                Ask a question to get started with Plane AI.
              </div>
            )}
            <div className="space-y-4">
              {messages.map((msg) => (
                <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div
                    className={`text-sm max-w-[80%] rounded-lg px-4 py-2 ${
                      msg.role === "user"
                        ? "bg-custom-primary text-white"
                        : "bg-custom-background-80 text-custom-text-200"
                    }`}
                  >
                    {/* MCP Tool Preview */}
                    {msg.mcpPreview && (
                      <div className="border-custom-border-200 bg-custom-background-100 text-xs mb-2 rounded border p-2">
                        <div className="mb-1 flex items-center gap-2">
                          <span className="font-medium">[MCP]</span>
                          <span>{msg.mcpPreview.tool.name}</span>
                          <span
                            className={`rounded px-1 text-[10px] ${
                              msg.mcpPreview.tool.status === "success"
                                ? "bg-green-100 text-green-700"
                                : msg.mcpPreview.tool.status === "blocked"
                                  ? "bg-yellow-100 text-yellow-700"
                                  : "bg-red-100 text-red-700"
                            }`}
                          >
                            {msg.mcpPreview.tool.status}
                          </span>
                          <span className="text-custom-text-400">{msg.mcpPreview.adapter}</span>
                        </div>
                        <div className="text-custom-text-200">{msg.mcpPreview.summary}</div>
                        {msg.mcpPreview.items.length > 0 && (
                          <ul className="mt-1 list-none space-y-0.5">
                            {msg.mcpPreview.items.slice(0, 8).map((item) => (
                              <li key={String(item.metadata?.id ?? item.title)} className="text-custom-text-200">
                                {item.title}
                                {item.subtitle && <span className="text-custom-text-400"> — {item.subtitle}</span>}
                              </li>
                            ))}
                            {msg.mcpPreview.items.length > 8 && (
                              <li className="text-custom-text-400">... and {msg.mcpPreview.items.length - 8} more</li>
                            )}
                          </ul>
                        )}
                        <div className="text-custom-text-400 mt-1 text-[10px]">
                          {msg.mcpPreview.safety?.write_operation
                            ? "Write proposed | Plan only"
                            : "Read-only | Permission filtered"}
                        </div>
                        {/* Phase 9.1: Confirmation card for write operations */}
                        {msg.mcpPreview.proposed_action && (
                          <div className="border-yellow-300 bg-yellow-50 text-xs mt-2 rounded border p-2">
                            <div className="text-yellow-800 font-medium">Write Operation Proposed</div>
                            <div className="text-yellow-700 mt-1">
                              <div>Action: {msg.mcpPreview.proposed_action.action_type}</div>
                              {msg.mcpPreview.proposed_action.target_display && (
                                <div>Target: {msg.mcpPreview.proposed_action.target_display}</div>
                              )}
                              {msg.mcpPreview.proposed_action.current_value && (
                                <div>Current: {msg.mcpPreview.proposed_action.current_value}</div>
                              )}
                              {msg.mcpPreview.proposed_action.proposed_value && (
                                <div>Proposed: {msg.mcpPreview.proposed_action.proposed_value}</div>
                              )}
                              <div>Risk: {msg.mcpPreview.proposed_action.risk_level}</div>
                              <div>
                                Expires: {new Date(msg.mcpPreview.proposed_action.expires_at).toLocaleTimeString()}
                              </div>
                            </div>
                            <div className="mt-2 flex gap-2">
                              <button
                                disabled={!msg.mcpPreview.proposed_action.execution_enabled}
                                className="bg-yellow-600 rounded px-2 py-1 text-white disabled:opacity-50"
                              >
                                {msg.mcpPreview.proposed_action.execution_enabled ? "Confirm" : "Confirm (not enabled)"}
                              </button>
                              <button className="bg-gray-300 text-gray-700 rounded px-2 py-1">Cancel</button>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                    {msg.content}
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-custom-background-80 text-sm text-custom-text-300 rounded-lg px-4 py-2">
                    Generating response...
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Input area */}
          <div className="border-custom-border-200 border-t p-4">
            {/* MCP Mode Toggle */}
            {enableAiMcpRuntime && (
              <div className="mb-3 flex items-center gap-2">
                <span className="text-xs text-custom-text-300">Mode:</span>
                <button
                  onClick={() => setChatMode("standard")}
                  className={`text-xs rounded-md px-2 py-1 ${
                    chatMode === "standard"
                      ? "bg-custom-primary text-white"
                      : "bg-custom-background-80 text-custom-text-200 hover:bg-custom-background-100"
                  }`}
                >
                  Standard Chat
                </button>
                <button
                  onClick={() => setChatMode("mcp")}
                  className={`text-xs rounded-md px-2 py-1 ${
                    chatMode === "mcp"
                      ? "bg-custom-primary text-white"
                      : "bg-custom-background-80 text-custom-text-200 hover:bg-custom-background-100"
                  }`}
                >
                  MCP Read-only
                </button>
                {chatMode === "mcp" && <span className="text-xs text-yellow-600">Read-only queries only</span>}
              </div>
            )}

            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder={chatMode === "mcp" ? "Ask about projects, work items, states..." : "Ask AI anything..."}
                className="border-custom-border-200 bg-custom-background-100 text-sm focus:border-custom-primary flex-1 rounded-lg border px-4 py-2 outline-none"
                disabled={isLoading}
              />
              <Button variant="primary" onClick={handleSend} loading={isLoading} disabled={!input.trim()}>
                Send
              </Button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

export default observer(PiChatPage);
