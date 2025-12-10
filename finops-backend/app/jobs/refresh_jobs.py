"""
Background jobs for data refresh and anomaly detection.
"""
import logging
import json
from datetime import datetime, date, timedelta
from typing import Optional

from app.database import get_db
from app.models.cost_history import (
    DailyCostHistory, 
    ServiceCostHistory, 
    AnomalyRecord,
    BudgetStatus,
    RecommendationCache,
    RICoverage
)

logger = logging.getLogger(__name__)


async def refresh_daily_costs():
    """
    Fetch latest daily costs and store in history.
    Runs every hour.
    """
    logger.info("Starting daily costs refresh...")
    
    try:
        from app.services.cost_service import CostService
        cost_service = CostService()
        
        # Get last 7 days to catch any late-arriving data
        daily_costs = cost_service.get_daily_costs(days=7)
        costs_by_service = cost_service.get_costs_by_service(days=7)
        
        with get_db() as db:
            for day_data in daily_costs:
                cost_date = _parse_date(day_data["date"])
                
                # Upsert daily total
                existing = db.query(DailyCostHistory).filter(
                    DailyCostHistory.date == cost_date
                ).first()
                
                if existing:
                    existing.total_cost = day_data["cost"]
                    existing.updated_at = datetime.utcnow()
                else:
                    record = DailyCostHistory(
                        date=cost_date,
                        total_cost=day_data["cost"],
                        currency=day_data.get("currency", "USD")
                    )
                    db.add(record)
            
            # Store service breakdown
            for svc_data in costs_by_service:
                # Simplified: store today's service costs
                today = date.today()
                existing = db.query(ServiceCostHistory).filter(
                    ServiceCostHistory.date == today,
                    ServiceCostHistory.service_name == svc_data["service"]
                ).first()
                
                if existing:
                    existing.cost = svc_data["cost"]
                else:
                    record = ServiceCostHistory(
                        date=today,
                        service_name=svc_data["service"],
                        cost=svc_data["cost"],
                        currency=svc_data.get("currency", "USD")
                    )
                    db.add(record)
            
            db.commit()
        
        logger.info(f"Daily costs refresh complete - {len(daily_costs)} days updated")
        
    except Exception as e:
        logger.error(f"Daily costs refresh failed: {e}")


async def refresh_recommendations():
    """
    Fetch latest RI/SP recommendations and cache them.
    Runs every 6 hours.
    """
    logger.info("Starting recommendations refresh...")
    
    try:
        from app.services.recommendation_service import RecommendationService
        rec_service = RecommendationService()
        all_recs = rec_service.get_all_recommendations()
        
        with get_db() as db:
            # Clear old cache
            db.query(RecommendationCache).delete()
            
            # Store RI recommendations
            for rec in all_recs.get("reservation_recommendations", []):
                cache_record = RecommendationCache(
                    recommendation_id=rec.get("id", f"ri-{datetime.utcnow().timestamp()}"),
                    recommendation_type="RI",
                    data_json=json.dumps(rec),
                    potential_savings=rec.get("net_savings", 0),
                    currency="USD",
                    impact="High" if rec.get("net_savings", 0) > 10000 else "Medium"
                )
                db.add(cache_record)
            
            # Store Advisor recommendations
            for rec in all_recs.get("advisor_recommendations", []):
                cache_record = RecommendationCache(
                    recommendation_id=rec.get("id", f"adv-{datetime.utcnow().timestamp()}"),
                    recommendation_type="Advisor",
                    data_json=json.dumps(rec),
                    potential_savings=rec.get("annual_savings", 0),
                    currency="USD",
                    impact=rec.get("impact", "Medium")
                )
                db.add(cache_record)
            
            db.commit()
        
        total = len(all_recs.get("reservation_recommendations", [])) + \
                len(all_recs.get("advisor_recommendations", []))
        logger.info(f"Recommendations refresh complete - {total} recommendations cached")
        
    except Exception as e:
        logger.error(f"Recommendations refresh failed: {e}")


async def refresh_budgets():
    """
    Fetch Azure Budget status and update cache.
    Runs every hour.
    """
    logger.info("Starting budgets refresh...")
    
    try:
        from app.services.budget_service import BudgetService
        budget_service = BudgetService()
        budgets = budget_service.get_all_budgets()
        
        with get_db() as db:
            for budget in budgets:
                existing = db.query(BudgetStatus).filter(
                    BudgetStatus.budget_name == budget["name"]
                ).first()
                
                if existing:
                    existing.current_spend = budget.get("current_spend", 0)
                    existing.forecasted_spend = budget.get("forecasted_spend", 0)
                    existing.spend_pct = budget.get("spend_pct", 0)
                    existing.threshold_60_status = "triggered" if budget.get("spend_pct", 0) >= 60 else "ok"
                    existing.threshold_80_status = "triggered" if budget.get("spend_pct", 0) >= 80 else "ok"
                    existing.threshold_90_status = "triggered" if budget.get("spend_pct", 0) >= 90 else "ok"
                    existing.threshold_100_status = "triggered" if budget.get("spend_pct", 0) >= 100 else "ok"
                    existing.last_synced = datetime.utcnow()
                else:
                    record = BudgetStatus(
                        budget_name=budget["name"],
                        budget_amount=budget.get("amount", 0),
                        time_grain=budget.get("time_grain", "Monthly"),
                        current_spend=budget.get("current_spend", 0),
                        forecasted_spend=budget.get("forecasted_spend", 0),
                        spend_pct=budget.get("spend_pct", 0),
                        category=budget.get("category"),
                        resource_group=budget.get("resource_group")
                    )
                    db.add(record)
            
            db.commit()
        
        logger.info(f"Budgets refresh complete - {len(budgets)} budgets updated")
        
    except Exception as e:
        logger.error(f"Budgets refresh failed: {e}")


async def detect_anomalies():
    """
    Compare current costs against baseline and detect anomalies.
    Runs every hour.
    """
    logger.info("Starting anomaly detection...")
    
    THRESHOLD_PCT = 25.0  # Alert if >25% above baseline
    
    try:
        with get_db() as db:
            # Get last 30 days for baseline
            thirty_days_ago = date.today() - timedelta(days=30)
            yesterday = date.today() - timedelta(days=1)
            
            # Calculate baseline (average of last 30 days, excluding yesterday)
            baseline_records = db.query(DailyCostHistory).filter(
                DailyCostHistory.date >= thirty_days_ago,
                DailyCostHistory.date < yesterday
            ).all()
            
            if not baseline_records:
                logger.warning("Not enough historical data for anomaly detection")
                return
            
            baseline_avg = sum(r.total_cost for r in baseline_records) / len(baseline_records)
            
            # Get yesterday's cost
            yesterday_record = db.query(DailyCostHistory).filter(
                DailyCostHistory.date == yesterday
            ).first()
            
            if not yesterday_record:
                logger.warning("No data for yesterday - skipping anomaly check")
                return
            
            actual = yesterday_record.total_cost
            variance_pct = ((actual - baseline_avg) / baseline_avg) * 100 if baseline_avg > 0 else 0
            variance_amount = actual - baseline_avg
            
            # Check if anomaly
            if variance_pct > THRESHOLD_PCT:
                # Check if we already recorded this anomaly
                existing = db.query(AnomalyRecord).filter(
                    AnomalyRecord.anomaly_date == yesterday,
                    AnomalyRecord.metric == "daily_total"
                ).first()
                
                if not existing:
                    severity = "critical" if variance_pct > 50 else "high" if variance_pct > 35 else "medium"
                    
                    anomaly = AnomalyRecord(
                        anomaly_date=yesterday,
                        metric="daily_total",
                        actual_value=actual,
                        baseline_value=baseline_avg,
                        threshold_pct=THRESHOLD_PCT,
                        variance_pct=round(variance_pct, 1),
                        variance_amount=round(variance_amount, 2),
                        severity=severity,
                        status="open"
                    )
                    db.add(anomaly)
                    db.commit()
                    
                    logger.warning(
                        f"ANOMALY DETECTED: Yesterday's cost ${actual:,.0f} is "
                        f"{variance_pct:.1f}% above baseline ${baseline_avg:,.0f}"
                    )
            else:
                logger.info(
                    f"No anomaly: Yesterday ${actual:,.0f} vs baseline ${baseline_avg:,.0f} "
                    f"({variance_pct:+.1f}%)"
                )
        
    except Exception as e:
        logger.error(f"Anomaly detection failed: {e}")


def _parse_date(date_val) -> date:
    """Parse date from string or return as-is."""
    if isinstance(date_val, date):
        return date_val
    if isinstance(date_val, str):
        return datetime.fromisoformat(date_val.replace("Z", "")).date()
    return date.today()
