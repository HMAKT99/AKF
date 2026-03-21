/**
 * Trust scoring demo — see how different inputs affect trust.
 *
 * Run: npm run trust
 */

import { effectiveTrust } from "akf-format";

const scenarios = [
  {
    name: "Expert human review (tier 1)",
    claim: { c: "Quarterly earnings beat estimates by 12%", t: 0.95, tier: 1, ai: false, src: "sec-filing", id: "a" },
  },
  {
    name: "AI-generated, medium confidence (tier 3)",
    claim: { c: "Customer churn expected to decrease 8%", t: 0.72, tier: 3, ai: true, src: "analytics-pipeline", id: "b" },
  },
  {
    name: "Speculative AI claim (tier 5)",
    claim: { c: "Market could reach $100B by 2030", t: 0.4, tier: 5, ai: true, src: "web-scrape", id: "c" },
  },
];

for (const s of scenarios) {
  const result = effectiveTrust(s.claim);

  console.log(`\n--- ${s.name} ---`);
  console.log(`Claim:    ${s.claim.c}`);
  console.log(`Raw:      ${s.claim.t}  →  Effective: ${result.score}`);
  console.log(`Decision: ${result.decision}`);
  console.log(`Breakdown:`, result.breakdown);
}
