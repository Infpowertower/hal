from django.urls import path
from .views import (
    DeviceViewSet, InterfaceViewSet, RouteViewSet, NATMappingViewSet,
    TopologyView, DeviceNetworksView, ConnectionDetailsView, RoutingPathView
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'devices', DeviceViewSet)
router.register(r'interfaces', InterfaceViewSet)
router.register(r'routes', RouteViewSet)
router.register(r'nat-mappings', NATMappingViewSet)

app_name = 'netmap'

urlpatterns = [
    path('topology/', TopologyView.as_view(), name='topology'),
    path('devices/<int:device_id>/networks/', DeviceNetworksView.as_view(), name='device-networks'),
    path('connections/', ConnectionDetailsView.as_view(), name='connection-details'),
    path('routing-path/', RoutingPathView.as_view(), name='routing-path'),
]

urlpatterns += router.urls