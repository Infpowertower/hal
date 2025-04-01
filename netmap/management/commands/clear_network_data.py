import yaml
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from netmap.models import Device, Interface, Route, NATMapping


class Command(BaseCommand):
    help = 'Removes all network data from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force deletion without confirmation',
        )

    @transaction.atomic
    def handle(self, *args, **kwargs):
        force = kwargs.get('force', False)
        
        # Count the existing data
        device_count = Device.objects.count()
        interface_count = Interface.objects.count()
        route_count = Route.objects.count()
        nat_count = NATMapping.objects.count()
        
        if not device_count and not interface_count and not route_count and not nat_count:
            self.stdout.write(self.style.SUCCESS('No network data found in the database.'))
            return
            
        # Show summary of data to be deleted
        self.stdout.write(f'Found {device_count} devices, {interface_count} interfaces, {route_count} routes, and {nat_count} NAT mappings.')
        
        # Ask for confirmation if not forced
        if not force:
            confirm = input('Are you sure you want to delete all network data? (yes/no): ')
            if confirm.lower() not in ['yes', 'y']:
                self.stdout.write(self.style.WARNING('Operation cancelled.'))
                return
        
        # Delete all network data
        self.stdout.write('Deleting all network data...')
        self.clear_network_data()
        
        self.stdout.write(self.style.SUCCESS('Successfully removed all network data!'))
    
    def clear_network_data(self):
        """Remove all network data from the database"""
        # Delete in reverse order of dependencies
        nat_count = NATMapping.objects.count()
        NATMapping.objects.all().delete()
        self.stdout.write(f"  Deleted {nat_count} NAT mappings")
        
        route_count = Route.objects.count()
        Route.objects.all().delete()
        self.stdout.write(f"  Deleted {route_count} routes")
        
        interface_count = Interface.objects.count()
        Interface.objects.all().delete()
        self.stdout.write(f"  Deleted {interface_count} interfaces")
        
        device_count = Device.objects.count()
        Device.objects.all().delete()
        self.stdout.write(f"  Deleted {device_count} devices")