"""
Main intelligence service - enriches Azure recommendations with business context.
"""
from datetime import date, datetime
from typing import Dict, List, Any, Optional
import re

from app.database import get_db
from app.models.workload_intelligence import (
    Workload, TechnologyEvaluation, RecommendationIntelligence,
    AgentAnalysis, WorkloadStatus, CommitmentAction, EvaluationStatus
)
from app.services.recommendation_service import RecommendationService
from app.agents.saas_evaluator import SaaSEvaluatorAgent


class IntelligenceService:
    """
    Enriches Azure recommendations with workload intelligence.
    
    This is the "brain" layer that prevents bad commitment decisions by:
    1. Matching recommendations to business workloads
    2. Checking for active technology evaluations
    3. Running AI analysis on evaluations
    4. Applying manual overrides
    5. Considering workload lifecycle status
    """
    
    def __init__(self):
        self.azure_recs = RecommendationService()
        self.saas_agent = SaaSEvaluatorAgent()
    
    def get_smart_recommendations(self) -> Dict[str, Any]:
        """
        Get Azure recommendations enriched with intelligence.
        
        Returns recommendations categorized by action:
        - approved: Safe to commit
        - modified: Commit with shorter term
        - hold: Wait for evaluation decision
        - blocked: Do not commit
        """
        # Get raw Azure recommendations
        azure_data = self.azure_recs.get_all_recommendations()
        
        # Enrich each recommendation
        enriched = []
        for rec in azure_data.get("reservation_recommendations", []):
            enriched.append(self._enrich_recommendation(rec, "RI"))
        
        for rec in azure_data.get("advisor_recommendations", []):
            enriched.append(self._enrich_recommendation(rec, "Advisor"))
        
        # Categorize by action
        approved = [r for r in enriched if r["intelligence"]["action"] == "approve"]
        modified = [r for r in enriched if r["intelligence"]["action"] == "modify"]
        hold = [r for r in enriched if r["intelligence"]["action"] == "hold"]
        blocked = [r for r in enriched if r["intelligence"]["action"] == "block"]
        
        return {
            "approved": approved,
            "modified": modified,
            "hold": hold,
            "blocked": blocked,
            "summary": {
                "total": len(enriched),
                "approved_count": len(approved),
                "approved_savings": sum(self._get_savings(r) for r in approved),
                "modified_count": len(modified),
                "modified_savings": sum(self._get_savings(r) for r in modified),
                "hold_count": len(hold),
                "hold_savings": sum(self._get_savings(r) for r in hold),
                "blocked_count": len(blocked),
                "blocked_savings": sum(self._get_savings(r) for r in blocked)
            }
        }
    
    def _get_savings(self, rec: Dict) -> float:
        """Extract savings from recommendation."""
        return rec.get("net_savings", 0) or rec.get("annual_savings", 0) or rec.get("monthly_savings", 0) or 0
    
    def _enrich_recommendation(self, rec: Dict, rec_type: str) -> Dict:
        """Add intelligence to a single recommendation."""
        
        with get_db() as db:
            # Try to match workload
            workload = self._match_workload(db, rec)
            
            # Check for blocking evaluations
            evaluation = self._find_blocking_evaluation(db, workload) if workload else None
            
            # Get latest agent analysis if exists
            agent_analysis = None
            if evaluation:
                agent_analysis = db.query(AgentAnalysis).filter(
                    AgentAnalysis.evaluation_id == evaluation.id
                ).order_by(AgentAnalysis.analyzed_at.desc()).first()
            
            # Check for manual override
            override = self._check_override(db, rec)
            
            # Determine action
            intelligence = self._determine_action(rec, workload, evaluation, agent_analysis, override)
            
            return {
                **rec,
                "recommendation_type": rec_type,
                "intelligence": intelligence,
                "workload": {
                    "id": workload.id if workload else None,
                    "name": workload.name if workload else None,
                    "status": workload.status.value if workload and workload.status else None,
                    "criticality": workload.criticality if workload else None
                } if workload else None,
                "evaluation": {
                    "id": evaluation.id,
                    "name": evaluation.name,
                    "status": evaluation.status.value if evaluation.status else None,
                    "decision_date": evaluation.decision_date.isoformat() if evaluation and evaluation.decision_date else None,
                    "adoption_probability": evaluation.adoption_probability_pct
                } if evaluation else None,
                "agent_analysis": {
                    "id": agent_analysis.id,
                    "risk_score": agent_analysis.risk_score,
                    "confidence": agent_analysis.confidence_score,
                    "summary": agent_analysis.analysis_summary,
                    "factors": agent_analysis.factors_analyzed,
                    "analyzed_at": agent_analysis.analyzed_at.isoformat()
                } if agent_analysis else None
            }
    
    def _match_workload(self, db, rec: Dict) -> Optional[Workload]:
        """Match recommendation to a workload based on resource patterns."""
        resource_id = rec.get("resource_id", "") or rec.get("scope", "") or ""
        sku = rec.get("sku", "") or rec.get("sku_name", "") or ""
        
        for workload in db.query(Workload).all():
            # Check resource group patterns
            if workload.resource_group_patterns:
                for pattern in workload.resource_group_patterns:
                    # Convert glob pattern to regex
                    regex_pattern = pattern.replace("*", ".*")
                    if re.search(regex_pattern, resource_id, re.IGNORECASE):
                        return workload
            
            # Check subscription IDs
            if workload.subscription_ids:
                for sub_id in workload.subscription_ids:
                    if sub_id.lower() in resource_id.lower():
                        return workload
        
        return None
    
    def _find_blocking_evaluation(self, db, workload: Workload) -> Optional[TechnologyEvaluation]:
        """Find any active evaluation that should block commitments."""
        if not workload:
            return None
        
        today = date.today()
        
        # Find evaluations that are actively blocking
        evaluation = db.query(TechnologyEvaluation).filter(
            TechnologyEvaluation.workload_id == workload.id,
            TechnologyEvaluation.hold_commitments == True,
            TechnologyEvaluation.status.in_([
                EvaluationStatus.EVALUATING,
                EvaluationStatus.POC,
                EvaluationStatus.PILOT
            ])
        ).first()
        
        # Check if hold has expired
        if evaluation and evaluation.hold_expires and evaluation.hold_expires < today:
            return None
        
        return evaluation
    
    def _check_override(self, db, rec: Dict) -> Optional[RecommendationIntelligence]:
        """Check for manual override."""
        rec_id = rec.get("id", "")
        
        if not rec_id:
            return None
        
        intel = db.query(RecommendationIntelligence).filter(
            RecommendationIntelligence.azure_recommendation_id == rec_id,
            RecommendationIntelligence.override_action.isnot(None)
        ).first()
        
        if intel and intel.override_expires and intel.override_expires < date.today():
            return None  # Override expired
        
        return intel
    
    def _determine_action(
        self,
        rec: Dict,
        workload: Optional[Workload],
        evaluation: Optional[TechnologyEvaluation],
        agent_analysis: Optional[AgentAnalysis],
        override: Optional[RecommendationIntelligence]
    ) -> Dict[str, Any]:
        """Determine the recommended action."""
        
        # Priority 1: Manual override
        if override and override.override_action:
            return {
                "action": override.override_action.value,
                "reason": f"Manual override: {override.override_reason}",
                "source": "override",
                "override_by": override.override_by,
                "override_expires": override.override_expires.isoformat() if override.override_expires else None
            }
        
        # Priority 2: Active evaluation with agent analysis
        if evaluation and agent_analysis:
            action = agent_analysis.recommended_action.value if agent_analysis.recommended_action else "hold"
            return {
                "action": action,
                "reason": agent_analysis.analysis_summary,
                "source": "agent_analysis",
                "risk_score": agent_analysis.risk_score,
                "confidence": agent_analysis.confidence_score,
                "evaluation_name": evaluation.name,
                "decision_date": evaluation.decision_date.isoformat() if evaluation.decision_date else None,
                "adoption_probability": evaluation.adoption_probability_pct
            }
        
        # Priority 3: Active evaluation without analysis
        if evaluation:
            return {
                "action": "hold",
                "reason": f"Active evaluation: {evaluation.name}. Run AI analysis for detailed assessment.",
                "source": "evaluation",
                "evaluation_name": evaluation.name,
                "decision_date": evaluation.decision_date.isoformat() if evaluation.decision_date else None,
                "needs_analysis": True
            }
        
        # Priority 4: Workload status
        if workload:
            if workload.status == WorkloadStatus.SUNSET:
                days_left = (workload.expected_end_date - date.today()).days if workload.expected_end_date else 0
                return {
                    "action": "block",
                    "reason": f"Workload '{workload.name}' scheduled for decommission in {days_left} days",
                    "source": "workload_lifecycle",
                    "sunset_date": workload.expected_end_date.isoformat() if workload.expected_end_date else None
                }
            
            if workload.status == WorkloadStatus.MIGRATING:
                return {
                    "action": "modify",
                    "reason": f"Workload '{workload.name}' migrating to {workload.migration_target}",
                    "source": "workload_lifecycle",
                    "max_term_months": workload.max_commitment_term_months,
                    "migration_target": workload.migration_target
                }
            
            if workload.status == WorkloadStatus.EVALUATING:
                return {
                    "action": "hold",
                    "reason": f"Workload '{workload.name}' under evaluation",
                    "source": "workload_lifecycle"
                }
        
        # Default: Approve
        return {
            "action": "approve",
            "reason": "No blocking factors identified" + (
                f". Workload '{workload.name}' is {workload.status.value}." if workload else ""
            ),
            "source": "default"
        }
    
    def run_analysis(self, evaluation_id: int) -> Dict[str, Any]:
        """Run SaaS evaluator agent on an evaluation."""
        return self.saas_agent.analyze(evaluation_id)
    
    def set_override(
        self,
        recommendation_id: str,
        action: str,
        reason: str,
        override_by: str,
        expires_date: Optional[date] = None
    ) -> RecommendationIntelligence:
        """Set a manual override for a recommendation."""
        
        with get_db() as db:
            intel = db.query(RecommendationIntelligence).filter(
                RecommendationIntelligence.azure_recommendation_id == recommendation_id
            ).first()
            
            if not intel:
                intel = RecommendationIntelligence(
                    azure_recommendation_id=recommendation_id
                )
                db.add(intel)
            
            intel.override_action = CommitmentAction(action)
            intel.override_reason = reason
            intel.override_by = override_by
            intel.override_at = datetime.utcnow()
            intel.override_expires = expires_date
            
            db.commit()
            db.refresh(intel)
            return intel
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of AI agents including RL integration."""
        return self.saas_agent.get_rl_status()


# Singleton instance
intelligence_service = IntelligenceService()
