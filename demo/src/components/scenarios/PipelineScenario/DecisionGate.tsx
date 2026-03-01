import { useState, useMemo, useCallback } from 'react';
import type { Claim } from '../../../lib/akf';
import { effectiveTrust } from '../../../lib/akf';
import { PIPELINE_SCENARIO } from '../../../lib/scenarios';
import ClaimCard from '../../shared/ClaimCard';

interface DecisionGateProps {
  claims: Claim[];
  question: string;
  onComplete: () => void;
}

const SOURCE_ORDER = ['Market Data', 'CRM Analysis', 'News Sentiment'] as const;

function sourceForClaim(claim: Claim): string {
  for (const source of PIPELINE_SCENARIO.sources) {
    if (source.claims.some((sc) => sc.id === claim.id)) {
      return source.name;
    }
  }
  return 'Unknown';
}

export default function DecisionGate({ claims, question, onComplete }: DecisionGateProps) {
  const [threshold, setThreshold] = useState(0.5);
  const [toastVisible, setToastVisible] = useState(false);
  const [decided, setDecided] = useState(false);

  const claimsWithTrust = useMemo(() => {
    return claims.map((c) => ({
      claim: c,
      et: effectiveTrust(c),
      source: sourceForClaim(c),
    }));
  }, [claims]);

  const grouped = useMemo(() => {
    const groups: Record<string, typeof claimsWithTrust> = {};
    for (const name of SOURCE_ORDER) {
      groups[name] = [];
    }
    for (const item of claimsWithTrust) {
      if (!groups[item.source]) {
        groups[item.source] = [];
      }
      groups[item.source].push(item);
    }
    for (const key of Object.keys(groups)) {
      groups[key].sort((a, b) => b.et.score - a.et.score);
    }
    return groups;
  }, [claimsWithTrust]);

  const passingCount = useMemo(() => {
    return claimsWithTrust.filter((c) => c.et.score >= threshold).length;
  }, [claimsWithTrust, threshold]);

  const majorityPass = passingCount > claims.length / 2;

  const handleRecordDecision = useCallback(() => {
    setDecided(true);
    setToastVisible(true);
    setTimeout(() => {
      setToastVisible(false);
    }, 3000);
    setTimeout(() => {
      onComplete();
    }, 1000);
  }, [onComplete]);

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 space-y-6 relative">
      {/* Question */}
      <div className="bg-gray-50 rounded-lg border border-gray-200 p-5">
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Decision Question</p>
        <p className="text-lg font-semibold text-gray-800">{question}</p>
      </div>

      {/* Main layout */}
      <div className="flex gap-6">
        {/* Left: Evidence panel (60%) */}
        <div className="w-[60%] space-y-5">
          <h4 className="text-sm font-semibold text-gray-700">Supporting Evidence</h4>
          {SOURCE_ORDER.map((sourceName) => {
            const items = grouped[sourceName];
            if (!items || items.length === 0) return null;
            return (
              <div key={sourceName} className="space-y-2">
                <h5 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  {sourceName}
                </h5>
                <div className="space-y-2">
                  {items.map((item, idx) => {
                    const belowThreshold = item.et.score < threshold;
                    return (
                      <div
                        key={item.claim.id || idx}
                        className={`transition-all duration-300 ${
                          belowThreshold ? 'opacity-40 grayscale' : 'opacity-100'
                        }`}
                      >
                        <div className={belowThreshold ? 'line-through decoration-red-400 decoration-2' : ''}>
                          <ClaimCard claim={item.claim} index={idx} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>

        {/* Right: Decision panel (40%) */}
        <div className="w-[40%] space-y-5">
          <h4 className="text-sm font-semibold text-gray-700">Decision Panel</h4>

          {/* Trust threshold slider */}
          <div className="space-y-3 bg-gray-50 rounded-lg border border-gray-200 p-4">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Trust Threshold
              </label>
              <span className="text-sm font-bold text-blue-600">
                {threshold.toFixed(2)}
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={threshold}
              onChange={(e) => setThreshold(parseFloat(e.target.value))}
              className="w-full h-2 rounded-lg appearance-none cursor-pointer accent-blue-600 bg-gray-200"
            />
            <div className="flex justify-between text-[10px] text-gray-400">
              <span>0.0</span>
              <span>0.25</span>
              <span>0.5</span>
              <span>0.75</span>
              <span>1.0</span>
            </div>
          </div>

          {/* Passing count */}
          <div className="text-center py-3 bg-gray-50 rounded-lg border border-gray-200">
            <p className="text-2xl font-bold text-gray-800">
              {passingCount} <span className="text-base font-normal text-gray-500">of</span> {claims.length}
            </p>
            <p className="text-xs text-gray-500 mt-0.5">claims meet threshold</p>
          </div>

          {/* Decision recommendation */}
          <div
            className={`rounded-lg border-2 p-5 transition-all duration-300 ${
              majorityPass
                ? 'border-green-400 bg-green-50'
                : 'border-red-400 bg-red-50'
            }`}
          >
            <div className="flex items-center gap-2 mb-2">
              {majorityPass ? (
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              ) : (
                <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              )}
              <span
                className={`text-lg font-bold ${
                  majorityPass ? 'text-green-700' : 'text-red-700'
                }`}
              >
                {majorityPass ? 'PROCEED' : 'HOLD'}
              </span>
            </div>
            <p
              className={`text-sm ${
                majorityPass ? 'text-green-700' : 'text-red-700'
              }`}
            >
              {majorityPass
                ? 'Sufficient evidence above threshold'
                : 'Insufficient high-trust evidence'}
            </p>
          </div>

          {/* Record Decision button */}
          <button
            onClick={handleRecordDecision}
            disabled={decided}
            className={`w-full py-3 px-4 rounded-lg text-sm font-semibold transition-all duration-200 ${
              decided
                ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700 active:bg-blue-800 shadow-sm'
            }`}
          >
            {decided ? 'Decision Recorded' : 'Record Decision'}
          </button>
        </div>
      </div>

      {/* Toast */}
      {toastVisible && (
        <div className="fixed bottom-6 right-6 z-50 animate-slide-in">
          <div className="flex items-center gap-3 bg-gray-900 text-white px-5 py-3 rounded-lg shadow-lg">
            <svg className="w-5 h-5 text-green-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
            </svg>
            <span className="text-sm">Decision recorded as derivative <span className="font-mono text-blue-300">.akf</span></span>
          </div>
        </div>
      )}
    </div>
  );
}
