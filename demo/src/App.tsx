import { useState } from 'react';
import type { AKFUnit } from './lib/akf';
import AKFEditor from './components/AKFEditor';
import CopilotEnrich from './components/CopilotEnrich';
import PurviewProtect from './components/PurviewProtect';

const STEPS = [
  { num: 1, label: 'Create', description: 'Human authors claims' },
  { num: 2, label: 'Enrich', description: 'AI + human review' },
  { num: 3, label: 'Protect', description: 'Egress & DLP' },
];

function App() {
  const [currentStep, setCurrentStep] = useState(0);
  const [akfUnit, setAkfUnit] = useState<AKFUnit | null>(null);

  const canGoNext = (step: number): boolean => {
    if (step === 0) return akfUnit !== null;
    if (step === 1) return akfUnit !== null && akfUnit.prov.length >= 3;
    return false;
  };

  const handleStep1Complete = (unit: AKFUnit) => {
    setAkfUnit(unit);
  };

  const handleStep2Complete = (unit: AKFUnit) => {
    setAkfUnit(unit);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                <span className="text-blue-600">AKF</span> Hackathon Demo
              </h1>
              <p className="text-sm text-gray-500 mt-0.5">
                Agent Knowledge Format — 3-hop trust & provenance
              </p>
            </div>
            <span className="text-xs font-mono bg-blue-50 text-blue-600 px-3 py-1 rounded-full">
              v1.0
            </span>
          </div>
        </div>
      </header>

      {/* Stepper */}
      <nav className="bg-white border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Steps */}
            <div className="flex items-center gap-0 flex-1">
              {STEPS.map((step, i) => (
                <div key={i} className="flex items-center flex-1">
                  <button
                    onClick={() => {
                      // Allow going back to completed steps
                      if (i <= currentStep) setCurrentStep(i);
                    }}
                    className={`flex items-center gap-3 px-4 py-2 rounded-lg transition-all ${
                      i === currentStep
                        ? 'bg-blue-50'
                        : i < currentStep
                          ? 'hover:bg-gray-50 cursor-pointer'
                          : 'opacity-50 cursor-not-allowed'
                    }`}
                    disabled={i > currentStep}
                  >
                    <span
                      className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                        i < currentStep
                          ? 'bg-green-500 text-white'
                          : i === currentStep
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-200 text-gray-500'
                      }`}
                    >
                      {i < currentStep ? (
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                        </svg>
                      ) : (
                        step.num
                      )}
                    </span>
                    <div className="text-left">
                      <p
                        className={`text-sm font-semibold ${
                          i === currentStep ? 'text-blue-700' : 'text-gray-700'
                        }`}
                      >
                        {step.label}
                      </p>
                      <p className="text-xs text-gray-400">{step.description}</p>
                    </div>
                  </button>
                  {i < STEPS.length - 1 && (
                    <div
                      className={`h-0.5 flex-1 mx-2 ${
                        i < currentStep ? 'bg-green-400' : 'bg-gray-200'
                      }`}
                    />
                  )}
                </div>
              ))}
            </div>

            {/* Navigation buttons */}
            <div className="flex items-center gap-2 ml-4">
              <button
                onClick={() => setCurrentStep(s => s - 1)}
                disabled={currentStep === 0}
                className="px-4 py-2 text-sm font-semibold text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              >
                Back
              </button>
              <button
                onClick={() => setCurrentStep(s => s + 1)}
                disabled={!canGoNext(currentStep)}
                className="px-4 py-2 text-sm font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {currentStep === 0 && (
          <AKFEditor onComplete={handleStep1Complete} />
        )}
        {currentStep === 1 && akfUnit && (
          <CopilotEnrich unit={akfUnit} onComplete={handleStep2Complete} />
        )}
        {currentStep === 2 && akfUnit && (
          <PurviewProtect unit={akfUnit} />
        )}
      </main>
    </div>
  );
}

export default App;
