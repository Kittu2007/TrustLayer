"use client";

import { useState, useEffect } from "react";

type ScanResponse = {
  success: boolean;
  metadata: { execution_time_ms: number; modules_executed: string[] };
  trust_score_data: {
    trust_score: number;
    risk_level: string;
    fraud_probability: number;
    confidence_reasoning: string[];
    recommended_actions: string[];
    verdict?: string;
    extraction_quality_label?: string;
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
    image_quality_score?: number;
    ocr_pass_count?: number;
  };
  fraud_intelligence_data: {
    fingerprint_match: boolean;
    match_confidence: number;
    match_count: number;
    fraud_type: string | null;
  };
} | null;

type ResultsPanelProps = {
  results: ScanResponse;
  isScanning?: boolean;
};

function getVerdictStyle(verdict: string): { color: string; icon: string } {
  const v = verdict.toLowerCase();
  if (v.includes("verified"))
    return { color: "#31f58b", icon: "✓" };
  if (v.includes("likely authentic"))
    return { color: "#31f58b", icon: "◉" };
  if (v.includes("partial verification"))
    return { color: "#ffb22e", icon: "◎" };
  if (v.includes("low confidence") || v.includes("verification recommended"))
    return { color: "#ffb22e", icon: "⚠" };
  if (v.includes("needs review"))
    return { color: "#ff9466", icon: "⚡" };
  if (v.includes("fake"))
    return { color: "#ffb59d", icon: "✕" };
  return { color: "#8899aa", icon: "?" };
}

function getQualityBadgeStyle(label: string): { bg: string; text: string } {
  const l = label.toLowerCase();
  if (l.includes("high quality"))
    return { bg: "rgba(49, 245, 139, 0.12)", text: "#31f58b" };
  if (l.includes("good"))
    return { bg: "rgba(49, 245, 139, 0.08)", text: "#7bf5a8" };
  if (l.includes("partial"))
    return { bg: "rgba(255, 178, 46, 0.10)", text: "#ffb22e" };
  if (l.includes("low"))
    return { bg: "rgba(255, 148, 102, 0.10)", text: "#ff9466" };
  return { bg: "rgba(255, 100, 80, 0.10)", text: "#ff6450" };
}

export function ResultsPanel({ results, isScanning }: ResultsPanelProps) {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    if (!isScanning) {
      setActiveStep(0);
      return;
    }
    const interval = setInterval(() => {
      setActiveStep((prev) => (prev < 4 ? prev + 1 : prev));
    }, 1200);
    return () => clearInterval(interval);
  }, [isScanning]);

  if (isScanning) {
    const steps = [
      { icon: "🔍", title: "NVIDIA Nemotron-VL Core OCR", desc: "Extracting transaction parameters, UPI handles & timestamps..." },
      { icon: "🧠", title: "Qwen 3.5-122B Reasoning Engine", desc: "Analyzing layout metadata, font properties, and digital anomalies..." },
      { icon: "🛡️", title: "Forensic Image & Color Profiling", desc: "Auditing pixel compression structures and image authenticity..." },
      { icon: "🔒", title: "Fraud Intelligence Hashing Check", desc: "Checking template matches, known fraudulent VPA targets & hashes..." }
    ];

    return (
      <div className="product-panel results-panel" style={{ padding: "32px", display: "flex", flexDirection: "column", gap: "20px" }}>
        <div className="product-panel-header" style={{ borderBottom: "none", marginBottom: "0px" }}>
          <span className="dot" style={{ backgroundColor: "var(--signal)", boxShadow: "0 0 12px var(--signal)" }} /> Active Scan Diagnostics
        </div>
        
        {/* Radar Spinner */}
        <div style={{ display: "grid", placeItems: "center", margin: "14px 0" }}>
          <div className="radar-scanner">
            <div className="radar-sweep" />
            <div className="radar-ping" />
            <span 
              style={{ 
                fontFamily: "var(--font-mono)", 
                fontSize: "0.74rem", 
                fontWeight: 950, 
                color: "#ffffff", 
                letterSpacing: "0.14em", 
                zIndex: 6,
                background: "#050505",
                border: "1px solid rgba(219, 255, 74, 0.3)",
                borderRadius: "999px",
                padding: "6px 14px",
                boxShadow: "0 4px 12px rgba(0, 0, 0, 0.5), 0 0 10px rgba(219, 255, 74, 0.15)",
                textShadow: "0 0 8px rgba(255, 255, 255, 0.3)"
              }}
            >
              {activeStep < 4 ? "RUNNING" : "RESOLVING"}
            </span>
          </div>
        </div>

        {/* Dynamic Scan Steps */}
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {steps.map((step, idx) => {
            const isCompleted = idx < activeStep;
            const isActive = idx === activeStep;
            const isPending = idx > activeStep;

            return (
              <div 
                key={idx} 
                className={`scanning-step ${isCompleted ? "completed" : isActive ? "active" : "pending"}`}
                style={{ opacity: isPending ? 0.38 : 1 }}
              >
                <span className="step-icon">{step.icon}</span>
                <div className="step-content">
                  <strong>{step.title}</strong>
                  <p>{step.desc}</p>
                </div>
                {isCompleted && <div className="step-checkmark">✓</div>}
                {isActive && <div className="scanning-spinner" />}
                {isPending && <div style={{ width: "10px", height: "10px", border: "1px solid var(--border)", borderRadius: "50%", alignSelf: "center", marginRight: "3px" }} />}
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  if (!results) {
    return (
      <div className="product-panel results-panel" style={{ display: "grid", placeItems: "center", minHeight: "300px", padding: "20px", textAlign: "center", color: "var(--foreground-dim)" }}>
        <p>Upload a screenshot and execute a scan to see forensic results.</p>
      </div>
    );
  }

  const { trust_score_data, ocr_data, fraud_intelligence_data, metadata } = results;

  const finalVerdict = trust_score_data.verdict || "Analysis Complete";
  const verdictStyle = getVerdictStyle(finalVerdict);
  
  const ocrConfidencePct = Math.round(ocr_data.confidence_score * 100);
  const qualityLabel = trust_score_data.extraction_quality_label;
  const qualityBadge = qualityLabel ? getQualityBadgeStyle(qualityLabel) : null;

  const scoreColor = verdictStyle.color;
  const imageQualityPct = ocr_data.image_quality_score != null 
    ? Math.round(ocr_data.image_quality_score * 100) 
    : null;

  return (
    <div className="product-panel results-panel">
      <div className="product-panel-header">
        <span className="dot" /> Forensic Results
      </div>

      <div className="result-block">
        <div className="result-score">
          <div className="result-score-number" style={{ color: scoreColor }}>
            {Math.round(trust_score_data.trust_score)}
          </div>
          <div className="result-score-label">Trust Score</div>
          <div className="result-verdict">
            <span>Verdict</span>
            <strong style={{ color: verdictStyle.color }}>
              {verdictStyle.icon} {finalVerdict}
            </strong>
          </div>
          {qualityLabel && qualityBadge && (
            <div
              style={{
                marginTop: "8px",
                display: "inline-block",
                padding: "4px 12px",
                borderRadius: "20px",
                fontSize: "0.72rem",
                fontWeight: 500,
                letterSpacing: "0.04em",
                background: qualityBadge.bg,
                color: qualityBadge.text,
                border: `1px solid ${qualityBadge.text}22`,
              }}
            >
              {qualityLabel}
            </div>
          )}
        </div>
      </div>

      <div className="result-block">
        <h4 className="result-block-title" style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          OCR Data
          <span
            style={{
              fontSize: "0.68rem",
              fontWeight: 400,
              padding: "2px 8px",
              borderRadius: "10px",
              background: ocrConfidencePct >= 70 ? "rgba(49,245,139,0.10)" : ocrConfidencePct >= 40 ? "rgba(255,178,46,0.10)" : "rgba(255,100,80,0.10)",
              color: ocrConfidencePct >= 70 ? "#31f58b" : ocrConfidencePct >= 40 ? "#ffb22e" : "#ff6450",
            }}
          >
            {ocrConfidencePct}% confidence
          </span>
        </h4>
        <div className="result-row">
          <span className="label">Amount</span>
          <span className="value">
            {ocr_data.fields.payment_amount
              ? (/^[₹$€£]|^(?:Rs\.?|INR)/i.test(ocr_data.fields.payment_amount)
                ? ocr_data.fields.payment_amount
                : `₹${ocr_data.fields.payment_amount}`)
              : "N/A"}
          </span>
        </div>
        <div className="result-row">
          <span className="label">Transaction ID</span>
          <span className="value">{ocr_data.fields.upi_transaction_id || "N/A"}</span>
        </div>
        <div className="result-row">
          <span className="label">Receiver</span>
          <span className="value">{ocr_data.fields.receiver_name || "N/A"}</span>
        </div>
        <div className="result-row">
          <span className="label">Timestamp</span>
          <span className="value">{ocr_data.fields.timestamp || "N/A"}</span>
        </div>
        <div className="result-row">
          <span className="label">Payment App</span>
          <span className="value">{ocr_data.fields.payment_app_name || "N/A"}</span>
        </div>
        {imageQualityPct != null && (
          <div className="result-row">
            <span className="label">Image Quality</span>
            <span className="value">{imageQualityPct}%</span>
          </div>
        )}
        {ocr_data.ocr_pass_count != null && ocr_data.ocr_pass_count > 1 && (
          <div className="result-row">
            <span className="label">OCR Passes</span>
            <span className="value">{ocr_data.ocr_pass_count} passes (multi-pass consensus)</span>
          </div>
        )}
      </div>

      <div className="result-block">
        <h4 className="result-block-title">Fraud Intelligence</h4>
        <div className="result-row">
          <span className="label">Template Match</span>
          <span className={`value ${fraud_intelligence_data.fingerprint_match ? "danger" : "success"}`}>
            {fraud_intelligence_data.fingerprint_match ? "DETECTED" : "CLEAR"}
          </span>
        </div>
        <div className="result-row">
          <span className="label">Confidence</span>
          <span className="value">{Math.round(fraud_intelligence_data.match_confidence * 100)}%</span>
        </div>
        <div className="result-row">
          <span className="label">Fraud Type</span>
          <span className="value">{fraud_intelligence_data.fraud_type || "N/A"}</span>
        </div>
      </div>

      <div className="result-block">
        <h4 className="result-block-title">AI Reasoning</h4>
        <ul style={{ paddingLeft: "16px", margin: "8px 0 0 0", listStyleType: "disc" }}>
          {trust_score_data.confidence_reasoning.length > 0 ? (
            trust_score_data.confidence_reasoning.map((reason, idx) => (
              <li key={idx} className="result-reason" style={{ fontSize: "0.80rem", color: "var(--foreground-dim)", lineHeight: "1.4", marginBottom: "6px" }}>
                {reason}
              </li>
            ))
          ) : (
            <li className="result-reason" style={{ fontSize: "0.80rem", color: "var(--foreground-dim)", lineHeight: "1.4", listStyleType: "none", marginLeft: "-16px" }}>
              Standard verification checks passed successfully.
            </li>
          )}
        </ul>
      </div>

      <div className="result-block">
        <h4 className="result-block-title">Recommended Actions</h4>
        <ul style={{ paddingLeft: "16px", margin: "8px 0 0 0", listStyleType: "square" }}>
          {trust_score_data.recommended_actions.length > 0 ? (
            trust_score_data.recommended_actions.map((action, idx) => (
              <li key={idx} className="result-action" style={{ fontSize: "0.80rem", color: "var(--foreground-dim)", lineHeight: "1.4", marginBottom: "6px" }}>
                {action}
              </li>
            ))
          ) : (
            <li className="result-action" style={{ fontSize: "0.80rem", color: "var(--foreground-dim)", lineHeight: "1.4", marginBottom: "6px" }}>
              Verify transaction UTR and receiver credentials directly in your banking app before releasing goods.
            </li>
          )}
        </ul>
      </div>
      
      <div className="result-block">
        <h4 className="result-block-title">Scan Metadata</h4>
        <div className="result-row">
          <span className="label">Execution Time</span>
          <span className="value">{metadata.execution_time_ms}ms</span>
        </div>
      </div>
    </div>
  );
}
