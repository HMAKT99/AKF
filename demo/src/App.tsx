import { useState } from 'react';
import DeveloperScenario from './components/scenarios/DeveloperScenario';
import AnalystScenario from './components/scenarios/AnalystScenario';
import PipelineScenario from './components/scenarios/PipelineScenario';

const TABS = [
  {
    id: 'developer' as const,
    label: 'Developer',
    subtitle: 'Code \u2192 PR \u2192 CI/CD',
    description: 'AKF travels from IDE to GitHub to pipeline',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
      </svg>
    ),
  },
  {
    id: 'analyst' as const,
    label: 'Analyst',
    subtitle: 'Excel \u2192 Teams \u2192 Email DLP',
    description: 'AKF enforced at egress boundary',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
  },
  {
    id: 'pipeline' as const,
    label: 'Pipeline',
    subtitle: 'Sources \u2192 Dashboard \u2192 Decision',
    description: 'Multiple AKF units aggregated for decisions',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
      </svg>
    ),
  },
];

type TabId = (typeof TABS)[number]['id'];

function App() {
  const [activeTab, setActiveTab] = useState<TabId>('developer');

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm shrink-0">
        <div className="max-w-[1400px] mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                <span className="text-blue-600">AKF</span> Integration Demo
              </h1>
              <p className="text-sm text-gray-500 mt-0.5">
                Agent Knowledge Format — invisible metadata across real workflows
              </p>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs text-gray-400">
                AKF is auto-generated. Click "View .akf" to peek behind the curtain.
              </span>
              <span className="text-xs font-mono bg-blue-50 text-blue-600 px-3 py-1 rounded-full">
                v1.0
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Tab selector */}
      <nav className="bg-white border-b border-gray-100 shrink-0">
        <div className="max-w-[1400px] mx-auto px-6">
          <div className="flex gap-1">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-3 px-5 py-3.5 border-b-2 transition-all ${
                  activeTab === tab.id
                    ? 'border-blue-600 bg-blue-50/50'
                    : 'border-transparent hover:bg-gray-50 hover:border-gray-300'
                }`}
              >
                <span
                  className={`${
                    activeTab === tab.id ? 'text-blue-600' : 'text-gray-400'
                  }`}
                >
                  {tab.icon}
                </span>
                <div className="text-left">
                  <p
                    className={`text-sm font-semibold ${
                      activeTab === tab.id ? 'text-blue-700' : 'text-gray-700'
                    }`}
                  >
                    {tab.label}
                  </p>
                  <p
                    className={`text-xs ${
                      activeTab === tab.id ? 'text-blue-500' : 'text-gray-400'
                    }`}
                  >
                    {tab.subtitle}
                  </p>
                </div>
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Scenario content */}
      <main className="flex-1 overflow-hidden">
        {activeTab === 'developer' && <DeveloperScenario />}
        {activeTab === 'analyst' && <AnalystScenario />}
        {activeTab === 'pipeline' && <PipelineScenario />}
      </main>
    </div>
  );
}

export default App;
