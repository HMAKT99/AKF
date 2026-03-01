import { useState, useEffect } from "react";
import { ANALYST_SCENARIO } from "../../../lib/scenarios";
import { useTypingEffect } from "../../../lib/simulation";
import SystemBadge from "../../shared/SystemBadge";

interface OfficeMockProps {
  onComplete: () => void;
}

export default function OfficeMock({ onComplete }: OfficeMockProps) {
  const [typingActive, setTypingActive] = useState(false);
  const [showStatusBar, setShowStatusBar] = useState(false);
  const [showToast, setShowToast] = useState(false);

  const { displayed, done: typingDone } = useTypingEffect(
    ANALYST_SCENARIO.copilotSummary,
    typingActive,
    8
  );

  // Start typing after 1s delay
  useEffect(() => {
    const timer = setTimeout(() => setTypingActive(true), 1000);
    return () => clearTimeout(timer);
  }, []);

  // When typing finishes, show status bar
  useEffect(() => {
    if (!typingDone) return;
    const timer = setTimeout(() => setShowStatusBar(true), 500);
    return () => clearTimeout(timer);
  }, [typingDone]);

  // After status bar appears, show toast
  useEffect(() => {
    if (!showStatusBar) return;
    const timer = setTimeout(() => setShowToast(true), 600);
    return () => clearTimeout(timer);
  }, [showStatusBar]);

  // After toast, call onComplete
  useEffect(() => {
    if (!showToast) return;
    const timer = setTimeout(() => onComplete(), 1800);
    return () => clearTimeout(timer);
  }, [showToast, onComplete]);

  return (
    <div className="animate-fade-in rounded-xl overflow-hidden border border-gray-200 shadow-lg bg-white">
      {/* Excel title bar */}
      <div className="flex items-center gap-2 px-4 py-2 bg-[#217346]">
        {/* Excel icon */}
        <svg className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="currentColor">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 1.5L18.5 9H13V3.5zM6 20V4h5v6h6v10H6z" />
          <path d="M8.5 13.5l1.7 2.5-1.7 2.5h1.5l1-1.6 1 1.6h1.5l-1.7-2.5 1.7-2.5H12l-1 1.6-1-1.6H8.5z" />
        </svg>
        <span className="text-white text-sm font-medium flex-1 truncate">
          {ANALYST_SCENARIO.docTitle}
        </span>
        <SystemBadge system="excel" />
        {/* Window controls */}
        <div className="flex items-center gap-1.5 ml-3">
          <div className="w-2.5 h-2.5 rounded-full bg-white/30" />
          <div className="w-2.5 h-2.5 rounded-full bg-white/30" />
          <div className="w-2.5 h-2.5 rounded-full bg-white/30" />
        </div>
      </div>

      {/* Ribbon bar */}
      <div className="flex items-center gap-4 px-4 py-1.5 bg-[#f3f3f3] border-b border-gray-200 text-xs text-gray-500">
        <span className="font-semibold text-gray-700">Home</span>
        <span>Insert</span>
        <span>Page Layout</span>
        <span>Formulas</span>
        <span>Data</span>
        <span>Review</span>
      </div>

      <div className="flex" style={{ minHeight: 400 }}>
        {/* Left: Spreadsheet (60%) */}
        <div className="w-[60%] border-r border-gray-200 relative">
          {/* Formula bar */}
          <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-50 border-b border-gray-200 text-xs">
            <span className="text-gray-400 font-mono w-10">A1</span>
            <div className="h-4 w-px bg-gray-300" />
            <span className="text-gray-600 italic">Revenue ($B)</span>
          </div>

          {/* Spreadsheet grid */}
          <div className="overflow-auto">
            <table className="w-full text-xs border-collapse">
              <thead>
                <tr>
                  <th className="bg-gray-100 border border-gray-200 px-3 py-2 text-left text-gray-500 font-semibold w-8">
                    {/* row number header */}
                  </th>
                  <th className="bg-gray-100 border border-gray-200 px-3 py-2 text-left text-gray-600 font-semibold">
                    Metric
                  </th>
                  <th className="bg-gray-100 border border-gray-200 px-3 py-2 text-center text-gray-600 font-semibold">
                    Q1
                  </th>
                  <th className="bg-gray-100 border border-gray-200 px-3 py-2 text-center text-gray-600 font-semibold">
                    Q2
                  </th>
                  <th className="bg-green-100 border border-green-300 px-3 py-2 text-center text-green-800 font-bold">
                    Q3
                  </th>
                  <th className="bg-gray-100 border border-gray-200 px-3 py-2 text-center text-gray-600 font-semibold">
                    Q4
                  </th>
                </tr>
              </thead>
              <tbody>
                {ANALYST_SCENARIO.spreadsheet.map((row, i) => (
                  <tr key={i} className={i % 2 === 0 ? "bg-white" : "bg-gray-50/50"}>
                    <td className="bg-gray-100 border border-gray-200 px-2 py-2 text-center text-gray-400 font-mono text-[10px]">
                      {i + 1}
                    </td>
                    <td className="border border-gray-200 px-3 py-2 text-gray-800 font-medium">
                      {row.metric}
                    </td>
                    <td className="border border-gray-200 px-3 py-2 text-center text-gray-600">
                      {row.q1}
                    </td>
                    <td className="border border-gray-200 px-3 py-2 text-center text-gray-600">
                      {row.q2}
                    </td>
                    <td className="border border-green-200 bg-green-50 px-3 py-2 text-center text-green-800 font-semibold">
                      {row.q3}
                    </td>
                    <td className="border border-gray-200 px-3 py-2 text-center text-gray-400">
                      {row.q4}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Empty rows to fill space */}
          <div className="border-t border-gray-200">
            {[6, 7, 8, 9].map((n) => (
              <div key={n} className="flex border-b border-gray-100">
                <div className="w-8 bg-gray-100 border-r border-gray-200 px-2 py-2 text-center text-[10px] text-gray-400 font-mono">
                  {n}
                </div>
                <div className="flex-1" />
              </div>
            ))}
          </div>

          {/* Status bar at bottom */}
          {showStatusBar && (
            <div className="absolute bottom-0 left-0 right-0 flex items-center gap-2 px-3 py-1.5 bg-[#217346] text-white text-xs animate-slide-in">
              <svg className="w-3.5 h-3.5 text-blue-200" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z" />
              </svg>
              <span className="font-medium">AKF: 4 claims | confidential</span>
            </div>
          )}
        </div>

        {/* Right: Copilot sidebar (40%) */}
        <div className="w-[40%] bg-[#1e1e2e] flex flex-col">
          {/* Copilot header */}
          <div className="flex items-center gap-2 px-4 py-3 border-b border-white/10">
            {/* Sparkle icon */}
            <svg className="w-5 h-5 text-purple-400" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2l2.09 6.26L20.18 10l-6.09 1.74L12 18l-2.09-6.26L3.82 10l6.09-1.74L12 2z" />
            </svg>
            <span className="text-white font-semibold text-sm">Copilot</span>
            <span className="text-purple-300 text-xs ml-auto">Analyzing...</span>
          </div>

          {/* Copilot chat area */}
          <div className="flex-1 overflow-auto p-4">
            {/* User prompt */}
            <div className="mb-4">
              <div className="flex items-center gap-2 mb-1.5">
                <div className="w-5 h-5 rounded-full bg-blue-500 flex items-center justify-center text-white text-[10px] font-bold">
                  S
                </div>
                <span className="text-xs text-gray-400">sarah@woodgrove.com</span>
              </div>
              <div className="bg-white/10 rounded-lg px-3 py-2 text-sm text-gray-200 ml-7">
                Summarize Q3 performance and highlight key risks.
              </div>
            </div>

            {/* Copilot response */}
            {typingActive && (
              <div>
                <div className="flex items-center gap-2 mb-1.5">
                  <svg className="w-5 h-5 text-purple-400" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2l2.09 6.26L20.18 10l-6.09 1.74L12 18l-2.09-6.26L3.82 10l6.09-1.74L12 2z" />
                  </svg>
                  <span className="text-xs text-purple-300">Copilot</span>
                </div>
                <div className="ml-7 text-sm text-gray-200 leading-relaxed whitespace-pre-wrap">
                  {displayed.split("\n").map((line, i) => {
                    // Bold markdown rendering
                    const parts = line.split(/(\*\*[^*]+\*\*)/g);
                    return (
                      <div key={i} className={line === "" ? "h-2" : ""}>
                        {parts.map((part, j) =>
                          part.startsWith("**") && part.endsWith("**") ? (
                            <span key={j} className="font-bold text-white">
                              {part.slice(2, -2)}
                            </span>
                          ) : (
                            <span key={j}>{part}</span>
                          )
                        )}
                      </div>
                    );
                  })}
                  {!typingDone && (
                    <span className="inline-block w-1.5 h-4 bg-purple-400 ml-0.5 animate-pulse" />
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Toast notification */}
      {showToast && (
        <div className="absolute bottom-16 left-8 animate-slide-in z-10">
          <div className="flex items-center gap-2 bg-gray-800 text-white text-xs px-4 py-2.5 rounded-lg shadow-xl border border-gray-700">
            <svg className="w-4 h-4 text-green-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span>Knowledge metadata saved to document properties</span>
          </div>
        </div>
      )}
    </div>
  );
}
