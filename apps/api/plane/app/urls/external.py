# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from django.urls import path


from plane.app.views import UnsplashEndpoint
from plane.app.views import GPTIntegrationEndpoint, WorkspaceGPTIntegrationEndpoint
from plane.app.views.ai import (
    AIAuditEventListEndpoint,
    AIMCPSettingsEndpoint,
    AIMCPTestConnectionEndpoint,
    AIMCPToolsEndpoint,
)
from plane.app.views.ai_native import NativeAIStatusEndpoint, NativeAIProposeEndpoint


urlpatterns = [
    path("unsplash/", UnsplashEndpoint.as_view(), name="unsplash"),
    path(
        "workspaces/<str:slug>/projects/<uuid:project_id>/ai-assistant/",
        GPTIntegrationEndpoint.as_view(),
        name="importer",
    ),
    path(
        "workspaces/<str:slug>/ai-assistant/",
        WorkspaceGPTIntegrationEndpoint.as_view(),
        name="importer",
    ),
    path(
        "workspaces/<str:slug>/ai-audit-events/",
        AIAuditEventListEndpoint.as_view(),
        name="ai-audit-events",
    ),
    path(
        "workspaces/<str:slug>/ai-assistant/mcp/settings/",
        AIMCPSettingsEndpoint.as_view(),
        name="ai-mcp-settings",
    ),
    path(
        "workspaces/<str:slug>/ai-assistant/mcp/test-connection/",
        AIMCPTestConnectionEndpoint.as_view(),
        name="ai-mcp-test-connection",
    ),
    path(
        "workspaces/<str:slug>/ai-assistant/mcp/tools/",
        AIMCPToolsEndpoint.as_view(),
        name="ai-mcp-tools",
    ),
    path(
        "workspaces/<str:slug>/ai-assistant/native/status/",
        NativeAIStatusEndpoint.as_view(),
        name="ai-native-status",
    ),
    path(
        "workspaces/<str:slug>/ai-assistant/native/propose/",
        NativeAIProposeEndpoint.as_view(),
        name="ai-native-propose",
    ),
]
