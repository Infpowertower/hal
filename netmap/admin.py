from django.contrib import admin
from .models import Device, Interface, Route, NATMapping


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    ordering = ('name',)


@admin.register(Interface)
class InterfaceAdmin(admin.ModelAdmin):
    list_display = ('device', 'name', 'ip_address', 'network', 'status', 'updated_at')
    list_filter = ('status', 'device')
    search_fields = ('name', 'ip_address', 'network')
    ordering = ('device', 'name')


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('source_device', 'destination_network', 'gateway_ip', 'type', 'metric')
    list_filter = ('type', 'source_device')
    search_fields = ('destination_network', 'gateway_ip')
    ordering = ('source_device', 'destination_network')


@admin.register(NATMapping)
class NATMappingAdmin(admin.ModelAdmin):
    list_display = ('device', 'type', 'logical_ip_or_network', 'real_ip_or_network')
    list_filter = ('type', 'device')
    search_fields = ('logical_ip_or_network', 'real_ip_or_network', 'description')
    ordering = ('device', 'type')