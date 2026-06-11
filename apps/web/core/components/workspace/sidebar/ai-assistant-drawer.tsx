/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useState, useCallback } from "react";
import { createPortal } from "react-dom";
import { observer } from "mobx-react";
import { useParams } from "next/navigation";
// plane imports
import { Button } from "@plane/propel/button";
// services
import { NativeAIService } from "@/services/native-ai.service";

const nativeAIService = new NativeAIService();

type ProposedAction = {
  source?: string;
  action_type: string;
  target_type: string;
  target_display?: string;
  title?: string;
  project?: { id: string; name: string };
  proposed_value?: string;
  risk_level?: string;
  requires_confirmation: boolean;
  execution_enabled: boolean;
  confirmation_token_present?: boolean;
};

type AIResponse = {
  route?: string;
  source?: string;
  response_type?: string;
  proposed_action?: ProposedAction;
  message?: string;
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
      const res = await nativeAIService.propose(workspaceSlug.toString(), {
        message: input.trim(),
      });

      // Validate source: only accept official_mcp_gateway
      const source = (res as Record<string, unknown>)?.source as string | undefined;
      if (source !== "official_mcp_gateway") {
        setResponse({
          error: "Unsupported AI route. Native AI only accepts official MCP gateway responses.",
        });
        return;
      }

      const responseType = (res as Record<string, unknown>)?.response_type as string | undefined;
      const proposedAction = (res as Record<string, unknown>)?.proposed_action as ProposedAction | undefined;
      const message = (res as Record<string, unknown>)?.message as string | undefined;
      const error = (res as Record<string, unknown>)?.error as string | undefined;

      if (error) {
        setResponse({ error });
      } else if (responseType === "proposed_action" && proposedAction) {
        // Validate proposed_action source
        if (proposedAction.source !== "official_mcp_gateway") {
          setResponse({
            error: "Unsupported AI route. Proposed action must come from official MCP gateway.",
          });
          return;
        }
        setResponse({
          route: "official_mcp",
          source: "official_mcp_gateway",
          response_type: "proposed_action",
          proposed_action: proposedAction,
        });
      } else if (responseType === "text" && message) {
        setResponse({
          route: "official_mcp",
          source: "official_mcp_gateway",
          response_type: "text",
          message,
        });
      } else {
        setResponse({
          error: "Could not process your request. Try a different phrasing.",
        });
      }
    } catch {
      setResponse({ error: "Failed to process request. Please try again." });
    } finally {
      setLoading(false);
    }
  }, [input, workspaceSlug]);

  if (!isOpen) return null;

  const pa = response?.proposed_action;
  const canConfirm = Boolean(pa?.execution_enabled && pa?.confirmation_token_present);

  return createPortal(
    <div className="shadow-2xl fixed inset-y-0 right-0 z-[100] flex w-96 flex-col border-l border-subtle bg-surface-1">
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
            ) : pa ? (
              <div className="border-yellow-300 bg-yellow-50 text-xs rounded-md border p-3">
                <div className="text-yellow-800 mb-2 font-medium">Write Operation Proposed</div>
                <div className="text-yellow-700 space-y-1">
                  <div>Action: {pa.action_type}</div>
                  <div>Project: {pa.project?.name ?? "Unknown project"}</div>
                  <div>Title: {pa.title || pa.target_display || "Untitled"}</div>
                  {pa.risk_level && <div>Risk: {pa.risk_level}</div>}
                  <div className="text-yellow-600 mt-1 text-[10px]">Confirmation required</div>
                </div>
                <div className="mt-3 flex gap-2">
                  <button
                    disabled={!canConfirm}
                    className="bg-blue-600 text-xs hover:bg-blue-700 rounded px-3 py-1.5 font-medium text-white disabled:opacity-50"
                  >
                    Confirm
                  </button>
                  <button className="bg-gray-300 text-xs text-gray-700 hover:bg-gray-400 rounded px-3 py-1.5">
                    Cancel
                  </button>
                </div>
              </div>
            ) : response.message ? (
              <div className="text-xs text-custom-text-200 rounded-md bg-surface-2 p-3">{response.message}</div>
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
    </div>,
    document.body
  );
});
