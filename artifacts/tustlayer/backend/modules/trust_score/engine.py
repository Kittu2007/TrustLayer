from backend.modules.trust_score.schemas import TrustScoreInput

class TrustScoreEngine:
    """
    Dynamic confidence-band scoring engine.
    
    Replaces rigid fixed deductions with OCR-aware weighted penalties.
    Penalties scale based on extraction quality — a missing field from
    a high-quality image is penalized more than one from a blurry screenshot.
    
    Weight Distribution:
        UPI Transaction Logic: 28%
        Metadata Intelligence: 22%
        AI Visual Reasoning: 20%
        Fraud Intelligence Match: 18%
        Layout Validation: 12%
    
    Score Bands (target outputs):
        Good screenshot (all fields, good OCR):    75–95
        WhatsApp forward (some fields, med OCR):   60–80
        Cropped screenshot (few fields, low qual):  50–75
        Suspicious (fraud signals):                 20–50
        Clearly edited (EXIF + fraud match):         0–30
    """
    
    @staticmethod
    def calculate_base_score(data: TrustScoreInput) -> float:
        score = 100.0
        
        # Derived ratios for dynamic scaling
        field_ratio = data.fields_extracted_count / max(1, data.fields_total_count)
        ocr_conf = data.ocr_confidence
        
        # --- 1. UPI Transaction Logic (max 28 points) ---
        # Instead of flat -14 per missing field, scale by OCR confidence.
        # Intuition: if OCR is poor, we're less certain the field is truly missing 
        # vs. just unreadable — so the penalty is softer.
        if not data.upi_transaction_id_valid:
            # Base penalty 14, but reduced if OCR confidence is low (we're unsure)
            # and increased if OCR confidence is high (field genuinely absent)
            certainty_multiplier = 0.4 + (ocr_conf * 0.6)  # Range: 0.4 – 1.0
            score -= 14.0 * certainty_multiplier
            
        if not data.payment_amount_valid:
            certainty_multiplier = 0.4 + (ocr_conf * 0.6)
            score -= 14.0 * certainty_multiplier
            
        # --- 2. Metadata Intelligence (max 22 points) ---
        if data.metadata_anomalies_detected > 0:
            deduction = min(22.0, data.metadata_anomalies_detected * 11.0)
            score -= deduction
            
        # --- 3. AI Visual Reasoning (max 20 points) ---
        if data.ai_visual_flags > 0:
            deduction = min(20.0, data.ai_visual_flags * 10.0)
            score -= deduction
            
        # --- 4. Fraud Intelligence Match (max 18 points) ---
        if data.fraud_fingerprint_match:
            score -= (18.0 * data.fraud_match_confidence)
            
        # --- 5. Layout Validation (max 12 points) ---
        if data.layout_inconsistencies_detected > 0:
            deduction = min(12.0, data.layout_inconsistencies_detected * 6.0)
            score -= deduction
        
        # --- 6. Field Extraction Bonus (up to +8 points) ---
        # Reward screenshots where OCR successfully extracted many fields.
        # This creates natural score variability between different screenshots.
        if field_ratio >= 0.7:
            extraction_bonus = 8.0 * (field_ratio - 0.7) / 0.3  # 0–8 points for 70–100% fields
            score += extraction_bonus
        
        # --- 7. App Detection Confidence Adjustment (up to +5 / -3 points) ---
        # Confident app detection is a positive signal; missing app is slightly negative
        app_conf = data.app_detection_confidence
        if app_conf >= 0.85:
            score += 5.0 * (app_conf - 0.85) / 0.15  # 0–5 bonus for 0.85–1.0
        elif app_conf < 0.3:
            score -= 3.0 * (1.0 - app_conf / 0.3)  # 0–3 penalty for <0.3
        
        # --- 8. Image Quality Micro-adjustment (up to ±3 points) ---
        # High quality image: small bonus. Low quality: small penalty.
        # This ensures identical extractions from different quality images score differently.
        iq = data.image_quality_score
        if iq >= 0.8:
            score += 3.0 * (iq - 0.8) / 0.2  # 0–3 bonus
        elif iq < 0.3:
            score -= 3.0 * (1.0 - iq / 0.3)  # 0–3 penalty
            
        return max(0.0, min(100.0, round(score, 2)))
