# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from plane.db.models import AIAuditEvent, Workspace

MIN_DAYS = 7
DEFAULT_DAYS = 90
DEFAULT_BATCH_SIZE = 1000
MAX_BATCH_SIZE = 10000


class Command(BaseCommand):
    help = "Clean up old AI audit events by hard-deleting records beyond the retention period."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=DEFAULT_DAYS,
            help=f"Retention period in days (min {MIN_DAYS}, default {DEFAULT_DAYS})",
        )
        parser.add_argument(
            "--workspace-slug",
            type=str,
            default=None,
            help="Only clean up events for this workspace",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=DEFAULT_BATCH_SIZE,
            help=f"Number of records to delete per batch (default {DEFAULT_BATCH_SIZE})",
        )
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Actually delete records. Without this flag, the command runs in dry-run mode.",
        )

    def handle(self, *args, **options):
        days = options["days"]
        workspace_slug = options["workspace_slug"]
        batch_size = options["batch_size"]
        confirm = options["confirm"]

        # Validate days
        if days < MIN_DAYS:
            raise CommandError(
                f"--days must be at least {MIN_DAYS} to prevent accidental data loss. Got: {days}"
            )

        # Validate batch_size
        if batch_size < 1 or batch_size > MAX_BATCH_SIZE:
            raise CommandError(
                f"--batch-size must be between 1 and {MAX_BATCH_SIZE}. Got: {batch_size}"
            )

        # Compute cutoff
        cutoff = timezone.now() - timedelta(days=days)

        # Build queryset
        qs = AIAuditEvent.all_objects.filter(created_at__lt=cutoff)

        # Optional workspace filter
        if workspace_slug:
            workspace = Workspace.objects.filter(slug=workspace_slug).first()
            if not workspace:
                self.stdout.write(
                    self.style.WARNING(f"Workspace '{workspace_slug}' not found. No records to clean.")
                )
                return
            qs = qs.filter(workspace=workspace)

        # Count matching records
        matched_count = qs.count()

        # Report
        self.stdout.write(f"Retention period : {days} days")
        self.stdout.write(f"Cutoff           : {cutoff.isoformat()}")
        if workspace_slug:
            self.stdout.write(f"Workspace        : {workspace_slug}")
        self.stdout.write(f"Matched records  : {matched_count}")

        if matched_count == 0:
            self.stdout.write(self.style.SUCCESS("No records to clean up."))
            return

        if not confirm:
            # Dry-run mode
            self.stdout.write("")
            self.stdout.write(
                self.style.WARNING(
                    "DRY-RUN: No records were deleted. "
                    "Pass --confirm to actually delete these records."
                )
            )
            return

        # Confirm mode — hard delete in batches
        self.stdout.write("")
        self.stdout.write("Deleting records...")
        total_deleted = 0
        batch_num = 0

        while True:
            # Get a batch of IDs
            batch_ids = list(
                qs.order_by("created_at").values_list("id", flat=True)[:batch_size]
            )
            if not batch_ids:
                break

            batch_num += 1
            deleted_count = AIAuditEvent.all_objects.filter(
                id__in=batch_ids
            ).delete()[0]
            total_deleted += deleted_count

            self.stdout.write(f"  Batch {batch_num}: deleted {deleted_count} records")

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(f"Done. Deleted {total_deleted} records in {batch_num} batches.")
        )
