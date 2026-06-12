import time
import json
import asyncio
from typing import Optional
from backend.modules.scan_pipeline.schemas import FinalScanResponse, ScanMetadata
from backend.modules.scan_pipeline.parallel_executor import ParallelTaskExecutor
from backend.modules.scan_pipeline.aggregator import ResultAggregator
from backend.modules.scan_pipeline.metadata import MetadataService
from backend.integrations.supabase_client import save_scan_result_async

from backend.modules.ocr.service import get_ocr_service
from backend.modules.fraud_intelligence.service import get_fraud_intelligence_service
from backend.modules.trust_score.service import get_final_decision_assembler
from backend.modules.app_forensics.service import get_app_forensics_service

class ScanPipelineService:
    def __init__(self):
        self.executor = ParallelTaskExecutor(
            ocr_service=get_ocr_service(),
            fraud_service=get_fraud_intelligence_service()
        )
        self.app_forensics_service = get_app_forensics_service()
        self.aggregator = ResultAggregator()
        self.trust_engine = get_final_decision_assembler()
        self.metadata_service = MetadataService()

    async def execute_full_scan(self, image_bytes: bytes) -> FinalScanResponse:
        start_time = time.time()
        
        # 1. Parallel Execution
        ocr_result, fraud_result = await self.executor.execute_all(image_bytes)
        
        # 2. Payment App Detection Layer (passing Vision-extracted payment_app)
        app_forensics_result = await self.app_forensics_service.analyze_image(
            image_bytes, ocr_result.raw_text or "", ocr_result.fields.payment_app
        )
        
        # 3. Synchronous Metadata Check
        metadata_anomalies = self.metadata_service.extract_anomalies(image_bytes)
        
        # 4. Normalize inputs for Trust Engine
        trust_input = self.aggregator.normalize_to_trust_input(
            ocr_result, fraud_result, metadata_anomalies, app_forensics_result
        )
        
        # 5. Final Trust Decision
        trust_result = await self.trust_engine.evaluate(trust_input)
        
        # 6. Cinematic Assembly
        execution_ms = int((time.time() - start_time) * 1000)
        
        final_response = FinalScanResponse(
            success=True,
            metadata=ScanMetadata(
                execution_time_ms=execution_ms,
                modules_executed=["OCR", "AppForensics", "FraudIntelligence", "Metadata", "TrustScore"]
            ),
            trust_score_data=trust_result,
            ocr_data=ocr_result,
            fraud_intelligence_data=fraud_result,
            app_forensics=app_forensics_result
        )
        
        # Async background save to database (will instantly fail silently if no keys)
        asyncio.create_task(save_scan_result_async(final_response.model_dump()))
        
        return final_response
        
    async def stream_full_scan(
        self, 
        image_bytes: bytes, 
        session_id: Optional[str] = None, 
        remaining_scans: int = -1
    ):
        """Generator for Server-Sent Events (SSE)."""
        start_time = time.time()
        
        # Initial status
        yield f'data: {json.dumps({"status": "processing", "step": "starting", "message": "Initializing TrustLayer Pipeline..."})}\n\n'
        await asyncio.sleep(0.5) # Artificial delay for cinematic effect
        
        # 1. Run parallel tasks (OCR and Fraud checks)
        yield f'data: {json.dumps({"status": "processing", "step": "scanning", "message": "Running OCR and Fraud scans concurrently..."})}\n\n'
        ocr_result, fraud_result = await self.executor.execute_all(image_bytes)
        metadata_anomalies = self.metadata_service.extract_anomalies(image_bytes)
        
        # 2. Run App Detection Layer
        yield f'data: {json.dumps({"status": "processing", "step": "app_detection", "message": "Verifying authentic app templates and logo footprints..."})}\n\n'
        await asyncio.sleep(0.5)
        app_forensics_result = await self.app_forensics_service.analyze_image(
            image_bytes, ocr_result.raw_text or "", ocr_result.fields.payment_app
        )
        
        yield f'data: {json.dumps({"status": "processing", "step": "scan_complete", "message": "Scans complete. Aggregating results..."})}\n\n'
        await asyncio.sleep(0.5)
        
        # 3. Final Trust Decision
        trust_input = self.aggregator.normalize_to_trust_input(
            ocr_result, fraud_result, metadata_anomalies, app_forensics_result
        )
        trust_result = await self.trust_engine.evaluate(trust_input)
        
        # 4. Assemble Final Payload
        execution_ms = int((time.time() - start_time) * 1000)
        final_response = FinalScanResponse(
            success=True,
            metadata=ScanMetadata(
                execution_time_ms=execution_ms,
                modules_executed=["OCR", "AppForensics", "FraudIntelligence", "Metadata", "TrustScore"]
            ),
            trust_score_data=trust_result,
            ocr_data=ocr_result,
            fraud_intelligence_data=fraud_result,
            app_forensics=app_forensics_result,
            anonymous_session_id=session_id,
            remaining_scans=remaining_scans
        )
        
        yield f'data: {json.dumps({"status": "complete", "step": "finalized", "payload": final_response.model_dump()})}\n\n'
        
        # Async background save to database
        asyncio.create_task(save_scan_result_async(final_response.model_dump()))

def get_scan_pipeline_service() -> ScanPipelineService:
    return ScanPipelineService()
