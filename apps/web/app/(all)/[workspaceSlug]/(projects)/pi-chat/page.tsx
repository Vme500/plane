/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useState } from "react";
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

// TODO: gate this page with enable_ai_assistant once the flag is added in Phase 4

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

function PiChatPage() {
  const { workspaceSlug } = useParams();
  const { config } = useInstance();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const hasLlmConfigured = config?.has_llm_configured ?? false;

  const handleSend = async () => {
    const prompt = input.trim();
    if (!prompt || !workspaceSlug) return;

    setError(null);
    setMessages((prev) => [...prev, { role: "user", content: prompt }]);
    setInput("");
    setIsLoading(true);

    try {
      const res = await aiService.createGptTask(workspaceSlug.toString(), {
        prompt,
        task: "chat",
      });

      const responseText =
        res?.response_html || res?.response || res?.message || JSON.stringify(res);

      setMessages((prev) => [...prev, { role: "assistant", content: responseText }]);
    } catch (err: any) {
      const errorMessage =
        err?.data?.error || err?.status === 429
          ? "Rate limit exceeded. Please try again later."
          : "Failed to get AI response. Please try again.";
      setError(errorMessage);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Error: ${errorMessage}` },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <PageHead title="Plane AI" />
      <div className="flex h-full flex-col overflow-hidden">
        {/* Status area */}
        {!hasLlmConfigured && (
          <div className="flex items-center justify-center p-4">
            <div className="rounded-lg border border-yellow-500/30 bg-yellow-500/10 px-4 py-3 text-sm text-yellow-700">
              LLM is not configured. Please configure LLM_API_KEY before using AI Assistant.
            </div>
          </div>
        )}

        {/* Chat area */}
        <div className="flex flex-1 flex-col overflow-hidden">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4">
            {messages.length === 0 && hasLlmConfigured && (
              <div className="flex h-full items-center justify-center text-sm text-custom-text-300">
                Ask a question to get started with Plane AI.
              </div>
            )}
            <div className="space-y-4">
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg px-4 py-2 text-sm ${
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
                  <div className="rounded-lg bg-custom-background-80 px-4 py-2 text-sm text-custom-text-300">
                    Generating response...
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Input area */}
          {hasLlmConfigured && (
            <div className="border-t border-custom-border-200 p-4">
              {error && (
                <div className="mb-2 text-xs text-red-500">{error}</div>
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
                  placeholder="Ask AI anything..."
                  className="flex-1 rounded-lg border border-custom-border-200 bg-custom-background-100 px-4 py-2 text-sm outline-none focus:border-custom-primary"
                  disabled={isLoading}
                />
                <Button
                  variant="primary"
                  onClick={handleSend}
                  loading={isLoading}
                  disabled={!input.trim()}
                >
                  Send
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

export default observer(PiChatPage);
