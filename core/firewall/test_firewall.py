import uuid
import time
import logging
from typing import Dict, List, Optional, Any
from .base import (
    FirewallConnector, IPObject, Group, Rule,
    ObjectNotFoundError, AuthenticationError
)

logger = logging.getLogger(__name__)

class TestFirewall(FirewallConnector):
    """
    Test implementation of FirewallConnector for development
    Returns mock data for all operations
    """
    
    def __init__(self):
        self.connected = False
        self.mock_ip_objects = {}
        self.mock_groups = {}
        self.mock_rules = {}
        self._generate_mock_data()
    
    def _generate_mock_data(self):
        """Generate sample data for testing"""
        # Create IP objects
        ips = [
            IPObject(
                name="Server1",
                value="192.168.1.10",
                type="host",
                uid=str(uuid.uuid4()),
                description="Production web server"
            ),
            IPObject(
                name="Server2",
                value="192.168.1.11",
                type="host",
                uid=str(uuid.uuid4()),
                description="Production database server"
            ),
            IPObject(
                name="DevNetwork",
                value="10.0.1.0/24",
                type="network",
                uid=str(uuid.uuid4()),
                description="Development network"
            ),
            IPObject(
                name="TestServer",
                value="192.168.2.50",
                type="host",
                uid=str(uuid.uuid4()),
                description="Test server - Safe to delete"
            )
        ]
        
        for ip in ips:
            self.mock_ip_objects[ip.uid] = ip
            # Also add by name for convenience
            self.mock_ip_objects[ip.name] = ip
        
        # Create groups
        web_servers_id = str(uuid.uuid4())
        all_servers_id = str(uuid.uuid4())
        
        web_servers = Group(
            name="WebServers",
            uid=web_servers_id,
            members=[ips[0].uid],  # Server1
            description="Web servers group"
        )
        
        all_servers = Group(
            name="AllServers",
            uid=all_servers_id,
            members=[ips[0].uid, ips[1].uid, ips[3].uid, web_servers_id],  # All servers and WebServers group
            description="All servers group"
        )
        
        self.mock_groups[web_servers.uid] = web_servers
        self.mock_groups[all_servers.uid] = all_servers
        self.mock_groups[web_servers.name] = web_servers
        self.mock_groups[all_servers.name] = all_servers
        
        # Create rules
        allow_web = Rule(
            name="AllowWebAccess",
            uid=str(uuid.uuid4()),
            source=[ips[2].uid],  # DevNetwork
            destination=[web_servers.uid],  # WebServers group
            action="allow",
            position=1
        )
        
        allow_test = Rule(
            name="AllowTestAccess",
            uid=str(uuid.uuid4()),
            source=["any"],
            destination=[ips[3].uid],  # TestServer
            action="allow",
            position=2
        )
        
        self.mock_rules[allow_web.uid] = allow_web
        self.mock_rules[allow_test.uid] = allow_test
        self.mock_rules[allow_web.name] = allow_web
        self.mock_rules[allow_test.name] = allow_test
    
    def connect(self, **kwargs) -> bool:
        logger.info(f"Connecting to test firewall with parameters: {kwargs}")
        # Simulate connection delay
        time.sleep(0.5)
        
        # Check for credential failure
        if kwargs.get('username') == 'fail':
            raise AuthenticationError("Authentication failed")
        
        self.connected = True
        logger.info("Connected to test firewall")
        return True
    
    def disconnect(self) -> bool:
        logger.info("Disconnecting from test firewall")
        time.sleep(0.2)  # Simulate delay
        self.connected = False
        return True
    
    def _check_connection(self):
        if not self.connected:
            raise ConnectionError("Not connected to firewall")
    
    def get_ip_objects(self, filter_params: Optional[Dict] = None) -> List[IPObject]:
        self._check_connection()
        logger.info(f"Getting IP objects with filter: {filter_params}")
        
        # Use a set to avoid duplicates (since we store objects by both UID and name)
        unique_ids = set()
        filtered_objects = []
        
        for obj_id, obj in self.mock_ip_objects.items():
            # Skip name duplicates
            if obj.uid in unique_ids:
                continue
            
            # Apply filters if provided
            if filter_params:
                match = True
                for key, value in filter_params.items():
                    if hasattr(obj, key) and getattr(obj, key) != value:
                        match = False
                        break
                if not match:
                    continue
            
            filtered_objects.append(obj)
            unique_ids.add(obj.uid)
        
        return filtered_objects
    
    def get_ip_object(self, identifier: str) -> Optional[IPObject]:
        self._check_connection()
        logger.info(f"Getting IP object: {identifier}")
        return self.mock_ip_objects.get(identifier)
    
    def get_groups(self, filter_params: Optional[Dict] = None) -> List[Group]:
        self._check_connection()
        logger.info(f"Getting groups with filter: {filter_params}")
        
        # Use a set to avoid duplicates
        unique_ids = set()
        filtered_groups = []
        
        for group_id, group in self.mock_groups.items():
            # Skip name duplicates
            if group.uid in unique_ids:
                continue
            
            # Apply filters if provided
            if filter_params:
                match = True
                for key, value in filter_params.items():
                    if hasattr(group, key) and getattr(group, key) != value:
                        match = False
                        break
                if not match:
                    continue
            
            filtered_groups.append(group)
            unique_ids.add(group.uid)
        
        return filtered_groups
    
    def get_group(self, identifier: str) -> Optional[Group]:
        self._check_connection()
        logger.info(f"Getting group: {identifier}")
        return self.mock_groups.get(identifier)
    
    def get_rules(self, filter_params: Optional[Dict] = None) -> List[Rule]:
        self._check_connection()
        logger.info(f"Getting rules with filter: {filter_params}")
        
        # Use a set to avoid duplicates
        unique_ids = set()
        filtered_rules = []
        
        for rule_id, rule in self.mock_rules.items():
            # Skip name duplicates
            if rule.uid in unique_ids:
                continue
            
            # Apply filters if provided
            if filter_params:
                match = True
                for key, value in filter_params.items():
                    if hasattr(rule, key) and getattr(rule, key) != value:
                        match = False
                        break
                if not match:
                    continue
            
            filtered_rules.append(rule)
            unique_ids.add(rule.uid)
        
        return filtered_rules
    
    def get_rule(self, identifier: str) -> Optional[Rule]:
        self._check_connection()
        logger.info(f"Getting rule: {identifier}")
        return self.mock_rules.get(identifier)
    
    def get_dependencies(self, ip_object_id: str) -> Dict[str, List[Any]]:
        self._check_connection()
        logger.info(f"Getting dependencies for IP object: {ip_object_id}")
        
        ip_object = self.get_ip_object(ip_object_id)
        if not ip_object:
            raise ObjectNotFoundError(f"IP object with ID {ip_object_id} not found")
        
        dependencies = {
            "groups": [],
            "rules": []
        }
        
        # Check group dependencies
        for group_id, group in self.mock_groups.items():
            if group.uid not in dependencies["groups"] and ip_object.uid in group.members:
                dependencies["groups"].append(group.uid)
        
        # Check rule dependencies
        for rule_id, rule in self.mock_rules.items():
            if rule.uid not in dependencies["rules"] and (
                ip_object.uid in rule.source or 
                ip_object.uid in rule.destination
            ):
                dependencies["rules"].append(rule.uid)
        
        return dependencies
    
    def remove_ip_from_group(self, group_id: str, ip_object_id: str) -> bool:
        self._check_connection()
        logger.info(f"Removing IP {ip_object_id} from group {group_id}")
        
        group = self.get_group(group_id)
        if not group:
            raise ObjectNotFoundError(f"Group with ID {group_id} not found")
        
        ip_object = self.get_ip_object(ip_object_id)
        if not ip_object:
            raise ObjectNotFoundError(f"IP object with ID {ip_object_id} not found")
        
        if ip_object.uid in group.members:
            group.members.remove(ip_object.uid)
            return True
        
        return False
    
    def remove_ip_from_rule(self, rule_id: str, ip_object_id: str) -> bool:
        self._check_connection()
        logger.info(f"Removing IP {ip_object_id} from rule {rule_id}")
        
        rule = self.get_rule(rule_id)
        if not rule:
            raise ObjectNotFoundError(f"Rule with ID {rule_id} not found")
        
        ip_object = self.get_ip_object(ip_object_id)
        if not ip_object:
            raise ObjectNotFoundError(f"IP object with ID {ip_object_id} not found")
        
        modified = False
        
        if ip_object.uid in rule.source:
            rule.source.remove(ip_object.uid)
            modified = True
        
        if ip_object.uid in rule.destination:
            rule.destination.remove(ip_object.uid)
            modified = True
        
        return modified
    
    def delete_empty_group(self, group_id: str) -> bool:
        self._check_connection()
        logger.info(f"Deleting empty group: {group_id}")
        
        group = self.get_group(group_id)
        if not group:
            raise ObjectNotFoundError(f"Group with ID {group_id} not found")
        
        if group.members:
            logger.warning(f"Group {group_id} is not empty, skipping deletion")
            return False
        
        # Find both name and UID entries and remove them
        keys_to_remove = []
        for key, value in self.mock_groups.items():
            if value.uid == group.uid:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.mock_groups[key]
        
        return True
    
    def delete_empty_rule(self, rule_id: str) -> bool:
        self._check_connection()
        logger.info(f"Deleting empty rule: {rule_id}")
        
        rule = self.get_rule(rule_id)
        if not rule:
            raise ObjectNotFoundError(f"Rule with ID {rule_id} not found")
        
        # Consider a rule empty if it has no source or no destination
        if rule.source and rule.destination:
            logger.warning(f"Rule {rule_id} is not empty, skipping deletion")
            return False
        
        # Find both name and UID entries and remove them
        keys_to_remove = []
        for key, value in self.mock_rules.items():
            if value.uid == rule.uid:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.mock_rules[key]
        
        return True
    
    def delete_ip_object(self, ip_object_id: str) -> bool:
        self._check_connection()
        logger.info(f"Deleting IP object: {ip_object_id}")
        
        ip_object = self.get_ip_object(ip_object_id)
        if not ip_object:
            raise ObjectNotFoundError(f"IP object with ID {ip_object_id} not found")
        
        # Check for any remaining dependencies
        dependencies = self.get_dependencies(ip_object_id)
        if dependencies["groups"] or dependencies["rules"]:
            dep_list = ", ".join(dependencies["groups"] + dependencies["rules"])
            logger.warning(f"IP object {ip_object_id} still has dependencies: {dep_list}")
            return False
        
        # Find both name and UID entries and remove them
        keys_to_remove = []
        for key, value in self.mock_ip_objects.items():
            if value.uid == ip_object.uid:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.mock_ip_objects[key]
        
        return True
    
    def commit_changes(self) -> bool:
        self._check_connection()
        logger.info("Committing changes to test firewall")
        time.sleep(1)  # Simulate commit delay
        return True