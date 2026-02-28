import { useState } from 'react';
import type { AKFUnit } from '../lib/akf';
import { addHop } from '../lib/akf';
import AKFCodeView from './AKFCodeView';
import ProvenanceTree from './ProvenanceTree';
import ClaimCard from './ClaimCard';

interface PurviewProtectProps {
  unit: AKFUnit;
}

export default function PurviewProtect({ unit }: PurviewProtectProps) {
  const [currentUnit, setCurrentUnit] = useState<AKFUnit>(unit);
  const [shareMode, setShareMode] = useState<'none' | 'internal' | 'external'>('none');
  const [showRawJson, setShowRawJson] = useState(false);
  const [animateDlp, setAnimateDlp] = useState(false);

  const hasAiClaims = currentUnit.claims.some(c => c.ai);
  const minTrust = Math.min(...currentUnit.claims.map(c => c.t));
  const maxTrust = Math.max(...currentUnit.claims.map(c => c.t));

  const shareInternal = () => {
    const updated = addHop(currentUnit, 'teams-connector', 'shared-internal', {
      delta: 'sent to #strategy channel',
    });
    setCurrentUnit(updated);
    setShareMode('internal');
    setAnimateDlp(false);
  };

  const shareExternal = () => {
    setShareMode('external');
    setAnimateDlp(true);
  };

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-xl font-bold text-gray-800 mb-1">Hop 3: Egress / Protect</h2>
        <p className="text-sm text-gray-500">
          Share the .akf unit internally or externally. Microsoft Purview DLP enforces data governance.
        </p>
      </div>

      {/* Share buttons */}
      <div className="flex gap-4">
        <button
          onClick={shareInternal}
          className="flex-1 py-3 bg-blue-600 text-white font-bold rounded-lg hover:bg-blue-700 transition-colors shadow-md flex items-center justify-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          Share Internal (Teams)
        </button>
        <button
          onClick={shareExternal}
          className="flex-1 py-3 bg-gray-700 text-white font-bold rounded-lg hover:bg-gray-800 transition-colors shadow-md flex items-center justify-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          Share External (Email)
        </button>
      </div>

      {/* Internal: Teams chat bubble */}
      {shareMode === 'internal' && (
        <div className="animate-fade-in">
          <div className="bg-white border border-gray-200 rounded-xl shadow-lg max-w-2xl mx-auto overflow-hidden">
            {/* Teams header */}
            <div className="bg-indigo-700 px-4 py-2 flex items-center gap-2">
              <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
                <path d="M19.19 8.77q-.46 0-.87.13a3.15 3.15 0 00-1.62-2.44 3.07 3.07 0 00-3-.11A3.84 3.84 0 0011 5.5a3.76 3.76 0 00-2 .57V6a3 3 0 00-3-3H5.5A2.5 2.5 0 003 5.5V6a3 3 0 003 3h.09A3.69 3.69 0 006 9.5v.46A2.51 2.51 0 004 12.35v4.18A2.47 2.47 0 006.5 19h3.83a4 4 0 001.52-2h3.3a4 4 0 001.52 2h2.14A2.19 2.19 0 0021 16.81v-5.64a2.39 2.39 0 00-1.81-2.4z"/>
              </svg>
              <span className="text-white text-sm font-semibold">Microsoft Teams</span>
              <span className="text-indigo-200 text-xs ml-2">#strategy-planning</span>
            </div>

            {/* Chat message */}
            <div className="p-4 space-y-3">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs font-bold shrink-0">
                  S
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-semibold text-gray-800">{currentUnit.author}</span>
                    <span className="text-xs text-gray-400">just now</span>
                  </div>
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 space-y-2">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xs font-mono bg-blue-100 text-blue-700 px-2 py-0.5 rounded">.akf</span>
                      <span className="text-xs text-gray-500">
                        {currentUnit.classification}
                      </span>
                    </div>
                    {currentUnit.claims.map((claim, i) => (
                      <ClaimCard key={i} claim={claim} index={i} />
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* External: DLP Block */}
      {shareMode === 'external' && animateDlp && (
        <div className="animate-fade-in">
          <div className="bg-red-50 border-2 border-red-400 rounded-xl shadow-lg max-w-2xl mx-auto overflow-hidden">
            {/* Red banner */}
            <div className="bg-red-600 px-4 py-3 flex items-center gap-3">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
              </svg>
              <span className="text-white font-bold text-lg">Blocked by Microsoft Purview DLP</span>
            </div>

            <div className="p-6 space-y-4">
              {/* Policy */}
              <div className="space-y-3">
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-red-100 rounded-full flex items-center justify-center shrink-0 mt-0.5">
                    <svg className="w-4 h-4 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-red-700">Policy Matched</p>
                    <p className="text-sm text-red-600">
                      Confidential AI-generated content cannot be shared externally
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-red-100 rounded-full flex items-center justify-center shrink-0 mt-0.5">
                    <svg className="w-4 h-4 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-red-700">Classification Detected</p>
                    <p className="text-sm text-red-600">
                      <span className="font-mono bg-red-100 px-1.5 py-0.5 rounded">{currentUnit.classification}</span>
                    </p>
                  </div>
                </div>

                {hasAiClaims && (
                  <div className="flex items-start gap-3">
                    <div className="w-6 h-6 bg-amber-100 rounded-full flex items-center justify-center shrink-0 mt-0.5">
                      <svg className="w-4 h-4 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-amber-700">AI Flags Detected</p>
                      <p className="text-sm text-amber-600">
                        {currentUnit.claims.filter(c => c.ai).length} claim(s) flagged as AI-generated
                      </p>
                    </div>
                  </div>
                )}

                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center shrink-0 mt-0.5">
                    <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-blue-700">Confidence Range</p>
                    <p className="text-sm text-blue-600">
                      {(minTrust * 100).toFixed(0)}% - {(maxTrust * 100).toFixed(0)}% across {currentUnit.claims.length} claims
                    </p>
                  </div>
                </div>
              </div>

              <div className="border-t border-red-200 pt-3">
                <p className="text-xs text-red-400">
                  This action has been logged. Contact your compliance administrator for exceptions.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Provenance Tree */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="space-y-4">
          <ProvenanceTree hops={currentUnit.prov} />
        </div>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-600">Raw .akf</h3>
            <button
              onClick={() => setShowRawJson(!showRawJson)}
              className="text-xs text-blue-600 hover:text-blue-800 font-semibold"
            >
              {showRawJson ? 'Hide' : 'View Raw .akf'}
            </button>
          </div>
          {showRawJson && <AKFCodeView unit={currentUnit} />}
        </div>
      </div>
    </div>
  );
}
