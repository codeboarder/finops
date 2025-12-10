"""
Service for fetching Azure Budget data.
"""
from datetime import datetime
from typing import Dict, List, Any
from .azure_client import get_azure_manager


class BudgetService:
    """Fetches Azure Budget configurations and status."""
    
    def __init__(self):
        self.azure = get_azure_manager()
        self.scope = f"/subscriptions/{self.azure.subscription_id}"
    
    def get_all_budgets(self) -> List[Dict[str, Any]]:
        """
        Get all budgets for the subscription with current spend.
        """
        budgets = []
        
        try:
            result = self.azure.consumption_client.budgets.list(scope=self.scope)
            
            for budget in result:
                props = budget.as_dict()
                
                # Calculate spend percentage
                amount = props.get("amount", 0)
                current_spend = props.get("current_spend", {}).get("amount", 0)
                spend_pct = (current_spend / amount * 100) if amount > 0 else 0
                
                # Get forecast if available
                forecast = props.get("forecast_spend", {}).get("amount", 0)
                
                budgets.append({
                    "id": props.get("id", ""),
                    "name": props.get("name", ""),
                    "amount": amount,
                    "time_grain": props.get("time_grain", "Monthly"),
                    "current_spend": round(current_spend, 2),
                    "forecasted_spend": round(forecast, 2),
                    "spend_pct": round(spend_pct, 1),
                    "category": props.get("category", "Cost"),
                    "resource_group": self._extract_resource_group(props.get("id", "")),
                    "notifications": self._parse_notifications(props.get("notifications", {})),
                    "start_date": props.get("time_period", {}).get("start_date", ""),
                    "end_date": props.get("time_period", {}).get("end_date", ""),
                    "fetched_at": datetime.utcnow().isoformat()
                })
        
        except Exception as e:
            print(f"Error fetching budgets: {e}")
        
        return budgets
    
    def get_budget_summary(self) -> Dict[str, Any]:
        """
        Get summary of all budgets with status counts.
        """
        budgets = self.get_all_budgets()
        
        total_budget = sum(b["amount"] for b in budgets)
        total_spend = sum(b["current_spend"] for b in budgets)
        
        # Count by status
        healthy = sum(1 for b in budgets if b["spend_pct"] < 80)
        warning = sum(1 for b in budgets if 80 <= b["spend_pct"] < 100)
        critical = sum(1 for b in budgets if b["spend_pct"] >= 100)
        
        return {
            "total_budgets": len(budgets),
            "total_budget_amount": round(total_budget, 2),
            "total_current_spend": round(total_spend, 2),
            "overall_spend_pct": round((total_spend / total_budget * 100) if total_budget > 0 else 0, 1),
            "status_counts": {
                "healthy": healthy,
                "warning": warning,
                "critical": critical
            },
            "budgets": budgets,
            "last_updated": datetime.utcnow().isoformat()
        }
    
    def _extract_resource_group(self, resource_id: str) -> str:
        """Extract resource group from resource ID."""
        if "/resourceGroups/" in resource_id:
            parts = resource_id.split("/resourceGroups/")
            if len(parts) > 1:
                return parts[1].split("/")[0]
        return ""
    
    def _parse_notifications(self, notifications: Dict) -> List[Dict]:
        """Parse budget notification thresholds."""
        parsed = []
        for name, config in notifications.items():
            parsed.append({
                "name": name,
                "threshold": config.get("threshold", 0),
                "operator": config.get("operator", "GreaterThan"),
                "enabled": config.get("enabled", True)
            })
        return parsed
