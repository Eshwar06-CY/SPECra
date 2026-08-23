import React from 'react';

export interface SpecraMarkProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | number;
  variant?: 'default' | 'light' | 'dark' | 'mono';
  className?: string;
  animated?: boolean;
}

export const SpecraMark: React.FC<SpecraMarkProps> = ({
  size = 'md',
  variant = 'default',
  className = '',
  animated = false,
}) => {
  const sizeMap = {
    xs: 18,
    sm: 24,
    md: 32,
    lg: 44,
    xl: 64,
  };

  const dim = typeof size === 'number' ? size : sizeMap[size] || 32;

  const getFills = () => {
    switch (variant) {
      case 'light':
      case 'mono':
        return {
          primary: '#FFFFFF',
          node: '#E2E8F0',
        };
      case 'dark':
        return {
          primary: '#090D16',
          node: '#2563EB',
        };
      case 'default':
      default:
        return {
          primary: 'url(#specraReactGrad)',
          node: '#38BDF8',
        };
    }
  };

  const fills = getFills();

  return (
    <svg
      width={dim}
      height={dim}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={`${animated ? 'transition-all duration-700 ease-out hover:scale-105' : ''} ${className}`}
      aria-label="SPECra Logo Mark"
    >
      <defs>
        <linearGradient id="specraReactGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#38BDF8" />
          <stop offset="50%" stopColor="#2563EB" />
          <stop offset="100%" stopColor="#06B6D4" />
        </linearGradient>
      </defs>

      {/* Top Segment: Data Intake & Structure */}
      <path
        d="M 22 28 C 22 20.268 28.268 14 36 14 L 74 14 C 79.523 14 84 18.477 84 24 C 84 29.523 79.523 34 74 34 L 44 34 C 38.477 34 34 38.477 34 44 C 34 45.1 34.18 46.16 34.5 47.15 L 23.8 42.5 C 22.65 38.1 22 33.2 22 28 Z"
        fill={fills.primary}
      />

      {/* Central Node: Synthesis & Intelligence */}
      <path
        d="M 38 48 L 56 36 L 68 44 L 50 56 Z"
        fill={fills.node}
        opacity={variant === 'default' ? 0.9 : 1}
      />

      {/* Bottom Segment: Normalized Output & Delivery */}
      <path
        d="M 78 72 C 78 79.732 71.732 86 64 86 L 26 86 C 20.477 86 16 81.523 16 76 C 16 70.477 20.477 66 26 66 L 56 66 C 61.523 66 66 61.523 66 56 C 66 54.9 65.82 53.84 65.5 52.85 L 76.2 57.5 C 77.35 61.9 78 66.8 78 72 Z"
        fill={fills.primary}
      />
    </svg>
  );
};
