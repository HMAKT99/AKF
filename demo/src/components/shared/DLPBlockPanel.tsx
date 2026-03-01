import type { AKFUnit } from '../../lib/akf';

interface DLPBlockPanelProps {
  unit: AKFUnit;
  recipientEmail: string;
  onDismiss: () => void;
}

export default function DLPBlockPanel({ unit, recipientEmail, onDismiss }: DLPBlockPanelProps) {
  const aiClaimCount = unit.claims.filter(c => c.ai).length;
  const trustValues = unit.claims.map(c => c.t);
  const minTrust = Math.min(...trustValues);
  const maxTrust = Math.max(...trustValues);
  const provDepth = unit.prov?.length ?? 0;

  return (
    <div className="animate-fade-in">
      <div className="bg-red-50 border-2 border-red-400 rounded-xl shadow-lg overflow-hidden">
        {/* Red banner */}
        <div className="bg-red-600 px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
            </svg>
            <span className="text-white font-bold text-lg">Blocked by Microsoft Purview DLP</span>
          </div>
          <button
            onClick={onDismiss}
            className="text-red-200 hover:text-white transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-6 space-y-4">
          {/* Recipient */}
          <div className="text-sm text-red-600">
            Attempted send to: <span className="font-mono font-semibold">{recipientEmail}</span>
          </div>

          <div className="space-y-3">
            {/* Policy Matched */}
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

            {/* Classification Detected */}
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 bg-red-100 rounded-full flex items-center justify-center shrink-0 mt-0.5">
                <svg className="w-4 h-4 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-semibold text-red-700">Classification Detected</p>
                <p className="text-sm text-red-600">
                  <span className="font-mono bg-red-100 px-1.5 py-0.5 rounded">
                    {unit.label || 'Unclassified'}
                  </span>
                </p>
              </div>
            </div>

            {/* AI-generated claims */}
            {aiClaimCount > 0 && (
              <div className="flex items-start gap-3">
                <div className="w-6 h-6 bg-amber-100 rounded-full flex items-center justify-center shrink-0 mt-0.5">
                  <svg className="w-4 h-4 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-semibold text-amber-700">AI-Generated Claims</p>
                  <p className="text-sm text-amber-600">
                    {aiClaimCount} claim{aiClaimCount !== 1 ? 's' : ''} flagged as AI-generated
                  </p>
                </div>
              </div>
            )}

            {/* Trust Score Range */}
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center shrink-0 mt-0.5">
                <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-semibold text-blue-700">Trust Score Range</p>
                <p className="text-sm text-blue-600">
                  {(minTrust * 100).toFixed(0)}% - {(maxTrust * 100).toFixed(0)}% across {unit.claims.length} claim{unit.claims.length !== 1 ? 's' : ''}
                </p>
              </div>
            </div>

            {/* Provenance Depth */}
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 bg-purple-100 rounded-full flex items-center justify-center shrink-0 mt-0.5">
                <svg className="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-semibold text-purple-700">Provenance Depth</p>
                <p className="text-sm text-purple-600">
                  {provDepth} hop{provDepth !== 1 ? 's' : ''} in chain
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
  );
}
