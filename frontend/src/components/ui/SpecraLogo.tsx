import React from 'react';
import { SpecraMark } from './SpecraMark';

export interface SpecraLogoProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'default' | 'light' | 'dark' | 'mono';
  layout?: 'horizontal' | 'stacked';
  showTagline?: boolean;
  className?: string;
}

export const SpecraLogo: React.FC<SpecraLogoProps> = ({
  size = 'md',
  variant = 'default',
  layout = 'horizontal',
  showTagline = false,
  className = '',
}) => {
  const markSizeMap = {
    sm: 'sm' as const,
    md: 'md' as const,
    lg: 'lg' as const,
    xl: 'xl' as const,
  };

  const textScaleMap = {
    sm: 'text-sm',
    md: 'text-lg',
    lg: 'text-2xl',
    xl: 'text-4xl',
  };

  const textColor = variant === 'dark' ? 'text-slate-900' : 'text-white';

  if (layout === 'stacked') {
    return (
      <div className={`flex flex-col items-center text-center space-y-2 select-none ${className}`}>
        <div className="p-2.5 rounded-2xl bg-slate-900/60 border border-slate-800/80 shadow-lg shadow-cyan-500/10">
          <SpecraMark size={size === 'xl' ? 'xl' : 'lg'} variant={variant} animated />
        </div>
        <div className="space-y-0.5">
          <span className={`${textScaleMap[size]} font-black tracking-tight ${textColor} flex items-center justify-center`}>
            SPEC<span className="text-cyan-400 font-bold">ra</span>
          </span>
          {showTagline && (
            <p className="text-[11px] text-slate-400 font-medium tracking-tight">
              Product intelligence, without the data chaos.
            </p>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className={`inline-flex items-center gap-2.5 select-none ${className}`}>
      <div className="p-1.5 rounded-xl bg-slate-900/60 border border-white/5 shadow-md shadow-cyan-500/10">
        <SpecraMark size={markSizeMap[size]} variant={variant} />
      </div>
      <div className="flex flex-col">
        <span className={`${textScaleMap[size]} font-black tracking-tight leading-none ${textColor} flex items-center gap-1`}>
          SPEC<span className="text-cyan-400 font-bold">ra</span>
        </span>
        {showTagline && (
          <span className="text-[10px] text-slate-400 font-medium tracking-tight mt-0.5">
            Product intelligence, without the data chaos.
          </span>
        )}
      </div>
    </div>
  );
};
