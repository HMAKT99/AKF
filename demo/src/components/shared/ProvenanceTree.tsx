import type { ProvHop } from '../../lib/akf';

interface ProvenanceTreeProps {
  hops: ProvHop[];
}

export default function ProvenanceTree({ hops }: ProvenanceTreeProps) {
  if (hops.length === 0) return null;

  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
      <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
        Provenance Chain
      </h4>
      <div className="font-mono text-sm text-gray-700 space-y-1">
        {hops.map((hop, i) => {
          const indent = i === 0 ? '' : '\u00A0'.repeat(i * 2);
          const arrow = i === 0 ? '' : '\u2514\u2192 ';
          const time = new Date(hop.at).toLocaleTimeString();

          const addCount = hop.adds?.length ?? 0;
          const dropCount = hop.drops?.length ?? 0;

          return (
            <div key={i} className="flex items-start">
              <span className="text-gray-400 whitespace-pre">{indent}{arrow}</span>
              <span>
                <span className="text-blue-600 font-semibold">{hop.by}</span>
                {' '}
                <span className="text-gray-500">{hop.do}</span>
                {addCount > 0 && (
                  <span className="text-green-600 ml-1">(+{addCount} claims)</span>
                )}
                {dropCount > 0 && (
                  <span className="text-red-500 ml-1">(-{dropCount} rejected)</span>
                )}
                <span className="text-gray-300 text-xs ml-2">{time}</span>
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
