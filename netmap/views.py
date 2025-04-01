from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from django.core.exceptions import ValidationError

from .models import Device, Interface, Route, NATMapping
from .serializers import (
    DeviceSerializer, InterfaceSerializer, RouteSerializer, NATMappingSerializer,
    TopologySerializer, DeviceNetworksSerializer, RoutingPathSerializer
)
from .services import TopologyService, RoutingService


@login_required
def topology_view(request):
    """
    Render the topology visualization page with React
    """
    return render(request, 'netmap/topology.html')


class DeviceViewSet(viewsets.ModelViewSet):
    """CRUD API for network devices"""
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticated]


class InterfaceViewSet(viewsets.ModelViewSet):
    """CRUD API for network interfaces"""
    queryset = Interface.objects.all()
    serializer_class = InterfaceSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['device', 'name', 'status']


class RouteViewSet(viewsets.ModelViewSet):
    """CRUD API for routes"""
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['source_device', 'type']


class NATMappingViewSet(viewsets.ModelViewSet):
    """CRUD API for NAT mappings"""
    queryset = NATMapping.objects.all()
    serializer_class = NATMappingSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['device', 'type']


class TopologyView(APIView):
    """API for network topology data"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Get network topology data.
        
        Query parameters:
            - include_stub_networks: Boolean (default: false)
        """
        include_stub_networks = request.query_params.get('include_stub_networks', '').lower() == 'true'
        
        topology_data = TopologyService.generate_topology(include_stub_networks=include_stub_networks)
        serializer = TopologySerializer(topology_data)
        
        return Response(serializer.data)


class DeviceNetworksView(APIView):
    """API for getting networks connected to a specific device"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, device_id):
        """
        Get all networks connected to a specific device.
        
        Query parameters:
            - include_stub_networks: Boolean (default: true)
        """
        try:
            include_stub_networks = request.query_params.get('include_stub_networks', 'true').lower() == 'true'
            
            networks = TopologyService.get_device_networks(
                device_id=device_id, 
                include_stub_networks=include_stub_networks
            )
            
            serializer = DeviceNetworksSerializer(networks, many=True)
            return Response(serializer.data)
            
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Device.DoesNotExist:
            return Response({'error': f'Device with ID {device_id} not found'}, 
                          status=status.HTTP_404_NOT_FOUND)


class ConnectionDetailsView(APIView):
    """API for getting details about a connection between devices"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Get details about a connection between devices.
        
        Query parameters:
            - device1_id: ID of the first device
            - device2_id: ID of the second device
            OR
            - network: Network CIDR (e.g., '192.168.1.0/24')
        """
        device1_id = request.query_params.get('device1_id')
        device2_id = request.query_params.get('device2_id')
        network = request.query_params.get('network')
        
        if network:
            # Find all devices with interfaces on this network
            interfaces = Interface.objects.filter(network=network, status='up')
            
            if not interfaces:
                return Response({'error': f'No interfaces found on network {network}'},
                              status=status.HTTP_404_NOT_FOUND)
                
            # Group interfaces by device
            devices = {}
            for interface in interfaces:
                if interface.device_id not in devices:
                    devices[interface.device_id] = {
                        'device_id': interface.device_id,
                        'device_name': interface.device.name,
                        'interfaces': []
                    }
                
                devices[interface.device_id]['interfaces'].append({
                    'interface_id': interface.id,
                    'name': interface.name,
                    'ip_address': interface.ip_address
                })
            
            # Find routes that use these interfaces as gateways
            routes = []
            for interface in interfaces:
                related_routes = Route.objects.filter(gateway_ip=interface.ip_address)
                
                for route in related_routes:
                    routes.append({
                        'route_id': route.id,
                        'source_device': route.source_device.name,
                        'destination_network': route.destination_network,
                        'gateway_ip': route.gateway_ip,
                        'type': route.type,
                        'metric': route.metric
                    })
            
            return Response({
                'network': network,
                'devices': list(devices.values()),
                'routes_through_connection': routes
            })
            
        elif device1_id and device2_id:
            # Find networks shared by both devices
            try:
                interfaces1 = Interface.objects.filter(device_id=device1_id, status='up')
                interfaces2 = Interface.objects.filter(device_id=device2_id, status='up')
                
                if not interfaces1:
                    return Response({'error': f'No interfaces found for device ID {device1_id}'},
                                  status=status.HTTP_404_NOT_FOUND)
                                  
                if not interfaces2:
                    return Response({'error': f'No interfaces found for device ID {device2_id}'},
                                  status=status.HTTP_404_NOT_FOUND)
                
                # Find common networks
                networks1 = set(i.network for i in interfaces1)
                networks2 = set(i.network for i in interfaces2)
                common_networks = networks1.intersection(networks2)
                
                if not common_networks:
                    return Response({'error': f'No shared networks found between devices {device1_id} and {device2_id}'},
                                  status=status.HTTP_404_NOT_FOUND)
                
                # For each common network, collect details
                connections = []
                for network in common_networks:
                    # Get interfaces on this network for each device
                    interfaces1_on_net = interfaces1.filter(network=network)
                    interfaces2_on_net = interfaces2.filter(network=network)
                    
                    # Find routes that use these interfaces as gateways
                    routes = []
                    for interface in list(interfaces1_on_net) + list(interfaces2_on_net):
                        related_routes = Route.objects.filter(gateway_ip=interface.ip_address)
                        
                        for route in related_routes:
                            routes.append({
                                'route_id': route.id,
                                'source_device': route.source_device.name,
                                'destination_network': route.destination_network,
                                'gateway_ip': route.gateway_ip,
                                'type': route.type,
                                'metric': route.metric
                            })
                    
                    connections.append({
                        'network': network,
                        'device1_interfaces': [{
                            'interface_id': i.id,
                            'name': i.name,
                            'ip_address': i.ip_address
                        } for i in interfaces1_on_net],
                        'device2_interfaces': [{
                            'interface_id': i.id,
                            'name': i.name,
                            'ip_address': i.ip_address
                        } for i in interfaces2_on_net],
                        'routes_through_connection': routes
                    })
                
                return Response({
                    'device1_id': device1_id,
                    'device2_id': device2_id,
                    'connections': connections
                })
                
            except Device.DoesNotExist:
                return Response({'error': 'One or both devices not found'}, 
                              status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({
                'error': 'Missing required parameters. Either provide network or both device1_id and device2_id'
            }, status=status.HTTP_400_BAD_REQUEST)


class RoutingPathView(APIView):
    """API for calculating the routing path between source and destination"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Calculate the routing path between source and destination.
        
        Query parameters:
            - source: Source IP or network in CIDR notation
            - destination: Destination IP or network in CIDR notation
        """
        source = request.query_params.get('source')
        destination = request.query_params.get('destination')
        
        if not source or not destination:
            error_response = {
                'status': 'error',
                'message': 'Both source and destination parameters are required',
                'source': source or '',
                'destination': destination or '',
                'path': [],
                'nat_applied': {'source': False, 'destination': False}
            }
            serializer = RoutingPathSerializer(error_response)
            return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            result = RoutingService.find_route_path(source, destination)
            
            # Ensure all expected fields are present in the result
            if 'path' not in result:
                result['path'] = []
            if 'nat_applied' not in result:
                result['nat_applied'] = {'source': False, 'destination': False}
                
            serializer = RoutingPathSerializer(result)
            
            if result['status'] == 'error':
                return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)
                
            return Response(serializer.data)
        except ValidationError as e:
            error_response = {
                'status': 'error',
                'message': str(e),
                'source': source,
                'destination': destination,
                'path': [],
                'nat_applied': {'source': False, 'destination': False}
            }
            serializer = RoutingPathSerializer(error_response)
            return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)