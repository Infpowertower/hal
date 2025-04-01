import yaml
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from netmap.models import Device, Interface, Route, NATMapping


class Command(BaseCommand):
    help = 'Populates the database with sample network data from YAML'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample data for network topology...')
        
        # Check if data already exists
        if Device.objects.exists():
            self.stdout.write(self.style.WARNING('Data already exists. Skipping sample data creation.'))
            return
            
        # Load data from YAML
        fixtures_path = os.path.join('netmap', 'fixtures', 'network_data.yaml')
        self.load_from_yaml(fixtures_path)
        
        self.stdout.write(self.style.SUCCESS('Successfully created sample network data!'))
    
    def load_from_yaml(self, file_path):
        """Load network data from YAML file"""
        try:
            with open(file_path, 'r') as file:
                data = yaml.safe_load(file)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error loading YAML file: {e}"))
            return
        
        if not data or 'devices' not in data:
            self.stdout.write(self.style.ERROR("Invalid YAML format: 'devices' section not found"))
            return
        
        # Create devices and their interfaces, routes, and NAT mappings
        for device_data in data['devices']:
            self.create_device_with_related(device_data)
    
    def create_device_with_related(self, device_data):
        """Create a device with its interfaces, routes, and NAT mappings"""
        # Extract device data
        name = device_data.get('name')
        description = device_data.get('description', '')
        
        # Create device
        device = Device.objects.create(name=name, description=description)
        self.stdout.write(f"  Created device: {device.name}")
        
        # Create interfaces
        if 'interfaces' in device_data:
            for interface_data in device_data['interfaces']:
                Interface.objects.create(
                    device=device,
                    name=interface_data.get('name'),
                    ip_address=interface_data.get('ip_address'),
                    network=interface_data.get('network'),
                    status=interface_data.get('status', 'up')
                )
                self.stdout.write(f"    Created interface: {interface_data.get('name')} ({interface_data.get('ip_address')})")
        
        # Create routes
        if 'routes' in device_data:
            for route_data in device_data['routes']:
                Route.objects.create(
                    source_device=device,
                    destination_network=route_data.get('destination_network'),
                    gateway_ip=route_data.get('gateway_ip', None),
                    type=route_data.get('type', 'static'),
                    metric=route_data.get('metric', 0)
                )
                dest_net = route_data.get('destination_network')
                gateway = route_data.get('gateway_ip', 'directly connected')
                self.stdout.write(f"    Created route: {dest_net} via {gateway}")
        
        # Create NAT mappings
        if 'nat_mappings' in device_data:
            for nat_data in device_data['nat_mappings']:
                NATMapping.objects.create(
                    device=device,
                    logical_ip_or_network=nat_data.get('logical_ip_or_network'),
                    real_ip_or_network=nat_data.get('real_ip_or_network'),
                    type=nat_data.get('type'),
                    description=nat_data.get('description', '')
                )
                self.stdout.write(f"    Created NAT mapping: {nat_data.get('type')} {nat_data.get('logical_ip_or_network')} -> {nat_data.get('real_ip_or_network')}")