import { useState, useCallback, useMemo } from "react";
import { ANALYST_SCENARIO } from "../../lib/scenarios";
import { createUnit, addHop } from "../../lib/akf";
import type { AKFUnit } from "../../lib/akf";
import StepProgress from "../shared/StepProgress";
import AKFPeekPanel from "../shared/AKFPeekPanel";
import OfficeMock from "./AnalystScenario/OfficeMock";
import TeamsSharePanel from "./AnalystScenario/TeamsSharePanel";
import OutlookComposePanel from "./AnalystScenario/OutlookComposePanel";

const STEPS = [
  { label: "Excel + Copilot Analysis", system: "Excel" },
  { label: "Teams Share", system: "Teams" },
  { label: "Outlook Share", system: "Outlook" },
];

export default function AnalystScenario() {
  const [step, setStep] = useState<0 | 1 | 2>(0);
  const [peekOpen, setPeekOpen] = useState(false);

  // Create AKF unit from scenario claims on mount
  const baseUnit = useMemo(
    () =>
      createUnit(ANALYST_SCENARIO.claims, {
        by: ANALYST_SCENARIO.author,
        label: "confidential",
        agent: "Microsoft 365 Copilot",
      }),
    []
  );

  // Build the unit with provenance hops based on current step
  const akfUnit: AKFUnit = useMemo(() => {
    let u = baseUnit;
    if (step >= 1) {
      u = addHop(u, "sarah@woodgrove.com", "shared-internal", {
        pen: 0,
      });
    }
    if (step >= 2) {
      u = addHop(u, "outlook-dlp@woodgrove.com", "blocked-external", {
        pen: -20,
      });
    }
    return u;
  }, [baseUnit, step]);

  const handleExcelComplete = useCallback(() => {
    setStep(1);
  }, []);

  const handleTeamsComplete = useCallback(() => {
    setStep(2);
  }, []);

  const handleOutlookComplete = useCallback(() => {
    // Final step — scenario is complete, no further navigation
  }, []);

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 relative">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-1">Analyst Scenario</h2>
        <p className="text-sm text-gray-500">
          Excel analysis with Copilot, internal Teams share, and external email blocked by DLP.
        </p>
      </div>

      {/* Step progress */}
      <div className="mb-8 bg-white border border-gray-200 rounded-xl px-6 py-4 shadow-sm">
        <StepProgress steps={STEPS} current={step} />
      </div>

      {/* Step content */}
      <div className="relative">
        {step === 0 && <OfficeMock onComplete={handleExcelComplete} />}
        {step === 1 && (
          <TeamsSharePanel
            docTitle={ANALYST_SCENARIO.docTitle}
            onComplete={handleTeamsComplete}
          />
        )}
        {step === 2 && (
          <OutlookComposePanel
            unit={akfUnit}
            onComplete={handleOutlookComplete}
          />
        )}
      </div>

      {/* Floating "View .akf" button */}
      <button
        onClick={() => setPeekOpen(true)}
        className="fixed bottom-6 right-6 z-40 flex items-center gap-2 bg-gray-900 text-white pl-4 pr-5 py-3 rounded-full shadow-lg hover:bg-gray-800 hover:shadow-xl transition-all duration-200 group"
      >
        <svg
          className="w-5 h-5 text-blue-400 group-hover:text-blue-300 transition-colors"
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
        <span className="text-xs text-gray-400 ml-1">
          {akfUnit.prov?.length ?? 0} hop{(akfUnit.prov?.length ?? 0) !== 1 ? "s" : ""}
        </span>
      </button>

      {/* AKF Peek Panel */}
      <AKFPeekPanel
        unit={akfUnit}
        open={peekOpen}
        onClose={() => setPeekOpen(false)}
        filename="Woodgrove-Q3-Analysis.akf"
      />
    </div>
  );
}
