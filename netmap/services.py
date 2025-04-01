"""
This module contains services for data ingestion, topology calculation,
and routing path finding for the netmap application.
"""
import ipaddress
from typing import Dict, List, Tuple, Optional, Set, Any, Union
from django.db.models import Q
from django.core.exceptions import ValidationError

from .models import Device, Interface, Route, NATMapping


class NetworkDataIngestionService:
    """
    Service for ingesting network data (interfaces, routes, NAT) into the system.
    """
    
    @staticmethod
    def ingest_interface_data(device_name: str, interface_name: str, 
                             ip_address: str, network: str, status: str = 'up') -> Interface:
        """
        Ingest interface data, validating and adding it to the database.
        
        Args:
            device_name: Name of the device the interface belongs to
            interface_name: Name of the interface (e.g., eth0)
            ip_address: IP address assigned to the interface
            network: Network in CIDR notation (e.g., 192.168.1.0/24)
            status: Status of the interface ('up' or 'down')
            
        Returns:
            The created or updated Interface object
            
        Raises:
            ValidationError: If the IP address is not within the specified network
        """
        # Validate IP is within network
        try:
            ip = ipaddress.ip_address(ip_address)
            net = ipaddress.ip_network(network, strict=False)
            
            if ip not in net:
                raise ValidationError(f"IP address {ip_address} is not within network {network}")
        except ValueError as e:
            raise ValidationError(f"Invalid IP or network format: {str(e)}")
        
        # Get or create device
        device, _ = Device.objects.get_or_create(name=device_name)
        
        # Get or create/update interface
        interface, created = Interface.objects.update_or_create(
            device=device,
            name=interface_name,
            ip_address=ip_address,
            defaults={
                'network': network,
                'status': status
            }
        )
        
        return interface
    
    @staticmethod
    def ingest_route_data(device_name: str, destination_network: str, 
                         gateway_ip: Optional[str] = None, route_type: str = 'static',
                         metric: int = 0) -> Route:
        """
        Ingest routing data, validating and adding it to the database.
        
        Args:
            device_name: Name of the device the route belongs to
            destination_network: Destination network in CIDR notation
            gateway_ip: Next hop gateway IP address (can be None for connected routes)
            route_type: Type of route ('static', 'ospf', 'bgp', etc.)
            metric: Routing metric/cost
            
        Returns:
            The created or updated Route object
        """
        # Get or create device
        device, _ = Device.objects.get_or_create(name=device_name)
        
        # Create or update route
        route, created = Route.objects.update_or_create(
            source_device=device,
            destination_network=destination_network,
            gateway_ip=gateway_ip,
            defaults={
                'type': route_type,
                'metric': metric
            }
        )
        
        return route
    
    @staticmethod
    def ingest_nat_mapping(device_name: str, logical_ip_or_network: str,
                          real_ip_or_network: str, nat_type: str,
                          description: str = '') -> NATMapping:
        """
        Ingest NAT mapping data, validating and adding it to the database.
        
        Args:
            device_name: Name of the device performing NAT
            logical_ip_or_network: Original IP or network (before NAT)
            real_ip_or_network: Translated IP or network (after NAT)
            nat_type: Type of NAT ('source' or 'destination')
            description: Optional description of the NAT mapping
            
        Returns:
            The created or updated NATMapping object
        """
        # Get or create device
        device, _ = Device.objects.get_or_create(name=device_name)
        
        # Create or update NAT mapping
        nat_mapping, created = NATMapping.objects.update_or_create(
            device=device,
            logical_ip_or_network=logical_ip_or_network,
            real_ip_or_network=real_ip_or_network,
            defaults={
                'type': nat_type,
                'description': description
            }
        )
        
        return nat_mapping


class TopologyService:
    """
    Service for generating network topology data.
    """
    
    @staticmethod
    def generate_topology(include_stub_networks: bool = False) -> Dict[str, List[Any]]:
        """
        Generate network topology data as a collection of nodes and edges.
        
        Args:
            include_stub_networks: Whether to include networks that are connected to only one device
            
        Returns:
            A dictionary with 'nodes' and 'edges' lists
        """
        # Get all devices and active interfaces
        devices = Device.objects.all()
        interfaces = Interface.objects.filter(status='up')
        
        # Prepare nodes (devices)
        nodes = []
        for device in devices:
            nodes.append({
                'id': device.id,
                'label': device.name,
                'interfaces_count': device.interfaces.count()
            })
        
        # Find common networks between devices to create edges
        networks_by_device = {}
        for interface in interfaces:
            if interface.device_id not in networks_by_device:
                networks_by_device[interface.device_id] = {}
            
            if interface.network not in networks_by_device[interface.device_id]:
                networks_by_device[interface.device_id][interface.network] = []
            
            networks_by_device[interface.device_id][interface.network].append({
                'interface_id': interface.id,
                'name': interface.name,
                'ip_address': interface.ip_address
            })
        
        # Create edges based on shared networks
        edges = []
        processed_networks = set()
        
        for device_id, networks in networks_by_device.items():
            device = next((d for d in nodes if d['id'] == device_id), None)
            
            for network, interfaces in networks.items():
                if network in processed_networks:
                    continue
                
                # Find all devices on this network
                devices_on_network = []
                for d_id, d_networks in networks_by_device.items():
                    if network in d_networks:
                        devices_on_network.append(d_id)
                
                if len(devices_on_network) > 1 or include_stub_networks:
                    # For non-stub networks or if explicitly including stub networks
                    for i, src_device_id in enumerate(devices_on_network):
                        src_device = next((d for d in nodes if d['id'] == src_device_id), None)
                        
                        # Connect each device to all other devices on this network
                        for dst_device_id in devices_on_network[i+1:]:
                            dst_device = next((d for d in nodes if d['id'] == dst_device_id), None)
                            
                            # Create an edge between these two devices
                            edges.append({
                                'source': src_device_id,
                                'target': dst_device_id,
                                'network': network,
                                'source_label': src_device['label'] if src_device else f"Device {src_device_id}",
                                'target_label': dst_device['label'] if dst_device else f"Device {dst_device_id}"
                            })
                
                processed_networks.add(network)
        
        return {
            'nodes': nodes,
            'edges': edges
        }
    
    @staticmethod
    def get_device_networks(device_id: int, include_stub_networks: bool = True) -> List[Dict[str, Any]]:
        """
        Get all networks connected to a specific device.
        
        Args:
            device_id: ID of the device
            include_stub_networks: Whether to include networks that are connected to only this device
            
        Returns:
            A list of networks with their associated interfaces
        """
        try:
            device = Device.objects.get(pk=device_id)
        except Device.DoesNotExist:
            raise ValidationError(f"Device with ID {device_id} does not exist")
        
        # Get all active interfaces for this device
        interfaces = Interface.objects.filter(device=device, status='up')
        
        # Group interfaces by network
        networks = {}
        for interface in interfaces:
            if interface.network not in networks:
                networks[interface.network] = []
            
            networks[interface.network].append({
                'interface_id': interface.id,
                'name': interface.name,
                'ip_address': interface.ip_address
            })
        
        # If we're not including stub networks, we need to check which networks are connected to other devices
        if not include_stub_networks:
            non_stub_networks = set()
            all_interfaces = Interface.objects.filter(status='up').exclude(device=device)
            
            for interface in all_interfaces:
                if interface.network in networks:
                    non_stub_networks.add(interface.network)
            
            # Filter networks to only include non-stub ones
            networks = {network: interfaces for network, interfaces in networks.items() 
                      if network in non_stub_networks}
        
        # Convert to list format for API
        result = []
        for network, interfaces in networks.items():
            result.append({
                'network': network,
                'interfaces': interfaces
            })
        
        return result


class RoutingService:
    """
    Service for performing routing lookups and path calculations.
    """
    
    @staticmethod
    def find_matching_networks(ip_or_network: str) -> List[Dict[str, Any]]:
        """
        Find networks that match the given IP or network (exact or containing).
        
        Args:
            ip_or_network: An IP address or network in CIDR notation
            
        Returns:
            A list of matching interface objects with their networks
        """
        try:
            # Try to parse as network
            if '/' in ip_or_network:
                query_network = ipaddress.ip_network(ip_or_network, strict=False)
                is_network = True
            else:
                # Parse as IP address
                query_ip = ipaddress.ip_address(ip_or_network)
                is_network = False
        except ValueError as e:
            raise ValidationError(f"Invalid IP or network format: {str(e)}")
        
        matching_interfaces = []
        
        # Check all interfaces' networks
        for interface in Interface.objects.filter(status='up'):
            try:
                interface_network = ipaddress.ip_network(interface.network, strict=False)
                
                # Check if this interface's network matches our query
                if is_network:
                    # Case 1: Query is a network, check for overlap
                    if query_network.overlaps(interface_network):
                        matching_interfaces.append({
                            'interface_id': interface.id,
                            'device': interface.device.name,
                            'device_id': interface.device.id,
                            'interface_name': interface.name,
                            'ip_address': interface.ip_address,
                            'network': interface.network,
                            'relationship': 'exact' if query_network == interface_network else 
                                          ('supernet' if query_network.supernet_of(interface_network) else 
                                           'subnet' if interface_network.supernet_of(query_network) else 'overlap')
                        })
                else:
                    # Case 2: Query is an IP, check if it's in this network
                    if query_ip in interface_network:
                        matching_interfaces.append({
                            'interface_id': interface.id,
                            'device': interface.device.name,
                            'device_id': interface.device.id,
                            'interface_name': interface.name,
                            'ip_address': interface.ip_address,
                            'network': interface.network,
                            'relationship': 'contains_ip'
                        })
                        
                        # Check if this IP exactly matches the interface IP
                        if str(query_ip) == interface.ip_address:
                            matching_interfaces[-1]['relationship'] = 'exact_ip_match'
                    
            except ValueError:
                # Skip invalid networks
                continue
        
        return matching_interfaces
    
    @staticmethod
    def check_supernet_conflicts(ip_or_network: str) -> List[Dict[str, Any]]:
        """
        Check if the provided IP or network is a supernet of any existing networks in the database.
        
        Args:
            ip_or_network: An IP address or network in CIDR notation
            
        Returns:
            A list of conflicting networks
        """
        conflicts = []
        
        if '/' not in ip_or_network:
            # It's an IP, not a network - no supernet conflicts possible
            return conflicts
            
        try:
            query_network = ipaddress.ip_network(ip_or_network, strict=False)
        except ValueError as e:
            raise ValidationError(f"Invalid network format: {str(e)}")
            
        # Check all interfaces' networks
        for interface in Interface.objects.filter(status='up'):
            try:
                interface_network = ipaddress.ip_network(interface.network, strict=False)
                
                # Check if query network is a supernet of this interface's network
                if query_network.supernet_of(interface_network) and query_network != interface_network:
                    conflicts.append({
                        'device': interface.device.name,
                        'interface_name': interface.name,
                        'network': interface.network
                    })
            except ValueError:
                # Skip invalid networks
                continue
                
        # Also check routes
        for route in Route.objects.all():
            try:
                route_network = ipaddress.ip_network(route.destination_network, strict=False)
                
                # Check if query network is a supernet of this route's network
                if query_network.supernet_of(route_network) and query_network != route_network:
                    conflicts.append({
                        'device': route.source_device.name,
                        'route_type': route.type,
                        'network': route.destination_network
                    })
            except ValueError:
                # Skip invalid networks
                continue
                
        return conflicts
    
    @staticmethod
    def find_nat_mapping(device_id: int, ip_or_network: str, nat_type: str) -> Optional[Dict[str, Any]]:
        """
        Find NAT mapping for an IP or network on a specific device.
        
        Args:
            device_id: ID of the device to check for NAT mappings
            ip_or_network: IP or network to check for NAT
            nat_type: Type of NAT to check ('source' or 'destination')
            
        Returns:
            NAT mapping details if found, None otherwise
        """
        nat_mappings = NATMapping.objects.filter(
            device_id=device_id,
            type=nat_type
        )
        
        for nat in nat_mappings:
            try:
                # Parse logical IP/network from NAT mapping
                if '/' in nat.logical_ip_or_network:
                    logical_net = ipaddress.ip_network(nat.logical_ip_or_network, strict=False)
                    
                    # Parse query IP/network
                    if '/' in ip_or_network:
                        query_net = ipaddress.ip_network(ip_or_network, strict=False)
                        if logical_net.overlaps(query_net):
                            return {
                                'nat_id': nat.id,
                                'device': nat.device.name,
                                'logical': nat.logical_ip_or_network,
                                'real': nat.real_ip_or_network,
                                'type': nat.type
                            }
                    else:
                        query_ip = ipaddress.ip_address(ip_or_network)
                        if query_ip in logical_net:
                            # Translate the IP if needed
                            if '/' not in nat.real_ip_or_network:
                                # Both are IPs, need to calculate the offset
                                logical_base = ipaddress.ip_address(nat.logical_ip_or_network.split('/')[0])
                                real_base = ipaddress.ip_address(nat.real_ip_or_network)
                                offset = int(query_ip) - int(logical_base)
                                translated_ip = ipaddress.ip_address(int(real_base) + offset)
                                
                                return {
                                    'nat_id': nat.id,
                                    'device': nat.device.name,
                                    'logical': nat.logical_ip_or_network,
                                    'real': nat.real_ip_or_network,
                                    'type': nat.type,
                                    'translated': str(translated_ip)
                                }
                            else:
                                # Network to network translation
                                return {
                                    'nat_id': nat.id,
                                    'device': nat.device.name,
                                    'logical': nat.logical_ip_or_network,
                                    'real': nat.real_ip_or_network,
                                    'type': nat.type,
                                    'note': 'Network to network translation - specific IP translation not calculated'
                                }
                else:
                    # Logical side is a single IP
                    logical_ip = ipaddress.ip_address(nat.logical_ip_or_network)
                    
                    if '/' not in ip_or_network and ip_or_network == str(logical_ip):
                        return {
                            'nat_id': nat.id,
                            'device': nat.device.name,
                            'logical': nat.logical_ip_or_network,
                            'real': nat.real_ip_or_network,
                            'type': nat.type
                        }
            except ValueError:
                # Skip invalid entries
                continue
                
        return None
    
    @staticmethod
    def find_route_path(source_ip_or_network: str, destination_ip_or_network: str) -> Dict[str, Any]:
        """
        Find the routing path between source and destination IPs or networks.
        
        Args:
            source_ip_or_network: Source IP or network in CIDR notation
            destination_ip_or_network: Destination IP or network in CIDR notation
            
        Returns:
            A dictionary with path information and status
        """
        result = {
            'status': 'success',
            'source': source_ip_or_network,
            'destination': destination_ip_or_network,
            'path': [],
            'nat_applied': {
                'source': False,
                'destination': False
            }
        }
        
        # Step 1: Check for supernet conflicts in source and destination
        source_conflicts = RoutingService.check_supernet_conflicts(source_ip_or_network)
        if source_conflicts:
            return {
                'status': 'error',
                'message': f"Source {source_ip_or_network} conflicts with more specific networks",
                'conflicts': source_conflicts
            }
            
        dest_conflicts = RoutingService.check_supernet_conflicts(destination_ip_or_network)
        if dest_conflicts:
            return {
                'status': 'error',
                'message': f"Destination {destination_ip_or_network} conflicts with more specific networks",
                'conflicts': dest_conflicts
            }
        
        # Step 2: Find source and destination networks
        source_matches = RoutingService.find_matching_networks(source_ip_or_network)
        if not source_matches:
            return {
                'status': 'error',
                'message': f"Source {source_ip_or_network} not found in any known network"
            }
            
        dest_matches = RoutingService.find_matching_networks(destination_ip_or_network)
        if not dest_matches:
            return {
                'status': 'error',
                'message': f"Destination {destination_ip_or_network} not found in any known network"
            }
        
        # For simplicity, just use the first match as the source/destination
        source_net = source_matches[0]
        dest_net = dest_matches[0]
        
        # If source and destination are on the same device, path is direct
        if source_net['device_id'] == dest_net['device_id']:
            result['path'] = [
                {
                    'device': source_net['device'],
                    'device_id': source_net['device_id'],
                    'ingress_interface': None,
                    'egress_interface': None,
                    'next_hop': None,
                    'note': 'Source and destination are on the same device'
                }
            ]
            return result
        
        # Start with the source device
        current_device_id = source_net['device_id']
        visited_devices = set()
        current_ip_or_network = destination_ip_or_network  # Start by looking for the original destination
        
        # Step 3: Check for source NAT on first device
        source_nat = RoutingService.find_nat_mapping(
            current_device_id, source_ip_or_network, 'source')
        
        if source_nat:
            result['nat_applied']['source'] = True
            result['nat_source_details'] = source_nat
            # Note: For now, we don't change the actual source for the path finding
        
        # Step 4: Check for destination NAT on last device
        dest_nat = RoutingService.find_nat_mapping(
            dest_net['device_id'], destination_ip_or_network, 'destination')
            
        if dest_nat:
            result['nat_applied']['destination'] = True
            result['nat_destination_details'] = dest_nat
            if 'translated' in dest_nat:
                current_ip_or_network = dest_nat['translated']
            else:
                current_ip_or_network = dest_nat['real']
        
        # Step 5: Perform hop-by-hop routing
        while current_device_id != dest_net['device_id'] and current_device_id not in visited_devices:
            visited_devices.add(current_device_id)
            
            # Get current device
            try:
                current_device = Device.objects.get(pk=current_device_id)
            except Device.DoesNotExist:
                return {
                    'status': 'error',
                    'message': f"Device with ID {current_device_id} not found",
                    'path': result['path']
                }
            
            # Find best matching route on current device
            best_route = None
            best_prefix_len = -1
            
            for route in Route.objects.filter(source_device_id=current_device_id):
                try:
                    route_network = ipaddress.ip_network(route.destination_network, strict=False)
                    
                    # Check if destination matches this route
                    if '/' in current_ip_or_network:
                        dest_network = ipaddress.ip_network(current_ip_or_network, strict=False)
                        if route_network.overlaps(dest_network):
                            prefix_len = route_network.prefixlen
                            if prefix_len > best_prefix_len:
                                best_route = route
                                best_prefix_len = prefix_len
                    else:
                        dest_ip = ipaddress.ip_address(current_ip_or_network)
                        if dest_ip in route_network:
                            prefix_len = route_network.prefixlen
                            if prefix_len > best_prefix_len:
                                best_route = route
                                best_prefix_len = prefix_len
                except ValueError:
                    # Skip invalid networks
                    continue
            
            if not best_route:
                return {
                    'status': 'error',
                    'message': f"No route found on device {current_device.name} for {current_ip_or_network}",
                    'path': result['path']
                }
            
            # Find the next hop device based on the gateway IP
            next_hop = None
            if best_route.gateway_ip:
                # Find which device has an interface with this gateway IP
                for interface in Interface.objects.filter(ip_address=best_route.gateway_ip, status='up'):
                    next_hop = {
                        'device_id': interface.device.id,
                        'device_name': interface.device.name,
                        'interface_id': interface.id,
                        'interface_name': interface.name,
                        'ip_address': interface.ip_address
                    }
                    break
            
            if not next_hop and best_route.type != 'connected':
                return {
                    'status': 'error',
                    'message': f"No next hop found for route {best_route.destination_network} on device {current_device.name}",
                    'path': result['path']
                }
            
            # Find egress interface on current device
            egress_interface = None
            if best_route.gateway_ip:
                # Find interface that can reach the gateway
                for interface in Interface.objects.filter(device=current_device, status='up'):
                    try:
                        interface_network = ipaddress.ip_network(interface.network, strict=False)
                        gateway_ip = ipaddress.ip_address(best_route.gateway_ip)
                        if gateway_ip in interface_network:
                            egress_interface = {
                                'interface_id': interface.id,
                                'name': interface.name,
                                'ip_address': interface.ip_address
                            }
                            break
                    except ValueError:
                        continue
            
            # Add hop to the path
            result['path'].append({
                'device': current_device.name,
                'device_id': current_device.id,
                'ingress_interface': None,  # Will be filled in next hop
                'egress_interface': egress_interface,
                'route': {
                    'network': best_route.destination_network,
                    'gateway': best_route.gateway_ip,
                    'type': best_route.type
                },
                'next_hop': next_hop['device_name'] if next_hop else "Directly Connected"
            })
            
            # Move to next hop
            if next_hop:
                # Set the ingress interface for the next hop
                ingress_interface = {
                    'interface_id': next_hop['interface_id'],
                    'name': next_hop['interface_name'],
                    'ip_address': next_hop['ip_address']
                }
                
                # Update for next iteration
                current_device_id = next_hop['device_id']
                
                # If this isn't the last hop, add the ingress interface
                if current_device_id != dest_net['device_id']:
                    if len(result['path']) > 0:
                        result['path'][-1]['next_hop_ingress'] = ingress_interface
            else:
                # Directly connected - we're done
                break
        
        # Check if we reached the destination or hit a loop
        if current_device_id == dest_net['device_id']:
            # Reached destination
            final_device = Device.objects.get(pk=current_device_id)
            
            result['path'].append({
                'device': final_device.name,
                'device_id': final_device.id,
                'ingress_interface': result['path'][-1].get('next_hop_ingress') if result['path'] else None,
                'egress_interface': None,
                'route': None,
                'next_hop': None,
                'note': 'Destination reached'
            })
            
            result['status'] = 'success'
        elif current_device_id in visited_devices:
            # Routing loop detected
            result['status'] = 'error'
            result['message'] = 'Routing loop detected'
        
        return result