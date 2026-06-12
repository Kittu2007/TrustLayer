from backend.modules.trust_score.schemas import TrustScoreInput
from backend.modules.ocr.schemas import OCRResult
from backend.modules.fraud_intelligence.schemas import FraudMatchResult
from backend.modules.app_forensics.schemas import AppForensicsResult

class ResultAggregator:
    @staticmethod
    def normalize_to_trust_input(
        ocr: OCRResult, 
        fraud: FraudMatchResult, 
        metadata_anomalies: int,
        app_forensics: AppForensicsResult
    ) -> TrustScoreInput:
        """
        Translates raw modular outputs into the strict schema required by the Trust Score Engine.
        Now includes OCR quality signals for dynamic scoring.
        """
        
        # 1. Validate UTR (Basic deterministic check: 12 digits)
        utr = ocr.fields.upi_transaction_id
        is_utr_valid = bool(utr and len(utr) == 12 and utr.isdigit())
        
        # 2. Validate Amount
        amount = ocr.fields.payment_amount
        is_amount_valid = bool(amount and len(amount) > 0)
        
        # 3. Dynamic layout inconsistencies from App Forensics
        layout_flaws = 0
        if app_forensics.suspected_clone:
            layout_flaws += 2
        if app_forensics.layout_consistency == "LOW":
            layout_flaws += 1
            
        # Hard UTR format violation check
        # If a transaction reference is extracted but is invalid (e.g. not 12 digits), it's highly suspicious!
        utr_format_violation = bool(utr and not is_utr_valid)
        if utr_format_violation:
            layout_flaws += 2
            
        # Check for foreign currency symbols (absolute fake UPI indicator)
        raw_text_lower = (ocr.raw_text or "").lower()
        amount_str = (ocr.fields.payment_amount or "").lower()
        has_foreign_currency = any(symbol in raw_text_lower or symbol in amount_str for symbol in ["$", "€", "£", "dollar", "eur", "usd"])
        if has_foreign_currency:
            layout_flaws += 2
            
        # 4. Dynamic AI visual flags
        ai_flags = 0
        if app_forensics.font_consistency in ["SUSPICIOUS", "INCONSISTENT"]:
            ai_flags += 1
        if app_forensics.app_authenticity_score < 0.6:
            ai_flags += 1
        if ocr.fields.ui_authenticity == "SUSPICIOUS":
            ai_flags += 1
            
        # If UTR violation or foreign currency is detected, flag it in AI flags as well to trigger escalation
        if utr_format_violation or has_foreign_currency:
            ai_flags += 2
        
        # 5. Count successfully extracted fields
        extractable_fields = [
            ocr.fields.payment_amount,
            ocr.fields.receiver_name,
            ocr.fields.upi_id,
            ocr.fields.transaction_reference,
            ocr.fields.payment_app,
            ocr.fields.timestamp,
            ocr.fields.payment_status if ocr.fields.payment_status != "UNKNOWN" else None,
        ]
        fields_extracted = sum(1 for f in extractable_fields if f)
        
        # 6. Combine app detection confidence from OCR and forensics
        # Use the higher of the two confidence signals
        combined_app_confidence = max(
            ocr.fields.app_detection_confidence,
            app_forensics.app_authenticity_score
        )
        
        # Assemble for Phase 4
        return TrustScoreInput(
            upi_transaction_id_valid=is_utr_valid,
            payment_amount_valid=is_amount_valid,
            fraud_fingerprint_match=fraud.fingerprint_match,
            fraud_match_confidence=fraud.match_confidence,
            
            metadata_anomalies_detected=metadata_anomalies, 
            layout_inconsistencies_detected=layout_flaws,
            ai_visual_flags=ai_flags,
            
            # NEW: OCR quality signals for dynamic scoring
            ocr_confidence=ocr.confidence_score,
            app_detection_confidence=combined_app_confidence,
            image_quality_score=ocr.image_quality_score,
            fields_extracted_count=fields_extracted,
            fields_total_count=7,
        )
