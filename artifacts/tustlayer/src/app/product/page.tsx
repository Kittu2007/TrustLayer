"use client";

import { useState } from "react";
import { UploadPanel } from "@/components/product/UploadPanel";
import { PhonePreview } from "@/components/product/PhonePreview";
import { ResultsPanel } from "@/components/product/ResultsPanel";
import { useLenisScroll } from "@/hooks/useLenisScroll";

type ScanResponse = {
  success: boolean;
  metadata: { execution_time_ms: number; modules_executed: string[] };
  trust_score_data: {
    trust_score: number;
    risk_level: string;
    fraud_probability: number;
    confidence_reasoning: string[];
    recommended_actions: string[];
  };
  ocr_data: {
    fields: {
      payment_amount: string | null;
      upi_transaction_id: string | null;
      receiver_name: string | null;
      timestamp: string | null;
      payment_app_name: string | null;
    };
    confidence_score: number;
    used_fallback: boolean;
  };
  fraud_intelligence_data: {
    fingerprint_match: boolean;
    match_confidence: number;
    match_count: number;
    fraud_type: string | null;
  };
} | null;

export default function ProductPage() {
  useLenisScroll();

  const [uploadedImage, setUploadedImage] = useState<string | null>(null);
  const [uploadedName, setUploadedName] = useState<string>("");
  const [isScanning, setIsScanning] = useState<boolean>(false);
  const [scanResults, setScanResults] = useState<ScanResponse>(null);

  const handleFileSelect = (file: File) => {
    setUploadedName(file.name);
    setScanResults(null);

    const reader = new FileReader();
    reader.onload = (e) => {
      if (e.target?.result && typeof e.target.result === "string") {
        setUploadedImage(e.target.result);
      }
    };
    reader.readAsDataURL(file);
  };

  const handleScan = async () => {
    if (!uploadedImage) return;

    setIsScanning(true);
    try {
      // Convert base64 data URL to a blob
      const responseBlob = await fetch(uploadedImage);
      const blob = await responseBlob.blob();
      
      const formData = new FormData();
      formData.append("file", blob, uploadedName || "screenshot.png");

      const response = await fetch("/api/v1/scan/execute", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setScanResults(data);
    } catch (error) {
      console.error("Forensic scan failed:", error);
    } finally {
      setIsScanning(false);
    }
  };

  const handleLoadDemo = () => {
    setUploadedName("phonepe_receipt_demo.svg");
    setScanResults(null);
    
    // Beautiful, fully standard PhonePe payment screenshot mockup SVG
    const demoSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="360" height="640" viewBox="0 0 360 640">
  <rect width="360" height="640" fill="#0f0f15"/>
  <circle cx="180" cy="120" r="100" fill="#5f259f" opacity="0.15" filter="blur(30px)"/>
  
  <rect width="360" height="56" fill="#5f259f"/>
  <text x="20" y="34" font-family="sans-serif" font-size="16" font-weight="bold" fill="white">Transaction Successful</text>
  
  <circle cx="180" cy="140" r="30" fill="#12b76a"/>
  <path d="M168 140l8 8 16-16" stroke="white" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  
  <text x="180" y="205" font-family="sans-serif" font-size="13" fill="#9ca3af" text-anchor="middle">Paid to</text>
  <text x="180" y="232" font-family="sans-serif" font-size="20" font-weight="bold" fill="white" text-anchor="middle">ONNARAM SHIVA</text>
  <text x="180" y="285" font-family="sans-serif" font-size="36" font-weight="900" fill="#dbff4a" text-anchor="middle">&#8377;150</text>
  
  <rect x="20" y="325" width="320" height="1" fill="#ffffff" opacity="0.1"/>
  
  <text x="20" y="360" font-family="sans-serif" font-size="12" fill="#9ca3af">Banking Name</text>
  <text x="340" y="360" font-family="sans-serif" font-size="12" font-weight="bold" fill="white" text-anchor="end">ONNARAM SHIVA</text>
  
  <text x="20" y="398" font-family="sans-serif" font-size="12" fill="#9ca3af">UPI ID</text>
  <text x="340" y="398" font-family="sans-serif" font-size="12" font-weight="bold" fill="white" text-anchor="end">7702799024@ybl</text>
  
  <text x="20" y="436" font-family="sans-serif" font-size="12" fill="#9ca3af">UTR (Transaction ID)</text>
  <text x="340" y="436" font-family="sans-serif" font-size="12" font-weight="bold" fill="#34e6ff" text-anchor="end">261490247702</text>
  
  <text x="20" y="474" font-family="sans-serif" font-size="12" fill="#9ca3af">Date &amp; Time</text>
  <text x="340" y="474" font-family="sans-serif" font-size="12" font-weight="bold" fill="white" text-anchor="end">26 May 2026, 1:23 PM</text>
  
  <rect x="20" y="510" width="320" height="1" fill="#ffffff" opacity="0.1"/>
  <circle cx="180" cy="550" r="14" fill="#5f259f"/>
  <text x="180" y="554" font-family="sans-serif" font-size="10" font-weight="bold" fill="white" text-anchor="middle">PP</text>
  <text x="180" y="582" font-family="sans-serif" font-size="11" fill="#9ca3af" text-anchor="middle">Powered by PhonePe</text>
</svg>`;

    const base64Svg = `data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(demoSvg)))}`;
    setUploadedImage(base64Svg);
  };

  return (
    <div className="product-page">
      <div className="product-layout">
        <UploadPanel
          onFileSelect={handleFileSelect}
          uploadedImage={uploadedImage}
          uploadedName={uploadedName}
          onScan={handleScan}
          isScanning={isScanning}
          hasResults={!!scanResults}
          onLoadDemo={handleLoadDemo}
        />
        
        <PhonePreview uploadedImage={uploadedImage} isScanning={isScanning} />
        
        <ResultsPanel results={scanResults} isScanning={isScanning} />
      </div>
    </div>
  );
}
