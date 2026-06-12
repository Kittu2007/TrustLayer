from typing import Tuple
from backend.modules.trust_score.schemas import TrustScoreInput, RiskLevel

class RiskEscalationLayer:
    """
    Graduated verdict system with confidence-aware escalation.
    
    Key principles:
    - OCR failure ≠ fraud. Poor extraction → "Verification Recommended", NOT "Likely Fake"
    - Verdicts use nuanced language reflecting actual confidence
    - "Likely Fake" is ONLY used when explicit fraud signals are present
    - Extraction quality labels provide transparency about OCR reliability
    """
    
    @staticmethod
    def _compute_extraction_quality_label(data: TrustScoreInput) -> str:
        """Generate a human-readable label for OCR extraction quality."""
        ocr = data.ocr_confidence
        field_ratio = data.fields_extracted_count / max(1, data.fields_total_count)
        iq = data.image_quality_score
        
        if ocr >= 0.85 and field_ratio >= 0.7:
            return "High Quality Extraction"
        elif ocr >= 0.6 and field_ratio >= 0.5:
            return "Good Extraction"
        elif ocr >= 0.4 and field_ratio >= 0.3:
            return "Partial Extraction"
        elif ocr >= 0.2:
            if iq < 0.3:
                return "Low Quality Image — Limited Extraction"
            return "Low OCR Confidence"
        else:
            if iq < 0.2:
                return "Very Low Quality Image — Extraction Unreliable"
            return "Minimal Extraction — Verification Recommended"
    
    @staticmethod
    def evaluate(data: TrustScoreInput, base_score: float) -> Tuple[float, RiskLevel, float, str]:
        """
        Returns (final_score, risk_level, fraud_probability, verdict)
        """
        extraction_label = RiskEscalationLayer._compute_extraction_quality_label(data)
        
        # ================================================================
        # HARD ESCALATION RULES (absolute overrides — genuine fraud signals)
        # ================================================================
        
        # ESCALATION RULE 1: Known Scam Match (Absolute Override)
        if data.fraud_fingerprint_match and data.fraud_match_confidence > 0.8:
            return (0.0, RiskLevel.HIGH, 0.99, "Likely Fake")
            
        # ESCALATION RULE 2: Multiple layout flaws AND visual flags (Clear Tampering)
        if data.layout_inconsistencies_detected >= 2 and data.ai_visual_flags >= 2:
            return (15.0, RiskLevel.HIGH, 0.85, "Likely Fake")
            
        # ESCALATION RULE 3: EXIF/Metadata Software editing tampering detected (Absolute Override)
        if data.metadata_anomalies_detected >= 2:
            return (5.0, RiskLevel.HIGH, 0.98, "Likely Fake")
        
        # ================================================================
        # SOFT ESCALATION: Decouple OCR failure from fraud
        # ================================================================
        
        # If BOTH critical fields are missing BUT OCR confidence is very low,
        # this is likely an extraction problem, not fraud.
        if not data.upi_transaction_id_valid and not data.payment_amount_valid:
            if data.ocr_confidence < 0.3:
                # OCR struggled — don't assume fraud
                final_score = min(base_score, 55.0)
                return (final_score, RiskLevel.MEDIUM, 0.25, "Verification Recommended")
            else:
                # OCR was decent but fields genuinely missing — more suspicious
                final_score = min(base_score, 40.0)
                return (final_score, RiskLevel.MEDIUM, 0.45, "Needs Review")
        
        # ================================================================
        # GRADUATED VERDICTS (based on score + OCR confidence)
        # ================================================================
        
        ocr = data.ocr_confidence
        
        if base_score >= 85.0 and ocr >= 0.75:
            verdict = "Verified"
            risk = RiskLevel.LOW
            prob = max(0.02, (100.0 - base_score) / 200.0)
            
        elif base_score >= 70.0:
            verdict = "Likely Authentic"
            risk = RiskLevel.LOW
            prob = max(0.05, (100.0 - base_score) / 150.0)
            
        elif base_score >= 55.0 and ocr >= 0.4:
            verdict = "Partial Verification"
            risk = RiskLevel.MEDIUM
            prob = (100.0 - base_score) / 120.0
            
        elif base_score >= 40.0:
            verdict = "Low Confidence"
            risk = RiskLevel.MEDIUM
            prob = (100.0 - base_score) / 100.0
            
        else:
            verdict = "Needs Review"
            risk = RiskLevel.MEDIUM
            prob = min(0.75, (100.0 - base_score) / 100.0)
        
        return (base_score, risk, round(prob, 3), verdict)
