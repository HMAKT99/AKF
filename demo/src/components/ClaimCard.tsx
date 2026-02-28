import type { Claim } from '../lib/akf';
import { effectiveTrust } from '../lib/akf';
import TrustBadge from './TrustBadge';

interface ClaimCardProps {
  claim: Claim;
  index: number;
  animateIn?: boolean;
  actions?: React.ReactNode;
}

export default function ClaimCard({ claim, index, animateIn, actions }: ClaimCardProps) {
  const eTrust = effectiveTrust(claim);

  return (
    <div
      className={`border rounded-lg p-4 bg-white shadow-sm transition-all duration-500 ${
        animateIn ? 'animate-slide-in' : ''
      } ${claim.ai ? 'border-amber-400 border-2' : 'border-gray-200'}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className="text-xs text-gray-400 font-mono">#{index + 1}</span>
            <TrustBadge trust={eTrust} />
            {claim.ai && (
              <span className="text-xs px-1.5 py-0.5 bg-amber-100 text-amber-700 rounded font-semibold">
                AI
              </span>
            )}
            {claim.verified && (
              <span className="text-xs px-1.5 py-0.5 bg-green-100 text-green-700 rounded font-semibold flex items-center gap-0.5">
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                </svg>
                Verified
              </span>
            )}
            {claim.risk && (
              <span className="text-xs px-1.5 py-0.5 bg-red-100 text-red-700 rounded font-semibold flex items-center gap-0.5">
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Risk
              </span>
            )}
            {claim.tier && (
              <span className="text-xs px-1.5 py-0.5 bg-blue-50 text-blue-600 rounded">
                Tier {claim.tier}
              </span>
            )}
          </div>
          <p className="text-sm text-gray-800 leading-relaxed">{claim.c}</p>
          {claim.src && (
            <p className="text-xs text-gray-400 mt-1">Source: {claim.src}</p>
          )}
          {claim.risk && (
            <p className="text-xs text-red-500 mt-1 italic">{claim.risk}</p>
          )}
        </div>
        {actions && <div className="flex gap-1 shrink-0">{actions}</div>}
      </div>
    </div>
  );
}
