import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from BotRequestProecessing.models import Department  # adjust the import if your app name is different

class Command(BaseCommand):
    help = "Seed the Department model with data from a CSV file."

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help='Path to the CSV file to load departments from',
        )

    def handle(self, *args, **options):
        # Determine file path: use the provided --file argument or default to a file in BASE_DIR.
        file_path = options['file'] or os.path.join(settings.BASE_DIR, 'departments.csv')

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"File {file_path} does not exist."))
            return

        # Open the CSV file and read data
        with open(file_path, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            count_created = 0
            for row in reader:
                name = row.get('name')
                file_field = row.get('file')
                if not name or not file_field:
                    self.stdout.write(self.style.WARNING("Skipping row with missing data."))
                    continue

                # Create or update the Department object
                department, created = Department.objects.get_or_create(
                    name=name,
                    defaults={'file': file_field}
                )
                if created:
                    count_created += 1
                    self.stdout.write(self.style.SUCCESS(f"Created Department: {name}"))
                else:
                    self.stdout.write(self.style.WARNING(f"Department {name} already exists."))

            self.stdout.write(self.style.SUCCESS(f"Seeding complete. {count_created} new department(s) created."))