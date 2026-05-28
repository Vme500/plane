/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { observer } from "mobx-react";
// plane imports
import { useTranslation } from "@plane/i18n";
// components
import { PageHead } from "@/components/core/page-title";
import { SettingsContentWrapper } from "@/components/settings/content-wrapper";
import { SettingsHeading } from "@/components/settings/heading";
// hooks
import { useInstance } from "@/hooks/store/use-instance";
import { useWorkspace } from "@/hooks/store/use-workspace";
// local imports
import { AIAssistantSettingsHeader } from "./header";

function AIAssistantSettingsPage() {
  // store hooks
  const { config } = useInstance();
  const { currentWorkspace } = useWorkspace();
  // translation
  const { t } = useTranslation();

  // derived values
  const enableAiAssistant = config?.enable_ai_assistant ?? false;
  const enableAiMcpRuntime = config?.enable_ai_mcp_runtime ?? false;
  const hasLlmConfigured = config?.has_llm_configured ?? false;

  const pageTitle = currentWorkspace?.name
    ? `${currentWorkspace.name} - ${t("workspace_settings.settings.ai_assistant.title")}`
    : undefined;

  return (
    <SettingsContentWrapper header={<AIAssistantSettingsHeader />}>
      <PageHead title={pageTitle} />
      <div className="w-full">
        <SettingsHeading
          title={t("workspace_settings.settings.ai_assistant.heading")}
          description={t("workspace_settings.settings.ai_assistant.description")}
        />

        <div className="mt-6 space-y-6">
          {/* AI Assistant Status */}
          <div className="border-custom-border-200 bg-custom-background-80 rounded-lg border p-4">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-sm text-custom-text-100 font-medium">AI Assistant</h4>
                <p className="text-xs text-custom-text-300 mt-1">Core AI chat functionality for this workspace.</p>
              </div>
              <span
                className={`text-xs inline-flex items-center rounded-full px-2.5 py-0.5 font-medium ${
                  enableAiAssistant ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-800"
                }`}
              >
                {enableAiAssistant ? "Enabled" : "Disabled"}
              </span>
            </div>
          </div>

          {/* MCP Runtime Status */}
          <div className="border-custom-border-200 bg-custom-background-80 rounded-lg border p-4">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-sm text-custom-text-100 font-medium">MCP Runtime</h4>
                <p className="text-xs text-custom-text-300 mt-1">MCP Runtime is reserved for a later phase.</p>
              </div>
              <span
                className={`text-xs inline-flex items-center rounded-full px-2.5 py-0.5 font-medium ${
                  enableAiMcpRuntime ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-800"
                }`}
              >
                {enableAiMcpRuntime ? "Enabled" : "Disabled"}
              </span>
            </div>
          </div>

          {/* LLM Configuration Status */}
          <div className="border-custom-border-200 bg-custom-background-80 rounded-lg border p-4">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-sm text-custom-text-100 font-medium">LLM Configuration</h4>
                <p className="text-xs text-custom-text-300 mt-1">
                  Configure LLM_API_KEY on the server to enable prompt-response features.
                </p>
              </div>
              <span
                className={`text-xs inline-flex items-center rounded-full px-2.5 py-0.5 font-medium ${
                  hasLlmConfigured ? "bg-green-100 text-green-800" : "bg-yellow-100 text-yellow-800"
                }`}
              >
                {hasLlmConfigured ? "Configured" : "Not configured"}
              </span>
            </div>
          </div>

          {/* Security Note */}
          <div className="border-blue-200 bg-blue-50 rounded-lg border p-4">
            <h4 className="text-sm text-blue-800 font-medium">Security note</h4>
            <ul className="text-xs text-blue-700 mt-2 list-disc space-y-1 pl-5">
              <li>API keys are never shown in the browser.</li>
              <li>This page is read-only in the current phase.</li>
              <li>Changes must be made server-side through environment variables.</li>
            </ul>
          </div>
        </div>
      </div>
    </SettingsContentWrapper>
  );
}

export default observer(AIAssistantSettingsPage);
