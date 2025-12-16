"""
Service for fetching cost data from Azure Cost Management API.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from azure.mgmt.costmanagement.models import (
    QueryDefinition,
    QueryTimePeriod,
    QueryDataset,
    QueryAggregation,
    QueryGrouping,
    TimeframeType,
    GranularityType,
    ExportType
)
from .azure_client import AzureClientManager


class CostService:
    """Fetches and processes Azure cost data."""
    
    def __init__(self, tenant_id: str = None, client_id: str = None,
                 client_secret: str = None, subscription_id: str = None):
        self.azure = AzureClientManager(tenant_id, client_id, client_secret, subscription_id)
        self.scope = f"/subscriptions/{self.azure.subscription_id}"
    
    def get_daily_costs(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get daily cost breakdown for the last N days.
        Returns list of {date, cost, currency} dicts.
        """
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        query = QueryDefinition(
            type=ExportType.ACTUAL_COST,
            timeframe=TimeframeType.CUSTOM,
            time_period=QueryTimePeriod(
                from_property=datetime.combine(start_date, datetime.min.time()),
                to=datetime.combine(end_date, datetime.min.time())
            ),
            dataset=QueryDataset(
                granularity=GranularityType.DAILY,
                aggregation={
                    "totalCost": QueryAggregation(
                        name="Cost",
                        function="Sum"
                    )
                }
            )
        )
        
        result = self.azure.cost_client.query.usage(
            scope=self.scope,
            parameters=query
        )
        
        # Parse response into clean format
        costs = []
        if result.rows:
            for row in result.rows:
                costs.append({
                    "date": row[0] if isinstance(row[0], str) else row[0].isoformat(),
                    "cost": float(row[1]),
                    "currency": row[2] if len(row) > 2 else "USD"
                })
        
        return costs
    
    def get_costs_by_service(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get cost breakdown by Azure service (MeterCategory).
        """
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        query = QueryDefinition(
            type=ExportType.ACTUAL_COST,
            timeframe=TimeframeType.CUSTOM,
            time_period=QueryTimePeriod(
                from_property=datetime.combine(start_date, datetime.min.time()),
                to=datetime.combine(end_date, datetime.min.time())
            ),
            dataset=QueryDataset(
                granularity=GranularityType.NONE,
                aggregation={
                    "totalCost": QueryAggregation(
                        name="Cost",
                        function="Sum"
                    )
                },
                grouping=[
                    QueryGrouping(
                        type="Dimension",
                        name="ServiceName"
                    )
                ]
            )
        )
        
        result = self.azure.cost_client.query.usage(
            scope=self.scope,
            parameters=query
        )
        
        services = []
        if result.rows:
            for row in result.rows:
                services.append({
                    "service": row[0],
                    "cost": float(row[1]),
                    "currency": row[2] if len(row) > 2 else "USD"
                })
        
        # Sort by cost descending
        services.sort(key=lambda x: x["cost"], reverse=True)
        return services
    
    def get_costs_by_resource_group(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get cost breakdown by resource group.
        """
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        query = QueryDefinition(
            type=ExportType.ACTUAL_COST,
            timeframe=TimeframeType.CUSTOM,
            time_period=QueryTimePeriod(
                from_property=datetime.combine(start_date, datetime.min.time()),
                to=datetime.combine(end_date, datetime.min.time())
            ),
            dataset=QueryDataset(
                granularity=GranularityType.NONE,
                aggregation={
                    "totalCost": QueryAggregation(
                        name="Cost",
                        function="Sum"
                    )
                },
                grouping=[
                    QueryGrouping(
                        type="Dimension",
                        name="ResourceGroup"
                    )
                ]
            )
        )
        
        result = self.azure.cost_client.query.usage(
            scope=self.scope,
            parameters=query
        )
        
        resource_groups = []
        if result.rows:
            for row in result.rows:
                resource_groups.append({
                    "resource_group": row[0],
                    "cost": float(row[1]),
                    "currency": row[2] if len(row) > 2 else "USD"
                })
        
        resource_groups.sort(key=lambda x: x["cost"], reverse=True)
        return resource_groups
    
    def get_monthly_summary(self) -> Dict[str, Any]:
        """
        Get current month cost summary with MTD and forecast.
        """
        now = datetime.utcnow()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Get MTD actual costs
        daily_costs = self.get_daily_costs(days=now.day)
        mtd_cost = sum(d["cost"] for d in daily_costs)
        
        # Simple forecast: (MTD / days elapsed) * days in month
        days_elapsed = now.day
        days_in_month = 30  # Simplified
        daily_avg = mtd_cost / days_elapsed if days_elapsed > 0 else 0
        forecast = daily_avg * days_in_month
        
        return {
            "mtd_cost": round(mtd_cost, 2),
            "daily_average": round(daily_avg, 2),
            "forecast": round(forecast, 2),
            "days_elapsed": days_elapsed,
            "currency": "USD",
            "last_updated": now.isoformat()
        }
