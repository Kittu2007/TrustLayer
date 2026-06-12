from backend.modules.app_forensics.schemas import AppForensicsResult
from backend.modules.app_forensics.engine import AppForensicsEngine

class AppForensicsService:
    def __init__(self):
        self.engine = AppForensicsEngine()

    async def analyze_image(self, image_bytes: bytes, raw_text: str, claimed_app: str = None) -> AppForensicsResult:
        """
        Executes deterministic app forensics on the uploaded UPI screenshot
        correlating image color profiling with OCR raw text extractions.
        """
        return self.engine.analyze(image_bytes, raw_text, claimed_app)

def get_app_forensics_service() -> AppForensicsService:
    return AppForensicsService()
