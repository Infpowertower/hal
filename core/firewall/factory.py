from typing import Dict, Optional, Any
import logging

from .base import FirewallConnector
from .test_firewall import TestFirewall
from .checkpoint import CheckpointFirewall
from .fortinet import FortinetFirewall

logger = logging.getLogger(__name__)

class FirewallFactory:
    """
    Factory class for creating firewall instances
    """
    
    @staticmethod
    def create(firewall_type: str, **kwargs) -> FirewallConnector:
        """
        Create a firewall instance of the specified type
        
        Args:
            firewall_type: Type of firewall ('checkpoint', 'fortinet', 'test')
            **kwargs: Connection parameters for the firewall
            
        Returns:
            FirewallConnector: An instance of the specified firewall type
            
        Raises:
            ValueError: If the firewall type is not supported
        """
        firewall_type = firewall_type.lower()
        
        if firewall_type == 'checkpoint':
            return CheckpointFirewall()
        elif firewall_type == 'fortinet':
            return FortinetFirewall()
        elif firewall_type == 'test':
            return TestFirewall()
        else:
            raise ValueError(f"Unsupported firewall type: {firewall_type}")
    
    @staticmethod
    def connect(firewall_type: str, **kwargs) -> FirewallConnector:
        """
        Create and connect to a firewall in one step
        
        Args:
            firewall_type: Type of firewall ('checkpoint', 'fortinet', 'test')
            **kwargs: Connection parameters for the firewall
            
        Returns:
            FirewallConnector: A connected instance of the specified firewall type
        """
        firewall = FirewallFactory.create(firewall_type, **kwargs)
        firewall.connect(**kwargs)
        return firewall