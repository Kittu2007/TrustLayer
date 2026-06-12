from typing import List
from backend.modules.trust_score.schemas import TrustScoreInput, RiskLevel
from backend.core.ai_orchestrator import AIReasoningOrchestrator


class ConfidenceReasoningGenerator:
    def __init__(self, ai_orchestrator: AIReasoningOrchestrator):
        self.ai = ai_orchestrator

    async def generate_reasons(self, data: TrustScoreInput) -> List[str]:
        context_data = data.model_dump()
        context_data['task'] = 'generate_reasons'
        return await self.ai.get_reasoning_with_fallback(context_data)


class RecommendationEngine:
    def __init__(self, ai_orchestrator: AIReasoningOrchestrator):
        self.ai = ai_orchestrator

    async def generate_recommendations(self, risk: RiskLevel, data: TrustScoreInput) -> List[str]:
        context_data = data.model_dump()
        context_data['task'] = 'generate_recommendations'
        return await self.ai.get_recommendations_with_fallback(risk.value, context_data)
