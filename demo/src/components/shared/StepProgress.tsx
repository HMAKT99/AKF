interface StepProgressProps {
  steps: { label: string; system: string }[];
  current: number;
}

export default function StepProgress({ steps, current }: StepProgressProps) {
  return (
    <div className="flex items-center justify-between w-full h-10">
      {steps.map((step, i) => {
        const isCompleted = i < current;
        const isCurrent = i === current;
        const isFuture = i > current;

        return (
          <div key={i} className="flex items-center flex-1 last:flex-none">
            {/* Dot + label */}
            <div className="flex flex-col items-center relative">
              <div
                className={`w-3.5 h-3.5 rounded-full border-2 transition-all duration-300 ${
                  isCompleted
                    ? 'bg-green-500 border-green-500'
                    : isCurrent
                      ? 'bg-blue-500 border-blue-500 animate-pulse'
                      : 'bg-gray-200 border-gray-300'
                }`}
              />
              <span
                className={`text-[10px] mt-0.5 whitespace-nowrap font-medium ${
                  isCompleted
                    ? 'text-green-600'
                    : isCurrent
                      ? 'text-blue-600'
                      : 'text-gray-400'
                }`}
              >
                {step.system}
              </span>
            </div>

            {/* Connecting line */}
            {i < steps.length - 1 && (
              <div
                className={`flex-1 h-0.5 mx-1.5 transition-colors duration-300 ${
                  isCompleted ? 'bg-green-400' : isFuture ? 'bg-gray-200' : 'bg-blue-300'
                }`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
