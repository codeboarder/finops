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
        # Azure returns columns in order: ['Cost', 'UsageDate', 'Currency']
        costs = []
        if result.rows:
            for row in result.rows:
                # Column order: Cost (index 0), UsageDate (index 1), Currency (index 2)
                cost_val = float(row[0]) if row[0] is not None else 0.0
                date_val = row[1]
                currency = row[2] if len(row) > 2 else "USD"
                
                # Handle different date formats from Azure API
                if isinstance(date_val, str):
                    date_str = date_val
                elif hasattr(date_val, 'isoformat'):
                    date_str = date_val.isoformat()
                elif isinstance(date_val, (int, float)):
                    # Azure returns dates as numeric values (YYYYMMDD format)
                    date_str = str(int(date_val))
                else:
                    date_str = str(date_val)
                
                costs.append({
                    "date": date_str,
                    "cost": cost_val,
                    "currency": currency
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
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """
        Get cost summary for discovery - monthly spend and AI savings.
        """
        try:
            summary = self.get_monthly_summary()
            
            # Get AI savings from advisor recommendations
            from .recommendation_service import RecommendationService
            rec_service = RecommendationService(
                self.azure.tenant_id,
                self.azure.client_id, 
                self.azure.client_secret,
                self.azure.subscription_id
            )
            ai_savings = rec_service.get_total_savings()
            
            return {
                "monthly_spend": summary.get("mtd_cost", 0),
                "ai_savings": ai_savings,
                "daily_average": summary.get("daily_average", 0),
                "forecast": summary.get("forecast", 0)
            }
        except Exception as e:
            print(f"Error getting cost summary: {e}")
            return {
                "monthly_spend": 0,
                "ai_savings": 0,
                "daily_average": 0,
                "forecast": 0
            }
