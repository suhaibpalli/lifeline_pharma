from django.core.management.base import BaseCommand
from apps.core.models import SiteConfiguration


class Command(BaseCommand):
    help = "Seeds the database with default site configuration"

    def handle(self, *args, **options):
        configs = [
            {
                "key": "site_name",
                "value": "Lifeline Healthcare",
                "description": "The name of the website",
            },
            {
                "key": "site_tagline",
                "value": "Your trusted online pharmacy for genuine medicines",
                "description": "Tagline displayed on the site",
            },
            {
                "key": "contact_email",
                "value": "abijith.apollo@gmail.com",
                "description": "Primary contact email",
            },
            {
                "key": "contact_phone",
                "value": "044 - 48633074",
                "description": "Primary contact phone number",
            },
            {
                "key": "contact_address",
                "value": "No.18/24, Ground Floor, Sri Ayyappa Nagar 2nd Main road, Virugambakkam, Chennai-600092",
                "description": "Physical address of the company",
            },
            {
                "key": "meta_description",
                "value": "Lifeline Healthcare - Your trusted online pharmacy for genuine medicines delivered to your doorstep in Chennai.",
                "description": "SEO meta description",
            },
            {"key": "facebook_url", "value": "", "description": "Facebook page URL"},
            {"key": "twitter_url", "value": "", "description": "Twitter profile URL"},
            {
                "key": "instagram_url",
                "value": "",
                "description": "Instagram profile URL",
            },
            {"key": "linkedin_url", "value": "", "description": "LinkedIn profile URL"},
        ]

        created_count = 0
        updated_count = 0

        for config_data in configs:
            obj, created = SiteConfiguration.objects.update_or_create(
                key=config_data["key"],
                defaults={
                    "value": config_data["value"],
                    "description": config_data["description"],
                    "is_active": True,
                },
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created: {obj.key}"))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f"Updated: {obj.key}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone! Created {created_count} configurations, updated {updated_count} configurations."
            )
        )
