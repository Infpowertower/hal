from django.urls import path
from .views import (
    DeviceViewSet, InterfaceViewSet, RouteViewSet, NATMappingViewSet,
    TopologyView, DeviceNetworksView, ConnectionDetailsView, RoutingPathView,
    topology_view
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'devices', DeviceViewSet)
router.register(r'interfaces', InterfaceViewSet)
router.register(r'routes', RouteViewSet)
router.register(r'nat-mappings', NATMappingViewSet)

app_name = 'netmap'

# Web UI routes
urlpatterns = [
    path('', topology_view, name='topology-view'),
]

# API routes
api_patterns = [
    path('topology/', TopologyView.as_view(), name='topology'),
    path('devices/<int:device_id>/networks/', DeviceNetworksView.as_view(), name='device-networks'),
    path('connections/', ConnectionDetailsView.as_view(), name='connection-details'),
    path('routing-path/', RoutingPathView.as_view(), name='routing-path'),
]

urlpatterns += api_patterns
urlpatterns += router.urls