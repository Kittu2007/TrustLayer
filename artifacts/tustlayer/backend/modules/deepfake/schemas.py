from pydantic import BaseModel, Field
from typing import List, Optional


class DeepfakeDetectionResult(BaseModel):
    deepfake_probability: float = Field(default=0.0, ge=0.0, le=1.0, description="0=real, 1=deepfake")
    is_deepfake: bool = False
    manipulation_type: str = Field(default="none", description="none/face_swap/image_generation/splicing/enhancement/unknown")
    signals: List[str] = Field(default_factory=list, description="Visual signals that triggered detection")
    model_used: str = "hive/deepfake-image-detection"
    error: Optional[str] = None
