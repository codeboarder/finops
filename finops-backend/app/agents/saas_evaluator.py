"""
SaaS Evaluator Agent - Analyzes technology evaluations to determine
commitment risk for affected Azure workloads.

Uses Microsoft Agent Lightning for RL-based continuous improvement.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, date
import json

from app.agents.base_agent import BaseAgent, AGENT_LIGHTNING_AVAILABLE
from app.models.workload_intelligence import (
    TechnologyEvaluation, EvaluationDocument, WorkloadDocument,
    WorkloadContext, AgentAnalysis, CommitmentAction
)
from app.database import get_db


class SaaSEvaluatorAgent(BaseAgent):
    """
    Analyzes SaaS/technology evaluations to assess commitment risk.
    
    Factors analyzed:
    - POC/pilot success metrics
    - Executive sponsorship level
    - Vendor pricing vs current Azure spend
    - Migration complexity
    - Timeline confidence
    - Historical evaluation patterns
    - Document content (proposals, reviews)
    - User-provided context
    
    Integrates with Microsoft Agent Lightning for:
    - Trace collection for RL training
    - Reward signals from user feedback
    - Continuous model improvement
    """
    
    def __init__(self):
        super().__init__()
        self.agent_type = "saas_evaluator"
        self.agent_version = "1.0.0"
    
    def analyze(self, evaluation_id: int) -> Dict[str, Any]:
        """
        Run full analysis on a technology evaluation.
        
        Returns:
            {
                "analysis_id": 123,
                "risk_score": 7.2,
                "confidence": 85,
                "recommended_action": "hold",
                "factors": [...],
                "reasoning": "...",
                "summary": "...",
                "validated": true,
                "rl_trace_id": "..."
            }
        """
        start_time = datetime.utcnow()
        
        with get_db() as db:
            # Load evaluation and related data
            evaluation = db.query(TechnologyEvaluation).filter(
                TechnologyEvaluation.id == evaluation_id
            ).first()
            
            if not evaluation:
                raise ValueError(f"Evaluation {evaluation_id} not found")
            
            # Gather all context
            context = self._gather_context(db, evaluation)
            
            # Build prompts
            system_prompt = self._get_system_prompt()
            user_prompt = self._build_user_prompt(context)
            
            # Call primary LLM (GPT-5)
            response = self._call_llm(system_prompt, user_prompt)
            result = self._extract_json(response)
            
            # Validate with secondary model (GPT-4.1)
            validation_result = self._validate_analysis(result, context)
            
            # Calculate duration
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            # Determine final action based on validation
            final_action = result.get("recommended_action", "hold")
            if validation_result and validation_result.get("override_action"):
                final_action = validation_result["override_action"]
            
            # Store analysis
            analysis = AgentAnalysis(
                evaluation_id=evaluation_id,
                agent_type=self.agent_type,
                agent_version=self.agent_version,
                risk_score=result.get("risk_score", 5.0),
                confidence_score=result.get("confidence", 50),
                recommended_action=CommitmentAction(final_action),
                analysis_summary=result.get("summary", ""),
                factors_analyzed=result.get("factors", []),
                reasoning=result.get("reasoning", ""),
                input_context=user_prompt[:5000],  # Truncate for storage
                analyzed_at=datetime.utcnow(),
                analysis_duration_ms=duration_ms,
                model_used=self.deployment
            )
            db.add(analysis)
            db.commit()
            db.refresh(analysis)
            
            # Generate RL trace ID for feedback
            rl_trace_id = f"saas_eval_{evaluation_id}_{analysis.id}_{int(datetime.utcnow().timestamp())}"
            
            return {
                "analysis_id": analysis.id,
                "risk_score": result.get("risk_score", 5.0),
                "confidence": result.get("confidence", 50),
                "recommended_action": final_action,
                "factors": result.get("factors", []),
                "reasoning": result.get("reasoning", ""),
                "summary": result.get("summary", ""),
                "validated": validation_result is not None,
                "validation_notes": validation_result.get("notes") if validation_result else None,
                "rl_trace_id": rl_trace_id,
                "duration_ms": duration_ms,
                "agent_lightning_enabled": AGENT_LIGHTNING_AVAILABLE
            }
    
    def _validate_analysis(self, primary_result: Dict, context: Dict) -> Optional[Dict]:
        """
        Use GPT-4.1 to validate the primary analysis.
        Returns validation result or None if validation fails.
        """
        validation_prompt = f"""You are a FinOps validation agent. Review this analysis and confirm or override it.

PRIMARY ANALYSIS:
Risk Score: {primary_result.get('risk_score', 'N/A')}/10
Recommended Action: {primary_result.get('recommended_action', 'N/A')}
Reasoning: {primary_result.get('reasoning', 'N/A')}

CONTEXT:
Evaluation: {context['evaluation']['name']}
Vendor: {context['evaluation']['vendor']}
POC Success: {context['evaluation']['poc_success_score']}/100
Adoption Probability: {context['evaluation']['adoption_probability']}%
Monthly Spend at Risk: ${context['evaluation']['monthly_spend_affected']:,.0f}

Respond with JSON:
{{
    "validated": true/false,
    "override_action": null or "approve"/"modify"/"hold"/"block",
    "notes": "brief validation notes"
}}"""

        try:
            response = self._call_validator(
                "You are a FinOps validation agent. Be concise.",
                validation_prompt
            )
            if response:
                return self._extract_json(response)
        except Exception as e:
            print(f"Validation failed: {e}")
        
        return None
    
    def _gather_context(self, db, evaluation: TechnologyEvaluation) -> Dict[str, Any]:
        """Gather all relevant context for analysis."""
        
        # Get workload info
        workload = evaluation.workload
        
        # Get documents
        eval_docs = db.query(EvaluationDocument).filter(
            EvaluationDocument.evaluation_id == evaluation.id
        ).all()
        
        workload_docs = []
        context_notes = []
        
        if workload:
            workload_docs = db.query(WorkloadDocument).filter(
                WorkloadDocument.workload_id == workload.id
            ).all()
            
            context_notes = db.query(WorkloadContext).filter(
                WorkloadContext.workload_id == workload.id
            ).order_by(WorkloadContext.added_at.desc()).limit(10).all()
        
        # Get previous analyses
        prev_analyses = db.query(AgentAnalysis).filter(
            AgentAnalysis.evaluation_id == evaluation.id
        ).order_by(AgentAnalysis.analyzed_at.desc()).limit(3).all()
        
        return {
            "evaluation": {
                "name": evaluation.name,
                "vendor": evaluation.vendor,
                "type": evaluation.evaluation_type,
                "status": evaluation.status.value if evaluation.status else "unknown",
                "started": evaluation.started_date.isoformat() if evaluation.started_date else None,
                "decision_date": evaluation.decision_date.isoformat() if evaluation.decision_date else None,
                "adoption_probability": evaluation.adoption_probability_pct or 50,
                "poc_success_score": evaluation.poc_success_score or 0,
                "poc_notes": evaluation.poc_notes,
                "executive_sponsor": evaluation.executive_sponsor,
                "affected_services": evaluation.affected_azure_services or [],
                "monthly_spend_affected": evaluation.estimated_monthly_spend_affected or 0
            },
            "workload": {
                "name": workload.name if workload else "Unknown",
                "status": workload.status.value if workload and workload.status else "unknown",
                "criticality": workload.criticality if workload else "standard",
                "owner": workload.owner_name if workload else None
            },
            "documents": [
                {
                    "filename": doc.original_filename,
                    "type": doc.document_type,
                    "content": doc.extracted_text[:5000] if doc.extracted_text else None
                }
                for doc in eval_docs
            ],
            "workload_documents": [
                {
                    "filename": doc.original_filename,
                    "content": doc.extracted_text[:3000] if doc.extracted_text else None
                }
                for doc in workload_docs[:3]
            ],
            "context_notes": [
                {
                    "content": note.content,
                    "added_by": note.added_by,
                    "date": note.added_at.isoformat()
                }
                for note in context_notes
            ],
            "previous_analyses": [
                {
                    "risk_score": a.risk_score,
                    "action": a.recommended_action.value if a.recommended_action else None,
                    "date": a.analyzed_at.isoformat()
                }
                for a in prev_analyses
            ]
        }
    
    def _get_system_prompt(self) -> str:
        return """You are a FinOps AI agent specializing in evaluating SaaS and technology transitions 
to assess Azure commitment risk. Your job is to analyze whether an organization should commit 
to Azure Reserved Instances or Savings Plans for workloads that might be replaced by SaaS solutions.

You analyze:
1. POC/pilot success indicators
2. Executive sponsorship and organizational buy-in
3. Vendor pricing competitiveness
4. Migration complexity and timeline
5. Historical patterns in similar evaluations
6. Document content (proposals, security reviews, TCO analyses)
7. User-provided context and notes

Output your analysis as JSON with this structure:
```json
{
    "risk_score": <0-10, where 10 = highest risk, do not commit>,
    "confidence": <0-100, your confidence in this assessment>,
    "recommended_action": <"approve" | "modify" | "hold" | "block">,
    "factors": [
        {"factor": "<name>", "score": <contribution to risk, can be negative>, "reasoning": "<why>"}
    ],
    "reasoning": "<2-3 sentence explanation of your overall assessment>",
    "summary": "<1 sentence recommendation for display>"
}
```

Risk score interpretation:
- 0-3: Low risk, safe to commit (approve)
- 4-5: Moderate risk, consider shorter term (modify)
- 6-7: High risk, recommend holding until decision (hold)
- 8-10: Very high risk, do not commit (block)

Be decisive. Factor in all available information. If POC metrics are positive, executive sponsor 
is engaged, and timeline is credible, the adoption probability should be weighted heavily."""

    def _build_user_prompt(self, context: Dict[str, Any]) -> str:
        monthly_spend = context['evaluation']['monthly_spend_affected']
        if monthly_spend is None:
            monthly_spend = 0
            
        return f"""Analyze this technology evaluation for commitment risk:

## EVALUATION DETAILS
Name: {context['evaluation']['name']}
Vendor: {context['evaluation']['vendor']}
Type: {context['evaluation']['type']}
Current Status: {context['evaluation']['status']}
Started: {context['evaluation']['started']}
Decision Date: {context['evaluation']['decision_date']}
Current Adoption Probability: {context['evaluation']['adoption_probability']}%
POC Success Score: {context['evaluation']['poc_success_score']}/100
Executive Sponsor: {context['evaluation']['executive_sponsor']}
Affected Azure Services: {context['evaluation']['affected_services']}
Monthly Spend at Risk: ${monthly_spend:,.0f}

## POC NOTES
{context['evaluation']['poc_notes'] or 'No POC notes available'}

## AFFECTED WORKLOAD
Name: {context['workload']['name']}
Status: {context['workload']['status']}
Criticality: {context['workload']['criticality']}
Owner: {context['workload']['owner']}

## UPLOADED DOCUMENTS
{self._format_documents(context['documents'])}

## USER-PROVIDED CONTEXT
{self._format_context_notes(context['context_notes'])}

## PREVIOUS ANALYSES
{self._format_previous_analyses(context['previous_analyses'])}

Based on all this information, provide your risk assessment for committing to Azure Reserved 
Instances or Savings Plans for the affected workloads."""

    def _format_documents(self, docs: List[Dict]) -> str:
        if not docs:
            return "No documents uploaded"
        
        result = []
        for doc in docs:
            result.append(f"### {doc['filename']} ({doc['type']})")
            if doc['content']:
                result.append(doc['content'][:2000])
            result.append("")
        return "\n".join(result)
    
    def _format_context_notes(self, notes: List[Dict]) -> str:
        if not notes:
            return "No context notes provided"
        
        result = []
        for note in notes:
            result.append(f"- [{note['date']}] {note['added_by']}: {note['content']}")
        return "\n".join(result)
    
    def _format_previous_analyses(self, analyses: List[Dict]) -> str:
        if not analyses:
            return "No previous analyses"
        
        result = []
        for a in analyses:
            result.append(f"- {a['date']}: Risk {a['risk_score']}/10, Action: {a['action']}")
        return "\n".join(result)
    
    def provide_feedback(self, analysis_id: int, feedback: str, reward: float):
        """
        Provide feedback on an analysis for RL training.
        
        Args:
            analysis_id: The analysis to provide feedback on
            feedback: Text feedback (accepted, rejected, modified)
            reward: Reward signal (-1 to 1)
        """
        rl_trace_id = f"saas_eval_feedback_{analysis_id}_{int(datetime.utcnow().timestamp())}"
        
        self.emit_reward(
            trace_id=rl_trace_id,
            reward=reward,
            metadata={
                "analysis_id": analysis_id,
                "feedback": feedback,
                "agent_type": self.agent_type
            }
        )
        
        return {"status": "feedback_recorded", "trace_id": rl_trace_id}
