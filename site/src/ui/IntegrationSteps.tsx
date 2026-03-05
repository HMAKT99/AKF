interface Step {
  title: string;
  description: string;
}

interface IntegrationStepsProps {
  steps: Step[];
}

export default function IntegrationSteps({ steps }: IntegrationStepsProps) {
  return (
    <div className="space-y-4">
      {steps.map((step, i) => (
        <div key={i} className="flex gap-4">
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-accent/20 text-accent flex items-center justify-center text-sm font-semibold">
            {i + 1}
          </div>
          <div>
            <div className="text-sm font-medium text-text-primary">{step.title}</div>
            <div className="text-sm text-text-secondary mt-0.5">{step.description}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
