# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from plane.app.permissions import ROLE, allow_permission
from plane.app.serializers.ai import AIAuditEventSerializer
from plane.db.models import AIAuditEvent

from .base import BaseAPIView

# Allowed filter field values (whitelist)
ALLOWED_EVENTS = [
    "ai.request",
    "ai.request.success",
    "ai.request.error",
    "ai.tool.call",
    "ai.tool.error",
    "ai.tool.blocked",
    "ai.tool.rejected",
]
ALLOWED_MODES = ["standard", "mcp"]
ALLOWED_ADAPTERS = ["none", "mock", "stdio"]
ALLOWED_TOOL_STATUSES = ["success", "blocked", "error", "rejected"]

DEFAULT_DAYS = 30
MAX_DAYS = 90
DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 100


class AIAuditEventListEndpoint(BaseAPIView):
    """Admin-only list endpoint for AI audit events.

    SECURITY:
    - Only workspace ADMIN can access.
    - Workspace scoped (no cross-workspace queries).
    - Never returns raw prompt, result, secrets, headers, stack trace, env.
    - Paginated, time-windowed, safe filters only.
    """

    @allow_permission(allowed_roles=[ROLE.ADMIN], level="WORKSPACE")
    def get(self, request, slug):
        # Time window
        now = timezone.now()
        default_after = now - timedelta(days=DEFAULT_DAYS)
        max_after = now - timedelta(days=MAX_DAYS)

        created_at_after = request.GET.get("created_at_after")
        created_at_before = request.GET.get("created_at_before")

        qs = AIAuditEvent.objects.filter(
            workspace__slug=slug,
        ).select_related("workspace", "actor")

        # Apply time filters
        if created_at_after:
            try:
                after = timezone.datetime.fromisoformat(created_at_after)
                if timezone.is_naive(after):
                    after = timezone.make_aware(after)
                # Clamp to max window
                if after < max_after:
                    after = max_after
                qs = qs.filter(created_at__gte=after)
            except (ValueError, TypeError):
                return Response(
                    {"error": "Invalid created_at_after format. Use ISO 8601."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            qs = qs.filter(created_at__gte=default_after)

        if created_at_before:
            try:
                before = timezone.datetime.fromisoformat(created_at_before)
                if timezone.is_naive(before):
                    before = timezone.make_aware(before)
                qs = qs.filter(created_at__lte=before)
            except (ValueError, TypeError):
                return Response(
                    {"error": "Invalid created_at_before format. Use ISO 8601."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Safe filters
        event = request.GET.get("event")
        if event and event in ALLOWED_EVENTS:
            qs = qs.filter(event=event)

        mode = request.GET.get("mode")
        if mode and mode in ALLOWED_MODES:
            qs = qs.filter(mode=mode)

        adapter = request.GET.get("adapter")
        if adapter and adapter in ALLOWED_ADAPTERS:
            qs = qs.filter(adapter=adapter)

        tool_name = request.GET.get("tool_name")
        if tool_name:
            qs = qs.filter(tool_name=tool_name)

        tool_status_param = request.GET.get("tool_status")
        if tool_status_param and tool_status_param in ALLOWED_TOOL_STATUSES:
            qs = qs.filter(tool_status=tool_status_param)

        actor_id = request.GET.get("actor_id")
        if actor_id:
            qs = qs.filter(actor_id=actor_id)

        source = request.GET.get("source")
        if source:
            qs = qs.filter(source=source)

        error_code = request.GET.get("error_code")
        if error_code:
            qs = qs.filter(error_code=error_code)

        write_op = request.GET.get("write_operation")
        if write_op is not None:
            if write_op.lower() == "true":
                qs = qs.filter(write_operation=True)
            elif write_op.lower() == "false":
                qs = qs.filter(write_operation=False)

        readonly = request.GET.get("readonly")
        if readonly is not None:
            if readonly.lower() == "true":
                qs = qs.filter(readonly=True)
            elif readonly.lower() == "false":
                qs = qs.filter(readonly=False)

        # Ordering
        qs = qs.order_by("-created_at")

        # Pagination
        try:
            per_page = int(request.GET.get("per_page", DEFAULT_PER_PAGE))
        except ValueError:
            per_page = DEFAULT_PER_PAGE
        per_page = max(1, min(per_page, MAX_PER_PAGE))

        try:
            page = int(request.GET.get("page", 1))
        except ValueError:
            page = 1
        page = max(1, page)

        total_count = qs.count()
        offset = (page - 1) * per_page
        items = qs[offset : offset + per_page]

        serializer = AIAuditEventSerializer(items, many=True)

        return Response(
            {
                "results": serializer.data,
                "total_count": total_count,
                "page": page,
                "per_page": per_page,
                "total_pages": max(1, -(-total_count // per_page)),  # ceil division
            },
            status=status.HTTP_200_OK,
        )
