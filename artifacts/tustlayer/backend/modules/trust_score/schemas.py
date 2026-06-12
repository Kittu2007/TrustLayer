from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

# Input DTO combining results from previous phases
class TrustScoreInput(BaseModel):
    # Phase 3: OCR Inputs
    upi_transaction_id_valid: bool = Field(..., description="True if UTR is 12 digits and matches checksum")
    payment_amount_valid: bool = Field(..., description="True if amount matches expected transaction format")
    
    # Phase 2: Fraud Intelligence
    fraud_fingerprint_match: bool = Field(..., description="True if matched a known scam template")
    fraud_match_confidence: float = Field(default=0.0, description="Confidence of the template match")
    
    # Future Phase Inputs (Mocked for now)
    metadata_anomalies_detected: int = Field(default=0, description="Number of EXIF/compression anomalies")
    layout_inconsistencies_detected: int = Field(default=0, description="Number of UI layout flaws")
    ai_visual_flags: int = Field(default=0, description="Visual anomalies flagged by LLM")
    
    # NEW: OCR Quality Signals (enables weighted confidence bands)
    ocr_confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Overall OCR extraction confidence from multi-pass engine")
    app_detection_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence of payment app identification")
    image_quality_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Image quality metric: blur/resolution/compression")
    fields_extracted_count: int = Field(default=0, ge=0, description="Number of OCR fields successfully extracted")
    fields_total_count: int = Field(default=7, ge=1, description="Total possible extractable fields")

class TrustScoreResult(BaseModel):
    trust_score: float = Field(..., ge=0.0, le=100.0, description="0 to 100 score. Higher is more trustworthy.")
    risk_level: RiskLevel
    fraud_probability: float = Field(..., ge=0.0, le=1.0)
    confidence_reasoning: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    verdict: Optional[str] = Field(None, description="The custom forensic verdict state, e.g. 'Likely Authentic'")
    
    # NEW: Extraction quality label for frontend display
    extraction_quality_label: Optional[str] = Field(None, description="Human-readable OCR quality label, e.g. 'Low OCR Confidence', 'Partial Extraction'")
