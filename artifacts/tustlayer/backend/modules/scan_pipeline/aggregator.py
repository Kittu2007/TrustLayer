"""
TrustLayer AI – Result Aggregator v2.0
Translates raw module outputs → TrustScoreInput (v2 schema with all new fields).
"""
import re
from typing import Optional
from backend.modules.trust_score.schemas import TrustScoreInput
from backend.modules.ocr.schemas import OCRResult
from backend.modules.fraud_intelligence.schemas import FraudMatchResult
from backend.modules.app_forensics.schemas import AppForensicsResult
from backend.modules.scan_pipeline.metadata import ExifForensicsResult


# ── PRD Section 12: 37 valid UPI handle suffixes ─────────────────────────────
VALID_UPI_HANDLES = {
    "@ybl", "@ibl", "@axl",             # PhonePe
    "@paytm",                            # Paytm
    "@okaxis", "@okicici", "@oksbi", "@okhdfcbank",  # Google Pay
    "@upi",                              # BHIM
    "@apl",                              # Amazon Pay
    "@abfspay",                          # Aditya Birla / Airtel Finance
    "@naviaxis",                         # Navi
    "@waicici", "@waxis",               # WhatsApp Pay
    "@yapl",                             # Yes Bank
    "@rapl",                             # RBL Bank
    "@pnb",                              # Punjab National Bank
    "@sbi",                              # State Bank of India
    "@hdfc",                             # HDFC Bank
    "@icici",                            # ICICI Bank
    "@axis",                             # Axis Bank
    "@federal",                          # Federal Bank
    "@indus",                            # IndusInd Bank
    "@kotak",                            # Kotak Mahindra
    "@fbl",                              # Fincare Bank
    "@barodampay",                       # Bank of Baroda
    "@mahb",                             # Bank of Maharashtra
    "@sib",                              # South Indian Bank
    "@idbi",                             # IDBI Bank
    "@centralbank",                      # Central Bank of India
    "@csbpay",                           # CSB Bank
    "@dcb",                              # DCB Bank
    "@jkb",                              # J&K Bank
    "@kvb",                              # Karur Vysya Bank
    "@lvb",                              # Lakshmi Vilas Bank
    "@scb",                              # Standard Chartered
    "@unionbank",                        # Union Bank of India
    "@zoicici",                          # Zomato Pay
    "@freecharge",                       # Freecharge
    "@airtelpaymentsbank",               # Airtel Payments Bank
}

DUMMY_UTR_PATTERNS = {
    "000000000000", "111111111111", "222222222222", "333333333333",
    "444444444444", "555555555555", "666666666666", "777777777777",
    "888888888888", "999999999999", "123456789012", "120000000000",
}

FOREIGN_CURRENCY_SIGNALS = ["$", "€", "£", "dollar", "eur", "usd", "pound", "euro"]


def _validate_vpa_handle(upi_id: Optional[str]) -> bool:
    """Check if UPI VPA has a known bank suffix."""
    if not upi_id:
        return False
    lower = upi_id.lower()
    return any(lower.endswith(handle) for handle in VALID_UPI_HANDLES)


def _validate_utr(utr: Optional[str]) -> tuple[bool, bool, bool]:
    """Returns (is_valid_format, format_violation, dummy_pattern)."""
    if not utr:
        return False, False, False
    is_valid = len(utr) == 12 and utr.isdigit()
    format_violation = bool(utr) and not is_valid
    dummy = utr in DUMMY_UTR_PATTERNS or (utr.isdigit() and len(set(utr)) == 1)
    return is_valid, format_violation, dummy


def _detect_foreign_currency(raw_text: Optional[str], amount: Optional[str]) -> bool:
    combined = ((raw_text or "") + " " + (amount or "")).lower()
    return any(sig in combined for sig in FOREIGN_CURRENCY_SIGNALS)


def _validate_amount(amount: Optional[str]) -> bool:
    """Amount plausibility: must be non-empty, use ₹ or be parseable INR, within ₹1–₹10L."""
    if not amount:
        return False
    clean = re.sub(r'[₹,\s]', '', amount)
    try:
        value = float(clean)
        return 1.0 <= value <= 1_000_000.0
    except ValueError:
        return bool(amount.strip())


def _validate_timestamp(timestamp: Optional[str]) -> tuple[bool, bool]:
    """Returns (timestamp_valid, is_late_night). Basic heuristic."""
    if not timestamp:
        return True, False  # Missing timestamp: don't penalize
    ts_lower = timestamp.lower()
    # Check for hour patterns suggesting late-night (0-5 AM)
    late_night_patterns = [
        r'\b0[0-5]:\d{2}',   # 00:xx - 05:xx
        r'\b12:[0-5]\d\s*am', # 12:xx AM
        r'\b1:[0-5]\d\s*am',
        r'\b2:[0-5]\d\s*am',
        r'\b3:[0-5]\d\s*am',
        r'\b4:[0-5]\d\s*am',
        r'\b5:[0-5]\d\s*am',
    ]
    late_night = any(re.search(p, ts_lower) for p in late_night_patterns)
    return True, late_night


class ResultAggregator:
    @staticmethod
    def normalize_to_trust_input(
        ocr: OCRResult,
        fraud: FraudMatchResult,
        metadata_anomalies: int,
        app_forensics: AppForensicsResult,
        exif_result: Optional[ExifForensicsResult] = None,
        deepfake_score: float = 0.0,
        vpa_exists_razorpay: Optional[bool] = None,
        vpa_name_match: Optional[bool] = None,
        replay_detected: bool = False,
        replay_count: int = 0,
    ) -> TrustScoreInput:
        """
        Translates raw modular outputs → TrustScoreInput v2.0.
        """
        raw_text = ocr.raw_text or ""
        utr = ocr.fields.upi_transaction_id
        upi_id = ocr.fields.upi_id
        amount = ocr.fields.payment_amount

        # ── UTR validation ────────────────────────────────────────────────────
        utr_valid, utr_format_violation, utr_dummy = _validate_utr(utr)

        # ── VPA validation ────────────────────────────────────────────────────
        vpa_handle_valid = _validate_vpa_handle(upi_id)

        # ── Currency / Amount ─────────────────────────────────────────────────
        foreign_currency = _detect_foreign_currency(raw_text, amount)
        amount_plausible = _validate_amount(amount)

        # ── Timestamp ─────────────────────────────────────────────────────────
        timestamp_valid, timestamp_late_night = _validate_timestamp(ocr.fields.timestamp)

        # ── EXIF ──────────────────────────────────────────────────────────────
        if exif_result is not None:
            exif_editing = exif_result.editing_software_found
            exif_software_name = exif_result.editing_software_name
            effective_metadata_anomalies = exif_result.anomaly_count
        else:
            exif_editing = False
            exif_software_name = None
            effective_metadata_anomalies = metadata_anomalies

        # ── App branding ──────────────────────────────────────────────────────
        app_branding_match = app_forensics.logo_match and app_forensics.app_authenticity_score >= 0.75

        # ── Layout inconsistencies (from app forensics) ───────────────────────
        layout_flaws = 0
        if app_forensics.suspected_clone:
            layout_flaws += 2
        if app_forensics.layout_consistency == "LOW":
            layout_flaws += 1
        if utr_format_violation:
            layout_flaws += 2
        if foreign_currency:
            layout_flaws += 2

        # ── AI visual flags ───────────────────────────────────────────────────
        ai_flags = 0
        if app_forensics.font_consistency in ["SUSPICIOUS", "INCONSISTENT"]:
            ai_flags += 1
        if app_forensics.app_authenticity_score < 0.6:
            ai_flags += 1
        if ocr.fields.ui_authenticity == "SUSPICIOUS":
            ai_flags += 1
        if utr_format_violation or foreign_currency:
            ai_flags += 2

        # ── Field extraction count ────────────────────────────────────────────
        extractable = [
            ocr.fields.payment_amount,
            ocr.fields.receiver_name,
            ocr.fields.upi_id,
            ocr.fields.transaction_reference,
            ocr.fields.payment_app,
            ocr.fields.timestamp,
            ocr.fields.payment_status if ocr.fields.payment_status != "UNKNOWN" else None,
        ]
        fields_extracted = sum(1 for f in extractable if f)

        # ── Combined app detection confidence ─────────────────────────────────
        combined_app_confidence = max(
            ocr.fields.app_detection_confidence,
            app_forensics.app_authenticity_score
        )

        # ── Deepfake ──────────────────────────────────────────────────────────
        deepfake_detected = deepfake_score > 0.30

        return TrustScoreInput(
            # v1 fields (backward compat)
            upi_transaction_id_valid=utr_valid,
            payment_amount_valid=bool(amount),
            fraud_fingerprint_match=fraud.fingerprint_match,
            fraud_match_confidence=fraud.match_confidence,
            metadata_anomalies_detected=effective_metadata_anomalies,
            layout_inconsistencies_detected=layout_flaws,
            ai_visual_flags=ai_flags,
            ocr_confidence=ocr.confidence_score,
            app_detection_confidence=combined_app_confidence,
            image_quality_score=ocr.image_quality_score,
            fields_extracted_count=fields_extracted,
            fields_total_count=7,

            # v2 new fields
            utr_format_violation=utr_format_violation,
            utr_dummy_pattern=utr_dummy,
            vpa_handle_valid=vpa_handle_valid,
            vpa_exists_razorpay=vpa_exists_razorpay,
            vpa_name_match=vpa_name_match,
            foreign_currency_detected=foreign_currency,
            amount_plausible=amount_plausible,
            exif_editing_software=exif_editing,
            exif_software_name=exif_software_name,
            app_branding_match=app_branding_match,
            deepfake_score=deepfake_score,
            deepfake_detected=deepfake_detected,
            timestamp_valid=timestamp_valid,
            timestamp_late_night=timestamp_late_night,
            replay_detected=replay_detected,
            replay_count=replay_count,
        )
