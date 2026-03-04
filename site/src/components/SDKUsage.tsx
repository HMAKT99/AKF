import SectionHeading from '../ui/SectionHeading';
import TabSwitcher from '../ui/TabSwitcher';
import CodeBlock from '../ui/CodeBlock';
import IntegrationSteps from '../ui/IntegrationSteps';

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

# Initialize AKF in your project
akf.init(git_hooks=True, agent="my-pipeline")

# Read the trust metadata already embedded in any file
unit = akf.read("report.pdf")
print(unit.claims)        # who made it, what evidence backs it
print(unit.provenance)    # every agent hop, timestamped

# Audit when you need compliance
result = akf.audit("report.pdf")
akf.check_regulation("report.pdf", "eu_ai_act")
print(result.passed)      # True / False`;

const typescriptCode = `import { init, read, audit, checkRegulation } from 'akf';

// Initialize AKF in your project
init();  // hooks into your environment — Office, git, agents

// Read the trust metadata already embedded in any file
const unit = await read('report.pdf');
console.log(unit.claims);       // who made it, what evidence backs it
console.log(unit.provenance);   // every agent hop, timestamped

// Audit when you need compliance
const result = await audit('report.pdf');
await checkRegulation('report.pdf', 'eu_ai_act');
console.log(result.passed);     // true / false`;

const officeSteps = [
  {
    title: 'Install the add-in',
    description: 'Load the AKF add-in from the Office Add-ins store or sideload for development.',
  },
  {
    title: 'Save your document normally',
    description: 'AKF metadata embeds into the file as a Custom XML Part — no extra steps needed.',
  },
  {
    title: 'View the trust panel',
    description: 'Click "AKF > View Trust" in the ribbon to see claims, provenance, and trust scores.',
  },
  {
    title: 'Run a compliance audit',
    description: 'Click "AKF > Audit" to check provenance, classification, AI labeling, and more — 7 checks total.',
  },
];

const googleSteps = [
  {
    title: 'Install the add-on',
    description: 'Install AKF from the Google Workspace Marketplace for Docs, Sheets, or Slides.',
  },
  {
    title: 'Edit your document normally',
    description: 'AKF metadata is stored in Document Properties — it persists automatically with your file.',
  },
  {
    title: 'Open the sidebar',
    description: 'Go to AKF > View Trust to see claims with colored trust indicators and provenance timeline.',
  },
  {
    title: 'Run a compliance audit',
    description: 'AKF > Run Audit checks all 7 compliance criteria and gives actionable recommendations.',
  },
];

export default function SDKUsage() {
  const tabs = [
    {
      label: 'CLI',
      content: <CodeBlock code={cliCode} language="bash" filename="terminal" />,
    },
    {
      label: 'Office',
      content: (
        <div className="rounded-lg border border-gray-800 bg-gray-900 p-6">
          <div className="text-sm font-medium text-text-primary mb-1">Microsoft Office Add-in</div>
          <div className="text-xs text-text-secondary mb-5">Word, Excel, and PowerPoint — trust metadata in the ribbon</div>
          <IntegrationSteps steps={officeSteps} />
        </div>
      ),
    },
    {
      label: 'Google',
      content: (
        <div className="rounded-lg border border-gray-800 bg-gray-900 p-6">
          <div className="text-sm font-medium text-text-primary mb-1">Google Workspace Add-on</div>
          <div className="text-xs text-text-secondary mb-5">Docs, Sheets, and Slides — trust metadata in the sidebar</div>
          <IntegrationSteps steps={googleSteps} />
        </div>
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
