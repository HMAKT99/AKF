export interface TrustThresholds {
  high: number;
  medium: number;
}

export type TrustBucket = "high" | "medium" | "low";

export function trustBucket(score: number, thresholds: TrustThresholds): TrustBucket {
  if (score >= thresholds.high) return "high";
  if (score >= thresholds.medium) return "medium";
  return "low";
}

export function trustColor(bucket: TrustBucket): string {
  switch (bucket) {
    case "high": return "#22c55e";
    case "medium": return "#eab308";
    case "low": return "#ef4444";
  }
}

export function trustEmoji(bucket: TrustBucket): string {
  switch (bucket) {
    case "high": return "\u{1F7E2}";   // green circle
    case "medium": return "\u{1F7E1}"; // yellow circle
    case "low": return "\u{1F534}";    // red circle
  }
}

export function trustLabel(bucket: TrustBucket): string {
  switch (bucket) {
    case "high": return "High";
    case "medium": return "Medium";
    case "low": return "Low";
  }
}

export function formatDate(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export function classificationColor(label: string): string {
  switch (label.toLowerCase()) {
    case "public": return "#22c55e";
    case "internal": return "#3b82f6";
    case "confidential": return "#f97316";
    case "restricted": return "#ef4444";
    default: return "#6b7280";
  }
}
