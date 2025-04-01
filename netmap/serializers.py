from rest_framework import serializers
from .models import Device, Interface, Route, NATMapping


class DeviceSerializer(serializers.ModelSerializer):
    """Serializer for Device model"""
    
    class Meta:
        model = Device
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']


class InterfaceSerializer(serializers.ModelSerializer):
    """Serializer for Interface model"""
    device_name = serializers.CharField(source='device.name', read_only=True)
    
    class Meta:
        model = Interface
        fields = ['id', 'device', 'device_name', 'name', 'ip_address', 
                 'network', 'status', 'created_at', 'updated_at']


class RouteSerializer(serializers.ModelSerializer):
    """Serializer for Route model"""
    device_name = serializers.CharField(source='source_device.name', read_only=True)
    
    class Meta:
        model = Route
        fields = ['id', 'source_device', 'device_name', 'destination_network',
                 'gateway_ip', 'type', 'metric', 'created_at', 'updated_at']


class NATMappingSerializer(serializers.ModelSerializer):
    """Serializer for NATMapping model"""
    device_name = serializers.CharField(source='device.name', read_only=True)
    
    class Meta:
        model = NATMapping
        fields = ['id', 'device', 'device_name', 'logical_ip_or_network',
                 'real_ip_or_network', 'type', 'description', 'created_at', 'updated_at']


class TopologySerializer(serializers.Serializer):
    """Serializer for network topology data"""
    nodes = serializers.ListField(child=serializers.DictField())
    edges = serializers.ListField(child=serializers.DictField())


class DeviceNetworksSerializer(serializers.Serializer):
    """Serializer for device networks data"""
    network = serializers.CharField()
    interfaces = serializers.ListField(child=serializers.DictField())


class PathSegmentSerializer(serializers.Serializer):
    """Serializer for a segment of a routing path"""
    device = serializers.CharField()
    device_id = serializers.IntegerField()
    ingress_interface = serializers.DictField(allow_null=True)
    egress_interface = serializers.DictField(allow_null=True)
    route = serializers.DictField(allow_null=True)
    next_hop = serializers.CharField(allow_null=True)
    note = serializers.CharField(required=False, allow_null=True)
    next_hop_ingress = serializers.DictField(required=False, allow_null=True)


class RoutingPathSerializer(serializers.Serializer):
    """Serializer for routing path results"""
    status = serializers.CharField()
    source = serializers.CharField()
    destination = serializers.CharField()
    message = serializers.CharField(required=False)
    path = serializers.ListField(child=PathSegmentSerializer(), required=False)
    nat_applied = serializers.DictField(required=False)
    nat_source_details = serializers.DictField(required=False)
    nat_destination_details = serializers.DictField(required=False)
    conflicts = serializers.ListField(child=serializers.DictField(), required=False)