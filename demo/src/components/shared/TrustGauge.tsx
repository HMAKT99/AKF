interface TrustGaugeProps {
  score: number;
  label?: string;
}

export default function TrustGauge({ score, label }: TrustGaugeProps) {
  const percentage = Math.round(score * 100);

  const fillColor =
    score >= 0.7
      ? 'bg-green-500'
      : score >= 0.4
        ? 'bg-amber-500'
        : 'bg-red-500';

  const textColor =
    score >= 0.7
      ? 'text-green-700'
      : score >= 0.4
        ? 'text-amber-700'
        : 'text-red-700';

  const decision =
    score >= 0.7 ? 'ACCEPT' : score >= 0.4 ? 'LOW' : 'REJECT';

  const decisionBg =
    score >= 0.7
      ? 'bg-green-100 text-green-700'
      : score >= 0.4
        ? 'bg-amber-100 text-amber-700'
        : 'bg-red-100 text-red-700';

  return (
    <div className="space-y-1.5">
      {label && (
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-gray-600">{label}</span>
          <span className={`text-xs font-bold px-1.5 py-0.5 rounded ${decisionBg}`}>
            {decision}
          </span>
        </div>
      )}
      {!label && (
        <div className="flex items-center justify-end">
          <span className={`text-xs font-bold px-1.5 py-0.5 rounded ${decisionBg}`}>
            {decision}
          </span>
        </div>
      )}
      <div className="flex items-center gap-2">
        <div className="flex-1 h-2.5 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ease-out ${fillColor}`}
            style={{ width: `${percentage}%` }}
          />
        </div>
        <span className={`text-sm font-bold tabular-nums w-10 text-right ${textColor}`}>
          {percentage}%
        </span>
      </div>
    </div>
  );
}
