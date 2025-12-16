"""
Azure client wrapper for Cost Management and Advisor APIs.
Uses service principal authentication.
Supports both environment variables and dynamic credential injection.
"""
import os
from datetime import datetime, timedelta
from typing import Optional
from azure.identity import ClientSecretCredential
from azure.mgmt.costmanagement import CostManagementClient
from azure.mgmt.advisor import AdvisorManagementClient
from azure.mgmt.consumption import ConsumptionManagementClient
from azure.mgmt.resource import ResourceManagementClient


class AzureClientManager:
    """Manages Azure SDK client connections."""
    
    def __init__(self, tenant_id: str = None, client_id: str = None, 
                 client_secret: str = None, subscription_id: str = None):
        # Use provided credentials or fall back to environment variables
        self.tenant_id = tenant_id or os.getenv("AZURE_TENANT_ID")
        self.client_id = client_id or os.getenv("AZURE_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("AZURE_CLIENT_SECRET")
        self.subscription_id = subscription_id or os.getenv("AZURE_SUBSCRIPTION_ID")
        
        if not all([self.tenant_id, self.client_id, self.client_secret, self.subscription_id]):
            raise ValueError("Missing required Azure credentials")
        
        self._credential = None
        self._cost_client = None
        self._advisor_client = None
        self._consumption_client = None
        self._resource_client = None
    
    @property
    def credential(self) -> ClientSecretCredential:
        if self._credential is None:
            self._credential = ClientSecretCredential(
                tenant_id=self.tenant_id,
                client_id=self.client_id,
                client_secret=self.client_secret
            )
        return self._credential
    
    @property
    def cost_client(self) -> CostManagementClient:
        if self._cost_client is None:
            self._cost_client = CostManagementClient(
                credential=self.credential,
                subscription_id=self.subscription_id
            )
        return self._cost_client
    
    @property
    def advisor_client(self) -> AdvisorManagementClient:
        if self._advisor_client is None:
            self._advisor_client = AdvisorManagementClient(
                credential=self.credential,
                subscription_id=self.subscription_id
            )
        return self._advisor_client
    
    @property
    def consumption_client(self) -> ConsumptionManagementClient:
        if self._consumption_client is None:
            self._consumption_client = ConsumptionManagementClient(
                credential=self.credential,
                subscription_id=self.subscription_id
            )
        return self._consumption_client
    
    @property
    def resource_client(self) -> ResourceManagementClient:
        if self._resource_client is None:
            self._resource_client = ResourceManagementClient(
                credential=self.credential,
                subscription_id=self.subscription_id
            )
        return self._resource_client
    
    def list_resources(self) -> dict:
        """List all resources in the subscription and categorize them."""
        resources = list(self.resource_client.resources.list())
        
        # Categorize resources by type
        categories = {
            "virtual_machines": 0,
            "sql_databases": 0,
            "storage_accounts": 0,
            "kubernetes_clusters": 0,
            "app_services": 0,
            "networking": 0,
            "other": 0
        }
        
        for resource in resources:
            resource_type = resource.type.lower() if resource.type else ""
            
            if "virtualmachines" in resource_type:
                categories["virtual_machines"] += 1
            elif "sql" in resource_type or "database" in resource_type:
                categories["sql_databases"] += 1
            elif "storageaccounts" in resource_type:
                categories["storage_accounts"] += 1
            elif "kubernetes" in resource_type or "containerservice" in resource_type:
                categories["kubernetes_clusters"] += 1
            elif "sites" in resource_type or "appservice" in resource_type:
                categories["app_services"] += 1
            elif "network" in resource_type or "virtualnetwork" in resource_type or "publicip" in resource_type:
                categories["networking"] += 1
            else:
                categories["other"] += 1
        
        categories["total"] = len(resources)
        return categories


# Singleton instance
_azure_manager: Optional[AzureClientManager] = None

def get_azure_manager() -> AzureClientManager:
    global _azure_manager
    if _azure_manager is None:
        _azure_manager = AzureClientManager()
    return _azure_manager
