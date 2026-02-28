import { useState } from 'react';
import type { Claim, AKFUnit } from '../lib/akf';
import { addHop } from '../lib/akf';
import ClaimCard from './ClaimCard';
import AKFCodeView from './AKFCodeView';
import ProvenanceTree from './ProvenanceTree';

interface CopilotEnrichProps {
  unit: AKFUnit;
  onComplete: (unit: AKFUnit) => void;
}

const AI_CLAIMS: Claim[] = [
  {
    c: 'AI copilot adoption rate is 34% across Fortune 500',
    t: 0.78,
    tier: 2,
    ai: true,
    src: 'Gartner 2025 survey',
  },
  {
    c: 'H2 revenue will accelerate to 25% growth',
    t: 0.63,
    tier: 5,
    ai: true,
    risk: 'AI inference \u2014 extrapolated from limited data',
  },
];

export default function CopilotEnrich({ unit, onComplete }: CopilotEnrichProps) {
  const [currentUnit, setCurrentUnit] = useState<AKFUnit>(unit);
  const [aiClaims, setAiClaims] = useState<Claim[]>([]);
  const [copilotAsked, setCopilotAsked] = useState(false);
  const [reviewedIndices, setReviewedIndices] = useState<Set<number>>(new Set());
  const [rejectedLog, setRejectedLog] = useState<string[]>([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newContent, setNewContent] = useState('');
  const [newTrust, setNewTrust] = useState(0.75);

  const askCopilot = () => {
    setCopilotAsked(true);
    // Simulate a brief delay for the AI claims
    setTimeout(() => {
      setAiClaims(AI_CLAIMS);
      const updated = addHop(
        { ...currentUnit, claims: [...currentUnit.claims, ...AI_CLAIMS] },
        'copilot-m365',
        'enriched',
        { delta: `+${AI_CLAIMS.length} claims` }
      );
      setCurrentUnit(updated);
    }, 600);
  };

  const confirmClaim = (index: number) => {
    setReviewedIndices(prev => new Set(prev).add(index));
  };

  const rejectClaim = (index: number) => {
    const claim = aiClaims[index];
    setRejectedLog(prev => [...prev, `Rejected: "${claim.c}"`]);
    setReviewedIndices(prev => new Set(prev).add(index));

    // Remove the claim from the unit
    const newClaims = currentUnit.claims.filter(c => c.c !== claim.c);
    setCurrentUnit(prev => ({ ...prev, claims: newClaims }));
    setAiClaims(prev => prev.map((c, i) => i === index ? { ...c, _rejected: true } as Claim & { _rejected: boolean } : c));
  };

  const addOwnClaim = () => {
    if (!newContent.trim()) return;
    const claim: Claim = {
      c: newContent.trim(),
      t: newTrust,
      tier: 2,
      verified: true,
      src: 'manual addition',
    };
    setCurrentUnit(prev => ({
      ...prev,
      claims: [...prev.claims, claim],
    }));
    setNewContent('');
    setShowAddForm(false);
  };

  const finishReview = () => {
    const rejectedCount = rejectedLog.length;
    const acceptedAiCount = aiClaims.length - rejectedCount;
    const updated = addHop(
      currentUnit,
      currentUnit.author,
      'reviewed',
      { delta: `+${acceptedAiCount}${rejectedCount > 0 ? `, -${rejectedCount} rejected` : ''}` }
    );
    setCurrentUnit(updated);
    onComplete(updated);
  };

  const allReviewed = aiClaims.length > 0 && aiClaims.every((_, i) => reviewedIndices.has(i));

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
      {/* Left: Claims & Controls */}
      <div className="lg:col-span-2 space-y-6">
        <div>
          <h2 className="text-xl font-bold text-gray-800 mb-1">Hop 2: AI + Human Review</h2>
          <p className="text-sm text-gray-500">
            Copilot enriches with AI-generated claims. Human reviews and approves.
          </p>
        </div>

        {/* Existing claims from Step 1 */}
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-gray-600">
            Original Claims ({unit.claims.length})
          </h3>
          {unit.claims.map((claim, i) => (
            <ClaimCard key={`orig-${i}`} claim={claim} index={i} />
          ))}
        </div>

        {/* Ask Copilot Button */}
        {!copilotAsked && (
          <button
            onClick={askCopilot}
            className="w-full py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white font-bold rounded-lg hover:from-purple-700 hover:to-blue-700 transition-all shadow-md flex items-center justify-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            Ask Copilot to Enrich
          </button>
        )}

        {/* AI Claims */}
        {aiClaims.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-amber-600">
              AI-Generated Claims ({aiClaims.length})
            </h3>
            {aiClaims.map((claim, i) => {
              const isRejected = (claim as Claim & { _rejected?: boolean })._rejected;
              const isReviewed = reviewedIndices.has(i);
              return (
                <div
                  key={`ai-${i}`}
                  className={`transition-opacity duration-300 ${isRejected ? 'opacity-30' : ''}`}
                >
                  <ClaimCard
                    claim={claim}
                    index={unit.claims.length + i}
                    animateIn={true}
                    actions={
                      !isReviewed ? (
                        <>
                          <button
                            onClick={() => confirmClaim(i)}
                            className="p-1.5 rounded-md bg-green-100 text-green-700 hover:bg-green-200 transition-colors"
                            title="Confirm"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                            </svg>
                          </button>
                          <button
                            onClick={() => rejectClaim(i)}
                            className="p-1.5 rounded-md bg-red-100 text-red-700 hover:bg-red-200 transition-colors"
                            title="Reject"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                          </button>
                        </>
                      ) : isRejected ? (
                        <span className="text-xs text-red-500 font-semibold px-2 py-1">Rejected</span>
                      ) : (
                        <span className="text-xs text-green-600 font-semibold px-2 py-1">Confirmed</span>
                      )
                    }
                  />
                </div>
              );
            })}
          </div>
        )}

        {/* Rejected log */}
        {rejectedLog.length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3">
            <h4 className="text-xs font-semibold text-red-600 mb-1">Rejection Log</h4>
            {rejectedLog.map((log, i) => (
              <p key={i} className="text-xs text-red-500">{log}</p>
            ))}
          </div>
        )}

        {/* Add own claim */}
        {copilotAsked && (
          <>
            {!showAddForm ? (
              <button
                onClick={() => setShowAddForm(true)}
                className="text-sm text-blue-600 hover:text-blue-800 font-semibold"
              >
                + Add my own claim
              </button>
            ) : (
              <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-3">
                <textarea
                  value={newContent}
                  onChange={e => setNewContent(e.target.value)}
                  rows={2}
                  placeholder="Your claim..."
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none resize-none"
                />
                <div className="flex items-center gap-4">
                  <label className="text-xs text-gray-600">Trust: {newTrust.toFixed(2)}</label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.01"
                    value={newTrust}
                    onChange={e => setNewTrust(parseFloat(e.target.value))}
                    className="flex-1 accent-blue-600"
                  />
                  <button
                    onClick={addOwnClaim}
                    disabled={!newContent.trim()}
                    className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 disabled:opacity-40"
                  >
                    Add
                  </button>
                  <button
                    onClick={() => setShowAddForm(false)}
                    className="px-3 py-1.5 text-gray-500 text-sm hover:text-gray-700"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </>
        )}

        {/* Finish button */}
        {allReviewed && (
          <button
            onClick={finishReview}
            className="w-full py-3 bg-blue-600 text-white font-bold rounded-lg hover:bg-blue-700 transition-colors shadow-md"
          >
            Finish Review & Proceed
          </button>
        )}
      </div>

      {/* Right sidebar */}
      <div className="space-y-4">
        <ProvenanceTree hops={currentUnit.prov} />
        <h3 className="text-sm font-semibold text-gray-600">JSON Preview</h3>
        <AKFCodeView unit={currentUnit} />
      </div>
    </div>
  );
}
