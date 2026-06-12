from backend.modules.trust_score.schemas import TrustScoreInput, TrustScoreResult
from backend.modules.trust_score.engine import TrustScoreEngine
from backend.modules.trust_score.escalation import RiskEscalationLayer
from backend.modules.trust_score.reasoning import ConfidenceReasoningGenerator, RecommendationEngine
from backend.core.ai_orchestrator import AIReasoningOrchestrator
from backend.integrations.nvidia_client import QwenReasoningProvider, PhiReasoningProvider

class FinalDecisionAssembler:
    """
    Orchestrates the deterministic scoring pipeline.
    """
    def __init__(self):
        self.engine = TrustScoreEngine()
        self.escalation = RiskEscalationLayer()
        self.ai_orchestrator = AIReasoningOrchestrator(
            primary=QwenReasoningProvider(),
            fallback=PhiReasoningProvider()
        )
        self.reasoning = ConfidenceReasoningGenerator(self.ai_orchestrator)
        self.recommendations = RecommendationEngine(self.ai_orchestrator)
        
    async def evaluate(self, data: TrustScoreInput) -> TrustScoreResult:
        # 1. Base deterministic math (now with dynamic confidence bands)
        base_score = self.engine.calculate_base_score(data)
        
        # 2. Risk Escalation (Overrides + graduated verdicts)
        final_score, risk_level, fraud_prob, verdict = self.escalation.evaluate(data, base_score)
        
        # 3. Extraction quality label (for frontend transparency)
        extraction_label = RiskEscalationLayer._compute_extraction_quality_label(data)
        
        # 4. Psychological Translation (via AI)
        reasons = await self.reasoning.generate_reasons(data)
        actions = await self.recommendations.generate_recommendations(risk_level, data)
        
        # 5. Assemble Result
        return TrustScoreResult(
            trust_score=final_score,
            risk_level=risk_level,
            fraud_probability=fraud_prob,
            confidence_reasoning=reasons,
            recommended_actions=actions,
            verdict=verdict,
            extraction_quality_label=extraction_label
        )

def get_final_decision_assembler() -> FinalDecisionAssembler:
    return FinalDecisionAssembler()
