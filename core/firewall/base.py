from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, Any
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class IPObject:
    """
    Represents an IP object in a firewall
    """
    name: str
    value: str  # IP address or subnet in CIDR notation
    type: str  # 'host', 'network', 'range', etc.
    uid: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class Group:
    """
    Represents a group of objects in a firewall
    """
    name: str
    members: List[Union[str, 'Group']]  # List of member UIDs or nested groups
    type: str = "group"
    uid: Optional[str] = None
    description: Optional[str] = None
    
    def __post_init__(self):
        if self.members is None:
            self.members = []


@dataclass
class Rule:
    """
    Represents a firewall rule
    """
    name: str
    uid: Optional[str] = None
    source: List[str] = None  # List of source object UIDs
    destination: List[str] = None  # List of destination object UIDs
    service: List[str] = None  # List of service UIDs
    action: str = "deny"  # Default to deny for safety
    enabled: bool = True
    position: Optional[int] = None
    
    def __post_init__(self):
        if self.source is None:
            self.source = []
        if self.destination is None:
            self.destination = []
        if self.service is None:
            self.service = []


class FirewallError(Exception):
    """Base exception for firewall operations"""
    pass


class AuthenticationError(FirewallError):
    """Authentication failed"""
    pass


class ObjectNotFoundError(FirewallError):
    """Object not found in firewall"""
    pass


class DependencyError(FirewallError):
    """Operation failed due to dependencies"""
    pass


class FirewallConnector(ABC):
    """
    Abstract connector for firewall management
    """
    
    @abstractmethod
    def connect(self, **kwargs) -> bool:
        """
        Connect to the firewall management interface
        
        Args:
            **kwargs: Connection parameters (host, credentials, etc.)
            
        Returns:
            bool: True if connection successful
            
        Raises:
            AuthenticationError: If authentication fails
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """
        Disconnect from the firewall management interface
        
        Returns:
            bool: True if disconnection successful
        """
        pass
    
    @abstractmethod
    def get_ip_objects(self, filter_params: Optional[Dict] = None) -> List[IPObject]:
        """
        Get IP objects from the firewall
        
        Args:
            filter_params: Optional filtering parameters
            
        Returns:
            List[IPObject]: List of IP objects
        """
        pass
    
    @abstractmethod
    def get_ip_object(self, identifier: str) -> Optional[IPObject]:
        """
        Get a specific IP object from the firewall
        
        Args:
            identifier: Name or UID of the IP object
            
        Returns:
            Optional[IPObject]: IP object if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_groups(self, filter_params: Optional[Dict] = None) -> List[Group]:
        """
        Get groups from the firewall
        
        Args:
            filter_params: Optional filtering parameters
            
        Returns:
            List[Group]: List of groups
        """
        pass
    
    @abstractmethod
    def get_group(self, identifier: str) -> Optional[Group]:
        """
        Get a specific group from the firewall
        
        Args:
            identifier: Name or UID of the group
            
        Returns:
            Optional[Group]: Group if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_rules(self, filter_params: Optional[Dict] = None) -> List[Rule]:
        """
        Get firewall rules
        
        Args:
            filter_params: Optional filtering parameters
            
        Returns:
            List[Rule]: List of firewall rules
        """
        pass
    
    @abstractmethod
    def get_rule(self, identifier: str) -> Optional[Rule]:
        """
        Get a specific firewall rule
        
        Args:
            identifier: Name or UID of the rule
            
        Returns:
            Optional[Rule]: Rule if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_dependencies(self, ip_object_id: str) -> Dict[str, List[Any]]:
        """
        Get all dependencies for an IP object
        
        Args:
            ip_object_id: ID of the IP object
            
        Returns:
            Dict[str, List[Any]]: Dictionary with dependencies by type
        """
        pass
    
    @abstractmethod
    def remove_ip_from_group(self, group_id: str, ip_object_id: str) -> bool:
        """
        Remove an IP object from a group
        
        Args:
            group_id: ID of the group
            ip_object_id: ID of the IP object
            
        Returns:
            bool: True if successful
        """
        pass
    
    @abstractmethod
    def remove_ip_from_rule(self, rule_id: str, ip_object_id: str) -> bool:
        """
        Remove an IP object from a rule
        
        Args:
            rule_id: ID of the rule
            ip_object_id: ID of the IP object
            
        Returns:
            bool: True if successful
        """
        pass
    
    @abstractmethod
    def delete_empty_group(self, group_id: str) -> bool:
        """
        Delete a group if it is empty
        
        Args:
            group_id: ID of the group
            
        Returns:
            bool: True if successful
        """
        pass
    
    @abstractmethod
    def delete_empty_rule(self, rule_id: str) -> bool:
        """
        Delete a rule if it has no sources or destinations
        
        Args:
            rule_id: ID of the rule
            
        Returns:
            bool: True if successful
        """
        pass
    
    @abstractmethod
    def delete_ip_object(self, ip_object_id: str) -> bool:
        """
        Delete an IP object from the firewall
        
        Args:
            ip_object_id: ID of the IP object
            
        Returns:
            bool: True if successful
        """
        pass
    
    @abstractmethod
    def commit_changes(self) -> bool:
        """
        Commit changes to the firewall
        
        Returns:
            bool: True if successful
        """
        pass
    
    def delete_ip_object_with_dependencies(self, ip_object_id: str, auto_commit: bool = True) -> Dict[str, Any]:
        """
        Delete an IP object and clean up any dependencies
        
        This method:
        1. Identifies all dependencies (groups and rules using the IP)
        2. Removes the IP from all groups
        3. Removes the IP from all rules
        4. Deletes any empty groups and rules
        5. Finally deletes the IP object itself
        6. Optionally commits the changes
        
        Args:
            ip_object_id: ID of the IP object to delete
            auto_commit: Whether to automatically commit changes
            
        Returns:
            Dict[str, Any]: Results of the operation
        """
        logger.info(f"Starting deletion of IP object {ip_object_id} with dependencies")
        result = {
            "success": False,
            "ip_object_deleted": False,
            "groups_modified": [],
            "groups_deleted": [],
            "rules_modified": [],
            "rules_deleted": [],
            "errors": []
        }
        
        try:
            # Get the object to confirm it exists
            ip_object = self.get_ip_object(ip_object_id)
            if not ip_object:
                raise ObjectNotFoundError(f"IP object with ID {ip_object_id} not found")
            
            # Get all dependencies
            dependencies = self.get_dependencies(ip_object_id)
            
            # Process group dependencies
            for group_id in dependencies.get("groups", []):
                try:
                    logger.debug(f"Removing IP {ip_object_id} from group {group_id}")
                    self.remove_ip_from_group(group_id, ip_object_id)
                    result["groups_modified"].append(group_id)
                    
                    # Check if group is now empty and delete if it is
                    group = self.get_group(group_id)
                    if group and not group.members:
                        logger.debug(f"Deleting empty group {group_id}")
                        self.delete_empty_group(group_id)
                        result["groups_deleted"].append(group_id)
                except Exception as e:
                    error_msg = f"Error processing group {group_id}: {str(e)}"
                    logger.error(error_msg)
                    result["errors"].append(error_msg)
            
            # Process rule dependencies
            for rule_id in dependencies.get("rules", []):
                try:
                    logger.debug(f"Removing IP {ip_object_id} from rule {rule_id}")
                    self.remove_ip_from_rule(rule_id, ip_object_id)
                    result["rules_modified"].append(rule_id)
                    
                    # Check if rule is now empty and delete if it is
                    rule = self.get_rule(rule_id)
                    if rule and not rule.source and not rule.destination:
                        logger.debug(f"Deleting empty rule {rule_id}")
                        self.delete_empty_rule(rule_id)
                        result["rules_deleted"].append(rule_id)
                except Exception as e:
                    error_msg = f"Error processing rule {rule_id}: {str(e)}"
                    logger.error(error_msg)
                    result["errors"].append(error_msg)
            
            # Delete the IP object itself
            logger.info(f"Deleting IP object {ip_object_id}")
            if self.delete_ip_object(ip_object_id):
                result["ip_object_deleted"] = True
            
            # Commit changes if auto_commit is True
            if auto_commit:
                logger.info("Committing changes to firewall")
                self.commit_changes()
            
            result["success"] = result["ip_object_deleted"] and not result["errors"]
            
        except Exception as e:
            error_msg = f"Error deleting IP object {ip_object_id}: {str(e)}"
            logger.error(error_msg)
            result["errors"].append(error_msg)
        
        return result