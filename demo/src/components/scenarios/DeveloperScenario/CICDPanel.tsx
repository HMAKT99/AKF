import { useState, useEffect, useCallback } from "react";
import SystemBadge from "../../shared/SystemBadge";

interface CICDPanelProps {
  onComplete: () => void;
}

interface PipelineStage {
  name: string;
  delayMs: number;
  logLines?: string[];
}

const PIPELINE_STAGES: PipelineStage[] = [
  { name: "Checkout", delayMs: 300 },
  { name: "Build", delayMs: 500 },
  { name: "Test", delayMs: 800 },
  {
    name: "AKF: Consume Knowledge Artifact",
    delayMs: 600,
    logLines: [
      'Reading caching-strategy.akf...',
      'Validating 3 claims...',
      'Trust scores: 0.88, 0.375, 0.95',
      'Adding provenance hop: azure-pipelines \u2192 consumed',
      '\u2713 Knowledge artifact consumed',
    ],
  },
  { name: "Deploy", delayMs: 500 },
];

export default function CICDPanel({ onComplete }: CICDPanelProps) {
  const [completedStages, setCompletedStages] = useState<number>(-1);
  const [activeStageIndex, setActiveStageIndex] = useState<number>(0);
  const [visibleLogLines, setVisibleLogLines] = useState<number>(0);
  const [expandedStage, setExpandedStage] = useState<number | null>(null);
  const [pipelineDone, setPipelineDone] = useState(false);

  const currentStage = PIPELINE_STAGES[activeStageIndex];
  const isAKFStage = currentStage?.logLines && currentStage.logLines.length > 0;

  // Process stages sequentially
  const advanceStage = useCallback(() => {
    if (activeStageIndex >= PIPELINE_STAGES.length) return;

    const stage = PIPELINE_STAGES[activeStageIndex];

    if (stage.logLines && stage.logLines.length > 0 && visibleLogLines < stage.logLines.length) {
      // AKF stage: show log lines one at a time
      setExpandedStage(activeStageIndex);
      return; // Log line timer handles advancement
    }

    // Non-log stage or all log lines shown: complete after delay
    const timer = setTimeout(() => {
      setCompletedStages(activeStageIndex);

      if (activeStageIndex < PIPELINE_STAGES.length - 1) {
        setActiveStageIndex((prev) => prev + 1);
        setVisibleLogLines(0);
        setExpandedStage(null);
      } else {
        setPipelineDone(true);
      }
    }, stage.delayMs);

    return () => clearTimeout(timer);
  }, [activeStageIndex, visibleLogLines]);

  // Trigger stage advancement
  useEffect(() => {
    const cleanup = advanceStage();
    return cleanup;
  }, [advanceStage]);

  // Show log lines for AKF stage
  useEffect(() => {
    if (!isAKFStage) return;
    if (visibleLogLines >= currentStage.logLines!.length) {
      // All log lines shown, complete stage after brief pause
      const timer = setTimeout(() => {
        setCompletedStages(activeStageIndex);
        if (activeStageIndex < PIPELINE_STAGES.length - 1) {
          setActiveStageIndex((prev) => prev + 1);
          setVisibleLogLines(0);
          setExpandedStage(null);
        } else {
          setPipelineDone(true);
        }
      }, 600);
      return () => clearTimeout(timer);
    }

    const timer = setTimeout(() => {
      setVisibleLogLines((prev) => prev + 1);
    }, 400);

    return () => clearTimeout(timer);
  }, [isAKFStage, visibleLogLines, currentStage, activeStageIndex]);

  // Fire onComplete when pipeline finishes
  useEffect(() => {
    if (!pipelineDone) return;
    const timer = setTimeout(() => onComplete(), 1500);
    return () => clearTimeout(timer);
  }, [pipelineDone, onComplete]);

  return (
    <div className="rounded-lg overflow-hidden border border-gray-200 shadow-lg bg-white">
      {/* Header */}
      <div className="border-b border-gray-200 px-6 py-4 bg-gray-50">
        <div className="flex items-center gap-3 mb-2">
          <SystemBadge system="azure-pipelines" />
          <span className="text-xs text-gray-400 font-mono">CI/CD Pipeline</span>
        </div>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              feat/redis-caching — Build #1247
            </h2>
            <p className="text-xs text-gray-500 mt-0.5">
              Triggered by push to{" "}
              <code className="bg-gray-100 px-1 py-0.5 rounded text-blue-600">
                feat/redis-caching
              </code>
            </p>
          </div>
          <div className="flex items-center gap-2">
            {pipelineDone ? (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-800">
                <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
                </svg>
                Succeeded
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800">
                <svg className="w-3.5 h-3.5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Running
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Pipeline stages */}
      <div className="px-6 py-5 min-h-[400px]">
        <div className="space-y-1">
          {PIPELINE_STAGES.map((stage, i) => {
            const isCompleted = i <= completedStages;
            const isActive = i === activeStageIndex && !isCompleted;
            const isFuture = i > activeStageIndex;
            const isExpanded = expandedStage === i;

            return (
              <div key={i}>
                {/* Stage row */}
                <div
                  className={`flex items-center gap-3 px-4 py-2.5 rounded-lg transition-all duration-300 ${
                    isActive
                      ? "bg-blue-50 border border-blue-200"
                      : isCompleted
                        ? "bg-gray-50"
                        : "opacity-50"
                  }`}
                >
                  {/* Status icon */}
                  <div className="w-6 h-6 flex items-center justify-center shrink-0">
                    {isCompleted ? (
                      <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                      </svg>
                    ) : isActive ? (
                      <svg className="w-5 h-5 text-blue-500 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                    ) : (
                      <div className="w-4 h-4 rounded-full border-2 border-gray-300" />
                    )}
                  </div>

                  {/* Stage name */}
                  <span
                    className={`text-sm font-medium flex-1 ${
                      isCompleted
                        ? "text-gray-700"
                        : isActive
                          ? "text-blue-700"
                          : "text-gray-400"
                    }`}
                  >
                    {stage.name}
                  </span>

                  {/* Duration (mock) */}
                  {isCompleted && (
                    <span className="text-xs text-gray-400 font-mono">
                      {(stage.delayMs / 1000 + Math.random() * 0.5).toFixed(1)}s
                    </span>
                  )}
                </div>

                {/* Expanded log lines for AKF stage */}
                {isExpanded && stage.logLines && (
                  <div className="ml-10 mr-4 my-1 bg-gray-900 rounded-lg overflow-hidden">
                    <div className="p-3 font-mono text-xs leading-6">
                      {stage.logLines.slice(0, visibleLogLines).map((line, j) => {
                        const isLast = line.startsWith("\u2713");
                        const isTrust = line.startsWith("Trust scores");
                        const isHop = line.startsWith("Adding provenance");

                        return (
                          <div
                            key={j}
                            className={`animate-fade-in ${
                              isLast
                                ? "text-green-400 font-semibold"
                                : isTrust
                                  ? "text-amber-300"
                                  : isHop
                                    ? "text-sky-400"
                                    : "text-gray-400"
                            }`}
                          >
                            <span className="text-gray-600 select-none mr-2">
                              {String(j + 1).padStart(2, " ")} |
                            </span>
                            {line}
                          </div>
                        );
                      })}
                      {visibleLogLines < stage.logLines.length && (
                        <span className="inline-block w-2 h-4 bg-gray-500 animate-pulse" />
                      )}
                    </div>
                  </div>
                )}

                {/* Also show completed log for AKF stage */}
                {isCompleted && stage.logLines && i !== expandedStage && (
                  <div className="ml-10 mr-4 my-1 bg-gray-900 rounded-lg overflow-hidden">
                    <div className="p-3 font-mono text-xs leading-6">
                      {stage.logLines.map((line, j) => {
                        const isLast = line.startsWith("\u2713");
                        const isTrust = line.startsWith("Trust scores");
                        const isHop = line.startsWith("Adding provenance");

                        return (
                          <div
                            key={j}
                            className={`${
                              isLast
                                ? "text-green-400 font-semibold"
                                : isTrust
                                  ? "text-amber-300"
                                  : isHop
                                    ? "text-sky-400"
                                    : "text-gray-400"
                            }`}
                          >
                            <span className="text-gray-600 select-none mr-2">
                              {String(j + 1).padStart(2, " ")} |
                            </span>
                            {line}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Connector line between stages */}
                {i < PIPELINE_STAGES.length - 1 && !isFuture && (
                  <div className="ml-7 h-2 border-l-2 border-gray-200" />
                )}
              </div>
            );
          })}
        </div>

        {/* Pipeline complete banner */}
        {pipelineDone && (
          <div className="mt-6 border border-green-200 bg-green-50 rounded-lg px-5 py-4 flex items-center gap-3 animate-fade-in">
            <div className="w-10 h-10 rounded-full bg-green-500 flex items-center justify-center shrink-0">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-semibold text-green-800">
                Pipeline completed successfully
              </p>
              <p className="text-xs text-green-600 mt-0.5">
                AKF knowledge artifact consumed and provenance chain updated.
                All 5 stages passed.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
