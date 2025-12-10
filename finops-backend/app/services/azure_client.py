"""
Azure client wrapper for Cost Management and Advisor APIs.
Uses service principal authentication.
"""
import os
from datetime import datetime, timedelta
from typing import Optional
from azure.identity import ClientSecretCredential
from azure.mgmt.costmanagement import CostManagementClient
from azure.mgmt.advisor import AdvisorManagementClient
from azure.mgmt.consumption import ConsumptionManagementClient


class AzureClientManager:
    """Manages Azure SDK client connections."""
    
    def __init__(self):
        self.tenant_id = os.getenv("AZURE_TENANT_ID")
        self.client_id = os.getenv("AZURE_CLIENT_ID")
        self.client_secret = os.getenv("AZURE_CLIENT_SECRET")
        self.subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
        
        if not all([self.tenant_id, self.client_id, self.client_secret, self.subscription_id]):
            raise ValueError("Missing required Azure environment variables")
        
        self._credential = None
        self._cost_client = None
        self._advisor_client = None
        self._consumption_client = None
    
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


# Singleton instance
_azure_manager: Optional[AzureClientManager] = None

def get_azure_manager() -> AzureClientManager:
    global _azure_manager
    if _azure_manager is None:
        _azure_manager = AzureClientManager()
    return _azure_manager
