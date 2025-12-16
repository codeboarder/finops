"""
Service for fetching RI/SP recommendations from Azure Advisor and Consumption APIs.
"""
from datetime import datetime
from typing import Dict, List, Any, Optional
from .azure_client import AzureClientManager


class RecommendationService:
    """Fetches reservation and savings plan recommendations from Azure."""
    
    def __init__(self, tenant_id: str = None, client_id: str = None,
                 client_secret: str = None, subscription_id: str = None):
        self.azure = AzureClientManager(tenant_id, client_id, client_secret, subscription_id)
        self.scope = f"/subscriptions/{self.azure.subscription_id}"
    
    def get_reservation_recommendations(self) -> List[Dict[str, Any]]:
        """
        Get VM Reserved Instance recommendations from Azure Consumption API.
        Returns recommendations with potential savings.
        """
        recommendations = []
        
        try:
            # Get reservation recommendations
            result = self.azure.consumption_client.reservation_recommendations.list(
                scope=self.scope,
                filter="properties/scope eq 'Shared'"
            )
            
            for rec in result:
                # Extract properties based on recommendation type
                props = rec.as_dict()
                
                recommendations.append({
                    "id": props.get("id", ""),
                    "name": props.get("name", ""),
                    "sku": props.get("sku_properties", {}).get("name", "Unknown"),
                    "location": props.get("location", ""),
                    "term": props.get("term", "P1Y"),  # P1Y = 1 year, P3Y = 3 years
                    "look_back_period": props.get("look_back_period", "Last30Days"),
                    "recommended_quantity": props.get("recommended_quantity", 0),
                    "cost_with_no_ri": round(props.get("cost_with_no_reserved_instances", 0), 2),
                    "cost_with_ri": round(props.get("total_cost_with_reserved_instances", 0), 2),
                    "net_savings": round(props.get("net_savings", 0), 2),
                    "savings_percent": self._calculate_savings_percent(
                        props.get("cost_with_no_reserved_instances", 0),
                        props.get("total_cost_with_reserved_instances", 0)
                    ),
                    "first_usage_date": props.get("first_usage_date", ""),
                    "scope": props.get("scope", "Shared"),
                    "resource_type": props.get("resource_type", "VirtualMachines"),
                    "recommendation_type": "RI",
                    "fetched_at": datetime.utcnow().isoformat()
                })
        
        except Exception as e:
            print(f"Error fetching reservation recommendations: {e}")
        
        return recommendations
    
    def get_advisor_cost_recommendations(self) -> List[Dict[str, Any]]:
        """
        Get cost optimization recommendations from Azure Advisor.
        Includes RI recommendations and other cost savings.
        """
        recommendations = []
        
        try:
            # Get all recommendations, filter to Cost category
            result = self.azure.advisor_client.recommendations.list()
            
            for rec in result:
                props = rec.as_dict()
                
                # Only include Cost category recommendations
                if props.get("category") != "Cost":
                    continue
                
                # Parse extended properties for savings info
                extended = props.get("extended_properties", {})
                
                recommendations.append({
                    "id": props.get("id", ""),
                    "name": props.get("name", ""),
                    "category": props.get("category", ""),
                    "impact": props.get("impact", ""),  # High, Medium, Low
                    "impacted_field": props.get("impacted_field", ""),
                    "impacted_value": props.get("impacted_value", ""),
                    "short_description": props.get("short_description", {}).get("solution", ""),
                    "description": props.get("short_description", {}).get("problem", ""),
                    "recommendation_type_id": props.get("recommendation_type_id", ""),
                    "annual_savings": self._parse_savings(extended.get("annualSavingsAmount", "0")),
                    "savings_currency": extended.get("savingsCurrency", "USD"),
                    "region": extended.get("region", ""),
                    "sku": extended.get("currentSku", ""),
                    "target_sku": extended.get("targetSku", ""),
                    "resource_id": props.get("resource_metadata", {}).get("resource_id", ""),
                    "last_updated": props.get("last_updated", ""),
                    "fetched_at": datetime.utcnow().isoformat()
                })
        
        except Exception as e:
            print(f"Error fetching advisor recommendations: {e}")
        
        return recommendations
    
    def get_all_recommendations(self) -> Dict[str, Any]:
        """
        Get combined RI and Advisor recommendations with summary stats.
        """
        ri_recs = self.get_reservation_recommendations()
        advisor_recs = self.get_advisor_cost_recommendations()
        
        # Calculate totals
        ri_savings = sum(r.get("net_savings", 0) for r in ri_recs)
        advisor_savings = sum(r.get("annual_savings", 0) for r in advisor_recs)
        
        return {
            "reservation_recommendations": ri_recs,
            "advisor_recommendations": advisor_recs,
            "summary": {
                "total_ri_recommendations": len(ri_recs),
                "total_advisor_recommendations": len(advisor_recs),
                "potential_ri_savings": round(ri_savings, 2),
                "potential_advisor_savings": round(advisor_savings, 2),
                "total_potential_savings": round(ri_savings + advisor_savings, 2),
                "currency": "USD",
                "last_updated": datetime.utcnow().isoformat()
            }
        }
    
    def get_ri_coverage(self) -> Dict[str, Any]:
        """
        Get current RI coverage percentage.
        """
        try:
            # This requires the Consumption API reservation summaries
            # Simplified version - in production, use reservation_summaries endpoint
            return {
                "coverage_percent": 4.0,  # Placeholder - will enhance
                "target_percent": 25.0,
                "note": "Full coverage calculation requires additional API setup",
                "last_updated": datetime.utcnow().isoformat()
            }
        except Exception as e:
            print(f"Error calculating RI coverage: {e}")
            return {"coverage_percent": 0, "error": str(e)}
    
    def _calculate_savings_percent(self, cost_without: float, cost_with: float) -> float:
        """Calculate savings percentage."""
        if cost_without <= 0:
            return 0.0
        savings = ((cost_without - cost_with) / cost_without) * 100
        return round(savings, 1)
    
    def _parse_savings(self, value: str) -> float:
        """Parse savings amount from string."""
        try:
            return float(value.replace(",", "").replace("$", ""))
        except (ValueError, AttributeError):
            return 0.0
