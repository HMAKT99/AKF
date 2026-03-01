type SystemName =
  | 'vscode'
  | 'github'
  | 'word'
  | 'excel'
  | 'teams'
  | 'outlook'
  | 'azure-pipelines'
  | 'powerbi';

interface SystemBadgeProps {
  system: SystemName;
}

const SYSTEM_CONFIG: Record<SystemName, { color: string; label: string }> = {
  vscode:            { color: '#007ACC', label: 'VS Code' },
  github:            { color: '#24292e', label: 'GitHub' },
  word:              { color: '#2B579A', label: 'Word' },
  excel:             { color: '#217346', label: 'Excel' },
  teams:             { color: '#6264A7', label: 'Teams' },
  outlook:           { color: '#0078D4', label: 'Outlook' },
  'azure-pipelines': { color: '#0078D4', label: 'Azure Pipelines' },
  powerbi:           { color: '#F2C811', label: 'Power BI' },
};

export default function SystemBadge({ system }: SystemBadgeProps) {
  const config = SYSTEM_CONFIG[system];
  const textColor = system === 'powerbi' ? '#1a1a1a' : '#ffffff';

  return (
    <span
      className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold whitespace-nowrap"
      style={{ backgroundColor: config.color, color: textColor }}
    >
      {config.label}
    </span>
  );
}
