"""
TrustLayer AI – Document Scanner Engine v2.0
Analyzes images and PDFs for:
  - Steganography (LSB noise analysis via numpy)
  - Embedded URLs / phishing links
  - PDF JavaScript / auto-actions
  - Embedded files
"""
import io
import re
from typing import List, Tuple


PHISHING_PATTERNS = [
    r'bit\.ly', r'tinyurl\.com', r'goo\.gl', r't\.co',
    r'upi-verify', r'kyc-update', r'bank-login', r'account-verify',
    r'paytm-secure', r'phonepe-support', r'gpay-help',
    r'reward-claim', r'cashback-offer', r'lucky-winner',
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',  # Raw IP addresses
]

URL_REGEX = re.compile(
    r'https?://[^\s<>"\')\]]+|www\.[^\s<>"\')\]]+',
    re.IGNORECASE
)


def _extract_urls_from_text(text: str) -> List[str]:
    return URL_REGEX.findall(text or "")


def _is_suspicious_url(url: str) -> bool:
    lower = url.lower()
    return any(re.search(p, lower) for p in PHISHING_PATTERNS)


class DocumentScannerEngine:

    def analyze_image(self, image_bytes: bytes) -> dict:
        """Analyze a raster image for steganography and embedded URLs."""
        signals = []
        urls = []
        stego_suspected = False

        # ── Steganography: LSB noise analysis ────────────────────────────────
        try:
            import numpy as np
            from PIL import Image

            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            arr = np.array(img, dtype=np.uint8)

            # Extract LSB plane of each channel
            lsb_r = arr[:, :, 0] & 1
            lsb_g = arr[:, :, 1] & 1
            lsb_b = arr[:, :, 2] & 1

            # Natural images have ~50% LSB entropy; stego raises it artificially
            total_pixels = lsb_r.size
            r_ratio = float(lsb_r.sum()) / total_pixels
            g_ratio = float(lsb_g.sum()) / total_pixels
            b_ratio = float(lsb_b.sum()) / total_pixels

            # Threshold: deviation from 0.5 < 0.03 in ALL channels = suspicious uniformity
            r_dev = abs(r_ratio - 0.5)
            g_dev = abs(g_ratio - 0.5)
            b_dev = abs(b_ratio - 0.5)

            if r_dev < 0.03 and g_dev < 0.03 and b_dev < 0.03:
                stego_suspected = True
                signals.append(
                    f"LSB steganography suspected: R={r_ratio:.3f} G={g_ratio:.3f} B={b_ratio:.3f} "
                    f"(deviations: {r_dev:.3f}, {g_dev:.3f}, {b_dev:.3f})"
                )
            elif any(d < 0.015 for d in [r_dev, g_dev, b_dev]):
                signals.append("LSB channel unusually uniform in one plane — low suspicion")

        except ImportError:
            signals.append("numpy not available — steganography check skipped")
        except Exception as e:
            print(f"[DOC-SCANNER] Stego analysis error: {e}")

        # ── Try to read text from image for URL extraction ────────────────────
        try:
            import pytesseract
            from PIL import Image
            img_pil = Image.open(io.BytesIO(image_bytes))
            text = pytesseract.image_to_string(img_pil)
            urls = _extract_urls_from_text(text)
        except Exception:
            pass

        suspicious = [u for u in urls if _is_suspicious_url(u)]
        return {
            "document_type": "image",
            "steganography_suspected": stego_suspected,
            "steganography_signals": signals,
            "urls_found": urls,
            "suspicious_urls": suspicious,
            "embedded_files_found": False,
            "embedded_file_count": 0,
            "pdf_javascript_found": False,
            "pdf_auto_action_found": False,
        }

    def analyze_pdf(self, pdf_bytes: bytes) -> dict:
        """Analyze a PDF for embedded threats."""
        signals = []
        urls = []
        js_found = False
        auto_action = False
        embedded_files = False
        embedded_count = 0
        page_count = 0

        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            page_count = doc.page_count

            # Extract all text for URL hunting
            full_text = ""
            for page in doc:
                full_text += page.get_text()

            urls = _extract_urls_from_text(full_text)

            # Check for JavaScript
            js_found = doc.is_pdf and "/JS" in full_text or "/JavaScript" in full_text
            auto_action = "/AA" in full_text or "/OpenAction" in full_text

            # Check for embedded files
            embedded_count = doc.embfile_count()
            embedded_files = embedded_count > 0

            if js_found:
                signals.append("PDF contains JavaScript — execution risk")
            if auto_action:
                signals.append("PDF has auto-action triggers (/OpenAction or /AA)")
            if embedded_files:
                signals.append(f"PDF contains {embedded_count} embedded file(s)")

            doc.close()

        except ImportError:
            signals.append("PyMuPDF not available — PDF deep scan skipped")
        except Exception as e:
            print(f"[DOC-SCANNER] PDF analysis error: {e}")
            signals.append(f"PDF analysis error: {str(e)[:80]}")

        suspicious = [u for u in urls if _is_suspicious_url(u)]
        return {
            "document_type": "pdf",
            "page_count": page_count,
            "steganography_suspected": False,
            "steganography_signals": [],
            "urls_found": urls[:20],
            "suspicious_urls": suspicious[:10],
            "embedded_files_found": embedded_files,
            "embedded_file_count": embedded_count,
            "pdf_javascript_found": js_found,
            "pdf_auto_action_found": auto_action,
        }
