from django.test import TestCase
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient
from .models import Device, Interface, Route, NATMapping
from .services import TopologyService, RoutingService, NetworkDataIngestionService


class ModelValidationTests(TestCase):
    """Test model validation"""
    
    def test_interface_ip_in_network(self):
        """Test that an interface IP must be within the specified network"""
        # Create a device
        device = Device.objects.create(name='router1')
        
        # Create a valid interface
        valid_interface = Interface(
            device=device,
            name='eth0',
            ip_address='192.168.1.1',
            network='192.168.1.0/24',
            status='up'
        )
        valid_interface.full_clean()  # Should not raise an error
        valid_interface.save()
        
        # Try to create an invalid interface
        invalid_interface = Interface(
            device=device,
            name='eth1',
            ip_address='10.0.0.1',  # IP not in network
            network='192.168.1.0/24',
            status='up'
        )
        
        # Should raise a validation error
        with self.assertRaises(ValidationError):
            invalid_interface.full_clean()
    
    def test_route_validation(self):
        """Test route validation logic"""
        # Create a device
        device = Device.objects.create(name='router1')
        
        # Create a valid connected route
        valid_connected = Route(
            source_device=device,
            destination_network='192.168.1.0/24',
            type='connected',
            gateway_ip=None,
            metric=0
        )
        valid_connected.full_clean()  # Should not raise an error
        valid_connected.save()
        
        # Create a valid static route
        valid_static = Route(
            source_device=device,
            destination_network='10.0.0.0/24',
            type='static',
            gateway_ip='192.168.1.254',
            metric=1
        )
        valid_static.full_clean()  # Should not raise an error
        valid_static.save()
        
        # Try to create an invalid connected route with gateway
        invalid_connected = Route(
            source_device=device,
            destination_network='172.16.0.0/24',
            type='connected',
            gateway_ip='192.168.1.254',  # Connected routes shouldn't have gateway
            metric=0
        )
        
        # Should raise a validation error
        with self.assertRaises(ValidationError):
            invalid_connected.full_clean()
            
        # Try to create an invalid static route without gateway
        invalid_static = Route(
            source_device=device,
            destination_network='172.16.0.0/24',
            type='static',
            gateway_ip=None,  # Static routes should have gateway
            metric=1
        )
        
        # Should raise a validation error
        with self.assertRaises(ValidationError):
            invalid_static.full_clean()
    
    def test_nat_mapping_validation(self):
        """Test NAT mapping validation"""
        # Create a device
        device = Device.objects.create(name='firewall1')
        
        # Valid NAT mappings
        valid_nat1 = NATMapping(
            device=device,
            logical_ip_or_network='192.168.1.0/24',
            real_ip_or_network='10.0.0.1',
            type='source'
        )
        valid_nat1.full_clean()  # Should not raise an error
        valid_nat1.save()
        
        valid_nat2 = NATMapping(
            device=device,
            logical_ip_or_network='10.0.0.5',
            real_ip_or_network='172.16.0.5',
            type='destination'
        )
        valid_nat2.full_clean()  # Should not raise an error
        valid_nat2.save()
        
        # Try invalid formats
        invalid_nat = NATMapping(
            device=device,
            logical_ip_or_network='not-an-ip',
            real_ip_or_network='10.0.0.1',
            type='source'
        )
        
        # Should raise a validation error
        with self.assertRaises(ValidationError):
            invalid_nat.full_clean()


class TopologyServiceTests(TestCase):
    """Test the TopologyService"""
    
    def setUp(self):
        """Set up test data"""
        # Create devices
        self.router1 = Device.objects.create(name='router1')
        self.router2 = Device.objects.create(name='router2')
        self.server1 = Device.objects.create(name='server1')
        
        # Create interfaces - shared network between routers
        Interface.objects.create(
            device=self.router1,
            name='eth0',
            ip_address='10.0.0.1',
            network='10.0.0.0/24',
            status='up'
        )
        
        Interface.objects.create(
            device=self.router2,
            name='eth0',
            ip_address='10.0.0.2',
            network='10.0.0.0/24',
            status='up'
        )
        
        # Create interface - stub network on router1
        Interface.objects.create(
            device=self.router1,
            name='eth1',
            ip_address='192.168.1.1',
            network='192.168.1.0/24',
            status='up'
        )
        
        # Create interface - stub network on router2 with server
        Interface.objects.create(
            device=self.router2,
            name='eth1',
            ip_address='192.168.2.1',
            network='192.168.2.0/24',
            status='up'
        )
        
        Interface.objects.create(
            device=self.server1,
            name='eth0',
            ip_address='192.168.2.10',
            network='192.168.2.0/24',
            status='up'
        )
        
        # Create a down interface - should not be included in topology
        Interface.objects.create(
            device=self.router1,
            name='eth2',
            ip_address='172.16.0.1',
            network='172.16.0.0/24',
            status='down'
        )
    
    def test_generate_topology(self):
        """Test generating the topology"""
        # Generate topology without stub networks
        topology = TopologyService.generate_topology(include_stub_networks=False)
        
        # Verify the expected structure
        self.assertIn('nodes', topology)
        self.assertIn('edges', topology)
        
        # Should have 3 nodes (all devices)
        self.assertEqual(len(topology['nodes']), 3)
        
        # Should have 1 edge (router1-router2)
        self.assertEqual(len(topology['edges']), 1)
        
        # Generate topology with stub networks
        topology_with_stubs = TopologyService.generate_topology(include_stub_networks=True)
        
        # Should still have 3 nodes
        self.assertEqual(len(topology_with_stubs['nodes']), 3)
        
        # Should have 3 edges now (router1-router2, router1-stub, router2-server1)
        # Note: exact count depends on how stub networks are represented in the implementation
        self.assertGreater(len(topology_with_stubs['edges']), 1)
    
    def test_get_device_networks(self):
        """Test getting networks for a specific device"""
        # Get router1 networks
        networks = TopologyService.get_device_networks(device_id=self.router1.id)
        
        # Should have 2 networks (10.0.0.0/24 and 192.168.1.0/24)
        self.assertEqual(len(networks), 2)
        
        # Get router1 networks without stub networks
        networks = TopologyService.get_device_networks(
            device_id=self.router1.id, 
            include_stub_networks=False
        )
        
        # Should have 1 network (10.0.0.0/24) as 192.168.1.0/24 is a stub
        self.assertEqual(len(networks), 1)
        self.assertEqual(networks[0]['network'], '10.0.0.0/24')


class RoutingServiceTests(TestCase):
    """Test the RoutingService"""
    
    def setUp(self):
        """Set up test data"""
        # Create devices
        self.router1 = Device.objects.create(name='router1')
        self.router2 = Device.objects.create(name='router2')
        self.router3 = Device.objects.create(name='router3')
        self.server1 = Device.objects.create(name='server1')
        
        # Create interfaces
        # Router 1
        self.r1_if1 = Interface.objects.create(
            device=self.router1,
            name='eth0',
            ip_address='10.0.0.1',
            network='10.0.0.0/24',  # Link to router2
            status='up'
        )
        
        self.r1_if2 = Interface.objects.create(
            device=self.router1,
            name='eth1',
            ip_address='192.168.1.1',
            network='192.168.1.0/24',  # Link to LAN
            status='up'
        )
        
        # Router 2
        self.r2_if1 = Interface.objects.create(
            device=self.router2,
            name='eth0',
            ip_address='10.0.0.2',
            network='10.0.0.0/24',  # Link to router1
            status='up'
        )
        
        self.r2_if2 = Interface.objects.create(
            device=self.router2,
            name='eth1',
            ip_address='10.1.0.1',
            network='10.1.0.0/24',  # Link to router3
            status='up'
        )
        
        # Router 3
        self.r3_if1 = Interface.objects.create(
            device=self.router3,
            name='eth0',
            ip_address='10.1.0.2',
            network='10.1.0.0/24',  # Link to router2
            status='up'
        )
        
        self.r3_if2 = Interface.objects.create(
            device=self.router3,
            name='eth1',
            ip_address='172.16.0.1',
            network='172.16.0.0/24',  # Link to server
            status='up'
        )
        
        # Server
        self.server_if = Interface.objects.create(
            device=self.server1,
            name='eth0',
            ip_address='172.16.0.10',
            network='172.16.0.0/24',
            status='up'
        )
        
        # Create routes
        # Connected routes
        for device in [self.router1, self.router2, self.router3, self.server1]:
            for interface in device.interfaces.all():
                Route.objects.create(
                    source_device=device,
                    destination_network=interface.network,
                    type='connected'
                )
        
        # Static routes - Router1
        Route.objects.create(
            source_device=self.router1,
            destination_network='10.1.0.0/24',
            type='static',
            gateway_ip='10.0.0.2',
            metric=10
        )
        
        Route.objects.create(
            source_device=self.router1,
            destination_network='172.16.0.0/24',
            type='static',
            gateway_ip='10.0.0.2',
            metric=20
        )
        
        # Static routes - Router2
        Route.objects.create(
            source_device=self.router2,
            destination_network='192.168.1.0/24',
            type='static',
            gateway_ip='10.0.0.1',
            metric=10
        )
        
        Route.objects.create(
            source_device=self.router2,
            destination_network='172.16.0.0/24',
            type='static',
            gateway_ip='10.1.0.2',
            metric=10
        )
        
        # Static routes - Router3
        Route.objects.create(
            source_device=self.router3,
            destination_network='10.0.0.0/24',
            type='static',
            gateway_ip='10.1.0.1',
            metric=10
        )
        
        Route.objects.create(
            source_device=self.router3,
            destination_network='192.168.1.0/24',
            type='static',
            gateway_ip='10.1.0.1',
            metric=20
        )
        
        # Default routes - Server
        Route.objects.create(
            source_device=self.server1,
            destination_network='0.0.0.0/0',
            type='static',
            gateway_ip='172.16.0.1',
            metric=1
        )
        
        # Create NAT mappings
        NATMapping.objects.create(
            device=self.router1,
            logical_ip_or_network='192.168.1.0/24',
            real_ip_or_network='100.64.0.1',
            type='source',
            description='LAN to Internet'
        )
        
        NATMapping.objects.create(
            device=self.router3,
            logical_ip_or_network='200.1.1.1',
            real_ip_or_network='172.16.0.10',
            type='destination',
            description='Public to Server'
        )
    
    def test_find_matching_networks(self):
        """Test finding matching networks for an IP or network"""
        # Test with an IP
        matches = RoutingService.find_matching_networks('10.0.0.5')
        
        # Should find the 10.0.0.0/24 network
        self.assertEqual(len(matches), 2)  # One match per interface on the network
        self.assertEqual(matches[0]['network'], '10.0.0.0/24')
        
        # Test with a network
        matches = RoutingService.find_matching_networks('192.168.1.0/24')
        
        # Should find the exact match
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]['relationship'], 'exact')
        
        # Test with a non-existent IP
        matches = RoutingService.find_matching_networks('8.8.8.8')
        
        # Should not find any matches
        self.assertEqual(len(matches), 0)
    
    def test_check_supernet_conflicts(self):
        """Test checking for supernet conflicts"""
        # Test with a supernet of an existing network
        conflicts = RoutingService.check_supernet_conflicts('10.0.0.0/16')
        
        # Should find conflicts with 10.0.0.0/24 and 10.1.0.0/24
        self.assertGreaterEqual(len(conflicts), 2)
        
        # Test with an exact match (should not conflict)
        conflicts = RoutingService.check_supernet_conflicts('10.0.0.0/24')
        
        # Should not find conflicts
        self.assertEqual(len(conflicts), 0)
        
        # Test with a subnet (should not conflict)
        conflicts = RoutingService.check_supernet_conflicts('10.0.0.0/25')
        
        # Should not find conflicts
        self.assertEqual(len(conflicts), 0)
    
    def test_find_nat_mapping(self):
        """Test finding NAT mappings"""
        # Test source NAT
        nat = RoutingService.find_nat_mapping(
            device_id=self.router1.id,
            ip_or_network='192.168.1.5',
            nat_type='source'
        )
        
        # Should find the mapping
        self.assertIsNotNone(nat)
        self.assertEqual(nat['type'], 'source')
        
        # Test destination NAT
        nat = RoutingService.find_nat_mapping(
            device_id=self.router3.id,
            ip_or_network='200.1.1.1',
            nat_type='destination'
        )
        
        # Should find the mapping
        self.assertIsNotNone(nat)
        self.assertEqual(nat['type'], 'destination')
        
        # Test non-existent NAT
        nat = RoutingService.find_nat_mapping(
            device_id=self.router2.id,
            ip_or_network='192.168.1.5',
            nat_type='source'
        )
        
        # Should not find a mapping
        self.assertIsNone(nat)
    
    def test_find_route_path(self):
        """Test finding routing paths"""
        # Test direct path on same device
        result = RoutingService.find_route_path(
            source_ip_or_network='192.168.1.5',
            destination_ip_or_network='192.168.1.10'
        )
        
        # Should succeed with a direct path
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['path']), 1)  # Just one hop (same device)
        
        # Test multi-hop path
        result = RoutingService.find_route_path(
            source_ip_or_network='192.168.1.5',
            destination_ip_or_network='172.16.0.10'
        )
        
        # Should succeed with a path from router1 to router3 via router2
        self.assertEqual(result['status'], 'success')
        self.assertGreaterEqual(len(result['path']), 3)  # At least 3 hops
        
        # Test path with source NAT
        result = RoutingService.find_route_path(
            source_ip_or_network='192.168.1.5',
            destination_ip_or_network='8.8.8.8'
        )
        
        # Should handle source NAT
        self.assertEqual(result['nat_applied']['source'], True)
        
        # Test path with destination NAT
        result = RoutingService.find_route_path(
            source_ip_or_network='192.168.1.5',
            destination_ip_or_network='200.1.1.1'
        )
        
        # Should handle destination NAT
        self.assertEqual(result['nat_applied']['destination'], True)
        
        # Test supernet conflict
        result = RoutingService.find_route_path(
            source_ip_or_network='10.0.0.0/8',
            destination_ip_or_network='172.16.0.10'
        )
        
        # Should fail due to supernet conflict
        self.assertEqual(result['status'], 'error')
        self.assertIn('conflicts', result)
        
        # Test non-existent destination
        result = RoutingService.find_route_path(
            source_ip_or_network='192.168.1.5',
            destination_ip_or_network='8.8.4.4'
        )
        
        # Should fail with an error
        self.assertEqual(result['status'], 'error')
        self.assertIn('message', result)


class APITests(TestCase):
    """Test the API endpoints"""
    
    def setUp(self):
        """Set up test data and client"""
        # Create a test user for authentication
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        
        # Set up the API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create some sample data
        self.device1 = Device.objects.create(name='router1', description='Test Router 1')
        self.device2 = Device.objects.create(name='router2', description='Test Router 2')
        
        self.interface1 = Interface.objects.create(
            device=self.device1,
            name='eth0',
            ip_address='192.168.1.1',
            network='192.168.1.0/24',
            status='up'
        )
        
        self.interface2 = Interface.objects.create(
            device=self.device2,
            name='eth0',
            ip_address='192.168.1.2',
            network='192.168.1.0/24',
            status='up'
        )
    
    def test_device_api(self):
        """Test device API endpoints"""
        # Get all devices
        response = self.client.get('/api/netmap/devices/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        
        # Get a specific device
        response = self.client.get(f'/api/netmap/devices/{self.device1.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'router1')
        
        # Create a new device
        new_device_data = {
            'name': 'switch1',
            'description': 'Test Switch 1'
        }
        response = self.client.post('/api/netmap/devices/', new_device_data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Device.objects.count(), 3)
    
    def test_topology_api(self):
        """Test topology API endpoint"""
        # Get topology
        response = self.client.get('/api/netmap/topology/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('nodes', response.data)
        self.assertIn('edges', response.data)
        
        # Get topology with stub networks
        response = self.client.get('/api/netmap/topology/?include_stub_networks=true')
        self.assertEqual(response.status_code, 200)
    
    def test_device_networks_api(self):
        """Test device networks API endpoint"""
        # Get networks for a device
        response = self.client.get(f'/api/netmap/devices/{self.device1.id}/networks/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['network'], '192.168.1.0/24')
    
    def test_routing_path_api(self):
        """Test routing path API endpoint"""
        # Create routes for testing
        Route.objects.create(
            source_device=self.device1,
            destination_network='192.168.1.0/24',
            type='connected'
        )
        
        Route.objects.create(
            source_device=self.device2,
            destination_network='192.168.1.0/24',
            type='connected'
        )
        
        # Test valid routing path
        response = self.client.get('/api/netmap/routing-path/', {
            'source': '192.168.1.10',
            'destination': '192.168.1.20'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'success')
        
        # Test missing parameters
        response = self.client.get('/api/netmap/routing-path/', {
            'source': '192.168.1.10'
        })
        self.assertEqual(response.status_code, 400)
        
        # Test invalid source/destination
        response = self.client.get('/api/netmap/routing-path/', {
            'source': '192.168.1.10',
            'destination': '10.0.0.1'  # Non-existent network
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['status'], 'error')