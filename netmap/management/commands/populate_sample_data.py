import random
from django.core.management.base import BaseCommand
from django.db import transaction
from netmap.models import Device, Interface, Route, NATMapping


class Command(BaseCommand):
    help = 'Populates the database with sample network data'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample data for network topology...')
        
        # Check if data already exists
        if Device.objects.exists():
            self.stdout.write(self.style.WARNING('Data already exists. Skipping sample data creation.'))
            return
            
        # Create devices
        self.create_devices()
        
        # Create interfaces with appropriate networks
        self.create_interfaces()
        
        # Create routes
        self.create_routes()
        
        # Create NAT mappings
        self.create_nat_mappings()
        
        self.stdout.write(self.style.SUCCESS('Successfully created sample network data!'))
    
    def create_devices(self):
        """Create sample network devices"""
        self.stdout.write('Creating devices...')
        
        # Define the devices
        devices = [
            {'name': 'router1', 'description': 'Core Router 1'},
            {'name': 'router2', 'description': 'Core Router 2'},
            {'name': 'firewall1', 'description': 'Perimeter Firewall'},
            {'name': 'switch1', 'description': 'Distribution Switch 1'},
            {'name': 'switch2', 'description': 'Distribution Switch 2'},
            {'name': 'server1', 'description': 'Web Server'},
            {'name': 'server2', 'description': 'Database Server'},
        ]
        
        # Create the devices
        for device_data in devices:
            device = Device.objects.create(**device_data)
            self.stdout.write(f'  Created device: {device.name}')
    
    def create_interfaces(self):
        """Create sample network interfaces"""
        self.stdout.write('Creating interfaces...')
        
        # Get all devices
        devices = Device.objects.all()
        
        # Define networks for different areas
        core_network = '10.0.0.0/24'
        dmz_network = '172.16.0.0/24'
        internal_networks = ['192.168.1.0/24', '192.168.2.0/24', '192.168.3.0/24']
        management_network = '10.99.0.0/24'
        internet_network = '203.0.113.0/24'
        
        # -------- Core Routers --------
        router1 = Device.objects.get(name='router1')
        router2 = Device.objects.get(name='router2')
        
        # Create core network interfaces between routers
        interfaces = [
            # Router 1 interfaces
            {'device': router1, 'name': 'eth0', 'ip_address': '10.0.0.1', 'network': core_network},
            {'device': router1, 'name': 'eth1', 'ip_address': '172.16.0.1', 'network': dmz_network},
            {'device': router1, 'name': 'eth2', 'ip_address': '192.168.1.1', 'network': internal_networks[0]},
            {'device': router1, 'name': 'eth3', 'ip_address': '10.99.0.1', 'network': management_network},
            {'device': router1, 'name': 'eth4', 'ip_address': '203.0.113.1', 'network': internet_network},
            
            # Router 2 interfaces
            {'device': router2, 'name': 'eth0', 'ip_address': '10.0.0.2', 'network': core_network},
            {'device': router2, 'name': 'eth1', 'ip_address': '192.168.2.1', 'network': internal_networks[1]},
            {'device': router2, 'name': 'eth2', 'ip_address': '192.168.3.1', 'network': internal_networks[2]},
            {'device': router2, 'name': 'eth3', 'ip_address': '10.99.0.2', 'network': management_network},
        ]
        
        # Create router interfaces
        for interface_data in interfaces:
            interface = Interface.objects.create(**interface_data)
            self.stdout.write(f'  Created interface: {interface.device.name} - {interface.name} ({interface.ip_address})')
        
        # -------- Firewall --------
        firewall1 = Device.objects.get(name='firewall1')
        
        # Create firewall interfaces
        firewall_interfaces = [
            {'device': firewall1, 'name': 'eth0', 'ip_address': '10.0.0.3', 'network': core_network},
            {'device': firewall1, 'name': 'eth1', 'ip_address': '172.16.0.2', 'network': dmz_network},
            {'device': firewall1, 'name': 'eth2', 'ip_address': '10.99.0.3', 'network': management_network},
        ]
        
        for interface_data in firewall_interfaces:
            interface = Interface.objects.create(**interface_data)
            self.stdout.write(f'  Created interface: {interface.device.name} - {interface.name} ({interface.ip_address})')
        
        # -------- Switches --------
        switch1 = Device.objects.get(name='switch1')
        switch2 = Device.objects.get(name='switch2')
        
        # Create switch interfaces
        switch_interfaces = [
            {'device': switch1, 'name': 'eth0', 'ip_address': '192.168.1.2', 'network': internal_networks[0]},
            {'device': switch1, 'name': 'eth1', 'ip_address': '10.99.0.11', 'network': management_network},
            
            {'device': switch2, 'name': 'eth0', 'ip_address': '192.168.2.2', 'network': internal_networks[1]},
            {'device': switch2, 'name': 'eth1', 'ip_address': '192.168.3.2', 'network': internal_networks[2]},
            {'device': switch2, 'name': 'eth2', 'ip_address': '10.99.0.12', 'network': management_network},
        ]
        
        for interface_data in switch_interfaces:
            interface = Interface.objects.create(**interface_data)
            self.stdout.write(f'  Created interface: {interface.device.name} - {interface.name} ({interface.ip_address})')
        
        # -------- Servers --------
        server1 = Device.objects.get(name='server1')
        server2 = Device.objects.get(name='server2')
        
        # Create server interfaces
        server_interfaces = [
            {'device': server1, 'name': 'eth0', 'ip_address': '172.16.0.100', 'network': dmz_network},
            {'device': server1, 'name': 'eth1', 'ip_address': '10.99.0.101', 'network': management_network},
            
            {'device': server2, 'name': 'eth0', 'ip_address': '192.168.3.100', 'network': internal_networks[2]},
            {'device': server2, 'name': 'eth1', 'ip_address': '10.99.0.102', 'network': management_network},
        ]
        
        for interface_data in server_interfaces:
            interface = Interface.objects.create(**interface_data)
            self.stdout.write(f'  Created interface: {interface.device.name} - {interface.name} ({interface.ip_address})')
            
        # Add some multiple IPs on the same interface examples
        additional_ips = [
            {'device': server1, 'name': 'eth0:1', 'ip_address': '172.16.0.101', 'network': dmz_network},
            {'device': server1, 'name': 'eth0:2', 'ip_address': '172.16.0.102', 'network': dmz_network},
            {'device': server2, 'name': 'eth0:1', 'ip_address': '192.168.3.101', 'network': internal_networks[2]},
        ]
        
        for interface_data in additional_ips:
            interface = Interface.objects.create(**interface_data)
            self.stdout.write(f'  Created additional IP: {interface.device.name} - {interface.name} ({interface.ip_address})')
    
    def create_routes(self):
        """Create sample routes"""
        self.stdout.write('Creating routes...')
        
        # Get devices
        router1 = Device.objects.get(name='router1')
        router2 = Device.objects.get(name='router2')
        firewall1 = Device.objects.get(name='firewall1')
        switch1 = Device.objects.get(name='switch1')
        switch2 = Device.objects.get(name='switch2')
        server1 = Device.objects.get(name='server1')
        server2 = Device.objects.get(name='server2')
        
        # Create connected routes for each device based on their interfaces
        for device in Device.objects.all():
            for interface in device.interfaces.all():
                route_data = {
                    'source_device': device,
                    'destination_network': interface.network,
                    'type': 'connected',
                    'metric': 0
                }
                route = Route.objects.create(**route_data)
                self.stdout.write(f'  Created connected route: {route}')
        
        # Create static routes
        static_routes = [
            # Router 1 default route to Internet
            {'source_device': router1, 'destination_network': '0.0.0.0/0', 'gateway_ip': '203.0.113.254', 'type': 'static', 'metric': 1},
            
            # Router 2 routes
            {'source_device': router2, 'destination_network': '0.0.0.0/0', 'gateway_ip': '10.0.0.1', 'type': 'static', 'metric': 1},
            # {'source_device': router2, 'destination_network': '172.16.0.0/24', 'gateway_ip': '10.0.0.1', 'type': 'static', 'metric': 5},
            
            # Firewall routes
            {'source_device': firewall1, 'destination_network': '0.0.0.0/0', 'gateway_ip': '10.0.0.1', 'type': 'static', 'metric': 1},
            {'source_device': firewall1, 'destination_network': '192.168.1.0/24', 'gateway_ip': '10.0.0.1', 'type': 'static', 'metric': 5},
            {'source_device': firewall1, 'destination_network': '192.168.2.0/24', 'gateway_ip': '10.0.0.2', 'type': 'static', 'metric': 5},
            {'source_device': firewall1, 'destination_network': '192.168.3.0/24', 'gateway_ip': '10.0.0.2', 'type': 'static', 'metric': 5},
            
            # Switch routes
            {'source_device': switch1, 'destination_network': '0.0.0.0/0', 'gateway_ip': '192.168.1.1', 'type': 'static', 'metric': 1},
            {'source_device': switch2, 'destination_network': '0.0.0.0/0', 'gateway_ip': '192.168.2.1', 'type': 'static', 'metric': 1},
            
            # Server routes
            {'source_device': server1, 'destination_network': '0.0.0.0/0', 'gateway_ip': '172.16.0.2', 'type': 'static', 'metric': 1},
            {'source_device': server2, 'destination_network': '0.0.0.0/0', 'gateway_ip': '192.168.3.1', 'type': 'static', 'metric': 1},
        ]
        
        for route_data in static_routes:
            route = Route.objects.create(**route_data)
            self.stdout.write(f'  Created static route: {route}')
        
        # Create some dynamic routes (simulating dynamic protocols)
        dynamic_routes = [
            # OSPF routes on router1
            {'source_device': router1, 'destination_network': '192.168.2.0/24', 'gateway_ip': '10.0.0.2', 'type': 'ospf', 'metric': 20},
            {'source_device': router1, 'destination_network': '192.168.3.0/24', 'gateway_ip': '10.0.0.2', 'type': 'ospf', 'metric': 30},
            
            # OSPF routes on router2
            {'source_device': router2, 'destination_network': '172.16.0.0/24', 'gateway_ip': '10.0.0.1', 'type': 'ospf', 'metric': 20},
            {'source_device': router2, 'destination_network': '203.0.113.0/24', 'gateway_ip': '10.0.0.1', 'type': 'ospf', 'metric': 30},
            
            # BGP routes on router1 (external networks)
            {'source_device': router1, 'destination_network': '8.8.8.0/24', 'gateway_ip': '203.0.113.254', 'type': 'bgp', 'metric': 100},
            {'source_device': router1, 'destination_network': '1.1.1.0/24', 'gateway_ip': '203.0.113.254', 'type': 'bgp', 'metric': 100},
        ]
        
        for route_data in dynamic_routes:
            route = Route.objects.create(**route_data)
            self.stdout.write(f'  Created dynamic route: {route}')
    
    def create_nat_mappings(self):
        """Create sample NAT mappings"""
        self.stdout.write('Creating NAT mappings...')
        
        # Get devices
        router1 = Device.objects.get(name='router1')
        firewall1 = Device.objects.get(name='firewall1')
        
        # Create NAT mappings
        nat_mappings = [
            # Source NAT on router1 (internal to internet)
            {'device': router1, 'logical_ip_or_network': '192.168.1.0/24', 'real_ip_or_network': '203.0.113.100', 
             'type': 'source', 'description': 'Internal network 1 to internet'},
            {'device': router1, 'logical_ip_or_network': '192.168.2.0/24', 'real_ip_or_network': '203.0.113.100', 
             'type': 'source', 'description': 'Internal network 2 to internet'},
            {'device': router1, 'logical_ip_or_network': '192.168.3.0/24', 'real_ip_or_network': '203.0.113.100', 
             'type': 'source', 'description': 'Internal network 3 to internet'},
            
            # Destination NAT on router1 (internet to DMZ)
            {'device': router1, 'logical_ip_or_network': '203.0.113.80', 'real_ip_or_network': '172.16.0.100', 
             'type': 'destination', 'description': 'Public IP to web server'},
            {'device': router1, 'logical_ip_or_network': '203.0.113.81', 'real_ip_or_network': '172.16.0.101', 
             'type': 'destination', 'description': 'Public IP to web server secondary IP'},
            
            # Source NAT on firewall (internal to DMZ)
            {'device': firewall1, 'logical_ip_or_network': '192.168.3.100', 'real_ip_or_network': '172.16.0.200', 
             'type': 'source', 'description': 'Database server to DMZ'},
        ]
        
        for nat_data in nat_mappings:
            nat = NATMapping.objects.create(**nat_data)
            self.stdout.write(f'  Created NAT mapping: {nat}')