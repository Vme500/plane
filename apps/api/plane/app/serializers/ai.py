# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from rest_framework import serializers

from plane.db.models import AIAuditEvent


class ActorLiteSerializer(serializers.Serializer):
    """Safe actor representation — never exposes full user object, password, token, etc."""

    id = serializers.UUIDField()
    display_name = serializers.SerializerMethodField()
    email = serializers.EmailField()

    def get_display_name(self, obj):
        first = getattr(obj, "first_name", "") or ""
        last = getattr(obj, "last_name", "") or ""
        name = f"{first} {last}".strip()
        return name if name else None


class AIAuditEventSerializer(serializers.ModelSerializer):
    """Read-only serializer for AI audit events.

    SECURITY: Never returns raw prompt, raw result, raw MCP result,
    token, API key, cookie, password, headers, stack trace, env,
    deleted_at, created_by, updated_by, or full model objects.
    """

    actor = ActorLiteSerializer(read_only=True, source="actor")
    workspace_slug = serializers.SlugRelatedField(
        source="workspace", read_only=True, slug_field="slug"
    )

    class Meta:
        model = AIAuditEvent
        fields = [
            "id",
            "created_at",
            "workspace_slug",
            "actor",
            "event",
            "mode",
            "adapter",
            "tool_name",
            "tool_status",
            "readonly",
            "permission_filtered",
            "raw_result_returned",
            "write_operation",
            "duration_ms",
            "item_count",
            "prompt_length",
            "error_code",
            "source",
            "request_id",
        ]
        read_only_fields = fields
