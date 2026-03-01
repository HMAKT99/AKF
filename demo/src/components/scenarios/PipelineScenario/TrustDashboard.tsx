import { useState, useEffect, useMemo } from 'react';
import type { Claim } from '../../../lib/akf';
import { effectiveTrust } from '../../../lib/akf';
import SystemBadge from '../../shared/SystemBadge';

interface TrustDashboardProps {
  claims: Claim[];
  onComplete: () => void;
}

export default function TrustDashboard({ claims, onComplete }: TrustDashboardProps) {
  const [visibleRows, setVisibleRows] = useState(0);
  const [loaded, setLoaded] = useState(false);

  const sortedClaims = useMemo(() => {
    return [...claims].sort((a, b) => effectiveTrust(b).score - effectiveTrust(a).score);
  }, [claims]);

  const metrics = useMemo(() => {
    const scores = claims.map((c) => effectiveTrust(c).score);
    const avg = scores.reduce((a, b) => a + b, 0) / scores.length;
    const highConf = scores.filter((s) => s > 0.7).length;
    const aiCount = claims.filter((c) => c.ai).length;
    return { total: claims.length, avg, highConf, aiCount };
  }, [claims]);

  const distribution = useMemo(() => {
    let accept = 0;
    let low = 0;
    let reject = 0;
    claims.forEach((c) => {
      const d = effectiveTrust(c).decision;
      if (d === 'ACCEPT') accept++;
      else if (d === 'LOW') low++;
      else reject++;
    });
    const total = claims.length;
    return {
      accept: { count: accept, pct: (accept / total) * 100 },
      low: { count: low, pct: (low / total) * 100 },
      reject: { count: reject, pct: (reject / total) * 100 },
    };
  }, [claims]);

  useEffect(() => {
    if (visibleRows >= sortedClaims.length) {
      const timer = setTimeout(() => {
        setLoaded(true);
        onComplete();
      }, 600);
      return () => clearTimeout(timer);
    }
    const timer = setTimeout(() => {
      setVisibleRows((v) => v + 1);
    }, 300);
    return () => clearTimeout(timer);
  }, [visibleRows, sortedClaims.length, onComplete]);

  function rowColor(score: number): string {
    if (score >= 0.7) return 'bg-green-50/60';
    if (score >= 0.4) return 'bg-amber-50/60';
    return 'bg-red-50/60';
  }

  function tierLabel(decision: 'ACCEPT' | 'LOW' | 'REJECT'): { text: string; cls: string } {
    switch (decision) {
      case 'ACCEPT':
        return { text: 'ACCEPT', cls: 'bg-green-100 text-green-700' };
      case 'LOW':
        return { text: 'LOW', cls: 'bg-amber-100 text-amber-700' };
      case 'REJECT':
        return { text: 'REJECT', cls: 'bg-red-100 text-red-700' };
    }
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-800">Trust Dashboard</h3>
        <SystemBadge system="powerbi" />
      </div>

      {/* Metric cards */}
      <div className="grid grid-cols-4 gap-4">
        <div className="rounded-lg border border-gray-200 p-4 text-center">
          <p className="text-2xl font-bold text-gray-800">{metrics.total}</p>
          <p className="text-xs text-gray-500 mt-1">Total Claims</p>
        </div>
        <div className="rounded-lg border border-gray-200 p-4 text-center">
          <p className="text-2xl font-bold text-blue-600">{(metrics.avg * 100).toFixed(0)}%</p>
          <p className="text-xs text-gray-500 mt-1">Average Trust</p>
        </div>
        <div className="rounded-lg border border-gray-200 p-4 text-center">
          <p className="text-2xl font-bold text-green-600">{metrics.highConf}</p>
          <p className="text-xs text-gray-500 mt-1">High Confidence (&gt;0.7)</p>
        </div>
        <div className="rounded-lg border border-gray-200 p-4 text-center">
          <p className="text-2xl font-bold text-amber-600">{metrics.aiCount}</p>
          <p className="text-xs text-gray-500 mt-1">AI-Generated</p>
        </div>
      </div>

      {/* Claims table */}
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="text-left px-4 py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">Claim</th>
              <th className="text-left px-4 py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">Source</th>
              <th className="text-center px-4 py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">Trust</th>
              <th className="text-center px-4 py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">Tier</th>
              <th className="text-center px-4 py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">AI?</th>
              <th className="text-center px-4 py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
            </tr>
          </thead>
          <tbody>
            {sortedClaims.map((claim, i) => {
              const et = effectiveTrust(claim);
              const tl = tierLabel(et.decision);
              const visible = i < visibleRows;
              return (
                <tr
                  key={claim.id || i}
                  className={`border-b border-gray-100 last:border-b-0 transition-all duration-500 ${
                    visible ? `opacity-100 ${rowColor(et.score)}` : 'opacity-0'
                  }`}
                >
                  <td className="px-4 py-3 max-w-[280px]">
                    <p className="text-gray-800 leading-snug truncate" title={claim.c}>
                      {claim.c}
                    </p>
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-500 whitespace-nowrap">{claim.src}</td>
                  <td className="px-4 py-3 text-center">
                    <span className="font-semibold text-gray-800">{(et.score * 100).toFixed(0)}%</span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className="text-xs px-1.5 py-0.5 bg-blue-50 text-blue-600 rounded">
                      Tier {claim.tier ?? 3}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    {claim.ai ? (
                      <span className="text-xs px-1.5 py-0.5 bg-amber-100 text-amber-700 rounded font-semibold">AI</span>
                    ) : (
                      <span className="text-xs text-gray-300">--</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={`text-xs px-2 py-0.5 rounded font-semibold ${tl.cls}`}>
                      {tl.text}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Trust distribution */}
      <div className="space-y-2">
        <h4 className="text-sm font-semibold text-gray-700">Trust Distribution</h4>
        <div className="flex h-6 rounded-full overflow-hidden border border-gray-200">
          {distribution.accept.pct > 0 && (
            <div
              className="bg-green-500 flex items-center justify-center transition-all duration-700"
              style={{ width: `${distribution.accept.pct}%` }}
            >
              <span className="text-[10px] font-bold text-white">
                ACCEPT ({distribution.accept.count})
              </span>
            </div>
          )}
          {distribution.low.pct > 0 && (
            <div
              className="bg-amber-400 flex items-center justify-center transition-all duration-700"
              style={{ width: `${distribution.low.pct}%` }}
            >
              <span className="text-[10px] font-bold text-white">
                LOW ({distribution.low.count})
              </span>
            </div>
          )}
          {distribution.reject.pct > 0 && (
            <div
              className="bg-red-500 flex items-center justify-center transition-all duration-700"
              style={{ width: `${distribution.reject.pct}%` }}
            >
              <span className="text-[10px] font-bold text-white">
                REJECT ({distribution.reject.count})
              </span>
            </div>
          )}
        </div>
        <div className="flex gap-4 text-xs text-gray-500">
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-full bg-green-500 inline-block" />
            Accept: {distribution.accept.count}
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-400 inline-block" />
            Low: {distribution.low.count}
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500 inline-block" />
            Reject: {distribution.reject.count}
          </span>
        </div>
      </div>

      {/* Loaded indicator */}
      {loaded && (
        <div className="flex items-center gap-2 text-sm text-green-600 animate-fade-in">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
          </svg>
          Dashboard loaded
        </div>
      )}
    </div>
  );
}
