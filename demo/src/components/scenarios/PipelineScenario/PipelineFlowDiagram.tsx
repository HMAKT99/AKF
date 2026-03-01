import { useState, useEffect } from 'react';
import { PIPELINE_SCENARIO } from '../../../lib/scenarios';
import { effectiveTrust } from '../../../lib/akf';

interface PipelineFlowDiagramProps {
  onComplete: () => void;
}

const SOURCE_COLORS: Record<string, { border: string; bg: string; text: string }> = {
  'Market Data': { border: 'border-l-green-500', bg: 'bg-green-50', text: 'text-green-700' },
  'CRM Analysis': { border: 'border-l-amber-500', bg: 'bg-amber-50', text: 'text-amber-700' },
  'News Sentiment': { border: 'border-l-red-500', bg: 'bg-red-50', text: 'text-red-700' },
};

const SOURCE_ICONS: Record<string, React.ReactNode> = {
  chart: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
  ),
  users: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  ),
  news: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
    </svg>
  ),
};

export default function PipelineFlowDiagram({ onComplete }: PipelineFlowDiagramProps) {
  const { sources } = PIPELINE_SCENARIO;
  const [visibleSources, setVisibleSources] = useState<number[]>([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisComplete, setAnalysisComplete] = useState(false);

  useEffect(() => {
    const timers: ReturnType<typeof setTimeout>[] = [];

    sources.forEach((_, i) => {
      timers.push(
        setTimeout(() => {
          setVisibleSources((prev) => [...prev, i]);
        }, 500 + i * 500)
      );
    });

    timers.push(
      setTimeout(() => {
        setAnalyzing(true);
      }, 500 + sources.length * 500 + 300)
    );

    timers.push(
      setTimeout(() => {
        setAnalyzing(false);
        setAnalysisComplete(true);
      }, 500 + sources.length * 500 + 2000)
    );

    timers.push(
      setTimeout(() => {
        onComplete();
      }, 500 + sources.length * 500 + 2800)
    );

    return () => timers.forEach(clearTimeout);
  }, [sources, onComplete]);

  function avgTrust(claims: typeof sources[0]['claims']): number {
    if (claims.length === 0) return 0;
    const sum = claims.reduce((acc, cl) => acc + effectiveTrust(cl).score, 0);
    return sum / claims.length;
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-8">
      <h3 className="text-lg font-semibold text-gray-800 mb-6">Pipeline Ingestion</h3>

      <div className="flex items-stretch gap-6">
        {/* Left column: Source cards */}
        <div className="flex flex-col gap-4 w-64 shrink-0">
          {sources.map((source, i) => {
            const colors = SOURCE_COLORS[source.name];
            const visible = visibleSources.includes(i);
            return (
              <div
                key={source.name}
                className={`border-l-4 ${colors.border} rounded-lg border border-gray-200 p-4 transition-all duration-500 ${
                  visible
                    ? 'opacity-100 translate-x-0'
                    : 'opacity-0 -translate-x-6'
                }`}
              >
                <div className="flex items-center gap-2 mb-2">
                  <span className={colors.text}>
                    {SOURCE_ICONS[source.icon]}
                  </span>
                  <span className="text-sm font-semibold text-gray-800">{source.name}</span>
                </div>
                <p className="text-xs text-gray-500 font-mono mb-1">{source.filename}</p>
                <p className="text-xs text-gray-400">{source.claims.length} claims</p>
              </div>
            );
          })}
        </div>

        {/* Center: Animated connectors */}
        <div className="flex flex-col justify-center gap-4 w-24 shrink-0">
          {sources.map((_, i) => {
            const visible = visibleSources.includes(i);
            return (
              <div key={i} className="flex items-center h-[72px]">
                <div
                  className={`h-0.5 flex-1 transition-all duration-700 ${
                    visible ? 'bg-blue-400' : 'bg-gray-100'
                  }`}
                />
                <svg
                  className={`w-4 h-4 shrink-0 transition-all duration-700 ${
                    visible ? 'text-blue-400' : 'text-gray-200'
                  }`}
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </div>
            );
          })}
        </div>

        {/* Right: AI Analysis box */}
        <div className="flex-1 flex flex-col justify-center">
          <div
            className={`rounded-xl border-2 p-6 transition-all duration-500 ${
              analysisComplete
                ? 'border-green-300 bg-green-50'
                : analyzing
                  ? 'border-blue-300 bg-blue-50'
                  : 'border-gray-200 bg-gray-50'
            }`}
          >
            <div className="flex items-center gap-2 mb-4">
              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              <span className="text-sm font-semibold text-gray-800">AI Analysis</span>
              {analyzing && (
                <svg className="w-4 h-4 text-blue-500 animate-spin ml-auto" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
              )}
              {analysisComplete && (
                <svg className="w-5 h-5 text-green-500 ml-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                </svg>
              )}
            </div>

            {analyzing && (
              <p className="text-sm text-blue-600 animate-pulse">Analyzing sources...</p>
            )}

            {analysisComplete && (
              <div className="space-y-3">
                <p className="text-sm font-medium text-green-700">
                  Analysis complete — 6 claims extracted
                </p>
                <div className="space-y-2">
                  {sources.map((source) => {
                    const avg = avgTrust(source.claims);
                    const dotColor =
                      avg >= 0.8 ? 'bg-green-500' : avg >= 0.5 ? 'bg-amber-500' : 'bg-red-500';
                    return (
                      <div
                        key={source.name}
                        className="flex items-center justify-between text-xs"
                      >
                        <span className="text-gray-600">{source.name}</span>
                        <span className="flex items-center gap-1.5">
                          <span className={`w-2 h-2 rounded-full ${dotColor}`} />
                          <span className="font-semibold text-gray-700">
                            {(avg * 100).toFixed(0)}%
                          </span>
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {!analyzing && !analysisComplete && (
              <p className="text-sm text-gray-400">Waiting for sources...</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
