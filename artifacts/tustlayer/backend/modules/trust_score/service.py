"""
TrustLayer AI – Trust Score Service v2.0
Orchestrates the full deterministic + AI reasoning pipeline.
"""
from backend.modules.trust_score.schemas import TrustScoreInput, TrustScoreResult
from backend.modules.trust_score.engine import TrustScoreEngine
from backend.modules.trust_score.escalation import RiskEscalationLayer
from backend.modules.trust_score.reasoning import ConfidenceReasoningGenerator, RecommendationEngine
from backend.core.ai_orchestrator import AIReasoningOrchestrator
from backend.integrations.nvidia_client import QwenReasoningProvider, PhiReasoningProvider


class FinalDecisionAssembler:
    """
    Orchestrates the v2.0 deterministic scoring + AI reasoning pipeline.
    """
    def __init__(self):
        self.engine = TrustScoreEngine()
        self.escalation = RiskEscalationLayer()
        self.qwen = QwenReasoningProvider()
        self.ai_orchestrator = AIReasoningOrchestrator(
            primary=self.qwen,
            fallback=PhiReasoningProvider()
        )
        self.reasoning = ConfidenceReasoningGenerator(self.ai_orchestrator)
        self.recommendations = RecommendationEngine(self.ai_orchestrator)

    async def evaluate(self, data: TrustScoreInput) -> TrustScoreResult:
        # 1. v2 additive scoring with hard caps
        final_score, breakdown, caps_triggered = TrustScoreEngine.calculate(data)

        # 2. Graduated verdict + risk level
        final_score, risk_level, fraud_prob, verdict = self.escalation.evaluate(data, final_score)

        # 3. Extraction quality label
        extraction_label = RiskEscalationLayer._compute_extraction_quality_label(data)

        # 4. AI reasoning (Qwen 397B → Phi fallback)
        reasons = await self.reasoning.generate_reasons(data)
        actions = await self.recommendations.generate_recommendations(risk_level, data)

        # 5. "What To Do Next" (Qwen generates user-facing guidance)
        what_to_do = await self.qwen.generate_what_to_do_next(risk_level.value, data.model_dump())

        # 6. Append triggered hard-cap warnings to confidence reasoning
        if caps_triggered:
            reasons = [f"[Hard Cap] {cap}" for cap in caps_triggered] + reasons

        return TrustScoreResult(
            trust_score=final_score,
            risk_level=risk_level,
            fraud_probability=fraud_prob,
            confidence_reasoning=reasons,
            recommended_actions=actions,
            verdict=verdict,
            extraction_quality_label=extraction_label,
            what_to_do_next=what_to_do,
            score_breakdown=breakdown,
        )


def get_final_decision_assembler() -> FinalDecisionAssembler:
    return FinalDecisionAssembler()
