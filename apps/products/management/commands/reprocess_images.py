"""
Management command: reprocess_images

Converts all existing non-WebP product/category/manufacturer/carousel images
to WebP in-place. Replace-original strategy — run an MinIO backup first:

    rsync -a /opt/pharma/minio-data/ /opt/pharma/minio-data.bak-$(date +%F)/

Then inside the container:

    python manage.py reprocess_images          # live run
    python manage.py reprocess_images --dry-run  # report only, no changes
"""
import logging

from django.core.management.base import BaseCommand

from apps.core.images import convert_to_webp
from apps.core.models import CarouselImage
from apps.products.models import Category, Manufacturer, ProductImage

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Convert all stored product/category/carousel images to WebP and resize."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would be converted without making changes.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — no files will be changed.\n"))

        jobs = [
            ("ProductImage", ProductImage.objects.exclude(image="").filter(image__isnull=False), "image"),
            ("Category", Category.objects.exclude(image="").filter(image__isnull=False), "image"),
            ("Manufacturer", Manufacturer.objects.exclude(logo="").filter(logo__isnull=False), "logo"),
            ("CarouselImage", CarouselImage.objects.exclude(image="").filter(image__isnull=False), "image"),
        ]

        total_converted = 0
        total_skipped = 0
        total_errors = 0

        for model_name, qs, field_name in jobs:
            count = qs.count()
            self.stdout.write(f"\n{model_name}: {count} objects with images")

            for obj in qs.iterator():
                field = getattr(obj, field_name)
                name = getattr(field, "name", "") or ""

                if name.lower().endswith(".webp"):
                    total_skipped += 1
                    continue

                try:
                    orig_size = field.size
                except Exception:
                    orig_size = None

                if dry_run:
                    self.stdout.write(
                        f"  [DRY] {model_name} pk={obj.pk}: {name} "
                        f"({orig_size or '?'} bytes) → would convert to .webp"
                    )
                    total_converted += 1
                    continue

                result = convert_to_webp(field)
                if result is None:
                    total_skipped += 1
                    continue

                try:
                    new_name, content = result
                    new_size = len(content)

                    # Save directly via storage to bypass upload_to (which would
                    # double-prefix the path if called through field.save()).
                    old_name = field.name
                    storage = field.storage
                    saved_name = storage.save(new_name, content)
                    # Update DB and in-memory field to the saved path
                    type(obj).objects.filter(pk=obj.pk).update(**{field_name: saved_name})
                    field.name = saved_name
                    # Delete old object; failure is non-fatal (orphan is harmless)
                    try:
                        storage.delete(old_name)
                    except Exception:
                        pass

                    reduction = ""
                    if orig_size:
                        pct = round((1 - new_size / orig_size) * 100, 1)
                        reduction = f" ({orig_size}→{new_size} bytes, {pct}% smaller)"

                    self.stdout.write(
                        self.style.SUCCESS(f"  ✓ {model_name} pk={obj.pk}: {old_name} → {new_name}{reduction}")
                    )
                    total_converted += 1
                except Exception as exc:
                    self.stderr.write(
                        self.style.ERROR(f"  ✗ {model_name} pk={obj.pk}: {exc}")
                    )
                    total_errors += 1

        self.stdout.write(
            f"\n{'[DRY RUN] ' if dry_run else ''}"
            f"Done. converted={total_converted} skipped={total_skipped} errors={total_errors}"
        )
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "\nRun without --dry-run to apply. "
                    "Back up /opt/pharma/minio-data first!\n"
                )
            )
