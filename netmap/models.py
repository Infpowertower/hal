from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
import ipaddress


class Device(models.Model):
    """
    Represents a network device such as a router, firewall, or switch.
    """
    name = models.CharField(max_length=255, unique=True, 
                           help_text="Unique identifier for the device")
    description = models.TextField(blank=True, 
                                  help_text="Optional description of the device")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Interface(models.Model):
    """
    Represents a network interface on a device.
    
    Multiple interfaces can exist for the same device,
    and multiple IPs can be assigned to what is logically
    the same physical interface (e.g., eth0, eth0:1).
    """
    STATUS_CHOICES = [
        ('up', 'Up'),
        ('down', 'Down'),
    ]
    
    device = models.ForeignKey(Device, on_delete=models.CASCADE, 
                              related_name='interfaces',
                              help_text="The device this interface belongs to")
    name = models.CharField(max_length=255, 
                           help_text="Interface name (e.g., 'eth0', 'ge-0/0/0')")
    ip_address = models.GenericIPAddressField(help_text="IP address assigned to this interface")
    network = models.CharField(max_length=18, 
                              validators=[
                                  RegexValidator(
                                      regex=r'^([0-9]{1,3}\.){3}[0-9]{1,3}/[0-9]{1,2}$',
                                      message="Enter a valid CIDR notation (e.g., '192.168.24.0/24')"
                                  )
                              ],
                              help_text="Network in CIDR notation (e.g., '192.168.24.0/24')")
    status = models.CharField(max_length=4, choices=STATUS_CHOICES, default='up',
                             help_text="Interface status ('up' or 'down')")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Allow the same interface name on different devices
        # Allow different IPs on the same interface name for a device
        constraints = [
            models.UniqueConstraint(
                fields=['device', 'name', 'ip_address'],
                name='unique_device_interface_ip'
            )
        ]

    def clean(self):
        """
        Validate that the IP address falls within the specified network CIDR.
        """
        try:
            if self.ip_address and self.network:
                ip = ipaddress.ip_address(self.ip_address)
                network = ipaddress.ip_network(self.network, strict=False)
                
                if ip not in network:
                    raise ValidationError({
                        'ip_address': f"IP address {self.ip_address} is not within the network {self.network}"
                    })
        except ValueError as e:
            raise ValidationError(f"Invalid IP or network format: {str(e)}")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.device.name} - {self.name} ({self.ip_address})"


class Route(models.Model):
    """
    Represents a routing table entry.
    """
    ROUTE_TYPE_CHOICES = [
        ('static', 'Static'),
        ('ospf', 'OSPF'),
        ('bgp', 'BGP'),
        ('connected', 'Connected'),
        ('rip', 'RIP'),
        ('eigrp', 'EIGRP'),
        ('other', 'Other'),
    ]
    
    source_device = models.ForeignKey(Device, on_delete=models.CASCADE, 
                                     related_name='routes',
                                     help_text="The device this route is defined on")
    destination_network = models.CharField(max_length=18, 
                                         validators=[
                                             RegexValidator(
                                                 regex=r'^([0-9]{1,3}\.){3}[0-9]{1,3}/[0-9]{1,2}$',
                                                 message="Enter a valid CIDR notation (e.g., '192.168.24.0/24')"
                                             )
                                         ],
                                         help_text="Destination network in CIDR notation")
    gateway_ip = models.GenericIPAddressField(
        help_text="Next hop gateway IP address",
        null=True, blank=True  # Allow null for directly connected routes
    )
    type = models.CharField(max_length=10, choices=ROUTE_TYPE_CHOICES, 
                           default='static',
                           help_text="Routing protocol or type")
    metric = models.IntegerField(default=0, 
                                help_text="Routing metric/cost (lower is preferred)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # A device should have only one route for a given destination network with the same gateway
        constraints = [
            models.UniqueConstraint(
                fields=['source_device', 'destination_network', 'gateway_ip'],
                name='unique_device_route'
            )
        ]

    def clean(self):
        """
        Validate routing information.
        """
        try:
            # Validate destination network format
            ipaddress.ip_network(self.destination_network, strict=False)
            
            # For non-connected routes, gateway IP is required
            if self.type != 'connected' and not self.gateway_ip:
                raise ValidationError({
                    'gateway_ip': "Gateway IP is required for non-connected routes"
                })
                
            # For connected routes, gateway should be None
            if self.type == 'connected' and self.gateway_ip:
                raise ValidationError({
                    'gateway_ip': "Gateway IP should be empty for connected routes"
                })
                
        except ValueError as e:
            raise ValidationError(f"Invalid network format: {str(e)}")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.gateway_ip:
            return f"{self.source_device.name}: {self.destination_network} via {self.gateway_ip} ({self.type})"
        return f"{self.source_device.name}: {self.destination_network} ({self.type})"


class NATMapping(models.Model):
    """
    Represents a Network Address Translation mapping.
    """
    NAT_TYPE_CHOICES = [
        ('source', 'Source NAT'),
        ('destination', 'Destination NAT'),
    ]
    
    device = models.ForeignKey(Device, on_delete=models.CASCADE, 
                              related_name='nat_mappings',
                              help_text="The device performing the NAT")
    logical_ip_or_network = models.CharField(max_length=18, 
                                           help_text="Original IP or network (before NAT)")
    real_ip_or_network = models.CharField(max_length=18, 
                                         help_text="Translated IP or network (after NAT)")
    type = models.CharField(max_length=11, choices=NAT_TYPE_CHOICES, 
                           help_text="Type of NAT ('source' or 'destination')")
    description = models.TextField(blank=True, 
                                  help_text="Optional description of the NAT mapping")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """
        Validate that the logical and real IPs or networks are in a valid format.
        """
        try:
            # Try to parse as IP or network
            for field in [self.logical_ip_or_network, self.real_ip_or_network]:
                if '/' in field:
                    ipaddress.ip_network(field, strict=False)
                else:
                    ipaddress.ip_address(field)
        except ValueError as e:
            raise ValidationError(f"Invalid IP or network format: {str(e)}")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.device.name}: {self.type} NAT {self.logical_ip_or_network} → {self.real_ip_or_network}"