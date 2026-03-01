import { useState, useEffect } from "react";
import type { Claim } from "../../../lib/akf";
import { effectiveTrust } from "../../../lib/akf";
import { DEV_SCENARIO } from "../../../lib/scenarios";
import ClaimCard from "../../shared/ClaimCard";
import SystemBadge from "../../shared/SystemBadge";

interface PRReviewPanelProps {
  claims: Claim[];
  onComplete: () => void;
}

type Tab = "conversation" | "files" | "knowledge";

export default function PRReviewPanel({ claims, onComplete }: PRReviewPanelProps) {
  const [activeTab, setActiveTab] = useState<Tab>("knowledge");
  const [reviewedClaims, setReviewedClaims] = useState<Set<number>>(new Set());
  const [showStatusCheck, setShowStatusCheck] = useState(false);

  // Sequentially approve claims
  useEffect(() => {
    if (reviewedClaims.size >= claims.length) return;

    const timer = setTimeout(() => {
      setReviewedClaims((prev) => {
        const next = new Set(prev);
        next.add(next.size);
        return next;
      });
    }, 1500);

    return () => clearTimeout(timer);
  }, [reviewedClaims.size, claims.length]);

  // Show status check after all claims reviewed
  useEffect(() => {
    if (reviewedClaims.size < claims.length) return;
    const timer = setTimeout(() => setShowStatusCheck(true), 800);
    return () => clearTimeout(timer);
  }, [reviewedClaims.size, claims.length]);

  // Fire onComplete after status check
  useEffect(() => {
    if (!showStatusCheck) return;
    const timer = setTimeout(() => onComplete(), 2000);
    return () => clearTimeout(timer);
  }, [showStatusCheck, onComplete]);

  // Compute overall trust pass
  const allTrustScores = claims.map((c) => effectiveTrust(c).score);
  const allAboveThreshold = allTrustScores.every((s) => s >= 0.5);

  const tabs: { key: Tab; label: string; count?: number }[] = [
    { key: "conversation", label: "Conversation", count: 3 },
    { key: "files", label: "Files changed", count: 4 },
    { key: "knowledge", label: "Knowledge (AKF)", count: claims.length },
  ];

  return (
    <div className="rounded-lg overflow-hidden border border-gray-200 shadow-lg bg-white">
      {/* PR Header */}
      <div className="border-b border-gray-200 px-6 py-4">
        <div className="flex items-center gap-3 mb-2">
          <SystemBadge system="github" />
          <span className="text-xs text-gray-400 font-mono">Pull Request</span>
        </div>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              {DEV_SCENARIO.prTitle}
              <span className="text-gray-400 font-normal ml-2">
                #{DEV_SCENARIO.prNumber}
              </span>
            </h2>
            <div className="flex items-center gap-3 mt-2">
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-green-100 text-green-800 border border-green-300">
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 24 24">
                  <circle cx="12" cy="12" r="4" />
                </svg>
                Open
              </span>
              <span className="text-xs text-gray-500">
                <span className="text-green-600 font-semibold">+247</span>
                {" "}
                <span className="text-red-500 font-semibold">-12</span>
              </span>
              <span className="text-xs text-gray-400">
                {DEV_SCENARIO.author} wants to merge into <code className="bg-gray-100 px-1 py-0.5 rounded text-blue-600">main</code>
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 px-6">
        <div className="flex gap-0">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.key
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              {tab.label}
              {tab.count !== undefined && (
                <span
                  className={`ml-1.5 px-1.5 py-0.5 rounded-full text-[11px] font-semibold ${
                    activeTab === tab.key
                      ? "bg-blue-100 text-blue-600"
                      : "bg-gray-100 text-gray-500"
                  }`}
                >
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      <div className="px-6 py-5 min-h-[400px]">
        {activeTab === "knowledge" && (
          <div className="space-y-4">
            {/* Section header */}
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-mono bg-blue-50 text-blue-600 px-2 py-0.5 rounded">
                .akf
              </span>
              <span className="text-sm font-semibold text-gray-700">
                Knowledge Claims
              </span>
              <span className="text-xs text-gray-400">
                from caching-strategy.akf
              </span>
            </div>

            {/* Claim cards with review status */}
            {claims.map((claim, i) => (
              <div key={claim.id || i} className="relative">
                <ClaimCard
                  claim={claim}
                  index={i}
                  animateIn
                  actions={
                    reviewedClaims.has(i) ? (
                      <div className="flex items-center gap-1.5 px-2 py-1 bg-green-50 border border-green-200 rounded-lg animate-fade-in">
                        <svg
                          className="w-4 h-4 text-green-600"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2.5}
                            d="M5 13l4 4L19 7"
                          />
                        </svg>
                        <span className="text-xs font-semibold text-green-700">
                          Reviewed
                        </span>
                      </div>
                    ) : undefined
                  }
                />
              </div>
            ))}

            {/* PR status check */}
            {showStatusCheck && (
              <div className="mt-4 border border-green-200 bg-green-50 rounded-lg px-4 py-3 flex items-center gap-3 animate-fade-in">
                <div className="w-8 h-8 rounded-full bg-green-500 flex items-center justify-center shrink-0">
                  <svg
                    className="w-5 h-5 text-white"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2.5}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-semibold text-green-800">
                    AKF Trust: {allAboveThreshold ? "PASS" : "WARN"}
                  </p>
                  <p className="text-xs text-green-600">
                    All claims above 0.5 threshold
                    {" \u2014 "}
                    scores: {allTrustScores.map((s) => s.toFixed(2)).join(", ")}
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === "conversation" && (
          <div className="text-sm text-gray-400 italic py-8 text-center">
            Conversation tab (demo focuses on Knowledge tab)
          </div>
        )}

        {activeTab === "files" && (
          <div className="text-sm text-gray-400 italic py-8 text-center">
            Files changed tab (demo focuses on Knowledge tab)
          </div>
        )}
      </div>
    </div>
  );
}
