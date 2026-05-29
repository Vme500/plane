# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from django.conf import settings
from django.db import models

from .base import BaseModel


class AIAuditEvent(BaseModel):
    """
    AI/MCP audit event log.

    SECURITY: This model NEVER stores raw prompt, raw result, raw MCP result,
    API keys, tokens, cookies, passwords, request headers, stack traces, env
    variables, full request/response bodies, or full user/model objects.
    """

    EVENT_CHOICES = (
        ("ai.request", "AI Request"),
        ("ai.request.success", "AI Request Success"),
        ("ai.request.error", "AI Request Error"),
        ("ai.tool.call", "AI Tool Call"),
        ("ai.tool.error", "AI Tool Error"),
        ("ai.tool.blocked", "AI Tool Blocked"),
        ("ai.tool.rejected", "AI Tool Rejected"),
    )

    MODE_CHOICES = (
        ("standard", "Standard"),
        ("mcp", "MCP"),
    )

    ADAPTER_CHOICES = (
        ("none", "None"),
        ("mock", "Mock"),
        ("stdio", "Stdio"),
    )

    TOOL_STATUS_CHOICES = (
        ("success", "Success"),
        ("blocked", "Blocked"),
        ("error", "Error"),
        ("rejected", "Rejected"),
    )

    workspace = models.ForeignKey(
        "db.Workspace",
        on_delete=models.CASCADE,
        related_name="ai_audit_events",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_audit_events",
    )

    event = models.CharField(max_length=64, choices=EVENT_CHOICES, db_index=True)
    mode = models.CharField(max_length=16, choices=MODE_CHOICES, null=True, blank=True)
    adapter = models.CharField(max_length=16, choices=ADAPTER_CHOICES, null=True, blank=True)
    tool_name = models.CharField(max_length=64, null=True, blank=True)
    tool_status = models.CharField(max_length=16, choices=TOOL_STATUS_CHOICES, null=True, blank=True)

    readonly = models.BooleanField(default=True)
    permission_filtered = models.BooleanField(null=True, blank=True)
    raw_result_returned = models.BooleanField(default=False)
    write_operation = models.BooleanField(default=False)

    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    item_count = models.PositiveIntegerField(null=True, blank=True)
    prompt_length = models.PositiveIntegerField(null=True, blank=True)
    error_code = models.CharField(max_length=64, null=True, blank=True)
    source = models.CharField(max_length=32, default="pi-chat")
    request_id = models.CharField(max_length=64, null=True, blank=True, db_index=True)

    class Meta:
        verbose_name = "AI Audit Event"
        verbose_name_plural = "AI Audit Events"
        db_table = "ai_audit_events"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["workspace", "created_at"], name="idx_ai_audit_ws_created"),
            models.Index(fields=["actor", "created_at"], name="idx_ai_audit_actor_created"),
            models.Index(fields=["event", "created_at"], name="idx_ai_audit_event_created"),
        ]

    def __str__(self):
        return f"{self.event} by {self.actor_id} at {self.created_at}"
