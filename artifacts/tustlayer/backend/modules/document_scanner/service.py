"""
TrustLayer AI – Document Scanner Service v2.0
"""
from backend.modules.document_scanner.schemas import DocumentThreatResult
from backend.modules.document_scanner.engine import DocumentScannerEngine


class DocumentScannerService:
    def __init__(self):
        self.engine = DocumentScannerEngine()

    async def scan(self, file_bytes: bytes, content_type: str) -> DocumentThreatResult:
        try:
            is_pdf = "pdf" in content_type.lower() or file_bytes[:4] == b"%PDF"

            if is_pdf:
                raw = self.engine.analyze_pdf(file_bytes)
            else:
                raw = self.engine.analyze_image(file_bytes)

            risk_signals = list(raw.get("steganography_signals", []))

            if raw.get("suspicious_urls"):
                for url in raw["suspicious_urls"]:
                    risk_signals.append(f"Suspicious URL: {url[:80]}")

            if raw.get("pdf_javascript_found"):
                risk_signals.append("JavaScript found in PDF")
            if raw.get("pdf_auto_action_found"):
                risk_signals.append("Auto-action trigger found in PDF")
            if raw.get("embedded_files_found"):
                risk_signals.append(f"{raw['embedded_file_count']} embedded file(s) in PDF")

            # Determine risk level
            critical = (
                raw.get("steganography_suspected")
                or raw.get("pdf_javascript_found")
                or raw.get("pdf_auto_action_found")
                or len(raw.get("suspicious_urls", [])) >= 2
            )
            medium = (
                len(raw.get("suspicious_urls", [])) >= 1
                or raw.get("embedded_files_found")
            )

            if critical:
                risk_level = "HIGH"
            elif medium:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"

            doc_type = raw.get("document_type", "unknown")
            pages = raw.get("page_count", 0)
            explanation = (
                f"Scanned {doc_type.upper()}"
                + (f" ({pages} pages)" if pages > 0 else "")
                + f". Risk level: {risk_level}."
                + (f" {len(risk_signals)} signal(s) detected." if risk_signals else " No threats found.")
            )

            return DocumentThreatResult(
                success=True,
                document_type=doc_type,
                page_count=pages,
                steganography_suspected=raw.get("steganography_suspected", False),
                steganography_signals=raw.get("steganography_signals", []),
                urls_found=raw.get("urls_found", []),
                suspicious_urls=raw.get("suspicious_urls", []),
                url_risk_level="HIGH" if raw.get("suspicious_urls") else "LOW",
                embedded_files_found=raw.get("embedded_files_found", False),
                embedded_file_count=raw.get("embedded_file_count", 0),
                pdf_javascript_found=raw.get("pdf_javascript_found", False),
                pdf_auto_action_found=raw.get("pdf_auto_action_found", False),
                risk_level=risk_level,
                risk_signals=risk_signals,
                explanation=explanation,
            )

        except Exception as e:
            print(f"[DOC-SCANNER] Service error: {e}")
            return DocumentThreatResult(
                success=False,
                error=str(e),
                explanation="Document scan failed due to an internal error.",
            )


def get_document_scanner_service() -> DocumentScannerService:
    return DocumentScannerService()
