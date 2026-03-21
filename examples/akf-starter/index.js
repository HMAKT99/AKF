/**
 * AKF Starter — stamp AI-generated content with trust metadata.
 *
 * Run: npm install && npm start
 */

import { AKFBuilder, toJSON, validate, effectiveTrust } from "akf-format";

// 1. Create an AKF unit with the fluent builder
const unit = new AKFBuilder()
  .claim("Revenue projected at $42.1B for FY2026", 0.85, {
    src: "financial-erp",
    tier: 2,
    ai: true,
  })
  .agent("gpt-4o")
  .label("internal")
  .evidence({ type: "document", detail: "10-K filing, page 47" })
  .build();

console.log("=== AKF Unit (compact JSON) ===");
console.log(toJSON(unit, 2));

// 2. Validate it
const result = validate(unit);
console.log("\n=== Validation ===");
console.log(`Valid: ${result.valid}  Level: ${result.level}/3`);
if (result.warnings.length) console.log("Warnings:", result.warnings);

// 3. Compute effective trust per claim
console.log("\n=== Trust Scores ===");
for (const claim of unit.claims) {
  const trust = effectiveTrust(claim);
  console.log(`Claim: "${claim.c}"`);
  console.log(`  Score: ${trust.score}  Decision: ${trust.decision}`);
  console.log(`  Breakdown:`, trust.breakdown);
}
