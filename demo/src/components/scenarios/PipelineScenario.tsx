import { useState, useMemo, useCallback } from 'react';
import { PIPELINE_SCENARIO } from '../../lib/scenarios';
import { createUnit, addHop, type AKFUnit, type Claim } from '../../lib/akf';
import StepProgress from '../shared/StepProgress';
import AKFPeekPanel from '../shared/AKFPeekPanel';
import PipelineFlowDiagram from './PipelineScenario/PipelineFlowDiagram';
import TrustDashboard from './PipelineScenario/TrustDashboard';
import DecisionGate from './PipelineScenario/DecisionGate';

const STEPS = [
  { label: 'Sources', system: 'Data Ingestion' },
  { label: 'Dashboard', system: 'Power BI' },
  { label: 'Decision', system: 'Decision Gate' },
];

export default function PipelineScenario() {
  const [step, setStep] = useState(0);
  const [peekOpen, setPeekOpen] = useState(false);
  const [selectedUnit, setSelectedUnit] = useState<{ unit: AKFUnit; filename: string } | null>(null);

  // Build 3 separate AKF units from each source's claims
  const akfUnits = useMemo(() => {
    return PIPELINE_SCENARIO.sources.map((source) => {
      const unit = createUnit(source.claims as Claim[], {
        by: source.name,
        label: source.filename,
        meta: { sourceType: source.icon },
      });
      return addHop(unit, 'Pipeline Ingestion', 'ingested', {
        adds: source.claims.map((c) => c.id!),
      });
    });
  }, []);

  // Build a merged unit combining all claims
  const mergedUnit = useMemo(() => {
    const allClaims = PIPELINE_SCENARIO.sources.flatMap((s) => s.claims) as Claim[];
    const unit = createUnit(allClaims, {
      by: 'Pipeline Aggregator',
      label: 'merged-pipeline.akf',
      meta: {
        sourceCount: PIPELINE_SCENARIO.sources.length,
        question: PIPELINE_SCENARIO.decisionQuestion,
      },
    });
    let enriched = addHop(unit, 'AI Analysis', 'analyzed', {
      adds: allClaims.map((c) => c.id!),
    });
    enriched = addHop(enriched, 'Trust Dashboard', 'scored');
    return enriched;
  }, []);

  const allClaims = useMemo(() => {
    return PIPELINE_SCENARIO.sources.flatMap((s) => s.claims) as Claim[];
  }, []);

  const handleFlowComplete = useCallback(() => {
    setStep(1);
  }, []);

  const handleDashboardComplete = useCallback(() => {
    setStep(2);
  }, []);

  const handleDecisionComplete = useCallback(() => {
    // Final step done - decision recorded
  }, []);

  const handleViewAKF = useCallback(() => {
    if (step === 0) {
      // Show the first source unit or whichever makes sense
      setSelectedUnit({ unit: akfUnits[0], filename: PIPELINE_SCENARIO.sources[0].filename });
    } else {
      // Show merged unit for dashboard and decision steps
      setSelectedUnit({ unit: mergedUnit, filename: 'merged-pipeline.akf' });
    }
    setPeekOpen(true);
  }, [step, akfUnits, mergedUnit]);

  return (
    <div className="space-y-6 relative">
      {/* Step progress */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm px-6 py-4">
        <StepProgress steps={STEPS} current={step} />
      </div>

      {/* Step content */}
      {step === 0 && (
        <PipelineFlowDiagram onComplete={handleFlowComplete} />
      )}
      {step === 1 && (
        <TrustDashboard claims={allClaims} onComplete={handleDashboardComplete} />
      )}
      {step === 2 && (
        <DecisionGate
          claims={allClaims}
          question={PIPELINE_SCENARIO.decisionQuestion}
          onComplete={handleDecisionComplete}
        />
      )}

      {/* Floating "View .akf" button */}
      <button
        onClick={handleViewAKF}
        className="fixed bottom-6 left-6 z-40 flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg shadow-lg hover:bg-blue-700 active:bg-blue-800 transition-colors text-sm font-semibold"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        View .akf
      </button>

      {/* AKF Peek Panel */}
      <AKFPeekPanel
        unit={selectedUnit?.unit ?? null}
        open={peekOpen}
        onClose={() => setPeekOpen(false)}
        filename={selectedUnit?.filename}
      />
    </div>
  );
}
