import { useState, useEffect } from "react";
import type { AKFUnit } from "../../../lib/akf";
import SystemBadge from "../../shared/SystemBadge";
import DLPBlockPanel from "../../shared/DLPBlockPanel";

interface OutlookComposePanelProps {
  unit: AKFUnit;
  onComplete: () => void;
}

const RECIPIENT_EMAIL = "partner@externalfirm.com";

export default function OutlookComposePanel({ unit, onComplete }: OutlookComposePanelProps) {
  const [sendClicked, setSendClicked] = useState(false);
  const [sending, setSending] = useState(false);
  const [blocked, setBlocked] = useState(false);

  // After 1.5s, simulate Send click
  useEffect(() => {
    const timer = setTimeout(() => setSendClicked(true), 1500);
    return () => clearTimeout(timer);
  }, []);

  // After Send click, show sending spinner
  useEffect(() => {
    if (!sendClicked) return;
    setSending(true);
    const timer = setTimeout(() => {
      setSending(false);
      setBlocked(true);
    }, 1000);
    return () => clearTimeout(timer);
  }, [sendClicked]);

  // After block shows, call onComplete
  useEffect(() => {
    if (!blocked) return;
    const timer = setTimeout(() => onComplete(), 500);
    return () => clearTimeout(timer);
  }, [blocked, onComplete]);

  return (
    <div className="animate-fade-in rounded-xl overflow-hidden border border-gray-200 shadow-lg bg-white">
      {/* Outlook title bar */}
      <div className="flex items-center gap-2 px-4 py-2 bg-[#0078D4]">
        {/* Outlook icon */}
        <svg className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10h5v-2h-5a8 8 0 01-8-8 8 8 0 018-8 8 8 0 018 8v1.43c0 .79-.71 1.57-1.5 1.57s-1.5-.78-1.5-1.57V12a5 5 0 00-5-5 5 5 0 00-5 5 5 5 0 005 5c1.38 0 2.64-.56 3.54-1.47.65.89 1.77 1.47 2.96 1.47 1.97 0 3.5-1.6 3.5-3.57V12c0-5.52-4.48-10-10-10zm0 13c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3z" />
        </svg>
        <span className="text-white text-sm font-medium flex-1">New Message — Outlook</span>
        <SystemBadge system="outlook" />
      </div>

      {/* Ribbon toolbar */}
      <div className="flex items-center gap-1 px-3 py-1.5 bg-[#f5f5f5] border-b border-gray-200">
        <button className="text-[11px] text-gray-600 px-2 py-1 rounded hover:bg-gray-200">
          Format Text
        </button>
        <button className="text-[11px] text-gray-600 px-2 py-1 rounded hover:bg-gray-200">
          Insert
        </button>
        <button className="text-[11px] text-gray-600 px-2 py-1 rounded hover:bg-gray-200">
          Options
        </button>
        <div className="flex-1" />
        <button className="text-[11px] text-gray-600 px-2 py-1 rounded hover:bg-gray-200">
          Discard
        </button>
      </div>

      <div className="relative" style={{ minHeight: 380 }}>
        {/* Compose form */}
        <div className={`${blocked ? "opacity-40 pointer-events-none" : ""} transition-opacity duration-300`}>
          {/* To field */}
          <div className="flex items-center gap-3 px-4 py-2.5 border-b border-gray-200">
            <span className="text-xs text-gray-500 font-medium w-12 shrink-0">To:</span>
            <div className="flex items-center gap-2 flex-1">
              <span className="inline-flex items-center gap-1.5 bg-blue-50 border border-blue-200 rounded-full px-2.5 py-1 text-xs text-blue-700">
                {RECIPIENT_EMAIL}
                <span className="inline-flex items-center gap-0.5 bg-red-100 text-red-600 text-[9px] px-1 py-0.5 rounded font-semibold">
                  <svg className="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 9v2m0 4h.01" />
                  </svg>
                  EXTERNAL
                </span>
              </span>
            </div>
          </div>

          {/* Subject field */}
          <div className="flex items-center gap-3 px-4 py-2.5 border-b border-gray-200">
            <span className="text-xs text-gray-500 font-medium w-12 shrink-0">Subject:</span>
            <span className="text-sm text-gray-800">Q3 Analysis — Woodgrove Financials</span>
          </div>

          {/* Body */}
          <div className="px-4 py-4">
            <p className="text-sm text-gray-700 leading-relaxed mb-4">
              Hi Partner,
            </p>
            <p className="text-sm text-gray-700 leading-relaxed mb-4">
              Please find attached our Q3 analysis with Copilot-generated summary and supporting data.
              The key findings include strong cloud growth and expanded enterprise pipeline.
            </p>
            <p className="text-sm text-gray-700 leading-relaxed mb-6">
              Let me know if you have questions on the methodology.
            </p>
            <p className="text-sm text-gray-700">
              Best regards,<br />
              Sarah Chen<br />
              <span className="text-gray-400 text-xs">Financial Analyst, Woodgrove</span>
            </p>
          </div>

          {/* Attachment */}
          <div className="px-4 pb-4">
            <div className="border border-gray-200 rounded-lg p-3 flex items-center gap-3 bg-gray-50 max-w-sm">
              <div className="w-10 h-10 bg-[#217346] rounded-lg flex items-center justify-center shrink-0">
                <svg className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z" />
                  <path d="M8.5 13.5l1.7 2.5-1.7 2.5h1.5l1-1.6 1 1.6h1.5l-1.7-2.5 1.7-2.5H12l-1 1.6-1-1.6H8.5z" opacity="0.6" />
                </svg>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-800 truncate">
                  Woodgrove-Q3-Analysis.xlsx
                </p>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <span className="text-[10px] font-mono bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded">
                    .akf
                  </span>
                  <span className="text-[10px] text-gray-400">4 claims attached</span>
                </div>
              </div>
              <svg className="w-4 h-4 text-gray-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
          </div>

          {/* Send button area */}
          <div className="px-4 pb-4 flex items-center gap-3">
            <button
              className={`flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-semibold transition-all duration-300 ${
                sendClicked
                  ? "bg-blue-700 text-white scale-95 ring-4 ring-blue-200"
                  : "bg-[#0078D4] text-white hover:bg-blue-700"
              }`}
            >
              {sending ? (
                <>
                  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  <span>Sending...</span>
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                  <span>Send</span>
                </>
              )}
            </button>
            {sending && (
              <span className="text-xs text-gray-400 animate-pulse">
                Checking compliance policies...
              </span>
            )}
          </div>
        </div>

        {/* DLP Block overlay */}
        {blocked && (
          <div className="absolute inset-0 flex items-center justify-center p-6 bg-white/60 backdrop-blur-sm">
            <div className="w-full max-w-md">
              <DLPBlockPanel
                unit={unit}
                recipientEmail={RECIPIENT_EMAIL}
                onDismiss={() => {}}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
