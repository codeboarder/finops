"""
Base class for AI agents with Microsoft Agent Lightning integration for RL.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
import json
import re
from openai import AzureOpenAI

# Microsoft Agent Lightning integration for RL
try:
    import agentlightning as agl
    from agentlightning.tracer import OtelTracer
    AGENT_LIGHTNING_AVAILABLE = True
except ImportError:
    AGENT_LIGHTNING_AVAILABLE = False
    agl = None
    OtelTracer = None


class BaseAgent(ABC):
    """
    Base class for all FinOps AI agents.
    
    Features:
    - Multi-model Azure OpenAI integration (GPT-5, O3, O4-Mini, GPT-4.1)
    - Microsoft Agent Lightning for RL training
    - Automatic trace collection for continuous improvement
    - Ensemble validation across multiple models
    """
    
    def __init__(self):
        # Primary model (GPT-5) - Main analyzer
        self.client = AzureOpenAI(
            azure_endpoint=os.getenv("GPT5_ENDPOINT", os.getenv("AZURE_OPENAI_ENDPOINT")),
            api_key=os.getenv("GPT5_API_KEY", os.getenv("AZURE_OPENAI_API_KEY")),
            api_version="2025-01-01-preview"
        )
        self.deployment = os.getenv("GPT5_DEPLOYMENT", "gpt-5")
        
        # O3 - Large Reasoning Model for deep validation
        self.o3_client = None
        o3_endpoint = os.getenv("O3_ENDPOINT")
        o3_key = os.getenv("O3_API_KEY")
        if o3_endpoint and o3_key:
            self.o3_client = AzureOpenAI(
                azure_endpoint=o3_endpoint,
                api_key=o3_key,
                api_version="2025-01-01-preview"
            )
        self.o3_deployment = "o3"
        
        # O4-Mini - Fast secondary validator
        self.o4_mini_client = None
        o4_endpoint = os.getenv("O4_MINI_ENDPOINT")
        o4_key = os.getenv("O4_MINI_API_KEY")
        if o4_endpoint and o4_key:
            self.o4_mini_client = AzureOpenAI(
                azure_endpoint=o4_endpoint,
                api_key=o4_key,
                api_version="2025-01-01-preview"
            )
        self.o4_mini_deployment = "o4-mini"
        
        # GPT-4.1 - Alternative analyzer for ensemble
        self.gpt41_client = None
        gpt41_endpoint = os.getenv("GPT41_ENDPOINT")
        gpt41_key = os.getenv("GPT41_API_KEY")
        if gpt41_endpoint and gpt41_key:
            self.gpt41_client = AzureOpenAI(
                azure_endpoint=gpt41_endpoint,
                api_key=gpt41_key,
                api_version="2024-02-15-preview"
            )
        self.gpt41_deployment = "gpt-4.1"
        
        # Legacy validator reference (for backward compatibility)
        self.validator_client = self.gpt41_client or self.client
        self.validator_deployment = self.gpt41_deployment if self.gpt41_client else self.deployment
        
        # Agent metadata
        self.agent_type = "base"
        self.agent_version = "1.0.0"
        
        # Track available models
        self.available_models = {
            "gpt5": True,
            "o3": self.o3_client is not None,
            "o4_mini": self.o4_mini_client is not None,
            "gpt41": self.gpt41_client is not None
        }
        
        # Agent Lightning tracer for RL
        self.tracer = None
        if AGENT_LIGHTNING_AVAILABLE:
            try:
                self.tracer = OtelTracer(
                    service_name=f"finops-{self.agent_type}",
                    enable_console=False
                )
            except Exception as e:
                print(f"Agent Lightning tracer init failed: {e}")
                self.tracer = None
    
    @abstractmethod
    def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run analysis and return results."""
        pass
    
    def _call_llm(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
        """Make LLM call with Agent Lightning tracing."""
        start_time = datetime.utcnow()
        
        # Emit trace start if Agent Lightning is available
        trace_id = None
        if self.tracer and AGENT_LIGHTNING_AVAILABLE:
            try:
                trace_id = self.tracer.start_span(
                    name=f"{self.agent_type}_llm_call",
                    attributes={
                        "agent_type": self.agent_type,
                        "model": self.deployment,
                        "prompt_length": len(user_prompt)
                    }
                )
            except Exception:
                pass
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=2000
            )
            result = response.choices[0].message.content
            
            # Emit trace end with success
            if trace_id and self.tracer:
                try:
                    duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                    self.tracer.end_span(
                        trace_id,
                        attributes={
                            "status": "success",
                            "duration_ms": duration_ms,
                            "response_length": len(result) if result else 0
                        }
                    )
                except Exception:
                    pass
            
            return result
            
        except Exception as e:
            # Emit trace end with error
            if trace_id and self.tracer:
                try:
                    self.tracer.end_span(
                        trace_id,
                        attributes={
                            "status": "error",
                            "error": str(e)
                        }
                    )
                except Exception:
                    pass
            raise
    
    def _call_validator(self, system_prompt: str, user_prompt: str, temperature: float = 0.1) -> str:
        """Call validator model (GPT-4.1) for cross-validation."""
        try:
            response = self.validator_client.chat.completions.create(
                model=self.validator_deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Validator call failed: {e}")
            return None
    
    def _call_o3(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Call O3 reasoning model for deep analysis validation."""
        if not self.o3_client:
            return None
        try:
            response = self.o3_client.chat.completions.create(
                model=self.o3_deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"O3 call failed: {e}")
            return None
    
    def _call_o4_mini(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> Optional[str]:
        """Call O4-Mini for fast secondary validation."""
        if not self.o4_mini_client:
            return None
        try:
            response = self.o4_mini_client.chat.completions.create(
                model=self.o4_mini_deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"O4-Mini call failed: {e}")
            return None
    
    def _call_gpt41(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> Optional[str]:
        """Call GPT-4.1 for alternative analysis."""
        if not self.gpt41_client:
            return None
        try:
            response = self.gpt41_client.chat.completions.create(
                model=self.gpt41_deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=1500
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"GPT-4.1 call failed: {e}")
            return None
    
    def _ensemble_analyze(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """
        Run ensemble analysis across multiple models for higher confidence.
        Returns aggregated results with confidence scoring.
        """
        results = {}
        
        # Primary analysis with GPT-5
        gpt5_result = self._call_llm(system_prompt, user_prompt)
        results["gpt5"] = self._extract_json(gpt5_result) if gpt5_result else None
        
        # O3 deep reasoning (if available)
        if self.o3_client:
            o3_result = self._call_o3(system_prompt, user_prompt)
            results["o3"] = self._extract_json(o3_result) if o3_result else None
        
        # O4-Mini fast validation (if available)
        if self.o4_mini_client:
            o4_result = self._call_o4_mini(system_prompt, user_prompt)
            results["o4_mini"] = self._extract_json(o4_result) if o4_result else None
        
        # GPT-4.1 alternative (if available)
        if self.gpt41_client:
            gpt41_result = self._call_gpt41(system_prompt, user_prompt)
            results["gpt41"] = self._extract_json(gpt41_result) if gpt41_result else None
        
        # Calculate ensemble confidence
        valid_results = [r for r in results.values() if r and "risk_score" in r]
        if valid_results:
            avg_risk = sum(r.get("risk_score", 5) for r in valid_results) / len(valid_results)
            confidence_boost = min(len(valid_results) * 5, 15)  # Up to 15% boost for multi-model agreement
            
            return {
                "ensemble_result": results.get("gpt5") or valid_results[0],
                "model_results": results,
                "models_used": [k for k, v in results.items() if v],
                "ensemble_risk_score": round(avg_risk, 1),
                "ensemble_confidence": min(95, 70 + confidence_boost),
                "agreement_level": "high" if len(valid_results) >= 3 else "medium" if len(valid_results) >= 2 else "single"
            }
        
        return {
            "ensemble_result": results.get("gpt5"),
            "model_results": results,
            "models_used": ["gpt5"],
            "ensemble_confidence": 70,
            "agreement_level": "single"
        }
    
    def _extract_json(self, text: str) -> Dict:
        """Extract JSON from LLM response."""
        if not text:
            return {"raw_response": "Empty response"}
        
        # Try to find JSON block
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Try to find any JSON object
        json_obj_match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
        if json_obj_match:
            try:
                return json.loads(json_obj_match.group(0))
            except json.JSONDecodeError:
                pass
        
        return {"raw_response": text}
    
    def emit_reward(self, trace_id: str, reward: float, metadata: Dict[str, Any] = None):
        """
        Emit reward signal for RL training via Agent Lightning.
        
        This allows the system to learn from feedback:
        - Positive reward when recommendations are accepted
        - Negative reward when recommendations are rejected
        - Partial reward based on user modifications
        """
        if not AGENT_LIGHTNING_AVAILABLE or not self.tracer:
            return
        
        try:
            # Agent Lightning reward emission
            if hasattr(agl, 'emit_reward'):
                agl.emit_reward(
                    trace_id=trace_id,
                    reward=reward,
                    metadata=metadata or {}
                )
        except Exception as e:
            print(f"Failed to emit reward: {e}")
    
    def get_rl_status(self) -> Dict[str, Any]:
        """Get status of RL/Agent Lightning integration."""
        return {
            "agent_lightning_available": AGENT_LIGHTNING_AVAILABLE,
            "tracer_active": self.tracer is not None,
            "agent_type": self.agent_type,
            "agent_version": self.agent_version,
            "primary_model": self.deployment,
            "validator_model": self.validator_deployment,
            "available_models": self.available_models,
            "ensemble_capable": sum(self.available_models.values()) >= 2
        }
