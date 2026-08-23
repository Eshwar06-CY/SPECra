import React from 'react';
import { Check } from 'lucide-react';

export interface WorkflowStep {
  id: string;
  label: string;
  tabKey: string;
}

interface WorkflowProgressProps {
  currentTab: string;
  onStepClick?: (tabKey: string) => void;
  completedTabs?: string[];
}

export const WORKFLOW_STEPS: WorkflowStep[] = [
  { id: 'upload', label: 'Upload', tabKey: 'upload' },
  { id: 'understand', label: 'Understand', tabKey: 'understand' },
  { id: 'requirements', label: 'Requirements', tabKey: 'requirements' },
  { id: 'process', label: 'Process', tabKey: 'process' },
  { id: 'results', label: 'Results', tabKey: 'results' },
  { id: 'export', label: 'Export', tabKey: 'export' },
];

export const WorkflowProgress: React.FC<WorkflowProgressProps> = ({
  currentTab,
  onStepClick,
  completedTabs = [],
}) => {
  const currentIndex = WORKFLOW_STEPS.findIndex((s) => s.tabKey === currentTab);

  return (
    <div className="w-full bg-slate-900/70 border border-slate-800/80 rounded-2xl p-4 mb-6 shadow-lg shadow-black/20 backdrop-blur-md">
      <div className="flex items-center justify-between max-w-4xl mx-auto px-2">
        {WORKFLOW_STEPS.map((step, idx) => {
          const isCurrent = step.tabKey === currentTab;
          const isCompleted =
            completedTabs.includes(step.tabKey) ||
            (currentIndex >= 0 && idx < currentIndex);
          const isClickable = onStepClick && (isCompleted || isCurrent);

          return (
            <React.Fragment key={step.id}>
              {/* Step Node */}
              <div
                onClick={() => isClickable && onStepClick(step.tabKey)}
                className={`flex items-center gap-2.5 transition-all ${
                  isClickable ? 'cursor-pointer group' : 'cursor-default'
                }`}
              >
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                    isCompleted
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 shadow-sm shadow-emerald-500/20'
                      : isCurrent
                      ? 'bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/30 scale-105 ring-4 ring-cyan-500/20'
                      : 'bg-slate-800 text-slate-500 border border-slate-700/60'
                  }`}
                >
                  {isCompleted ? (
                    <Check className="w-4 h-4 stroke-[3]" />
                  ) : (
                    <span>{idx + 1}</span>
                  )}
                </div>
                <span
                  className={`text-xs font-semibold hidden md:inline transition-colors ${
                    isCurrent
                      ? 'text-cyan-300'
                      : isCompleted
                      ? 'text-slate-200 group-hover:text-white'
                      : 'text-slate-500'
                  }`}
                >
                  {step.label}
                </span>
              </div>

              {/* Connecting Line */}
              {idx < WORKFLOW_STEPS.length - 1 && (
                <div
                  className={`flex-1 h-0.5 mx-2 md:mx-3 transition-colors ${
                    idx < currentIndex || isCompleted
                      ? 'bg-emerald-500/40'
                      : 'bg-slate-800'
                  }`}
                />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
