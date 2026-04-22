
import { clsx } from 'clsx';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  color?: 'primary' | 'secondary' | 'white';
  className?: string;
}

const sizeClasses = {
  sm: 'w-4 h-4',
  md: 'w-6 h-6',
  lg: 'w-8 h-8',
};

const colorClasses = {
  primary: 'border-primary-dark',
  secondary: 'border-quaternary',
  white: 'border-white',
};

export function LoadingSpinner({ 
  size = 'md', 
  color = 'primary', 
  className 
}: LoadingSpinnerProps) {
  return (
    <div
      className={clsx(
        'inline-block border-2 border-gray-300 border-t-transparent rounded-full animate-spin',
        sizeClasses[size],
        colorClasses[color],
        className
      )}
      role="status"
      aria-label="Loading"
    >
      <span className="sr-only">Loading...</span>
    </div>
  );
}
