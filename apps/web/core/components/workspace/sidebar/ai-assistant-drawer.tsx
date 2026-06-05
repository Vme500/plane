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
// services
import { AIService } from "@/services/ai.service";

const aiService = new AIService();

type ProposedAction = {
  action_type: string;
  target_type: string;
  target_display?: string;
  proposed_value?: string;
  risk_level?: string;
  requires_confirmation: boolean;
  execution_enabled: boolean;
  confirmation_token?: string;
};

type AIResponse = {
  route?: string;
  mode?: string;
  action_type?: string;
  proposed_action?: ProposedAction;
  project?: { id: string; name: string };
  title?: string;
  error?: string;
};

type Props = {
  isOpen: boolean;
  onClose: () => void;
};

export const AIAssistantDrawer = observer(function AIAssistantDrawer({ isOpen, onClose }: Props) {
  const { workspaceSlug } = useParams();
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<AIResponse | null>(null);

  const handleSend = useCallback(async () => {
    if (!input.trim() || !workspaceSlug) return;
    setLoading(true);
    setResponse(null);
    try {
      const res = await aiService.createGptTask(workspaceSlug.toString(), {
        prompt: input.trim(),
        task: "chat",
        mode: "mcp",
      });
      // Parse the response
      const mcpPreview = (res as Record<string, unknown>)?.mcp_preview as Record<string, unknown> | undefined;
      const proposedAction = mcpPreview?.proposed_action as ProposedAction | undefined;
      const tool = mcpPreview?.tool as Record<string, unknown> | undefined;

      if (proposedAction) {
        setResponse({
          route: "official_mcp",
          mode: "proposed_action",
          action_type: proposedAction.action_type,
          proposed_action: proposedAction,
          title: proposedAction.target_display || "",
          project: undefined,
        });
      } else if (tool) {
        setResponse({
          route: "official_mcp",
          mode: "tool_result",
          action_type: tool.name as string,
        });
      } else {
        setResponse({
          error: "Could not process your request. Please try a different phrasing.",
        });
      }
    } catch {
      setResponse({ error: "Failed to process request. Please try again." });
    } finally {
      setLoading(false);
    }
  }, [input, workspaceSlug]);

  if (!isOpen) return null;

  return (
    <div className="shadow-lg fixed inset-y-0 right-0 z-50 flex w-96 flex-col border-l border-subtle bg-surface-1">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-subtle px-4 py-3">
        <h2 className="text-sm text-custom-text-100 font-medium">Plane AI</h2>
        <button onClick={onClose} className="text-custom-text-300 hover:text-custom-text-100">
          ✕
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {/* Provider status */}
        <div className="text-xs text-custom-text-300 mb-4 rounded-md bg-surface-2 p-3">
          <div>Provider: official MCP</div>
          <div>Writes require confirmation</div>
        </div>

        {/* Response area */}
        {response && (
          <div className="mb-4">
            {response.error ? (
              <div className="border-red-200 bg-red-50 text-xs text-red-700 rounded-md border p-3">
                {response.error}
              </div>
            ) : response.proposed_action ? (
              <div className="border-yellow-300 bg-yellow-50 text-xs rounded-md border p-3">
                <div className="text-yellow-800 mb-2 font-medium">Write Operation Proposed</div>
                <div className="text-yellow-700 space-y-1">
                  <div>Action: {response.proposed_action.action_type}</div>
                  {response.project && <div>Project: {response.project.name}</div>}
                  {response.title && <div>Title: {response.title}</div>}
                  {response.proposed_action.risk_level && <div>Risk: {response.proposed_action.risk_level}</div>}
                  <div className="text-yellow-600 mt-1 text-[10px]">Confirmation required</div>
                </div>
                <div className="mt-3 flex gap-2">
                  <button
                    disabled={!response.proposed_action.execution_enabled}
                    className="bg-yellow-600 text-xs rounded px-3 py-1 text-white disabled:opacity-50"
                  >
                    Confirm
                  </button>
                  <button className="bg-gray-300 text-xs text-gray-700 rounded px-3 py-1">Cancel</button>
                </div>
              </div>
            ) : (
              <div className="text-xs text-custom-text-200 rounded-md bg-surface-2 p-3">
                Request processed successfully.
              </div>
            )}
          </div>
        )}
      </div>

      {/* Input area */}
      <div className="border-t border-subtle p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !loading && handleSend()}
            placeholder="Ask Plane AI..."
            disabled={loading}
            className="text-sm text-custom-text-100 placeholder:text-custom-text-400 focus:border-custom-primary flex-1 rounded-md border border-subtle bg-surface-1 px-3 py-2 focus:outline-none"
          />
          <Button onClick={handleSend} disabled={loading || !input.trim()} size="sm">
            {loading ? "..." : "Send"}
          </Button>
        </div>
      </div>
    </div>
  );
});
