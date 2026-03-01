import { useState, useEffect, useCallback } from "react";
import type { AKFUnit } from "../../lib/akf";
import { createUnit, addHop } from "../../lib/akf";
import { DEV_SCENARIO } from "../../lib/scenarios";
import StepProgress from "../shared/StepProgress";
import AKFPeekPanel from "../shared/AKFPeekPanel";
import IDEChatPanel from "./DeveloperScenario/IDEChatPanel";
import PRReviewPanel from "./DeveloperScenario/PRReviewPanel";
import CICDPanel from "./DeveloperScenario/CICDPanel";

const STEPS = [
  { label: "IDE Chat", system: "VS Code" },
  { label: "PR Review", system: "GitHub" },
  { label: "CI/CD Pipeline", system: "Azure Pipelines" },
];

export default function DeveloperScenario() {
  const [step, setStep] = useState<0 | 1 | 2>(0);
  const [akfUnit, setAkfUnit] = useState<AKFUnit | null>(null);
  const [peekOpen, setPeekOpen] = useState(false);

  // Build AKF unit when Copilot finishes (step 0 completes)
  const handleIDEComplete = useCallback(() => {
    const unit = createUnit(DEV_SCENARIO.claims, {
      by: "copilot",
      agent: "github-copilot",
      label: "caching-strategy",
      meta: { pr: DEV_SCENARIO.prNumber, question: DEV_SCENARIO.question },
    });
    setAkfUnit(unit);

    // Auto-advance to PR review after a brief delay
    setTimeout(() => setStep(1), 1200);
  }, []);

  // Add provenance hop when PR review completes
  const handlePRComplete = useCallback(() => {
    setAkfUnit((prev) => {
      if (!prev) return prev;
      return addHop(prev, "github-pr-review", "reviewed", {
        adds: prev.claims.map((c) => c.id!),
      });
    });

    // Auto-advance to CI/CD after a brief delay
    setTimeout(() => setStep(2), 1200);
  }, []);

  // Add provenance hop when CI/CD completes
  const handleCICDComplete = useCallback(() => {
    setAkfUnit((prev) => {
      if (!prev) return prev;
      return addHop(prev, "azure-pipelines", "consumed");
    });
  }, []);

  return (
    <div className="space-y-6">
      {/* Step progress bar */}
      <div className="bg-white border border-gray-200 rounded-lg px-6 py-4 shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-sm font-semibold text-gray-700">
            Developer Scenario
          </h2>
          <span className="text-xs text-gray-400">
            Step {step + 1} of {STEPS.length}
          </span>
        </div>
        <StepProgress steps={STEPS} current={step} />
      </div>

      {/* Active panel */}
      <div className="relative">
        {step === 0 && <IDEChatPanel onComplete={handleIDEComplete} />}
        {step === 1 && (
          <PRReviewPanel
            claims={DEV_SCENARIO.claims}
            onComplete={handlePRComplete}
          />
        )}
        {step === 2 && <CICDPanel onComplete={handleCICDComplete} />}
      </div>

      {/* Floating "View .akf" button */}
      {akfUnit && (
        <button
          onClick={() => setPeekOpen(true)}
          className="fixed bottom-6 right-6 z-40 flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg transition-all hover:shadow-xl active:scale-95"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"
            />
          </svg>
          <span className="text-sm font-semibold">View .akf</span>
        </button>
      )}

      {/* AKF Peek Panel */}
      <AKFPeekPanel
        unit={akfUnit}
        open={peekOpen}
        onClose={() => setPeekOpen(false)}
        filename="caching-strategy.akf"
      />
    </div>
  );
}
