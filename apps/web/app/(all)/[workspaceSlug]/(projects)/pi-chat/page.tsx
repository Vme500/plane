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

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt: string;
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

function PiChatPage() {
  const { workspaceSlug } = useParams();
  const { config } = useInstance();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const enableAiAssistant = config?.enable_ai_assistant ?? false;
  const hasLlmConfigured = config?.has_llm_configured ?? false;

  const handleSend = useCallback(async () => {
    const prompt = input.trim();
    if (!prompt || !workspaceSlug) return;

    const userMessage: ChatMessage = {
      id: generateId(),
      role: "user",
      content: prompt,
      createdAt: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const res = await aiService.createGptTask(workspaceSlug.toString(), {
        prompt,
        task: "chat",
      });

      const assistantMessage: ChatMessage = {
        id: generateId(),
        role: "assistant",
        content: extractAIResponse(res),
        createdAt: new Date().toISOString(),
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
      };
      setMessages((prev) => [...prev, errorAssistantMessage]);
    } finally {
      setIsLoading(false);
    }
  }, [input, workspaceSlug]);

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
                placeholder="Ask AI anything..."
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
