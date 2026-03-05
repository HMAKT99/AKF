import SectionHeading from '../ui/SectionHeading';
import TabSwitcher from '../ui/TabSwitcher';
import CodeBlock from '../ui/CodeBlock';

const cliCode = `# Initialize AKF in your project
akf init --git-hooks --agent my-pipeline

# Trust metadata is already embedded — just read it
akf read report.pdf
akf read quarterly-deck.pptx

# See full provenance trail
akf provenance report.pdf

# Audit when you need compliance
akf audit report.pdf
akf audit report.pdf --regulation eu_ai_act
akf audit ./outputs/ --recursive`;

const pythonCode = `import akf

# Stamp any file with trust metadata
unit = akf.stamp_file("report.pdf",
    model="gpt-4o",
    claims=["Summary verified by legal team"],
    trust_score=0.92
)

# Read trust metadata from any file
unit = akf.read("report.pdf")
print(unit.trust_score)    # 0.92
print(unit.claims)         # who made it, what evidence backs it
print(unit.prov)           # every agent hop, timestamped

# Streaming — attach trust as content generates
with akf.stream("output.md", model="claude-4") as s:
    for chunk in llm.generate():
        s.write(chunk)     # trust metadata updates incrementally

# Audit for compliance
result = akf.audit("report.pdf", regulation="eu_ai_act")
print(result.compliant)    # True / False
print(result.recommendations)  # actionable next steps

# Run all 10 security detection classes
report = akf.run_all_detections("report.pdf")
print(report.triggered_count)  # number of detections fired`;

const typescriptCode = `import { stampFile, read, audit, stream, runAllDetections } from 'akf';

// Stamp any file with trust metadata
await stampFile('report.pdf', {
  model: 'gpt-4o',
  claims: ['Summary verified by legal team'],
  trustScore: 0.92,
});

// Read trust metadata from any file
const unit = await read('report.pdf');
console.log(unit.trustScore);    // 0.92
console.log(unit.claims);        // who made it, what evidence backs it
console.log(unit.prov);          // every agent hop, timestamped

// Streaming — attach trust as content generates
const s = stream('output.md', { model: 'claude-4' });
for await (const chunk of llm.generate()) {
  s.write(chunk);                // trust metadata updates incrementally
}
await s.close();

// Audit for compliance
const result = await audit('report.pdf', { regulation: 'eu_ai_act' });
console.log(result.compliant);   // true / false

// Run all 10 security detection classes
const report = await runAllDetections('report.pdf');
console.log(report.triggeredCount);  // number of detections fired`;

interface Feature {
  icon: React.ReactNode;
  label: string;
}

function IntegrationCard({
  appName,
  appSubtitle,
  appIcon,
  features,
  steps,
  ribbonLabel,
  ribbonItems,
}: {
  appName: string;
  appSubtitle: string;
  appIcon: React.ReactNode;
  features: Feature[];
  steps: { title: string; detail: string }[];
  ribbonLabel: string;
  ribbonItems: string[];
}) {
  return (
    <div className="rounded-lg border border-gray-700 overflow-hidden bg-gradient-to-b from-gray-800 to-gray-900">
      {/* Header bar */}
      <div className="flex items-center justify-between px-5 py-3.5 bg-gradient-to-r from-accent/15 to-transparent border-b border-gray-700">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-accent/20 text-accent flex items-center justify-center ring-1 ring-accent/30">
            {appIcon}
          </div>
          <div>
            <div className="text-sm font-semibold text-white">{appName}</div>
            <div className="text-[11px] text-gray-400">{appSubtitle}</div>
          </div>
        </div>
        <span className="px-2 py-0.5 rounded text-[10px] font-mono text-accent bg-accent/10 border border-accent/20 uppercase tracking-wider">AKF</span>
      </div>

      <div className="p-5">
        {/* Mock ribbon / menu */}
        <div className="rounded-lg border border-accent/20 bg-accent/5 px-4 py-3 mb-5">
          <div className="text-[10px] font-semibold text-accent uppercase tracking-wider mb-2.5">{ribbonLabel}</div>
          <div className="flex flex-wrap gap-2">
            {ribbonItems.map((item) => (
              <span
                key={item}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-gray-800 border border-gray-600 text-xs font-medium text-white shadow-sm hover:border-accent/40 transition-colors"
              >
                {item}
              </span>
            ))}
          </div>
        </div>

        {/* Feature badges */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-5">
          {features.map((f) => (
            <div key={f.label} className="flex items-center gap-2 rounded-lg bg-gray-800 border border-gray-700 px-3 py-2.5">
              <span className="text-emerald-400 shrink-0">{f.icon}</span>
              <span className="text-xs font-medium text-gray-200">{f.label}</span>
            </div>
          ))}
        </div>

        {/* Steps */}
        <div className="space-y-3">
          {steps.map((step, i) => (
            <div key={i} className="flex gap-3.5 items-start rounded-lg bg-gray-800/60 border border-gray-700/50 p-3.5">
              <div className="w-7 h-7 rounded-full bg-accent text-white flex items-center justify-center text-xs font-bold shrink-0">
                {i + 1}
              </div>
              <div>
                <div className="text-sm font-semibold text-white">{step.title}</div>
                <div className="text-xs text-gray-400 mt-1 leading-relaxed">{step.detail}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

const shieldIcon = (
  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
  </svg>
);
const eyeIcon = (
  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
    <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
  </svg>
);
const docIcon = (
  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
  </svg>
);
const chartIcon = (
  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
  </svg>
);

const officeIcon = (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
  </svg>
);

const notepadIcon = (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
  </svg>
);

const googleIcon = (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-1.605.42-3.113 1.157-4.418" />
  </svg>
);

export default function SDKUsage() {
  const tabs = [
    {
      label: 'CLI',
      content: <CodeBlock code={cliCode} language="bash" filename="terminal" />,
    },
    {
      label: 'MS Office',
      content: (
        <IntegrationCard
          appName="Microsoft Office Add-in"
          appSubtitle="Word, Excel, PowerPoint — trust metadata in the ribbon"
          appIcon={officeIcon}
          ribbonLabel="Ribbon Commands"
          ribbonItems={['View Trust', 'Stamp', 'Audit', 'Provenance', 'Settings']}
          features={[
            { icon: shieldIcon, label: 'Custom XML Part' },
            { icon: eyeIcon, label: 'Trust panel' },
            { icon: docIcon, label: '.docx .xlsx .pptx' },
            { icon: chartIcon, label: '10 audit checks' },
          ]}
          steps={[
            { title: 'Install the add-in', detail: 'One-click install from the Office Add-ins store. Available for Word, Excel, and PowerPoint on desktop and web.' },
            { title: 'Work as usual — AKF embeds automatically', detail: 'Trust metadata is stored as a Custom XML Part inside your document. No extra save steps, no sidecar files.' },
            { title: 'View trust scores in the panel', detail: 'Click "AKF > View Trust" in the ribbon to see claims, provenance chain, trust scores with color indicators, and AI labeling status.' },
            { title: 'Run compliance audit on demand', detail: 'Click "AKF > Audit" to run all 10 compliance checks — provenance, integrity hash, classification, sourcing, AI labeling, risk disclosure, structure, origin tracking, review status, and freshness.' },
          ]}
        />
      ),
    },
    {
      label: 'Google Workspace',
      content: (
        <IntegrationCard
          appName="Google Workspace Add-on"
          appSubtitle="Docs, Sheets, Slides — trust metadata in the sidebar"
          appIcon={googleIcon}
          ribbonLabel="Sidebar Actions"
          ribbonItems={['View Trust', 'Stamp', 'Audit', 'Provenance', 'Export']}
          features={[
            { icon: shieldIcon, label: 'Document Properties' },
            { icon: eyeIcon, label: 'Trust sidebar' },
            { icon: docIcon, label: 'Docs, Sheets, Slides' },
            { icon: chartIcon, label: '10 audit checks' },
          ]}
          steps={[
            { title: 'Install the add-on', detail: 'Install from the Google Workspace Marketplace. Works across Docs, Sheets, and Slides with a unified sidebar experience.' },
            { title: 'Edit normally — metadata persists automatically', detail: 'AKF metadata is stored in Document Properties. It travels with the file on export and survives re-imports.' },
            { title: 'Open the trust sidebar', detail: 'Go to Extensions > AKF > View Trust to see claims with colored trust indicators, provenance timeline, and AI content breakdown.' },
            { title: 'Run compliance audit', detail: 'Extensions > AKF > Run Audit checks all 10 compliance criteria with actionable recommendations and exportable reports.' },
          ]}
        />
      ),
    },
    {
      label: 'Python',
      content: <CodeBlock code={pythonCode} language="python" filename="example.py" />,
    },
    {
      label: 'TypeScript',
      content: <CodeBlock code={typescriptCode} language="typescript" filename="example.ts" />,
    },
    {
      label: 'Notepad',
      content: (
        <IntegrationCard
          appName="Notepad & Plain Text Editors"
          appSubtitle="Vim, Nano, Notepad, Notepad++ — sidecar trust for any file"
          appIcon={notepadIcon}
          ribbonLabel="CLI Commands"
          ribbonItems={['akf stamp', 'akf read', 'akf audit', 'akf provenance']}
          features={[
            { icon: shieldIcon, label: 'Sidecar .akf.json' },
            { icon: eyeIcon, label: 'CLI viewer' },
            { icon: docIcon, label: '.txt .csv .log any' },
            { icon: chartIcon, label: 'Full audit support' },
          ]}
          steps={[
            { title: 'Edit your file in any text editor', detail: 'Use Notepad, Vim, Nano, or any editor you like. AKF doesn\'t need a plugin — it works alongside your files.' },
            { title: 'Stamp with the CLI', detail: 'Run "akf stamp notes.txt" to create a companion .akf.json sidecar file with trust metadata, provenance, and claims.' },
            { title: 'Read trust metadata anytime', detail: 'Run "akf read notes.txt" to see trust scores, claims, and provenance — the CLI finds the sidecar automatically.' },
            { title: 'Audit for compliance', detail: 'Run "akf audit notes.txt" for full compliance checks. Works identically to native formats — same 10 checks, same reports.' },
          ]}
        />
      ),
    },
  ];

  return (
    <section id="sdk" className="py-20 px-6">
      <div className="max-w-4xl mx-auto">
        <SectionHeading
          title="Get started in minutes"
          subtitle="Install, init, done. Trust metadata flows automatically — read or audit it whenever you need to."
        />
        <TabSwitcher tabs={tabs} />
      </div>
    </section>
  );
}
