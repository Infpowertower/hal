from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction


class Command(BaseCommand):
    help = 'Removes all existing network data and repopulates with sample data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reset without confirmation',
        )
        parser.add_argument(
            '--no-repopulate',
            action='store_true',
            help='Do not repopulate with sample data after clearing',
        )

    @transaction.atomic
    def handle(self, *args, **kwargs):
        force = kwargs.get('force', False)
        no_repopulate = kwargs.get('no_repopulate', False)
        
        # Ask for confirmation if not forced
        if not force:
            confirm = input('Are you sure you want to reset all network data? This will delete all existing data. (yes/no): ')
            if confirm.lower() not in ['yes', 'y']:
                self.stdout.write(self.style.WARNING('Operation cancelled.'))
                return
        
        # Clear existing data
        self.stdout.write('Clearing existing network data...')
        call_command('clear_network_data', force=True)
        
        # Repopulate with sample data if requested
        if not no_repopulate:
            self.stdout.write('Repopulating with sample data...')
            call_command('populate_sample_data')
        
        self.stdout.write(self.style.SUCCESS('Network data reset completed successfully!'))