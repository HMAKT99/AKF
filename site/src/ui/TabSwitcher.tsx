import { useState } from 'react';

interface Tab {
  label: string;
  content: React.ReactNode;
}

interface TabSwitcherProps {
  tabs: Tab[];
}

export default function TabSwitcher({ tabs }: TabSwitcherProps) {
  const [active, setActive] = useState(0);

  return (
    <div>
      <div className="flex gap-1 mb-4 bg-surface-overlay rounded-lg p-1 inline-flex">
        {tabs.map((tab, i) => (
          <button
            key={tab.label}
            onClick={() => setActive(i)}
            className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
              active === i
                ? 'bg-accent text-white'
                : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div>{tabs[active].content}</div>
    </div>
  );
}
