/**
 * Security detection demo — find risky AI claims.
 *
 * Run: npm run detect
 */

import { AKFBuilder, runAllDetections, toJSON } from "akf-format";

// Build a unit with some intentional red flags
const unit = new AKFBuilder()
  .claim("Patient diagnosis: Type 2 diabetes confirmed", 0.6, {
    tier: 4,
    ai: true,
    // No evidence, no review — detections should flag this
  })
  .claim("Treatment plan: Metformin 500mg twice daily", 0.55, {
    tier: 5,
    ai: true,
    risk: "AI-generated medical advice without physician review",
  })
  .agent("medical-ai-v2")
  .label("confidential")
  .build();

console.log("=== AKF Unit ===");
console.log(toJSON(unit, 2));

console.log("\n=== Running Security Detections ===");
const report = runAllDetections(unit);

console.log(`\nTriggered: ${report.triggeredCount}/10  Critical: ${report.criticalCount}  High: ${report.highCount}`);
console.log(`Clean: ${report.clean}`);

for (const r of report.results.filter((r) => r.triggered)) {
  console.log(`\n  [${r.severity.toUpperCase()}] ${r.detectionClass}`);
  for (const f of r.findings) {
    console.log(`    - ${f}`);
  }
  if (r.recommendation) console.log(`    → ${r.recommendation}`);
}
