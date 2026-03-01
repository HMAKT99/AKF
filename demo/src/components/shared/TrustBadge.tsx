interface TrustBadgeProps {
  trust: number;
  size?: 'sm' | 'md';
}

export default function TrustBadge({ trust, size = 'sm' }: TrustBadgeProps) {
  const color =
    trust >= 0.8
      ? 'bg-green-500'
      : trust >= 0.5
        ? 'bg-amber-500'
        : 'bg-red-500';

  const textColor =
    trust >= 0.8
      ? 'text-green-700'
      : trust >= 0.5
        ? 'text-amber-700'
        : 'text-red-700';

  const dims = size === 'sm' ? 'w-3 h-3' : 'w-4 h-4';
  const textSize = size === 'sm' ? 'text-xs' : 'text-sm';

  return (
    <span className="inline-flex items-center gap-1.5">
      <span className={`${dims} rounded-full ${color} inline-block`} />
      <span className={`${textSize} font-semibold ${textColor}`}>
        {(trust * 100).toFixed(0)}%
      </span>
    </span>
  );
}
