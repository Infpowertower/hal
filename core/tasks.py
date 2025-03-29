import logging
from celery import shared_task
from .firewall.factory import FirewallFactory

logger = logging.getLogger(__name__)

@shared_task
def sample_task(name="sample_task"):
    """
    A sample task that logs a message.
    This is just a demo task - replace with your actual tasks.
    """
    logger.info(f"Task {name} executed successfully")
    return True

@shared_task
def periodic_task():
    """
    A sample periodic task that will be scheduled with celery beat.
    This is just a demo task - replace with your actual periodic tasks.
    """
    logger.info("Periodic task executed successfully")
    return True

@shared_task
def delete_ip_object(firewall_type: str, ip_object_id: str, connection_params: dict, auto_commit: bool = True):
    """
    Delete an IP object from a firewall and clean up dependencies
    
    Args:
        firewall_type: Type of firewall ('checkpoint', 'fortinet', 'test')
        ip_object_id: ID of the IP object to delete
        connection_params: Connection parameters for the firewall
        auto_commit: Whether to automatically commit changes
        
    Returns:
        dict: Results of the operation
    """
    logger.info(f"Starting deletion task for IP object {ip_object_id} on {firewall_type} firewall")
    result = {
        "success": False,
        "message": "",
        "details": {}
    }
    
    firewall = None
    try:
        # Create and connect to the firewall
        firewall = FirewallFactory.create(firewall_type)
        firewall.connect(**connection_params)
        
        # Delete the IP object with dependencies
        deletion_result = firewall.delete_ip_object_with_dependencies(ip_object_id, auto_commit)
        
        result["success"] = deletion_result["success"]
        result["details"] = deletion_result
        
        if result["success"]:
            result["message"] = f"Successfully deleted IP object {ip_object_id} and its dependencies"
        else:
            errors = deletion_result.get("errors", [])
            result["message"] = f"Failed to delete IP object: {'; '.join(errors)}"
            
    except Exception as e:
        logger.exception(f"Error in delete_ip_object task: {str(e)}")
        result["success"] = False
        result["message"] = f"Error: {str(e)}"
        
    finally:
        # Always disconnect from the firewall
        if firewall:
            try:
                firewall.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting from firewall: {str(e)}")
    
    return result